"""
Malzeme Listesi AI Import Scripti
Çalıştır: python malzeme_import.py
"""

import requests, csv, io, os, json, sys, time
import anthropic

# ── AYARLAR ────────────────────────────────────────────────────────────────
SHEETS_URL = 'https://docs.google.com/spreadsheets/d/1XK6NT73wyhERitYle4A60a5X1VpskuJ6/export?format=csv'
BATCH_SIZE = 40       # Her AI çağrısında kaç malzeme işlensin
STOK_KOD_BASLANGIC = 1
# ───────────────────────────────────────────────────────────────────────────

def csv_indir():
    print("CSV indiriliyor...")
    r = requests.get(SHEETS_URL, allow_redirects=True, timeout=30)
    r.raise_for_status()
    return r.content.decode('utf-8-sig')

def malzemeleri_cek(icerik):
    reader = csv.reader(io.StringIO(icerik))
    rows = list(reader)
    print(f"Toplam satır: {len(rows)}")
    malzemeler = []
    for row in rows[1:]:
        if len(row) < 13:
            continue
        k = row[9].strip()   # Malzeme Adı
        l = row[10].strip()  # Marka/Model
        m = row[11].strip()  # Standart
        h = row[7].strip()   # Proje/Makine
        birim = row[14].strip() if len(row) > 14 else ''
        if not k or k in ('0', '-', '', 'Malzeme Adı'):
            continue
        malzemeler.append({'k': k, 'l': l, 'm': m, 'h': h, 'birim': birim})
    # Benzersiz k+l kombinasyonları
    goruldu = set()
    tekil = []
    for mal in malzemeler:
        anahtar = (mal['k'].lower()[:50], mal['l'].lower()[:30])
        if anahtar not in goruldu:
            goruldu.add(anahtar)
            tekil.append(mal)
    print(f"Benzersiz malzeme: {len(tekil)}")
    return tekil

def ai_temizle(malzeme_listesi, client):
    """Claude API ile malzeme adlarını temizle, Türkçeleştir, kategorize et."""
    giris_metni = ""
    for i, mal in enumerate(malzeme_listesi):
        satir = f"{i+1}. ADI: {mal['k']}"
        if mal['l'] and mal['l'] not in ('0', '-'):
            satir += f" | MODEL: {mal['l']}"
        if mal['m'] and mal['m'] not in ('0', '-'):
            satir += f" | STANDART: {mal['m']}"
        giris_metni += satir + "\n"

    prompt = f"""Aşağıdaki {len(malzeme_listesi)} malzeme kaydı bir satın alma sisteminden alınmıştır.
Her biri için şunu yap:
1. Anlamlı, kısa Türkçe malzeme adı oluştur (Almanca/İngilizce isimleri çevir)
2. Model/ölçü bilgisini ada ekle (varsa)
3. Kategori belirle: Mekanik | Elektronik | Pnömatik | Kimyasal | Alet/Teçhizat | Ham Madde | Sarf Malzeme | Bağlantı Elemanı | Diğer
4. Birim öner: adet | kg | metre | litre | kutu | rulo | takım

JSON dizisi döndür, başka hiçbir şey yazma:
[{{"idx":1,"isim":"Temizlenmiş Malzeme Adı","kategori":"Mekanik","birim":"adet"}}, ...]

Malzemeler:
{giris_metni}"""

    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=4000,
        messages=[{'role': 'user', 'content': prompt}]
    )
    metin = msg.content[0].text.strip()
    # JSON parse
    if metin.startswith('['):
        return json.loads(metin)
    # Bazen ```json ... ``` içinde gelir
    import re
    m = re.search(r'\[.*\]', metin, re.DOTALL)
    if m:
        return json.loads(m.group())
    return []

def main():
    from app import create_app
    app = create_app()

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("HATA: ANTHROPIC_API_KEY bulunamadı")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # CSV indir ve malzemeleri çek
    icerik = csv_indir()
    malzemeler = malzemeleri_cek(icerik)

    with app.app_context():
        from app import db
        from app.models import Malzeme

        mevcut_sayisi = Malzeme.query.count()
        print(f"Mevcut malzeme: {mevcut_sayisi}")
        stok_no = STOK_KOD_BASLANGIC + mevcut_sayisi

        eklenen = 0
        hata = 0

        # Batch işleme
        for batch_start in range(0, len(malzemeler), BATCH_SIZE):
            batch = malzemeler[batch_start:batch_start + BATCH_SIZE]
            print(f"\nBatch {batch_start//BATCH_SIZE + 1}/{(len(malzemeler)-1)//BATCH_SIZE + 1} işleniyor ({len(batch)} malzeme)...")

            try:
                temiz = ai_temizle(batch, client)
                temiz_map = {t['idx']: t for t in temiz}
            except Exception as e:
                print(f"  AI hatası: {e}, batch atlanıyor")
                hata += len(batch)
                time.sleep(2)
                continue

            for i, mal in enumerate(batch):
                ai_sonuc = temiz_map.get(i + 1, {})
                isim = ai_sonuc.get('isim') or mal['k']
                kategori = ai_sonuc.get('kategori', 'Diğer')
                birim = ai_sonuc.get('birim') or mal['birim'] or 'adet'

                # Açıklama: orijinal + model
                aciklama_parcalar = []
                if mal['k'] != isim:
                    aciklama_parcalar.append(f"Orijinal: {mal['k']}")
                if mal['l'] and mal['l'] not in ('0', '-'):
                    aciklama_parcalar.append(f"Model: {mal['l']}")
                if mal['m'] and mal['m'] not in ('0', '-'):
                    aciklama_parcalar.append(f"Standart: {mal['m']}")
                aciklama = ' | '.join(aciklama_parcalar) if aciklama_parcalar else None

                # Proje/Makine kullanım notu
                kullanim = mal['h'] if mal['h'] and mal['h'] not in ('0', '-') else None

                m_obj = Malzeme(
                    stok_kodu=str(stok_no),
                    malzeme_adi=isim[:200],
                    birim=birim,
                    kategori=kategori,
                    aciklama=aciklama,
                    kullanim_notu=kullanim,
                    is_active=True
                )
                db.session.add(m_obj)
                stok_no += 1
                eklenen += 1
                print(f"  [{stok_no-1}] {isim[:60]}")

            db.session.commit()
            time.sleep(0.5)  # API rate limit

        print(f"\n{'='*60}")
        print(f"Tamamlandı: {eklenen} eklendi, {hata} hata")
        print(f"Toplam malzeme: {Malzeme.query.count()}")

if __name__ == '__main__':
    main()
