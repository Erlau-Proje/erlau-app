# GÖREVLER — AI Koordinasyon Dosyası

## Sorumluluklar
| AI | Rol |
|---|---|
| **Claude** | G-002, G-005, G-009 + tüm görevleri review eder |
| **Codex** | G-001, G-003, G-008 |
| **Gemini** | G-004, G-006, G-007 |

## Sıra (bağımlılık sırası)
1. G-002 (Claude — DB temeli, diğerleri buna bağlı)
2. G-001 (Codex — bağımsız)
3. G-004 (Gemini — G-002 sonrası)
4. G-003 (Codex — G-004 sonrası)
5. G-006, G-007, G-008 (paralel — G-002 sonrası)
6. G-005 (Claude — G-003 ve G-004 sonrası)
7. G-009 (Claude — G-005 sonrası)

---

## FAZ 1 — Temel

### [G-002] CLAUDE — Veritabanı Modelleri `[DEVAM EDİYOR]`
**Dosya:** `app/models.py`, `app/utils.py`
**Durum:** `[✓] Claude üstlendi`

---

### [G-001] CODEX — Portal Landing Page `[BEKLIYOR]`
**Dosya:** `app/templates/portal.html` (YENİ), `app/routes.py` (auth blueprint'e `/` route ekle)
**Açıklama:**
- IP:5000'e gelen kullanıcı bu sayfayı görür, login gerekmez
- 5 büyük kart/buton: Satınalma, Üretim, Bakım, Sevkiyat, Planlama
- Tasarım: koyu gradient arka plan (siyah-lacivert-mor), glassmorphism kart efekti, her kartta ikon + başlık + kısa açıklama
- Sevkiyat: disabled, üstünde "Yakında" etiketi, tıklanamaz (pointer-events: none, opacity: 0.5)
- Tailwind CSS CDN (zaten `base.html`'de var, ama portal base'i extend etmeyecek — standalone sayfa)
- Mobil uyumlu grid (md:grid-cols-3, sm:grid-cols-2)
- Bağlantılar: Satınalma→`/login`, Üretim→`/uretim`, Bakım→`/bakim`, Planlama→`/planlama`
- `app/routes.py` dosyasındaki `auth` blueprint'ine şu route'u ekle:
  ```python
  @auth.route('/', methods=['GET'])
  def portal():
      if current_user.is_authenticated:
          return redirect(url_for('main.dashboard'))
      return render_template('portal.html')
  ```
**Durum:** `[ ] Bekliyor`

---

## FAZ 2 — Satınalma İyileştirmeleri

### [G-003] CODEX — Autocomplete (Malzeme + Ürün) `[BEKLIYOR — G-004 SONRASI]`
**Dosya:** `app/templates/yeni_talep.html`
**Açıklama:**
- Malzeme adı input'una kullanıcı 3+ karakter girince `/api/malzeme-ara?q=XXX` çağır (fetch API)
- Sonuçları input'un altında dropdown olarak göster, seçince birim alanı otomatik dolsun
- Proje/Makine/Ürün alanına 3+ karakter girince `/api/urun-ara?q=XXX` çağır
- Listede yoksa otomatik `POST /api/urun-ekle` ile kaydet (kullanıcıya bildir: "Yeni ürün eklendi")
- Saf JS kullan, harici kütüphane yok
- Dropdown klavye ile de gezinebilsin (ArrowUp, ArrowDown, Enter)
**Durum:** `[ ] Bekliyor`

---

### [G-005] CLAUDE — Çoklu Tedarikçi Teklif Sistemi `[BEKLIYOR — G-004 SONRASI]`
**Dosya:** `app/routes.py`, `app/templates/`
**Durum:** `[✓] Claude üstlendi`

---

## FAZ 3 — Yeni Modüller

### [G-004] GEMINI — Malzeme + Ürün CRUD `[BEKLIYOR — G-002 SONRASI]`
**Dosya:** `app/routes.py` (admin blueprint), yeni template'ler
**Açıklama:**
- `/admin/malzemeler` → Malzeme listesi sayfası
  - Tablo: stok_kodu, malzeme_adi, birim, kategori, is_active, işlemler
  - Her satır inline düzenlenebilir (double-click ile edit modu) VEYA modal
  - Yeni malzeme ekle butonu (form: malzeme_adi, birim, kategori)
  - Sil butonu (soft delete: is_active=False)
  - stok_kodu otomatik: `utils.generate_stok_kodu()` çağır
- `/admin/urunler` → Ürün listesi sayfası (aynı yapı)
  - Tablo: urun_kodu, urun_adi, proje, makine, is_active, işlemler
  - urun_kodu otomatik: `utils.generate_urun_kodu()` çağır
- API endpoint'leri (JSON döndür):
  - `GET /api/malzeme-ara?q=XXX` → `[{"id":1,"malzeme_adi":"Vida","birim":"Adet","stok_kodu":"MLZ-00001"}]`
  - `GET /api/urun-ara?q=XXX` → `[{"id":1,"urun_adi":"Zincir A","urun_kodu":"URN-00001"}]`
  - `POST /api/urun-ekle` body: `{"urun_adi":"XXX"}` → yeni Urun kaydı oluştur, JSON döndür
- Sol menüde admin rolüne "Malzeme Listesi" ve "Ürün Listesi" linkleri ekle (`base.html`)
**Durum:** `[ ] Bekliyor`

---

### [G-006] GEMINI — Üretim Modülü `[BEKLIYOR — G-002 SONRASI]`
**Dosya:** `app/routes.py` (uretim blueprint ekle), `app/templates/uretim/`
**Açıklama:**
- Blueprint: `uretim = Blueprint('uretim', __name__, url_prefix='/uretim')`
- `/uretim/` → Dashboard: bugünkü plan + istasyon kartları + toplam planlanan/gerçekleşen
- `/uretim/giris` → Günlük üretim giriş formu
  - İstasyon seç, ürün seç, tarih (bugün default), planlanan adet (readonly, plandan gelir), gerçekleşen adet, fire, açıklama
  - Kaydet → `UretimKaydi` oluştur
- `/uretim/ariza` → Arıza kaydı formu (istasyon, başlangıç/bitiş saati, açıklama)
- `/uretim/raporlar` → Planlanan vs Gerçekleşen tablosu
  - Filtre: tarih aralığı, istasyon, ürün
  - Grafik: Chart.js bar chart (CDN zaten var)
  - Erişim: rol in ['uretim', 'departman_yoneticisi', 'gm', 'admin']
- `/uretim/istasyonlar` → İstasyon CRUD (sadece rol='departman_yoneticisi' ve department='Üretim')
- Sol menüde "Üretim Raporları" linki: tüm DY ve GM görebilir
- `create_app()` içine blueprint'i kaydet
**Durum:** `[ ] Bekliyor`

---

### [G-007] GEMINI — Bakım Modülü `[BEKLIYOR — G-002 SONRASI]`
**Dosya:** `app/routes.py` (bakim blueprint ekle), `app/templates/bakim/`
**Açıklama:**
- Blueprint: `bakim = Blueprint('bakim', __name__, url_prefix='/bakim')`
- `/bakim/` → Dashboard: bugünkü bakımlar + yaklaşan periyodikler (7 gün içinde)
- `/bakim/kayit` → Bakım kaydı formu (makine seç, tür: günlük/periyodik/arıza, tarih, yapılan işler, süre)
- `/bakim/makineler` → Makine listesi CRUD (makine_kodu otomatik: `MKN-00001`)
- `/bakim/plan` → Makine bazlı periyodik bakım planları (makine, bakım_adi, periyot_gun, son_bakim_tarihi)
  - `sonraki_bakim_tarihi` = son_bakim_tarihi + periyot_gun (otomatik hesapla)
- `/bakim/takvim` → Aylık takvim view (basit tablo: satır=makine, sütun=günler, hücreler renkli)
- `/bakim/raporlar` → Makine bakım geçmişi, filtre: makine, tarih aralığı
  - Erişim: rol in ['bakim', 'departman_yoneticisi', 'gm', 'admin']
- Sol menüde "Bakım Raporları" linki: DY ve GM görebilir
- `create_app()` içine blueprint'i kaydet
**Durum:** `[ ] Bekliyor`

---

### [G-008] CODEX — Planlama Modülü Arayüzü `[BEKLIYOR — G-002 SONRASI]`
**Dosya:** `app/routes.py` (planlama blueprint ekle), `app/templates/planlama/`
**Açıklama:**
- Blueprint: `planlama = Blueprint('planlama', __name__, url_prefix='/planlama')`
- `/planlama/` → Dashboard: bu haftanın aktif planı, özet kartlar
- `/planlama/yeni` → Yeni haftalık plan formu
  - Plan no otomatik: `utils.generate_plan_no()`
  - Dinamik satır ekle: ürün seç (autocomplete), istasyon seç, 5 güne adet gir (Pzt-Sal-Çar-Per-Cum)
  - "Kaydet Taslak" ve "Aktif Et" butonları
- `/planlama/planlar` → Geçmiş planlar listesi (plan_no, tarih aralığı, durum, toplam adet)
- Erişim: rol in ['planlama', 'departman_yoneticisi'] AND department in ['Planlama ve Tedarik Zinciri']
- `create_app()` içine blueprint'i kaydet
**Durum:** `[ ] Bekliyor`

---

## FAZ 4 — AI

### [G-009] CLAUDE — AI Teklif Analizi `[BEKLIYOR — G-005 SONRASI]`
**Durum:** `[✓] Claude üstlendi`

---

## DURUM ÖZETİ

| # | Görev | Sorumlu | Durum |
|---|---|---|---|
| G-001 | Portal Landing Page | Codex | ⬜ Bekliyor |
| G-002 | DB Modelleri + utils | Claude | 🔄 Devam ediyor |
| G-003 | Autocomplete JS | Codex | ⬜ Bekliyor (G-004 sonrası) |
| G-004 | Malzeme/Ürün CRUD | Gemini | ⬜ Bekliyor (G-002 sonrası) |
| G-005 | Çoklu Teklif Sistemi | Claude | ⬜ Bekliyor (G-004 sonrası) |
| G-006 | Üretim Modülü | Gemini | ⬜ Bekliyor (G-002 sonrası) |
| G-007 | Bakım Modülü | Gemini | ⬜ Bekliyor (G-002 sonrası) |
| G-008 | Planlama Arayüzü | Codex | ⬜ Bekliyor (G-002 sonrası) |
| G-009 | AI Teklif Analizi | Claude | ⬜ Bekliyor (G-005 sonrası) |
