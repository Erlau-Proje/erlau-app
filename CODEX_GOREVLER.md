# CODEX — Görev Dosyası

> Bu dosyayı oku ve aşağıdaki görevleri sırayla yap.
> Diğer hiçbir dosyayı okumana gerek yok — ihtiyacın olan her şey burada.
> Her görevi tamamladıktan sonra sonraki göreve geç.

---

## Proje Bağlamı

**Erlau Satın Alma & Üretim Yönetim Sistemi** — Python Flask uygulaması.

**Teknoloji:**
- Flask + Jinja2 template engine
- Tailwind CSS (CDN üzerinden, `base.html`'de mevcut)
- Vanilla JS (harici kütüphane kullanma — Chart.js hariç, CDN'den eklenebilir)
- Bootstrap veya jQuery kullanma

**Proje dizini:** `/root/erlau-app/`
**Template dizini:** `/root/erlau-app/app/templates/`

---

## Kritik Kodlama Kuralları

1. **Tailwind `hidden` class'ı KULLANMA** — show/hide için `element.style.display='none'/'flex'/'block'` kullan
2. **Türkçe karakter kullanma** değişken/sınıf/id adlarında (ı, ş, ğ, ü, ö, ç) — HTML metin içeriğinde serbestsin
3. Her template `{% extends 'base.html' %}` ile başlar ve `{% block content %}...{% endblock %}` içerir
4. Form action URL'leri `{{ url_for('blueprint.route_adi') }}` formatıyla yaz
5. Flash mesajları her template'in en üstüne ekle:
   ```html
   {% with msgs = get_flashed_messages(with_categories=true) %}
     {% for cat, msg in msgs %}
     <div class="mb-4 px-4 py-3 rounded-lg {% if cat=='success' %}bg-green-50 text-green-700{% else %}bg-red-50 text-red-700{% endif %} text-sm">{{ msg }}</div>
     {% endfor %}
   {% endwith %}
   ```
6. Tablo satırlarında hover: `hover:bg-gray-50`
7. Buton stilleri:
   - Yeşil (kaydet/ekle): `class="erlau-green text-white px-4 py-2 rounded-lg text-sm font-medium"`
   - Mavi: `style="background:#3b82f6;color:#fff;padding:7px 14px;border-radius:8px;font-size:13px;font-weight:600;border:none;cursor:pointer"`
   - Kırmızı (sil): `class="text-xs text-red-400 hover:text-red-600"`
8. **Card bileşeni:** `<div class="card p-5 mb-4">` veya `<div class="card overflow-hidden mb-6">`
9. Sayfa başlığı pattern:
   ```html
   <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
     <div>
       <a href="..." class="text-sm text-gray-400 hover:underline">← Geri</a>
       <h1 class="text-2xl font-semibold text-gray-800 mt-1">Sayfa Başlığı</h1>
     </div>
     <div><!-- sağ taraf butonlar --></div>
   </div>
   ```
10. Mevcut `base.html`'de sol sidebar menüsü var — yeni sayfalar için sidebar'a link ekleme gerekiyorsa `base.html`'i düzenle.
11. **Onay gerektiren silme/pasifleştirme formları:** `onsubmit="return confirm('...')"` kullan

---

## Mevcut Blueprint'ler ve URL Prefixleri

| Blueprint | Prefix | Örnek route |
|---|---|---|
| `auth` | — | `url_for('auth.login')` |
| `main` | — | `url_for('main.dashboard')` |
| `satin_alma` | `/satinalma/` | `url_for('satin_alma.panel')` |
| `admin` | `/admin/` | `url_for('admin.kullanici_listesi')` |
| `muhasebe` | `/muhasebe/` | `url_for('muhasebe.panel')` |
| `uretim` | `/uretim/` | `url_for('uretim.uretim_dashboard')` |
| `planlama` | `/planlama/` | `url_for('planlama.planlama_dashboard')` |
| `bakim` | `/bakim/` | `url_for('bakim.bakim_dashboard')` |
| `kalite` | `/kalite/` | `url_for('kalite.kalite_dashboard')` |

---

## Mevcut Veri Modelleri (Özet)

```python
# Kullanıcılar
User: id, name, email, role, department_id
# role değerleri: 'admin','satinalma','muhasebe','personel','uretim','planlama','bakim','kalite','gm','departman_yoneticisi'

# Üretim
IsIstasyonu: id, istasyon_kodu, istasyon_adi, is_active
UretimPersoneli: id, ad, soyad, istasyon_id, sicil_no, is_active, created_at
UretimPlani: id, plan_no, hafta, yil, baslangic_tarihi, bitis_tarihi, durum ('taslak'|'aktif'|'tamamlandi')
UretimPlaniSatir: id, plan_id, urun_id, istasyon_id, tarih, planlanan_adet, devir_adet, kaynak ('plan'|'devir'|'tamir')
UretimKaydi: id, plan_satir_id, istasyon_id, urun_id, uretim_personeli_id, tarih, gerceklesen_adet, fire_adet
ArizaKaydi: id, istasyon_id, tarih, baslangic_saati, bitis_saati, aciklama, durum

# Kalite
KaliteKontrol: id, tarih, uretim_kaydi_id, urun_id, istasyon_id, ok_adet, nok_adet, nok_neden, nok_akibet, tamir_plan_satir_id
DOF: id, dof_no, tarih, durum, hedef_departman, hedef_kullanici_id, acan_kullanici_id, problem_tanimi, kok_neden, planlanan_kapatma_tarihi, gercek_kapatma_tarihi, tip ('ic'|'tedis'), tedarikci_id
DOFAksiyon: id, dof_id, aksiyon_tanimi, sorumlu_id, planlanan_tarih, tamamlama_tarihi, durum ('bekliyor'|'tamamlandi'|'gecikti')
DOFEk: id, dof_id, dosya_adi, dosya_yolu, dosya_turu ('resim'|'pdf'|'diger'), yukleyen_id
SekizD: id, sekizd_no, tarih, tedarikci_id, urun_kodu, urun_adi, revizyon_no, durum, d1_ekip_lideri, d1_ekip_uyeleri, d2_problem_ozeti, d2_kim, d2_ne, d2_nerede, d2_ne_zaman, d2_neden, d2_nasil, d2_ne_kadar, d2_ilk_tespit, d3_onlem, d3_sorumlu, d3_tarih, d3_etkinlik, d4_kok_neden, d4_analiz_metod, d5_aksiyon, d6_uygulama, d6_tarih, d6_dogrulama, d7_onleyici, d8_tadir
IsAkisiSurec: id, surec_kodu, surec_adi, departman, aciklama, versiyon, durum ('taslak'|'aktif'|'arsiv')
IsAkisiAdim: id, surec_id, sira, adim_tipi ('baslangic'|'islem'|'karar'|'belge'|'bitis'), adim_adi, aciklama, sorumlu_departman, sure_hedef_saat, evet_sonraki_sira, hayir_sonraki_sira

# Diğer
Urun: id, urun_kodu, urun_adi, is_active
Tedarikci: id, name, email
```

---

## Jinja2 Şablonunda Kullanılabilecek Yardımcı Değişkenler

```jinja2
{{ current_user.name }}          # login kullanıcının adı
{{ current_user.role }}          # rolü
{{ current_user.id }}            # id
{{ url_for('blueprint.route') }} # URL üretimi
{% if current_user.role == 'kalite' %}...{% endif %}
```

---

## GÖREV LİSTESİ

---

## GÖREV P-004b — Personel Yönetimi + Performans UI

**Oluşturulacak dosyalar:**
- `app/templates/uretim/personel.html`
- `app/templates/uretim/personel_detay.html`

**Sidebar'a eklenecek:** `app/templates/base.html` — Üretim bölümüne "Personel" linki

**Kullanılacak route'lar:**
```
GET  /uretim/personel                  → personel listesi
POST /uretim/personel/ekle             → ekle (form: ad, soyad, istasyon_id, sicil_no)
POST /uretim/personel/<id>/duzenle     → düzenle (form: ad, soyad, istasyon_id, sicil_no)
POST /uretim/personel/<id>/pasif       → pasifleştir
GET  /uretim/personel/<id>             → detay sayfası
```

### `personel.html`

Sayfa başlığı: "Üretim Personeli"

**Üst sağ buton:** "Yeni Personel Ekle" — tıklayınca sayfanın altındaki ekle formuna scroll eder

**Personel tablosu:**
```
Sicil No | Ad Soyad | İstasyon | Bu Hafta (adet) | Bu Ay (adet) | Durum | İşlemler
```
- `Bu Hafta` ve `Bu Ay` değerleri context'ten gelir: `personel.bu_hafta` ve `personel.bu_ay`
- Durum badge: aktif → `<span class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Aktif</span>`, pasif → gri
- İşlemler: "Detay" linki + "Düzenle" modal butonu + "Pasifleştir" form butonu
- Pasifleştirme: `onsubmit="return confirm('Personeli pasife almak istediğinize emin misiniz?')"` onaylı form

**Düzenle Modal:**
```html
<div id="modalDuzenle-{{ p.id }}" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:50;align-items:center;justify-content:center">
  <div style="background:#fff;padding:24px;border-radius:12px;width:420px">
    <h3>Personel Düzenle</h3>
    <form method="POST" action="{{ url_for('uretim.personel_duzenle', id=p.id) }}">
      <!-- Ad, Soyad, Sicil No, İstasyon select -->
      <button type="submit">Kaydet</button>
      <button type="button" onclick="document.getElementById('modalDuzenle-{{ p.id }}').style.display='none'">İptal</button>
    </form>
  </div>
</div>
```

**Ekle Formu** (sayfanın altında, card içinde):
- Ad (zorunlu), Soyad (opsiyonel), Sicil No (opsiyonel)
- İstasyon select: `{% for i in istasyonlar %}<option value="{{ i.id }}">{{ i.istasyon_adi }}</option>{% endfor %}`
- Submit: "Personel Ekle"

**Context değişkenleri:**
```python
personeller: list[UretimPersoneli]    # her objenin .bu_hafta ve .bu_ay attribute'u var
istasyonlar: list[IsIstasyonu]
```

---

### `personel_detay.html`

Sayfa başlığı: Personelin tam adı

**Geri linki:** `← Personel Listesi` → `/uretim/personel`

**Üst kart (sol):**
- Büyük harf avatar dairesi (ad baş harfleri): `<div style="width:60px;height:60px;background:#3b82f6;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:22px;font-weight:700">{{ personel.ad[0] }}</div>`
- Ad Soyad (büyük), İstasyon adı, Sicil No, Çalışma Başlangıcı
- Durum badge

**4 istatistik kartı (grid-cols-4):**
| Kart | Değer |
|---|---|
| Bu Hafta Üretim | `{{ bu_hafta_toplam }} adet` |
| Bu Ay Üretim | `{{ bu_ay_toplam }} adet` |
| Günlük Ortalama | `{{ "%.1f"|format(gunluk_ortalama) }} adet` |
| Çalıştığı İstasyon | `{{ personel.istasyon.istasyon_adi if personel.istasyon else '—' }}` |

**Grafik — Son 30 Gün Günlük Üretim:**
Chart.js CDN ile bar chart. Context'ten `performans_30gun` listesi gelir:
```javascript
// performans_30gun = [{"tarih": "2026-04-15", "toplam_adet": 45}, ...]
const labels = {{ performans_30gun | map(attribute='tarih') | list | tojson }};
const data = {{ performans_30gun | map(attribute='toplam_adet') | list | tojson }};
```
Chart.js CDN: `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>`

**Ürün Bazlı Dağılım Tablosu (bu ay):**
```
Ürün Adı | Toplam Adet | Oran (%)
```
Context: `urun_dagilimi: list[{urun_adi, toplam, oran}]`

**Son 10 Üretim Kaydı:**
```
Tarih | İstasyon | Ürün | Adet | Kaynak
```
Context: `son_kayitlar: list[UretimKaydi]`

---

## GÖREV P-006 — Planlama Dashboard HTML

**Dosya:** `app/templates/planlama/dashboard.html` — **Mevcut dosyayı tamamen yeniden yaz.**

**Context değişkenleri:**
```python
aktif: UretimPlani | None
planlar: list[UretimPlani]          # son 5 plan
aktif_ozet: list[dict]              # {urun, istasyon, pzt, sal, car, per, cum, toplam}
haftalik_veri: list[dict]           # {gun_adi, planlanan, gerceklesen, devir} — 5 gün
istasyon_kapasite: list[dict]       # {istasyon_adi, planlanan, gerceklesen, oran}
kalite_ozet: dict                   # {ok_adet, nok_adet, ok_oran, hurda_adet, tamir_adet}
toplam_hedef: int
toplam_gerceklesen: int
tamamlanma_yuzdesi: float
toplam_devir: int
bugun: date
acik_dof_sayisi: int                # bu departmana açık DÖF
geciken_aksiyon_sayisi: int         # geciken DÖF aksiyonu
```

**Sayfa yapısı:**

### 1. Başlık alanı
- Sol: "Planlama Dashboard" + aktif plan no + tarih aralığı
- Sağ: "Yeni Plan" butonu + "Gün Sonu Kapat" butonu (POST `/planlama/gun-sonu-devir`, onay modal)

### 2. DÖF Uyarı Banner'ı (varsa)
```html
{% if acik_dof_sayisi > 0 or geciken_aksiyon_sayisi > 0 %}
<div style="background:#fef3c7;border:1px solid #fcd34d;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:12px">
  <span style="font-size:18px">⚠️</span>
  <span style="font-size:13px;color:#92400e">
    Departmanınıza açık <strong>{{ acik_dof_sayisi }}</strong> DÖF
    {% if geciken_aksiyon_sayisi > 0 %} ve <strong class="text-red-600">{{ geciken_aksiyon_sayisi }}</strong> geciken aksiyon{% endif %} var.
    <a href="{{ url_for('kalite.dof_benim') }}" style="color:#1d4ed8;text-decoration:underline">Görüntüle →</a>
  </span>
</div>
{% endif %}
```

### 3. Özet Kartlar (4 kart, grid-cols-4)
```
Bu Hafta Hedef  |  Gerçekleşen  |  Tamamlanma %  |  Toplam Devir
   [sayı]       |    [sayı]     |    [% bar]     |    [sayı]
```
Her kart: `<div class="card p-4 text-center">`

### 4. Grafik: Günlük Hedef vs Gerçekleşen vs Devir
Chart.js Bar chart (grouped):
```javascript
// haftalik_veri = [
//   {"gun_adi": "Pazartesi", "planlanan": 120, "gerceklesen": 105, "devir": 15},
//   ...
// ]
```
3 dataset:
- Planlanan → gri `#9ca3af`
- Gerçekleşen → yeşil `#16a34a`
- Devir → turuncu `#f59e0b`

### 5. İstasyon Kapasite Kullanımı (Yatay bar)
Her istasyon için inline progress bar:
```html
{% for ist in istasyon_kapasite %}
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
  <div style="width:140px;font-size:12px;color:#374151;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ ist.istasyon_adi }}</div>
  <div style="flex:1;background:#f3f4f6;border-radius:4px;height:16px;position:relative">
    <div style="width:{{ ist.oran }}%;background:{% if ist.oran >= 90 %}#16a34a{% elif ist.oran >= 70 %}#f59e0b{% else %}#dc2626{% endif %};height:100%;border-radius:4px;transition:width .3s"></div>
  </div>
  <div style="width:45px;font-size:12px;text-align:right;font-weight:600;color:{% if ist.oran >= 90 %}#16a34a{% elif ist.oran >= 70 %}#d97706{% else %}#dc2626{% endif %}">{{ "%.0f"|format(ist.oran) }}%</div>
</div>
{% endfor %}
```

### 6. Kalite Özeti (küçük, sağ panelde veya card)
- OK Adet: yeşil
- NOK Adet: kırmızı + hurda/tamir alt detay
- NOK Oranı

### 7. Aktif Plan Özeti Tablosu
```
Ürün Kodu | Ürün Adı | İstasyon | Pzt | Sal | Çar | Per | Cum | Toplam Hedef | Gerçekleşen | Kalan | %
```
Context: `aktif_ozet`

### 8. Son Planlar Listesi (küçük tablo)
```
Plan No | Hafta | Tarih Aralığı | Durum | İşlemler
```

---

## GÖREV P-007 — Üretim Dashboard HTML

**Dosya:** `app/templates/uretim/dashboard.html` — **Mevcut dosyayı tamamen yeniden yaz.**

**Context değişkenleri:**
```python
bugun: date
istasyon_durumlar: list[dict]    # {istasyon, personel_adi, hedef, gerceklesen, fark, yuzde, renk}
plan_satirlari: list[UretimPlaniSatir]
kayit_map: dict                  # {plan_satir_id: UretimKaydi}
haftalik_ilerleme: list[dict]    # {tarih, gun_adi, toplam_hedef, toplam_gerceklesen, yuzde}
personel_siralaması: list[dict]  # {ad, toplam_hafta, gun_ort}
ariza_ozet: dict                 # {bu_hafta_adet, bu_hafta_sure_saat, en_cok_ariza_istasyon}
toplam_hedef: int
toplam_gerceklesen: int
acik_dof_sayisi: int
geciken_aksiyon_sayisi: int
```

**Sayfa yapısı:**

### 1. DÖF Uyarı Banner'ı (P-006 ile aynı pattern)

### 2. Üst Özet Satırı (3 kart)
- Bugün Hedef | Bugün Gerçekleşen | Tamamlanma %

### 3. İstasyon Durum Kartları (grid, responsive)
Her istasyon için kart:
```html
<div class="card p-4" style="border-left:4px solid {{ renk }}">
  <div style="font-size:13px;font-weight:600;color:#374151">{{ ist.istasyon }}</div>
  <div style="font-size:11px;color:#6b7280">{{ ist.personel_adi or '—' }}</div>
  <div style="display:flex;justify-content:space-between;margin-top:8px">
    <div><div style="font-size:10px;color:#9ca3af">Hedef</div><div style="font-size:20px;font-weight:700">{{ ist.hedef }}</div></div>
    <div><div style="font-size:10px;color:#9ca3af">Gerçekleşen</div><div style="font-size:20px;font-weight:700;color:{{ '#16a34a' if ist.gerceklesen >= ist.hedef else '#dc2626' }}">{{ ist.gerceklesen }}</div></div>
    <div><div style="font-size:10px;color:#9ca3af">%</div><div style="font-size:18px;font-weight:700">{{ ist.yuzde }}%</div></div>
  </div>
  <!-- mini progress bar -->
  <div style="margin-top:8px;background:#f3f4f6;border-radius:4px;height:6px">
    <div style="width:{{ [ist.yuzde, 100]|min }}%;background:{{ ist.renk }};height:100%;border-radius:4px"></div>
  </div>
</div>
```
renk: `#16a34a` (≥100%), `#f59e0b` (≥70%), `#dc2626` (<70%)

### 4. Haftalık İlerleme (Progress bar serisi)
Her gün için sıralı satır:
- Gün adı | tarih | bar (hedef vs gerçekleşen) | %
- Bugün vurgulansın (border veya arka plan farkıyla)
- Gelecek günler (gerceklesen=0) gri göster

### 5. Bugünkü Üretim Tablosu
```
Ürün | İstasyon | Personel | Planlanan | Devir | Hedef | Gerçekleşen | Fark | Kaynak
```
Kaynak badge: `plan` (mavi `#3b82f6`), `devir` (turuncu `#f59e0b`), `tamir` (kırmızı `#dc2626`)
Fark: negatifse kırmızı, sıfır veya pozitifse yeşil

### 6. Personel Sıralaması (bu hafta)
```
Sıra | Ad Soyad | İstasyon | Bu Hafta Toplam | Günlük Ort.
```
İlk 3 kişi altın/gümüş/bronz badge

### 7. Arıza Özeti Mini Kart
- Bu hafta arıza sayısı
- Toplam süre (saat)
- En çok sorun yaşayan istasyon

---

## GÖREV P-008 — Kalite Dashboard HTML

**Dosya:** `app/templates/kalite/dashboard.html` — **YENİ dosya oluştur.**
(Dizin `app/templates/kalite/` mevcut değilse oluştur)

**Context değişkenleri:**
```python
bugun: date
bugun_ok: int
bugun_nok: int
bugun_kontrol_edilen: int
bugun_nok_orani: float            # 0–100
trend_7gun: list[dict]            # {tarih, ok_adet, nok_adet}
istasyon_kalite: list[dict]       # {istasyon_adi, ok, nok, oran}
nok_neden_dagilim: list[dict]     # {neden, adet, oran, hurda, tamir}
tamir_kuyrugu: list[UretimPlaniSatir]  # kaynak='tamir' olan satırlar
acik_dof_sayisi: int
```

**Sayfa yapısı:**

### 1. Üst Özet Kartlar (4 kart)
- Bugün Kontrol Edilen | OK Adet (yeşil) | NOK Adet (kırmızı) | NOK Oranı %

### 2. 7 Günlük OK/NOK Trendi
Chart.js Line chart:
- OK → yeşil çizgi
- NOK → kırmızı çizgi
- X ekseni: son 7 günün tarihleri

### 3. İstasyon Bazlı Kalite Tablosu
```
İstasyon | OK | NOK | OK Oranı (%) | Progress Bar
```
Progress bar: yeşil dolgu, NOK var mı → kırmızı border

### 4. NOK Nedenleri Dağılımı
```
Neden | Adet | % | Hurda | Tamir
```
Neden etiketleri:
- `hammadde_hatasi` → "Hammadde Hatası"
- `isleme_hatasi` → "İşleme Hatası"
- `olcu_hatasi` → "Ölçü Hatası"
- `diger` → "Diğer"

### 5. Tamir Kuyruğu Tablosu
```
Ürün | İstasyon | Tamir Adedi | Plan No | Plan Tarihi | Durum
```
Kaynak='tamir' olan UretimPlaniSatir satırları

### 6. Hızlı Linkler
- "Günlük Kontrol Gir" → `/kalite/kontrol`
- "DÖF Listesi" → `/kalite/dof`
- "8D Raporları" → `/kalite/8d`
- "Süreçler" → `/kalite/surecler`

---

## GÖREV K-002 — DÖF Arayüzü HTML

**Oluşturulacak dosyalar:**
- `app/templates/kalite/dof_listesi.html`
- `app/templates/kalite/dof_yeni.html`
- `app/templates/kalite/dof_detay.html`

---

### `dof_listesi.html`

**Context:** `doflar: list[DOF]`, `departmanlar: list[str]`, `secili_durum: str`, `secili_dept: str`

**Sayfa başlığı:** "DÖF Listesi" | Sağ: "Yeni DÖF Aç" butonu (sadece `current_user.role == 'kalite'` ise görünür)

**Filtre satırı:**
```html
<form method="GET">
  <select name="durum"><option value="">Tüm Durumlar</option>...acik/isleniyor/kapali/gecikti</select>
  <select name="dept"><option value="">Tüm Departmanlar</option>{% for d in departmanlar %}<option>{{d}}</option>{% endfor %}</select>
  <input type="date" name="bas"> – <input type="date" name="bit">
  <button type="submit">Filtrele</button>
</form>
```

**Tab:**
- "Tümü" | "Benim Açtıklarım" | "Bana Açılanlar"
- Tab değişimi: JS ile `display` toggle, veya her tab ayrı URL parametresi

**DÖF Tablosu:**
```
DÖF No | Tarih | Tip | Hedef Departman/Tedarikçi | Problem (max 60 karakter...) | Durum | Planlanan Kapanış | İşlem
```

Durum badge renkleri:
- `acik` → sarı bg-yellow-100 text-yellow-700
- `isleniyor` → mavi bg-blue-100 text-blue-700
- `kapali` → yeşil bg-green-100 text-green-700
- `gecikti` → kırmızı bg-red-100 text-red-700
- `iptal` → gri

İşlem: "Detay" butonu

---

### `dof_yeni.html`

**Context:** `kullanicilar: list[User]`, `tedarikciler: list[Tedarikci]`

**Departman listesi (select):**
```python
# Şu departmanlar: Satınalma, Üretim, Bakım, Planlama, Muhasebe, Kalite, İnsan Kaynakları, Yönetim
```

**Form alanları:**

1. **Tip seçimi** (radio, büyük buton stilinde):
   - "İç DÖF" (department bazlı)
   - "Tedarikçi DÖF" (8D ile bağlantılı)

2. **İç DÖF alanları** (tip=ic ise):
   - Hedef Departman (select)
   - Hedef Kullanıcı (select, opsiyonel)

3. **Tedarikçi DÖF alanları** (tip=tedis ise, JS ile göster/gizle):
   - Tedarikçi (select, mevcut tedarikçi listesinden)

4. **Problem Tanımı** (textarea, zorunlu)
5. **Kök Neden** (textarea, opsiyonel)
6. **Planlanan Kapatma Tarihi** (date, zorunlu)

7. **Aksiyonlar** (dinamik satır):
   ```html
   <div id="aksiyonlar">
     <div class="aksiyon-satir" style="display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:8px;margin-bottom:8px">
       <input name="aksiyon_tanimi[]" placeholder="Aksiyon tanımı">
       <select name="sorumlu_id[]"><option value="">Sorumlu seç</option>...</select>
       <input type="date" name="planlanan_tarih[]">
       <button type="button" onclick="satırSil(this)">Sil</button>
     </div>
   </div>
   <button type="button" onclick="aksiyon_ekle()">+ Aksiyon Ekle</button>
   ```

**JS:** Tip değişince ilgili alanları göster/gizle

---

### `dof_detay.html`

**Context:** `dof: DOF`, `dof.aksiyonlar`, `dof.ekler`, `kullanicilar: list[User]`, `tedarikci: Tedarikci|None`

**Layout:** İki kolon (sol 2/3, sağ 1/3)

**Sol kolon:**

*Problem Bilgileri card:*
- DÖF No, Tarih, Tip badge
- Hedef: departman veya tedarikçi adı
- Problem Tanımı (tam metin)
- Kök Neden (varsa)

*Aksiyonlar tablosu:*
```
Tanım | Sorumlu | Planlanan Tarih | Tamamlama Tarihi | Durum | İşlem
```
- Durum: bekliyor/tamamlandi/gecikti (renkli badge)
- İşlem: "Tamamlandı" butonu (sadece sorumlu kullanıcı veya kalite görür)
  ```html
  <form method="POST" action="{{ url_for('kalite.aksiyon_tamamla', aksiyon_id=a.id) }}">
    <input type="date" name="tamamlama_tarihi" value="{{ today }}">
    <button type="submit">✓ Tamamlandı</button>
  </form>
  ```

*Yeni Aksiyon Ekle (kalite rolü için, dof.durum != 'kapali'):*
- Tek satır inline form

**Sağ kolon:**

*Durum Card:*
- Büyük durum badge
- Planlanan kapanış tarihi (kırmızı ise geçmiş)
- Gerçekleşen kapanış tarihi (varsa)
- Açan kullanıcı + tarih

*Ekler Card:*
- Yüklü dosyalar/resimler (resim ise `<img>` thumbnail)
- Dosya yükleme formu (enctype="multipart/form-data"):
  ```html
  <form method="POST" action="{{ url_for('kalite.dof_ek_yukle', id=dof.id) }}" enctype="multipart/form-data">
    <input type="file" name="dosya" accept="image/*,.pdf">
    <button type="submit">Yükle</button>
  </form>
  ```

*DÖF Kapat Card (kalite rolü + durum != 'kapali'):*
```html
<form method="POST" action="{{ url_for('kalite.dof_kapat', id=dof.id) }}" onsubmit="return confirm('DÖF kapatılsın mı?')">
  <textarea name="kapatma_notu" placeholder="Kapatma notu (zorunlu)" required></textarea>
  <input type="date" name="gercek_kapatma_tarihi" value="{{ today }}">
  <button type="submit">DÖF'ü Kapat</button>
</form>
```

*Zaman Çizelgesi (Timeline):*
```html
<div style="position:relative;padding-left:20px;border-left:2px solid #e2e8f0">
  <div style="...">📅 Açıldı — {{ dof.tarih }}</div>
  {% for a in dof.aksiyonlar if a.tamamlama_tarihi %}
  <div>✅ Aksiyon tamamlandı — {{ a.tamamlama_tarihi }}</div>
  {% endfor %}
  {% if dof.gercek_kapatma_tarihi %}
  <div>🔒 Kapandı — {{ dof.gercek_kapatma_tarihi }}</div>
  {% endif %}
</div>
```

---

## GÖREV K-004 — 8D Arayüzü HTML

**Oluşturulacak dosyalar:**
- `app/templates/kalite/sekizd_listesi.html`
- `app/templates/kalite/sekizd_form.html`
- `app/templates/kalite/sekizd_detay.html`

---

### `sekizd_listesi.html`

**Context:** `sekizd_listesi: list[SekizD]`, `tedarikciler: list[Tedarikci]`

**Tablo:**
```
8D No | Tarih | Tedarikçi | Ürün | Durum | İşlemler
```
İşlemler: Detay | PDF | Excel | Outlook Taslağı | Düzenle

Durum badge: `taslak` (gri), `gonderildi` (mavi), `kapali` (yeşil)

"Yeni 8D" butonu (sadece kalite rolü)

---

### `sekizd_form.html`

**Context:** `sekizd: SekizD|None`, `tedarikciler: list[Tedarikci]`, `form_action: str`, `baslik: str`

Hem yeni hem düzenle için kullanılır. `baslik` değişkeni: "Yeni 8D Raporu" veya "8D Düzenle".

**Bölüm yapısı:** Her D bölümü accordion (JS ile açılır/kapanır)

```html
<!-- Header Accordion örneği -->
<div class="card mb-3">
  <div onclick="toggleD(1)" style="padding:14px 20px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;background:#f8fafc;border-radius:8px">
    <h3 style="font-weight:600;color:#1e293b">D1 — Ekip Oluşturma</h3>
    <span id="chevron-1">▼</span>
  </div>
  <div id="d-block-1" style="padding:16px 20px">
    <label>Ekip Lideri</label>
    <input type="text" name="d1_ekip_lideri" value="{{ sekizd.d1_ekip_lideri if sekizd else '' }}">
    <label>Ekip Üyeleri</label>
    <textarea name="d1_ekip_uyeleri">{{ sekizd.d1_ekip_uyeleri if sekizd else '' }}</textarea>
  </div>
</div>
```

**Header bölümü (her zaman görünür):**
- Tedarikçi select, Ürün Kodu, Ürün Adı, Revizyon No

**D2 bölümü özel:** 5W2H için 7 alan 3-kolon grid:
```
Problem Özeti (tam genişlik textarea)
Kim | Ne | Nerede
Ne Zaman | Neden | Nasıl
Ne Kadar | İlk Tespit Yeri
```

**D4 Kök Neden:** Analiz Metodu radio (5 Why / Balık Kılçığı / Diğer) + Kök Neden textarea

**Alt butonlar:** "Taslak Kaydet" + "Tamamlandı Olarak Kaydet"

**JS:**
```javascript
function toggleD(n) {
  const block = document.getElementById('d-block-' + n);
  const ch = document.getElementById('chevron-' + n);
  block.style.display = block.style.display === 'none' ? 'block' : 'none';
  ch.textContent = block.style.display === 'none' ? '▶' : '▼';
}
// Başlangıçta D1 açık, diğerleri kapalı
document.querySelectorAll('[id^="d-block-"]').forEach((el, i) => {
  if (i > 0) el.style.display = 'none';
});
```

---

### `sekizd_detay.html`

**Context:** `sekizd: SekizD`, `tedarikci: Tedarikci`

Salt okunur görünüm. Her D bölümü card.

**Üst başlık:**
- 8D No, Tedarikçi adı, Ürün, Durum badge

**İndir butonları:**
```html
<a href="{{ url_for('kalite.sekizd_pdf', id=sekizd.id) }}" target="_blank">📄 PDF İndir</a>
<a href="{{ url_for('kalite.sekizd_excel', id=sekizd.id) }}">📊 Excel İndir</a>
<a href="{{ url_for('kalite.sekizd_eml', id=sekizd.id) }}">✉️ Outlook Taslağı</a>
```

D1–D8 bölümlerini okunabilir şekilde göster (label + metin çifti, boş alanlar için "—")

"Düzenle" butonu (kalite rolü)

---

## GÖREV K-006 — İş Akışı Süreç UI

**Oluşturulacak dosyalar:**
- `app/templates/kalite/surec_listesi.html`
- `app/templates/kalite/surec_goruntur.html`
- `app/templates/kalite/surec_duzenle.html`

---

### `surec_listesi.html`

**Context:** `surecler: list[IsAkisiSurec]`, `departmanlar: list[str]`

**Kart grid (grid-cols-3):** Her süreç için:
```html
<div class="card p-5">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <span style="font-size:11px;color:#94a3b8;font-family:monospace">{{ s.surec_kodu }}</span>
      <h3 style="font-size:15px;font-weight:600;color:#1e293b;margin-top:2px">{{ s.surec_adi }}</h3>
      <span style="font-size:12px;color:#6b7280">{{ s.departman }}</span>
    </div>
    <!-- Durum badge -->
  </div>
  <div style="margin-top:12px;font-size:12px;color:#9ca3af">v{{ s.versiyon }} · {{ s.adimlar|length }} adım</div>
  <div style="margin-top:12px;display:flex;gap:8px">
    <a href="{{ url_for('kalite.surec_goruntur', id=s.id) }}" style="...">Görüntüle</a>
    {% if current_user.role in ['kalite','admin'] %}
    <a href="{{ url_for('kalite.surec_duzenle', id=s.id) }}" style="...">Düzenle</a>
    {% endif %}
  </div>
</div>
```

Filtreler: Departman select + Durum select + form GET

"Yeni Süreç" butonu (kalite/admin)

---

### `surec_goruntur.html`

**Context:** `surec: IsAkisiSurec`, `surec.adimlar: list[IsAkisiAdim]`

**Üst:** Süreç kodu, adı, departman, versiyon, durum badge + "Yazdır" butonu (window.print())

**Akış Şeması (SVG tabanlı, yatay):**

Adımları SVG olarak çiz. Her adım tipi farklı şekil:
- `baslangic`/`bitis` → `<ellipse>` (yuvarlak)
- `islem` → `<rect>` (dikdörtgen)
- `karar` → `<polygon>` (baklava/diamond)
- `belge` → `<rect>` (dalgalı alt kenar, basit dikdörtgen yeterli)

Her şeklin içine `<text>` ile adım adı (uzunsa kes: max ~20 karakter)

Oklar: `<line>` veya `<path>` marker-end ile ok başı
Karar adımları: iki ok çıkar (Evet/Hayır etiketli)

Tooltip (title tag ile): adım açıklaması + sorumlu + süre

Basit örnek SVG yapısı (yatay, soldan sağa):
```html
<svg width="100%" height="300" style="overflow-x:auto">
  <!-- adım 1 -->
  <ellipse cx="80" cy="150" rx="60" ry="30" fill="#dcfce7" stroke="#16a34a" stroke-width="2"/>
  <text x="80" y="155" text-anchor="middle" font-size="12">Başlangıç</text>
  <!-- ok -->
  <line x1="140" y1="150" x2="180" y2="150" stroke="#6b7280" stroke-width="2" marker-end="url(#arrow)"/>
  <!-- adım 2 -->
  <rect x="180" y="120" width="120" height="60" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="2"/>
  <text x="240" y="155" text-anchor="middle" font-size="12">İşlem Adı</text>
  ...
</svg>
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#6b7280"/>
  </marker>
</defs>
```

Adım sayısı fazlaysa SVG genişliği artar — `overflow-x: auto` ile kaydırılabilir.

Sağ panel: Adım listesi (tablo: Sıra | Ad | Tip | Sorumlu | Süre)

---

### `surec_duzenle.html`

**Context:** `surec: IsAkisiSurec`, `surec.adimlar`, `kullanicilar: list[User]`

**Üst form:** Süreç adı, departman, açıklama, versiyon (güncelle butonu ayrı)

**Adımlar tablosu:**
```
Sıra | Tip | Adım Adı | Açıklama | Sorumlu Dept | Süre (h) | Sıra ↑↓ | Sil
```

Her satır düzenlenebilir (inline form veya modal):
- Tip: `<select>` (baslangic, islem, karar, belge, bitis)
- Karar tipi seçilince: "Evet → Sıra" ve "Hayır → Sıra" alanları belir

"+ Yeni Adım" satırı (sayfanın altında inline form):
```html
<form method="POST" action="{{ url_for('kalite.adim_ekle', id=surec.id) }}">
  <select name="adim_tipi">islem/karar/belge/bitis</select>
  <input name="adim_adi" placeholder="Adım adı">
  <input name="aciklama" placeholder="Açıklama (opsiyonel)">
  <input name="sorumlu_departman" placeholder="Sorumlu departman">
  <input type="number" name="sure_hedef_saat" placeholder="Süre (h)">
  <button type="submit">Ekle</button>
</form>
```

Sıra değiştirme butonları: POST `/kalite/surecler/<id>/adim-sira` (yukari/asagi)

---

## GÖREV K-007 — DÖF Performans Widget'ları

**Oluşturulacak dosyalar:**
- `app/templates/kalite/dof_performans.html` (yeni)

**Düzenlenecek dosyalar:**
- `app/templates/uretim/dashboard.html` — DÖF mini widget ekle
- `app/templates/planlama/dashboard.html` — DÖF mini widget ekle (P-006'da zaten var, kontrol et)
- `app/templates/bakim/dashboard.html` — DÖF mini widget ekle

---

### `dof_performans.html`

**Context:**
```python
dept_performans: list[dict]  # {departman, acik, geciken, kapali, ort_kapat_gun, performans_yuzdesi}
filtre_gun: int              # 30, 90 veya 365
toplam_acik: int
toplam_geciken: int
toplam_kapali: int
```

**Filtre:** Son 30 gün / 90 gün / Bu Yıl (GET parametresi)

**Özet kartlar:**
- Toplam Açık DÖF | Toplam Geciken | Toplam Kapalı

**Departman Performans Tablosu:**
```
Departman | Açık | Geciken | Kapalı | Ort. Kapanış (gün) | Performans %
```
- Performans %: (Zamanında kapanan / toplam kapanan) × 100
- Renk kodu: %100 → yeşil, %80+ → sarı, <%80 → kırmızı

**Grafik: Stacked Bar (departman bazlı)**
Chart.js ile:
- X: Departmanlar
- Dataset 1 (yeşil): Kapalı
- Dataset 2 (sarı): Açık
- Dataset 3 (kırmızı): Geciken

---

### Dashboard'lara Eklenecek Mini DÖF Widget'ı

`uretim/dashboard.html`, `planlama/dashboard.html`, `bakim/dashboard.html` dosyalarının sayfa başlığının hemen altına (DÖF uyarı banner olarak) ekle:

```html
{% if acik_dof_sayisi > 0 or geciken_aksiyon_sayisi > 0 %}
<div style="background:#fef3c7;border:1px solid #fcd34d;border-radius:10px;padding:12px 18px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between">
  <div style="display:flex;align-items:center;gap:10px">
    <span style="font-size:20px">⚠️</span>
    <div>
      <div style="font-size:13px;font-weight:600;color:#92400e">Açık DÖF Bildirimi</div>
      <div style="font-size:12px;color:#78350f">
        Departmanınıza açık <strong>{{ acik_dof_sayisi }}</strong> DÖF
        {% if geciken_aksiyon_sayisi > 0 %},
        <strong style="color:#dc2626">{{ geciken_aksiyon_sayisi }}</strong> geciken aksiyon
        {% endif %} bulunmaktadır.
      </div>
    </div>
  </div>
  <a href="{{ url_for('kalite.dof_benim') }}"
     style="background:#f59e0b;color:#fff;padding:6px 14px;border-radius:8px;font-size:12px;font-weight:600;text-decoration:none">
    Görüntüle →
  </a>
</div>
{% endif %}
```

Bu değişkenleri context olarak gönderecek route'lar Claude tarafından güncellenecektir.

---

## GÜNCEL DURUM — P-001 TAMAMLANDI

**P-001 Claude tarafından tamamlandı (2026-05-02):**
- Tüm yeni modeller oluşturuldu (UretimPersoneli, KaliteKontrol, DOF, DOFAksiyon, DOFEk, SekizD, IsAkisiSurec, IsAkisiAdim)
- 12 istasyon + 14 personel seed verisi yüklendi
- `app/kalite_routes.py` — tüm kalite blueprint route'ları hazır
- Migration tamamlandı, servis çalışıyor

**Codex için şu an açık (unblocked) görevler:**
- **P-004b** → personel.html + personel_detay.html ← HEMEN BAŞLA
- **K-002** → dof_listesi.html + dof_yeni.html + dof_detay.html ← HEMEN BAŞLA
- **K-004** → sekizd_listesi.html + sekizd_form.html + sekizd_detay.html ← HEMEN BAŞLA
- **K-006** → surec_listesi.html + surec_goruntur.html + surec_duzenle.html ← HEMEN BAŞLA

**Codex için yakında açılacak (Claude bitirince):**
- P-006 → Planlama dashboard (P-002/P-003 bitmesi gerekiyor)
- P-007 → Üretim dashboard (P-004a bitmesi gerekiyor)
- P-008 → Kalite dashboard (zaten hazır backend ile)
- K-007 → DÖF performans widget'ları

---

## GÖREVLERI TAMAMLAMA SIRASI

1. **P-004b** → personel.html + personel_detay.html (HEMEN BAŞLA)
2. **K-002** → dof_listesi.html + dof_yeni.html + dof_detay.html (HEMEN BAŞLA)
3. **K-004** → sekizd_listesi.html + sekizd_form.html + sekizd_detay.html (HEMEN BAŞLA)
4. **K-006** → surec_listesi.html + surec_goruntur.html + surec_duzenle.html (HEMEN BAŞLA)
5. **P-008** → kalite/dashboard.html oluştur (backend hazır, hemen başlanabilir)
6. **P-006** → planlama/dashboard.html yeniden yaz (Claude P-002/P-003 bitince)
7. **P-007** → uretim/dashboard.html yeniden yaz (Claude P-004a bitince)
8. **K-007** → dof_performans.html + dashboard widget'ları (en son)

---

## ÖNEMLİ NOTLAR

- `app/templates/kalite/` dizini yoksa oluştur: `mkdir -p /root/erlau-app/app/templates/kalite/`
- Tüm templateler Türkçe karakter içerebilir (metin olarak), ama HTML id/name/class'larında kullanma
- `current_user` değişkeni her template'de otomatik mevcut (Flask-Login)
- Tarih formatı: `{{ tarih.strftime('%d.%m.%Y') }}`
- Yüzde formatı: `{{ "%.1f"|format(deger) }}%`
- Boş değer: `{{ deger or '—' }}`
- Chart.js CDN: `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>` — `{% block content %}` içinde son satıra ekle
