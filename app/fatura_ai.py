import os, json, base64, re
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

SISTEM_PROMPT = """Sen bir fatura analiz uzmanısın. Sana verilen PDF faturasından aşağıdaki bilgileri çıkar ve SADECE geçerli JSON döndür, başka hiçbir şey yazma.

Çıkarılacak JSON formatı:
{
  "fatura_no": "string veya null",
  "fatura_tarihi": "YYYY-MM-DD veya null",
  "vade_tarihi": "YYYY-MM-DD veya null",
  "tedarikci_adi": "string",
  "ara_toplam": number veya null,
  "iskonto_tutari": number veya null,
  "iskonto_orani": number veya null,
  "kdv_tutari": number veya null,
  "genel_toplam": number veya null,
  "para_birimi": "TL veya USD veya EUR",
  "kalemler": [
    {
      "malzeme_adi": "string",
      "miktar": number,
      "birim": "string",
      "liste_fiyati": number,
      "iskonto_orani": number veya null,
      "iskonto_tutari": number veya null,
      "br_fiyat": number,
      "kdv_orani": number veya null,
      "toplam_fiyat": number
    }
  ],
  "guven_skoru": 0.0-1.0
}

Kurallar:
- Tarihleri YYYY-MM-DD formatına çevir
- Sayıları virgüllü Türk formatından (1.234,56) float'a çevir (1234.56)
- Bulamadığın alanlar için null kullan
- liste_fiyati: iskonto uygulanmadan önceki birim fiyat
- br_fiyat: iskonto uygulandıktan sonraki net birim fiyat (KDV hariç)
- Eğer faturada iskonto/indirim satırı varsa mutlaka kaydet
- guven_skoru: verinin ne kadar net okunabildiğinin tahmini (0=çok belirsiz, 1=çok net)"""

def pdf_oku(dosya_yolu: str, tedarikci_ornegi: str = None) -> dict:
    """PDF faturayı okur, AI ile analiz eder, dict döndürür."""
    with open(dosya_yolu, 'rb') as f:
        pdf_data = base64.standard_b64encode(f.read()).decode('utf-8')

    mesajlar = []

    # Tedarikçi hafızası varsa örnek olarak ekle
    if tedarikci_ornegi:
        mesajlar.append({
            "role": "user",
            "content": f"Bu tedarikçiden daha önce işlenen fatura örneği:\n{tedarikci_ornegi}\nBu formatı referans al."
        })
        mesajlar.append({
            "role": "assistant",
            "content": "Anladım, bu tedarikçinin formatını referans alacağım."
        })

    mesajlar.append({
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data
                }
            },
            {
                "type": "text",
                "text": "Bu faturayı analiz et ve istenen JSON formatında çıktı ver."
            }
        ]
    })

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=SISTEM_PROMPT,
        messages=mesajlar
    )

    content = response.content[0].text.strip()
    
    # JSON bloğunu daha güvenli şekilde ayıkla (Markdown içindeyse)
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        content = json_match.group(0)
    
    return json.loads(content)


def net_birim_fiyat(kalem: dict) -> float:
    """Fatura kaleminden KDV hariç, iskonto uygulanmış net birim fiyatı hesaplar.

    Öncelik sırası:
    1. br_fiyat varsa direkt kullan (AI zaten net fiyatı verdi)
    2. liste_fiyati + iskonto varsa hesapla
    3. toplam_fiyat / miktar dan türet
    """
    br = kalem.get('br_fiyat') or 0
    liste = kalem.get('liste_fiyati') or 0
    iskonto_oran = kalem.get('iskonto_orani') or 0
    iskonto_tutar = kalem.get('iskonto_tutari') or 0
    miktar = kalem.get('miktar') or 1
    toplam = kalem.get('toplam_fiyat') or 0
    kdv = kalem.get('kdv_orani') or 0

    if br > 0:
        net = br
    elif liste > 0 and iskonto_oran > 0:
        net = liste * (1 - iskonto_oran / 100)
    elif liste > 0 and iskonto_tutar > 0:
        net = liste - (iskonto_tutar / miktar)
    elif toplam > 0 and miktar > 0:
        net = toplam / miktar
        # toplam KDV dahilse temizle
        if kdv > 0:
            net = net / (1 + kdv / 100)
    else:
        return 0

    return round(net, 4)


def _normalize_anahtar(ad: str) -> str:
    """Hafıza anahtarı için normalize et — küçük harf, boşluk temizle."""
    return re.sub(r'\s+', ' ', (ad or '').lower().strip())


def hafizaya_kaydet(fatura_kalem_adi: str, talep_kalem_adi: str):
    """Onaylanan eşleşmeyi öğrenme hafızasına kaydeder veya sayacı artırır."""
    from app import db
    from sqlalchemy import text
    fk = _normalize_anahtar(fatura_kalem_adi)
    tk = _normalize_anahtar(talep_kalem_adi)
    if not fk or not tk:
        return
    try:
        with db.engine.connect() as conn:
            mevcut = conn.execute(
                text("SELECT id, eslesme_sayisi FROM eslestirme_hafizasi WHERE fatura_kalem_adi=:fk AND talep_kalem_adi=:tk"),
                {"fk": fk, "tk": tk}
            ).fetchone()
            if mevcut:
                conn.execute(
                    text("UPDATE eslestirme_hafizasi SET eslesme_sayisi=eslesme_sayisi+1, son_guncelleme=CURRENT_TIMESTAMP WHERE id=:id"),
                    {"id": mevcut[0]}
                )
            else:
                conn.execute(
                    text("INSERT INTO eslestirme_hafizasi (fatura_kalem_adi, talep_kalem_adi) VALUES (:fk, :tk)"),
                    {"fk": fk, "tk": tk}
                )
            conn.commit()
    except Exception:
        pass


def hafizadan_bul(fatura_kalem_adi: str) -> list:
    """Bu fatura kalemi için daha önce eşleştirilmiş talep kalem adlarını döndürür."""
    from app import db
    from sqlalchemy import text
    fk = _normalize_anahtar(fatura_kalem_adi)
    try:
        with db.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT talep_kalem_adi, eslesme_sayisi FROM eslestirme_hafizasi WHERE fatura_kalem_adi=:fk ORDER BY eslesme_sayisi DESC LIMIT 5"),
                {"fk": fk}
            ).fetchall()
            return [(r[0], r[1]) for r in rows]
    except Exception:
        return []


_STOP_WORDS = {'ve', 'ile', 'için', 'adet', 'kg', 'mt', 'mm', 'cm', 'm', 'lt', 'gr',
               'no', 'no.', 'tip', 'std', 'st', 'the', 'a', 'an', 'of', '-', '/', '*'}

_MALZEME_GRUPLARI = [
    {'sac', 'levha', 'plaka', 'sheet', 'plate'},
    {'boru', 'pipe', 'tüp', 'tube'},
    {'profil', 'köşebent', 'lama', 'kare', 'yuvarlak', 'çubuk', 'bar'},
    {'civata', 'somun', 'vida', 'cıvata', 'bolt', 'nut', 'screw'},
    {'kayış', 'zincir', 'chain', 'belt'},
    {'rulman', 'bearing', 'yataklama'},
    {'yağ', 'gres', 'oil', 'grease'},
    {'boya', 'astar', 'paint', 'primer'},
    {'elektrod', 'kaynak', 'welding'},
]


def _urun_grubu(ad: str) -> int:
    """Ürün adından malzeme grubunu döndürür. Aynı gruptaki ürünler daha yüksek skor alır."""
    ad_lower = ad.lower()
    for i, grup in enumerate(_MALZEME_GRUPLARI):
        if any(k in ad_lower for k in grup):
            return i
    return -1


def _normalize(ad: str) -> set:
    """Ürün adını normalleştirir: küçük harf, stop word temizle, rakamları koru."""
    import re
    ad = ad.lower()
    # Teknik kodları kelimeye böl: ST37/S235 → {st37, s235}
    ad = re.sub(r'[/*]', ' ', ad)
    kelimeler = set(ad.split()) - _STOP_WORDS
    return kelimeler


def _eslesme_skoru(fk_ad: str, tk_ad: str, fk_birim: str, tk_birim: str) -> float:
    """İki ürün adı arasındaki benzerlik skorunu hesaplar (0-1)."""
    fk_set = _normalize(fk_ad)
    tk_set = _normalize(tk_ad)

    if not fk_set or not tk_set:
        return 0

    # Ortak kelime oranı
    ortak = fk_set & tk_set
    birlesim = fk_set | tk_set
    jaccard = len(ortak) / len(birlesim)

    # Kısa ürün adı uzun adın içinde geçiyor mu? (örn. "SAC" → "SICAK HAD. PAKET SAC")
    kisa = min(fk_set, tk_set, key=len)
    uzun = max(fk_set, tk_set, key=len)
    icerik_skoru = len(kisa & uzun) / max(len(kisa), 1)

    # Birim eşleşmesi bonus
    birim_bonus = 0.15 if (fk_birim or '').lower() == (tk_birim or '').lower() else 0

    # Malzeme grubu bonus
    grup_bonus = 0.1 if _urun_grubu(fk_ad) == _urun_grubu(tk_ad) >= 0 else 0

    skor = max(jaccard, icerik_skoru) + birim_bonus + grup_bonus
    return min(skor, 1.0)


def siparis_eslestir(fatura_kalemler: list, talep_kalemleri: list) -> list:
    """Fatura kalemlerini sipariş kalemleriyle eşleştirir.
    Fiyat karşılaştırması: KDV hariç, iskonto uygulanmış net birim fiyat."""
    sonuclar = []
    for fk in fatura_kalemler:
        en_iyi = None
        en_iyi_skor = 0
        fk_ad = fk.get('malzeme_adi') or ''
        fk_birim = fk.get('birim') or ''

        # Önce hafızaya bak
        hafiza_eslesimleri = hafizadan_bul(fk_ad)
        hafiza_aday = {_normalize_anahtar(tk_ad): sayi for tk_ad, sayi in hafiza_eslesimleri}

        for tk in talep_kalemleri:
            tk_ad = tk.malzeme_adi or ''
            tk_birim = tk.birim or ''
            skor = _eslesme_skoru(fk_ad, tk_ad, fk_birim, tk_birim)

            # Hafıza bonusu — ne kadar çok onaylandıysa o kadar güçlü
            tk_norm = _normalize_anahtar(tk_ad)
            if tk_norm in hafiza_aday:
                onay_sayisi = hafiza_aday[tk_norm]
                skor = min(1.0, skor + min(0.5, 0.1 * onay_sayisi))

            if skor > en_iyi_skor:
                en_iyi_skor = skor
                en_iyi = tk

        durum = 'eslesmiyor'
        not_ = ''
        tk_id = None

        if en_iyi and en_iyi_skor > 0.15:
            tk_id = en_iyi.id
            fatura_net = net_birim_fiyat(fk)
            siparis_net = en_iyi.br_fiyat or 0

            if siparis_net > 0 and fatura_net > 0:
                fark = abs(fatura_net - siparis_net)
                yuzde = fark / siparis_net * 100

                iskonto_notu = ''
                if fk.get('iskonto_orani') or fk.get('iskonto_tutari'):
                    liste = fk.get('liste_fiyati') or fk.get('br_fiyat') or 0
                    oran = fk.get('iskonto_orani') or 0
                    iskonto_notu = f" (Liste: {liste:.2f}, İskonto: %{oran})"

                if yuzde > 5:
                    durum = 'fiyat_farki'
                    not_ = (f"Siparişteki net br. fiyat: {siparis_net:.2f} | "
                            f"Faturadaki net br. fiyat: {fatura_net:.2f}"
                            f"{iskonto_notu} | Fark: %{yuzde:.1f}")
                else:
                    durum = 'eslesti'
                    if iskonto_notu:
                        not_ = f"İskontolu fiyat eşleşti{iskonto_notu}"
            else:
                durum = 'eslesti'

        sonuclar.append({
            'fatura_kalem': fk,
            'talep_kalem_id': tk_id,
            'eslesme_durumu': durum,
            'eslesme_notu': not_
        })
    return sonuclar
