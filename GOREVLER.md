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

### [G-002] CLAUDE — Veritabanı Modelleri `[TAMAMLANDI]`
**Dosya:** `app/models.py`, `app/utils.py`
**Durum:** `[✅] Tamamlandı — sunucuda test edildi`

---

### [G-001] CODEX — Portal Landing Page `[TAMAMLANDI]`
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
**Durum:** `[✅] Tamamlandı`

---

## FAZ 2 — Satınalma İyileştirmeleri

### [G-003] CODEX — Autocomplete (Malzeme + Ürün) `[TAMAMLANDI]`
**Dosya:** `app/templates/yeni_talep.html`
**Açıklama:**
- Malzeme adı input'una kullanıcı 3+ karakter girince `/api/malzeme-ara?q=XXX` çağır (fetch API)
- Sonuçları input'un altında dropdown olarak göster, seçince birim alanı otomatik dolsun
- Proje/Makine/Ürün alanına 3+ karakter girince `/api/urun-ara?q=XXX` çağır
- Listede yoksa otomatik `POST /api/urun-ekle` ile kaydet (kullanıcıya bildir: "Yeni ürün eklendi")
- Saf JS kullan, harici kütüphane yok
- Dropdown klavye ile de gezinebilsin (ArrowUp, ArrowDown, Enter)
**Durum:** `[✅] Tamamlandı`

---

### [G-005] CLAUDE — Çoklu Tedarikçi Teklif Sistemi `[TAMAMLANDI]`
**Dosya:** `app/routes.py`, `app/templates/teklifler.html`, `app/templates/teklif_detay.html`
**Durum:** `[✅] Tamamlandı — deploy edildi`

---

## FAZ 3 — Yeni Modüller

### [G-004] ~~GEMINI~~ CLAUDE — Malzeme + Ürün CRUD `[TAMAMLANDI]`
**Durum:** `[✅] Tamamlandı — Claude üstlendi, deploy edildi`

---

### [G-006] ~~GEMINI~~ CLAUDE — Üretim Modülü `[TAMAMLANDI]`
**Durum:** `[✅] Tamamlandı — Claude üstlendi, deploy edildi`

---

### [G-007] ~~GEMINI~~ CLAUDE — Bakım Modülü `[TAMAMLANDI]`
**Durum:** `[✅] Tamamlandı — Claude üstlendi, deploy edildi`

---

### [G-008] CODEX — Planlama Modülü Arayüzü `[TAMAMLANDI]`
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
**Durum:** `[✅] Tamamlandı`

---

## FAZ 4 — AI

### [G-009] CLAUDE — AI Teklif Analizi `[✅ TAMAMLANDI]`
**Durum:** `[✓] Claude üstlendi`

---

## HIZLI İYİLEŞTİRMELER

### [I-001] CODEX — Portal'a Geri Dönüş Navigasyonu `[TAMAMLANDI]`
**Dosya:** `app/routes.py`, `app/templates/base.html`, `app/templates/portal.html`, `docs/PORTAL_NAVIGATION.md`
**Açıklama:**
- `/portal` route'u eklendi; giriş yapmış kullanıcılar da portal ekranına dönebilir.
- Sol menüye "Uygulama Portalı" linki eklendi.
- Sidebar logosu portal ekranına bağlandı.
- Portal kartları giriş durumuna göre login veya ilgili modül paneline yönlendirir.
**Durum:** `[✅] Tamamlandı`

---

## DURUM ÖZETİ

| # | Görev | Sorumlu | Durum |
|---|---|---|---|
| G-001 | Portal Landing Page | Codex | ✅ Tamamlandı |
| G-002 | DB Modelleri + utils | Claude | ✅ Tamamlandı |
| G-003 | Autocomplete JS | Codex | ✅ Tamamlandı |
| G-004 | Malzeme/Ürün CRUD | Claude | ✅ Tamamlandı |
| G-005 | Çoklu Teklif Sistemi | Claude | ✅ Tamamlandı |
| G-006 | Üretim Modülü | Claude | ✅ Tamamlandı |
| G-007 | Bakım Modülü | Claude | ✅ Tamamlandı |
| G-008 | Planlama Arayüzü | Codex | ✅ Tamamlandı |
| G-009 | AI Teklif Analizi | Claude | ✅ Tamamlandı (route + UI mevcut) |

---

## FAZ 5 — Üretim Planlama & Takip Modülü (YENİ)

> **Kaynak veri:** Google Sheets "2026 - Üretim Takip Listesi" (14 personel, 12 istasyon)
> **Bağımlılık sırası:** P-001 → P-002 → P-003 → P-004 (paralel) → P-005 → P-006 → P-007 (paralel)

---

### [P-001] CLAUDE — Veritabanı Modelleri + Seed Verisi `[✅ TAMAMLANDI]`

**Dosyalar:** `app/models.py`, `app/utils.py`, migration

**YENİ Modeller:**

#### `UretimPersoneli`
```python
id, ad (str 100), soyad (str 100, nullable),
istasyon_id (FK → is_istasyonu, nullable),
sicil_no (str 20, nullable, unique),
is_active (bool, default=True),
created_at
```
- Sistem kullanıcısından (User) bağımsız, fiziksel üretim çalışanları
- İstasyon ataması zorunlu değil (birden fazla istasyona geçici atama yapılabilir)

#### `KaliteKontrol`
```python
id,
tarih (date, nullable=False),
uretim_kaydi_id (FK → uretim_kaydi, nullable=True),
urun_id (FK → urun, nullable=False),
istasyon_id (FK → is_istasyonu, nullable=False),
kontrol_eden_id (FK → user, nullable=True),
ok_adet (int, default=0),
nok_adet (int, default=0),
nok_neden (str 50, nullable): 'hammadde_hatasi' | 'isleme_hatasi' | 'olcu_hatasi' | 'diger',
nok_neden_aciklama (text, nullable),
nok_akibet (str 20, nullable): 'hurda' | 'tamir',
tamir_plan_satir_id (FK → uretim_plani_satir, nullable): NOK-tamir ise ilgili satır,
created_at
```

**GÜNCELLENECEKler:**

- `UretimKaydi` → `uretim_personeli_id` (FK → uretim_personeli, nullable) ekle
- `UretimPlaniSatir` → `devir_adet` (int, default=0) ekle — bir önceki günden devreden eksik
- `UretimPlaniSatir` → `kaynak` (str 20, default='plan'): 'plan' | 'devir' | 'tamir' ekle

**Seed Verisi (migration sonrası çalıştırılacak script):**

İstasyonlar (12 adet — `is_istasyonu` tablosuna insert):
```
Boru Büküm, Sac Lazer, Bornholm, Harmony, Kaynak-1, Kaynak-2,
CNC-Kayar Tezgah, CNC-Fulland, CNC-Topper, Boru Lazer, Abkant, Schlatter
```

Personel (14 kişi — `uretim_personeli` tablosuna insert, istasyon ataması ile):
```
Celalettin       → Boru Büküm
Mehmet Eyigün    → Sac Lazer
Doğan Alıcı      → Bornholm
Osman Aktar      → Harmony
Yahya Sefa Korkut→ Kaynak-1
Lokman Önlü      → Kaynak-2
Özgün            → CNC-Kayar Tezgah
Alişan Yılmaz    → CNC-Fulland
Kadir Kethüda    → CNC-Topper
Ahmet Eryılmaz   → Boru Lazer
Efe Kalaça       → Abkant
Gökhan Ocak      → Schlatter
Oktay Torun      → (atanmamış)
Elvan Kızar      → (atanmamış)
```

**utils.py eklemeleri:**
- `devir_gunu(tarih: date) -> date` — hafta sonu/tatil atlayarak sonraki çalışma gününü döndürür
- `haftalik_gunden_gune_dagit(haftalik_adet: int, gun_sayisi: int=5) -> list[int]` — eşit böl, kalanı ilk güne ekle

---

### [P-002] CLAUDE — Haftalık Plan Girişi (Yeniden Tasarım) `[✅ TAMAMLANDI]`

**Dosyalar:** `app/routes.py` (planlama blueprint), `app/templates/planlama/yeni_plan.html`

**Mevcut yeni_plan.html tamamen yeniden yazılacak.**

**Mantık:**
1. Kullanıcı şunu girer: **Ürün** + **İstasyon** + **Haftalık Toplam Adet**
2. Sistem otomatik olarak 5 günlük satır oluşturur (`haftalik_gunden_gune_dagit()`)
3. Kullanıcı dağılımı görebilir ve gün bazlı manuel düzeltme yapabilir (inline edit)
4. "Taslak Kaydet" veya "Aktive Et" butonu

**Route değişikliği:**
```
POST /planlama/yeni
  form fields:
    urun_id[]       → her satır için ürün
    istasyon_id[]   → her satır için istasyon
    haftalik_adet[] → her satır için haftalık toplam hedef
    adet_pzt[]..adet_cum[] → günlük override (opsiyonel, sistem hesaplar)
    baslangic_tarihi, bitis_tarihi, hafta, yil, eylem
```

**Template özellikleri:**
- Dinamik satır ekleme (JS)
- Her satırda haftalık adet girilince gün kutucukları otomatik dolar (JS hesap)
- Ürün autocomplete (mevcut `/api/urun-ara` endpoint'i)
- İstasyon dropdown
- Hafta başlangıç tarihi seçilince Pzt-Cum başlıkları güncellenir (JS)

---

### [P-003] CLAUDE — Gün Sonu Devir Mekanizması `[✅ TAMAMLANDI]`

**Dosyalar:** `app/routes.py` (yeni route), `app/templates/planlama/devir.html`

**Route:**
```
POST /planlama/gun-sonu-devir?tarih=YYYY-MM-DD
```

**Mantık:**
```
1. Verilen tarihe ait aktif plan satırlarını bul
2. Her satır için: eksik = planlanan_adet + devir_adet - toplam_gerceklesen
3. eksik > 0 ise → sonraki çalışma gününde (devir_gunu()) aynı ürün+istasyon için
   YENİ UretimPlaniSatir oluştur: planlanan_adet=eksik, kaynak='devir', devir_adet=0
4. Flash mesajıyla özet göster: "X satırda toplam Y adet devredildi"
```

**Yetki:** `planlama`, `departman_yoneticisi`, `admin`

**UI:** Planlama dashboard'una "Gün Sonu Kapat" butonu eklenir (bugünün tarihi için)
- Onay modalı: "Bugün için XX adet eksik üretim var, yarına devredilecek. Onaylıyor musunuz?"

---

### [P-004a] CLAUDE — Günlük Üretim Girişi (Upgrade) `[✅ TAMAMLANDI]`

**Dosyalar:** `app/routes.py` (uretim blueprint), `app/templates/uretim/giris.html`

**Mevcut `uretim_giris` route'u ve template tamamen yeniden yazılacak.**

**Yeni mantık:**
- Bugünkü aktif plan satırlarını listele (ürün, istasyon, planlanan+devir_adet = toplam hedef)
- Her satır için: gerçekleşen adet + personel seçimi (`UretimPersoneli`)
- Satırlara "Kaynaklı" tag: plan satırı mı, devir mi, tamir mi (renk kodlu)
- Plan dışı (plansız) üretim giriş alanı da bulunur (istasyon + ürün + adet)
- Toplu kayıt: tüm satırlar tek form submit ile kaydedilir

**Template:**
- Tablo: Ürün Kodu | Ürün Adı | İstasyon | Personel | Planlanan | Devir | Toplam Hedef | Gerçekleşen | Fark
- Her satır: `<input type="number" name="gerceklesen_SATIRID">` + personel `<select>`
- Kaynak badge: `plan` (mavi), `devir` (turuncu), `tamir` (kırmızı)
- Alt özet: Toplam hedef / Toplam girilen / Kalan

---

### [P-004b] CODEX — Üretim Personeli Yönetimi + Performans UI `[✅ TAMAMLANDI]`

**Dosyalar:** `app/templates/uretim/personel.html`, `app/templates/uretim/personel_detay.html`

> Backend route'ları Claude tarafından P-001 ile birlikte yazılır. Codex yalnızca template'leri yazar.

**Backend routes (Claude yazar, Codex kullanır):**
```
GET  /uretim/personel                     → personel listesi
POST /uretim/personel/ekle                → yeni personel ekle
POST /uretim/personel/<id>/duzenle        → düzenle
POST /uretim/personel/<id>/pasif          → işten çıkan/pasifleştir
GET  /uretim/personel/<id>                → performans detay sayfası
```

**Template: `personel.html`**
- Tablo: Sicil No | Ad Soyad | İstasyon | Durum (aktif/pasif) | Bu Hafta Üretim | İşlemler
- Ekle formu (inline veya modal): Ad, Soyad, İstasyon seç, Sicil No
- Durum badge: aktif (yeşil), pasif (gri, üstü çizgili)
- Pasifleştirme: onay modal + "işten çıkış tarihi" girişi
- Performans mini widget: her personel satırında son 7 günlük mini bar (sparkline)

**Template: `personel_detay.html`**
- Üst kart: Ad Soyad, İstasyon, Sicil No, Durum, Çalışma Başlangıç Tarihi
- Performans özeti:
  - Bu hafta: Toplam üretim adedi / Çalışılan gün
  - Bu ay: Toplam üretim adedi
  - Günlük ortalama (bu ay)
- Grafik — Son 30 Gün Günlük Üretim (basit bar, Chart.js CDN)
- Tablo — Ürün Bazlı Üretim Dağılımı (bu ay): Ürün | Toplam Adet | %
- Tablo — Son 10 Üretim Kaydı: Tarih | İstasyon | Ürün | Adet

**Context değişkenleri (route'dan gelir):**
```python
# personel.html
personeller: list[UretimPersoneli]  # .performans_bu_hafta eklenir route'da

# personel_detay.html
personel: UretimPersoneli
performans_30gun: list[{tarih, toplam_adet}]
urun_dagilimi: list[{urun_adi, toplam, oran}]
son_kayitlar: list[UretimKaydi]
bu_hafta_toplam: int
bu_ay_toplam: int
gunluk_ortalama: float
```

---

### [P-005] CLAUDE — Kalite Kontrol Modülü `[✅ TAMAMLANDI]`

**Dosyalar:** `app/routes.py` (yeni `kalite` blueprint), `app/templates/kalite/`

**Yeni blueprint:** `kalite = Blueprint('kalite', __name__, url_prefix='/kalite')`
`create_app()` içine kaydet.

**Routes:**
```
GET  /kalite/              → Kalite dashboard (bugünkü + haftalık özet)
GET  /kalite/kontrol       → Günlük kontrol giriş formu
POST /kalite/kontrol       → Kaydet
GET  /kalite/gecmis        → Geçmiş kontroller (filtreli)
```

**Kontrol giriş mantığı:**
1. Bugünkü UretimKaydi'leri listele (istasyon + ürün + toplam gerçekleşen)
2. Her satır için: OK adet + NOK adet girişi (toplam = gerceklesen_adet kontrolü)
3. NOK > 0 ise: neden dropdown + açıklama + akıbet seçimi (hurda/tamir)
4. Tamir seçilirse → o günün aktif plan ID'sine tamir satırı eklenir (`kaynak='tamir'`)
5. `KaliteKontrol` kaydı oluşturulur

**Yetki tanımı:**
```python
def kalite_required(f):
    # rol: 'kalite', 'departman_yoneticisi', 'admin'
```

**Not:** `User.role` alanında `'kalite'` değeri şu an yoktur.
CLAUDE.md'deki rol listesine eklenecek.

---

### [P-006] CLAUDE — Planlama Dashboard Zenginleştirme `[✅ TAMAMLANDI]`

**Dosyalar:** `app/templates/planlama/dashboard.html`

**Mevcut dashboard yeniden tasarlanacak.**

**Gösterilecek veriler ve widget'lar:**

#### Üst Özet Kartlar (4 adet)
| Kart | Veri |
|---|---|
| Bu Hafta Hedef | Aktif plandaki toplam planlanan adet |
| Bu Hafta Gerçekleşen | Toplam UretimKaydi adet (bu hafta) |
| Tamamlanma % | (Gerçekleşen / Hedef) × 100 |
| Devir Adet | Bu hafta biriken toplam devir |

#### Grafik 1 — Günlük Hedef vs Gerçekleşen (Bar Chart)
- X ekseni: Haftanın günleri (Pzt–Cum)
- Bar 1 (gri): Planlanan
- Bar 2 (yeşil): Gerçekleşen
- Bar 3 (turuncu): Devir
- Saf JS + inline SVG veya basit tablo-grafik (Chart.js CDN eklenebilir)

#### Grafik 2 — İstasyon Bazlı Kapasite Kullanımı (Yatay Bar)
- Her istasyon için: gerçekleşen / planlanan (%)
- Renk: >90% yeşil, 70-90% sarı, <70% kırmızı

#### Grafik 3 — Kalite Özeti (Küçük Pie/Donut)
- OK % ve NOK % (bu hafta)
- NOK alt dağılım: hurda / tamir

#### Tablo — Aktif Plan Özeti
- Ürün | İstasyon | Haftalık Hedef | Gerçekleşen | Kalan | % | Devir

#### Devir Takibi
- Devir satırları olan günlerin listesi, kaç adet devretti

---

### [P-007] CLAUDE — Üretim Dashboard Zenginleştirme `[✅ TAMAMLANDI]`

**Dosyalar:** `app/templates/uretim/dashboard.html`

**Mevcut dashboard yeniden tasarlanacak.**

**Widget'lar:**

#### İstasyon Durum Kartları (her istasyon için ayrı kart)
- İstasyon adı | Personel adı | Bugün Hedef | Bugün Gerçekleşen | %
- Renk kodu: tamamlandı (yeşil), devam ediyor (sarı), gecikme (kırmızı)

#### Günlük Üretim Tablosu
- Satır: Ürün | İstasyon | Personel | Planlanan | Gerçekleşen | Fark | Kaynak
- Kaynak renk badge: plan/devir/tamir

#### Haftalık İlerleme Çubuğu
- Her gün için: tamamlanan % (progress bar)
- Bugünkü gün vurgulı

#### Arıza Özeti
- Bu hafta toplam arıza süresi (saat)
- Hangi istasyonlarda arıza var

#### Personel Üretim Sıralaması (bu hafta)
- Ad | Toplam adet | Ortalama günlük

---

### [P-008] CLAUDE — Kalite Dashboard `[✅ TAMAMLANDI]`

**Dosyalar:** `app/templates/kalite/dashboard.html`

**Widget'lar:**

#### Üst Özet Kartlar
- Bugün Kontrol Edilen | OK Adet | NOK Adet | NOK Oranı %

#### Grafik — Günlük OK/NOK Trendi (Son 7 Gün)
- Çizgi grafik: ok_adet ve nok_adet

#### Tablo — NOK Nedenleri Dağılımı (bu hafta)
- Neden | Adet | % | Akıbet (hurda/tamir)

#### Tablo — İstasyon Bazlı Kalite Oranı
- İstasyon | OK | NOK | Oran | Son Kontrol Tarihi

#### Tamir Kuyruğu
- Tamir için plana eklenen satırların listesi: Ürün | İstasyon | Tamir Adedi | Hangi Plan | Durum

---

---

## FAZ 6 — Kalite Yönetim Sistemi (KYS)

> **Bağımlılık:** K-001 → K-002, K-003, K-005 paralel → K-004, K-006 → K-007

---

### [K-001] CLAUDE — DÖF Backend (Model + Logic + Bildirim) `[✅ TAMAMLANDI]`

**Dosyalar:** `app/models.py`, `app/routes.py` (kalite blueprint genişletme)

**YENİ Modeller:**

#### `DOF`
```python
id
dof_no          str(20), unique, not null   # DOF-2026-00001
tarih           date, not null
durum           str(20): 'acik'|'isleniyor'|'kapali'|'gecikti'|'iptal'
hedef_departman str(50)                     # hangi departmana açıldı
hedef_kullanici_id FK → user (nullable)
acan_kullanici_id  FK → user
problem_tanimi  text
kok_neden       text (nullable)
planlanan_kapatma_tarihi date (nullable)
gercek_kapatma_tarihi    date (nullable)
kapatan_kullanici_id FK → user (nullable)
kapatma_notu    text (nullable)
tip             str(10): 'ic'|'tedis'       # iç DÖF veya tedarikçi DÖF
tedarikci_id    FK → tedarikci (nullable)   # tip='tedis' ise dolu
created_at
updated_at
aksiyonlar: relationship → DOFAksiyon
ekler:     relationship → DOFEk
```

#### `DOFAksiyon`
```python
id
dof_id          FK → dof
aksiyon_tanimi  text
sorumlu_id      FK → user (nullable)
planlanan_tarih date
tamamlama_tarihi date (nullable)
durum           str(20): 'bekliyor'|'tamamlandi'|'gecikti'
created_at
```

#### `DOFEk`
```python
id
dof_id          FK → dof
dosya_adi       str(200)
dosya_yolu      str(500)          # app/static/dof_ekler/
dosya_turu      str(20): 'resim'|'pdf'|'diger'
yukleyen_id     FK → user
created_at
```

**utils.py:** `generate_dof_no()` → `DOF-YYYY-NNNNN`

**Routes (kalite blueprint):**
```
GET  /kalite/dof                    → DÖF listesi (tüm, filtreli)
GET  /kalite/dof/yeni               → Yeni DÖF formu
POST /kalite/dof/yeni               → DÖF oluştur
GET  /kalite/dof/<id>               → DÖF detay
POST /kalite/dof/<id>/aksiyon-ekle  → Aksiyon ekle
POST /kalite/dof/<id>/kapat         → DÖF kapat (resim ekle + not)
POST /kalite/dof/<id>/ek-yukle      → Dosya/resim yükle (multipart)
GET  /kalite/dof/benim              → Benim departmanıma açılan DÖF'ler
GET  /api/dof-uyarilar              → JSON: yaklaşan/geciken aksiyonlar
```

**Bildirim mantığı (`/api/dof-uyarilar`):**
```python
# Login olan kullanıcının departmanına açılmış, 3 gün içinde kapanması gereken
# veya süresi geçmiş DÖF/Aksiyonları döndür
{
  "geciken_dof": [...],         # planlanan_kapatma < bugün, durum != 'kapali'
  "yaklasan_aksiyon": [...],    # planlanan_tarih <= bugun+3, durum='bekliyor'
  "geciken_aksiyon": [...]      # planlanan_tarih < bugun, durum='bekliyor'
}
```
Her sayfanın `base.html`'ine küçük bir JS snippet eklenir: login olunca `/api/dof-uyarilar` çağrılır, sonuç varsa header'da badge/uyarı gösterilir.

**Yetki:**
- Açma: `'kalite'` rolü
- Görme (kendi departmanına açılan): tüm roller
- Kapatma: hedef departman kullanıcısı veya `kalite`

---

### [K-002] CODEX — DÖF Arayüzü `[✅ TAMAMLANDI]`

**Dosyalar:** `app/templates/kalite/dof_listesi.html`, `kalite/dof_yeni.html`, `kalite/dof_detay.html`

**`dof_listesi.html`:**
- Filtreler: Departman | Durum | Tarih aralığı | Tip (iç/tedarikçi)
- Tablo: DÖF No | Tarih | Hedef Departman | Problem (kısa) | Durum badge | Aksiyon Tarihi | İşlem
- Durum renkleri: acik=sarı, isleniyor=mavi, kapali=yeşil, gecikti=kırmızı
- "Yeni DÖF Aç" butonu (sadece kalite rolü için görünür)
- Tab: Tümü / Benim Açtıklarım / Benim Departmanıma Açılanlar

**`dof_yeni.html`:**
- Form: Hedef Departman (select), Hedef Kullanıcı (select, opsiyonel)
- Tip seçimi (iç DÖF / Tedarikçi DÖF)
- Tedarikçi seçimi (tip=tedarikçi ise görünür, mevcut tedarikçi listesinden)
- Problem Tanımı (textarea)
- Kök Neden (textarea, opsiyonel)
- Planlanan Kapatma Tarihi (date)
- Aksiyonlar (dinamik: + Aksiyon ekle butonu, her satır: aksiyon, sorumlu, tarih)

**`dof_detay.html`:**
- Başlık: DÖF No, tarih, durum badge
- Sol panel: Problem, Kök Neden, Hedef Departman
- Aksiyonlar tablosu: Tanım | Sorumlu | Planlanan Tarih | Tamamlama Tarihi | Durum | İşlemler
  - Aksiyon tamamla butonu (hedef departman kullanıcısı)
  - Tamamlama tarihi giriş alanı
- Ekler galerisi (yüklenen resimler thumbnail olarak)
- Dosya yükleme formu (resim/pdf)
- Kapat DÖF bölümü (sadece kalite + kapanış notu zorunlu)
- Zaman çizelgesi (timeline): açılış, aksiyon ekleme, tamamlama, kapanış

**Context değişkenleri:**
```python
# dof_listesi.html
doflar: list[DOF]
departmanlar: list[str]  # distinct hedef_departman values
benim_doflarim: list[DOF]

# dof_detay.html
dof: DOF
dof.aksiyonlar: list[DOFAksiyon]
dof.ekler: list[DOFEk]
tedarikci: Tedarikci | None
```

---

### [K-003] CLAUDE — 8D Backend (Model + PDF + Excel) `[✅ TAMAMLANDI]`

**Dosyalar:** `app/models.py`, `app/routes.py` (kalite blueprint)

**YENİ Model: `SekizD`**
```python
id
sekizd_no       str(20), unique               # 8D-2026-00001
tarih           date
tedarikci_id    FK → tedarikci
urun_kodu       str(50, nullable)
urun_adi        str(200, nullable)
revizyon_no     str(10, default='1')
durum           str(20): 'taslak'|'gonderildi'|'kapali'
# D1
d1_ekip_lideri  str(100, nullable)
d1_ekip_uyeleri text (nullable)
# D2 - Problem (5W2H)
d2_problem_ozeti text
d2_kim           str(200, nullable)
d2_ne            str(200, nullable)
d2_nerede        str(200, nullable)
d2_ne_zaman      str(200, nullable)
d2_neden         str(200, nullable)
d2_nasil         str(200, nullable)
d2_ne_kadar      str(200, nullable)
d2_ilk_tespit    str(100, nullable)
# D3 - Geçici Önlem
d3_onlem         text (nullable)
d3_sorumlu       str(100, nullable)
d3_tarih         date (nullable)
d3_etkinlik      str(200, nullable)
# D4 - Kök Neden
d4_kok_neden     text (nullable)
d4_analiz_metod  str(50, nullable): '5why'|'balik_kilcigi'|'diger'
# D5 - Kalıcı Düzeltici Aksiyon
d5_aksiyon       text (nullable)
# D6 - Uygulama
d6_uygulama      text (nullable)
d6_tarih         date (nullable)
d6_dogrulama     str(200, nullable)
# D7 - Önleyici
d7_onleyici      text (nullable)
# D8
d8_tadir         text (nullable)
acan_kullanici_id FK → user
created_at
updated_at
```

**utils.py:** `generate_sekizd_no()` → `8D-YYYY-NNNNN`

**Routes:**
```
GET  /kalite/8d                  → 8D listesi
GET  /kalite/8d/yeni             → Yeni form
POST /kalite/8d/yeni             → Kaydet
GET  /kalite/8d/<id>             → Detay / Düzenle
POST /kalite/8d/<id>             → Güncelle
GET  /kalite/8d/<id>/pdf         → PDF indir (ReportLab)
GET  /kalite/8d/<id>/excel       → Excel indir (openpyxl)
GET  /kalite/8d/<id>/eml         → Outlook taslağı (PDF ekli, mevcut .eml mantığıyla)
```

**PDF içeriği (ReportLab):**
- ERLAU logo alanı, 8D No, Tarih, Tedarikçi, Ürün
- D1–D8 her bölüm ayrı tablo/kutu olarak
- Şirket imza alanı

**Excel içeriği (openpyxl):**
- Tek sayfa, profesyonel format
- Her D bölümü renkli başlık, birleştirilmiş hücreler
- Tedarikçi bilgileri kutusu

---

### [K-004] CODEX — 8D Arayüzü `[✅ TAMAMLANDI]`

**Dosyalar:** `app/templates/kalite/sekizd_listesi.html`, `kalite/sekizd_form.html`, `kalite/sekizd_detay.html`

**`sekizd_listesi.html`:**
- Tablo: 8D No | Tarih | Tedarikçi | Ürün | Durum | İşlemler (PDF, Excel, EML, Detay)
- Filtre: Tedarikçi, Durum, Tarih aralığı
- "Yeni 8D" butonu

**`sekizd_form.html` (yeni + düzenle aynı template):**
- **Bölüm Header:** Tedarikçi seç (dropdown, mevcut `/admin/tedarikciler`'den), Ürün Kodu, Ürün Adı, Revizyon
- **D1 kutu:** Ekip Lideri + Ekip Üyeleri (textarea)
- **D2 kutu:** Problem Özeti (textarea) + 5W2H grid (6 input 2x3 grid)
- **D3 kutu:** Geçici Önlem + Sorumlu + Tarih + Etkinlik
- **D4 kutu:** Kök Neden (textarea) + Analiz Metodu (radio: 5 Why / Balık Kılçığı / Diğer)
- **D5 kutu:** Kalıcı Aksiyon (textarea)
- **D6 kutu:** Uygulama (textarea) + Tarih + Doğrulama
- **D7 kutu:** Önleyici Tedbirler (textarea)
- **D8 kutu:** Ekip Takdiri (textarea)
- Her kutu accordion tarzında açılıp kapanabilir
- "Taslak Kaydet" + "Tamamlandı Kaydet" butonları

**`sekizd_detay.html`:**
- Salt okunur görünüm (D1–D8 bölümleri)
- İndir: PDF | Excel | Outlook Taslağı butonları
- "Düzenle" butonu (kalite rolü)
- Durum badge

---

### [K-005] CLAUDE — İş Akışı Süreçleri Backend `[✅ TAMAMLANDI]`

**Dosyalar:** `app/models.py`, `app/routes.py` (kalite blueprint)

**YENİ Modeller:**

#### `IsAkisiSurec`
```python
id
surec_kodu      str(20), unique               # SRC-001
surec_adi       str(200)
departman       str(50)
aciklama        text (nullable)
versiyon        str(10, default='1.0')
durum           str(20): 'taslak'|'aktif'|'arsiv'
olusturan_id    FK → user
created_at
updated_at
adimlar: relationship → IsAkisiAdim (order_by sira)
```

#### `IsAkisiAdim`
```python
id
surec_id        FK → is_akisi_surec
sira            int                            # gösterim sırası
adim_tipi       str(20): 'baslangic'|'islem'|'karar'|'belge'|'bitis'
adim_adi        str(200)
aciklama        text (nullable)
sorumlu_departman str(50, nullable)
sure_hedef_saat int (nullable)                 # tahmini süre (saat)
evet_sonraki_sira int (nullable)               # karar adımı → evet → hangi sıra
hayir_sonraki_sira int (nullable)              # karar adımı → hayır → hangi sıra
created_at
```

**utils.py:** `generate_surec_kodu()` → `SRC-YYYY-NNN`

**Routes:**
```
GET  /kalite/surecler                   → Süreç listesi
GET  /kalite/surecler/yeni              → Yeni süreç formu
POST /kalite/surecler/yeni              → Kaydet
GET  /kalite/surecler/<id>              → Süreç görüntüle (akış şeması)
GET  /kalite/surecler/<id>/duzenle      → Düzenle
POST /kalite/surecler/<id>/duzenle      → Güncelle
POST /kalite/surecler/<id>/adim-ekle    → Adım ekle
POST /kalite/surecler/<id>/adim-sil     → Adım sil
POST /kalite/surecler/<id>/durum        → Taslak/Aktif/Arşiv
```

**Yetki:**
- Oluştur/Düzenle: `'kalite'`, `admin`
- Görüntüle: Tüm departmanlar (login gerekli)

---

### [K-006] CODEX — İş Akışı Süreç UI `[✅ TAMAMLANDI]`

**Dosyalar:** `app/templates/kalite/surec_listesi.html`, `kalite/surec_goruntur.html`, `kalite/surec_duzenle.html`

**`surec_listesi.html`:**
- Kartlar grid: Her süreç kart → Kod | Ad | Departman | Versiyon | Durum badge | Görüntüle butonu
- Filtre: Departman, Durum
- "Yeni Süreç" butonu (kalite rolü)

**`surec_goruntur.html`:**
Süreç adımlarını görsel akış şeması olarak göster (saf HTML/CSS + JS):
```
Yatay veya dikey akış:
  ⬤ Başlangıç → □ Adım 1 → ◇ Karar?
                              ↓ Evet          ↓ Hayır
                            □ Adım 2a       □ Adım 2b
                              ↓                ↓
                            ⬛ Bitiş         □ Adım 3
```
- SVG tabanlı basit şema (statik, d3.js veya saf SVG)
- Tıklanabilir adımlar: tooltip ile açıklama + sorumlu + süre göster
- Sağ panel: Süreç bilgileri (kod, ad, departman, versiyon, durum)
- PDF/print butonu (window.print() style)

**`surec_duzenle.html`:**
- Üst: Süreç meta bilgileri (ad, departman, açıklama, versiyon)
- Adımlar tablosu: Sıra | Tip | Ad | Açıklama | Sorumlu | Süre | Evet→ | Hayır→ | Sil
- "+ Adım Ekle" satırı (inline form)
- Sıra değiştirme: Yukarı/Aşağı ok butonları
- Her satırda: tip select, adım adı, açıklama, sorumlu departman, süre (saat)

---

### [K-007] CODEX — DÖF & Kalite Performans Widget'ları `[✅ TAMAMLANDI]`

**Dosyalar:** `app/templates/kalite/dof_performans.html` (yeni sayfa), mevcut dashboard template'lerine widget ekleme

**Yeni route (Claude yazar):**
```
GET /kalite/performans          → Tüm departman DÖF performansı (admin/gm için)
GET /kalite/dof/benim-performans → Login kullanıcının departmanının DÖF performansı
```

**`dof_performans.html` (admin/gm görünümü):**
- Tablo: Departman | Açık DÖF | Geciken DÖF | Tamamlanan | Ort. Kapanış Süresi (gün) | Performans %
- Renk kodu: %100 yeşil, %80+ sarı, <%80 kırmızı
- Grafik: Departman bazlı stacked bar (Açık / Geciken / Kapalı)
- Filtre: Tarih aralığı (son 30 gün / 90 gün / bu yıl)

**Her departman dashboard'una eklenecek mini widget:**
```html
<!-- app/templates/base.html'e koşullu olarak veya ilgili departman dashboard'una -->
<div id="dof-widget">
  <span>Açık DÖF: <strong>{{ acik_dof_sayisi }}</strong></span>
  <span>Geciken Aksiyon: <strong class="text-red-600">{{ geciken_aksiyon }}</strong></span>
</div>
```
- `uretim/dashboard.html`, `planlama/dashboard.html`, `bakim/dashboard.html`'e ekle
- Tıklayınca `/kalite/dof/benim` sayfasına gider

---

## GÖREV DAĞILIMI — Kim Ne Yapıyor

### Claude (Backend + Logic)
| # | Görev |
|---|---|
| P-001 | DB Modelleri + Seed |
| P-002 | Haftalık Plan Logic |
| P-003 | Devir Mekanizması |
| P-004a | Günlük Üretim Girişi Backend |
| P-005 | Kalite Kontrol OK/NOK Backend |
| K-001 | DÖF Backend + Bildirim |
| K-003 | 8D Backend + PDF + Excel |
| K-005 | İş Akışı Backend |

### Codex (Frontend + Templates)
| # | Görev |
|---|---|
| P-004b | Personel Yönetimi + Performans UI |
| P-006 | Planlama Dashboard HTML |
| P-007 | Üretim Dashboard HTML |
| P-008 | Kalite Dashboard HTML |
| K-002 | DÖF Arayüzü HTML |
| K-004 | 8D Arayüzü HTML |
| K-006 | İş Akışı Süreç UI |
| K-007 | DÖF Performans Widget'ları |

---

## TAM GÖREV TABLOSU

| # | Görev | Sorumlu | Bağımlılık | Durum |
|---|---|---|---|---|
| P-001 | DB Modelleri + Seed | Claude | — | ✅ |
| P-002 | Haftalık Plan Logic | Claude | P-001 | ✅ |
| P-003 | Devir Mekanizması | Claude | P-002 | ✅ |
| P-004a | Günlük Üretim Girişi | Claude | P-002 | ✅ |
| P-004b | Personel Yönetimi UI | Codex | P-001 | ✅ |
| P-005 | Kalite Kontrol Backend | Claude | P-004a | ✅ |
| P-006 | Planlama Dashboard HTML | Claude | P-003, P-005 | ✅ |
| P-007 | Üretim Dashboard HTML | Claude | P-004a | ✅ |
| P-008 | Kalite Dashboard HTML | Codex | P-005 | ✅ |
| K-001 | DÖF Backend + Bildirim | Claude | — | ✅ |
| K-002 | DÖF Arayüzü HTML | Codex | K-001 | ✅ |
| K-003 | 8D Backend + PDF/Excel | Claude | K-001 ile paralel | ✅ |
| K-004 | 8D Arayüzü HTML | Codex | K-003 | ✅ |
| K-005 | İş Akışı Backend | Claude | — | ✅ |
| K-006 | İş Akışı UI | Codex | K-005 | ✅ |
| K-007 | DÖF Performans Widget'ları | Codex | K-001, K-002 | ✅ |

---

## FAZ 7 — Bakım Yönetim Sistemi (B serisi)

> **Gereksinim:** Planlı bakım takvimi, arıza tamir kayıt, periyodik dış kontroller, üretim planı ile entegrasyon, GM dashboard erişimi.

### [B-001] CLAUDE — DB Model Güncellemeleri + 127 Makine Import `[✅ TAMAMLANDI — 2026-05-02]`
- `Makine` modeline `islev`, `lokasyon`, `guc_kw`, `uretim_yili`, `istasyon_id` eklendi
- `BakimKaydi` modeline `baslangic_saati`, `bitis_saati`, `parca_kullanildi`, `kullanilan_parcalar` eklendi
- Yeni model: `PlanliBakim` (tarihli bakım penceresi, durum takibi)
- Yeni model: `PeriyodikKontrol` (dış firma kontrolleri, periyot uyarısı)
- Google Sheets'ten 127 makine import edildi (MAK-0001 → MAK-0127)

### [B-002] CLAUDE — Backend Routes `[✅ TAMAMLANDI — 2026-05-02]`
- `GET/POST /bakim/program` — Planlı bakım listesi + ekleme, durum güncelleme
- `GET/POST /bakim/ariza-tamir` — Arıza tamir kaydı (süre, parça, başlangıç/bitiş saati)
- `GET/POST /bakim/periyodik` — Periyodik kontrol listesi + ekleme + güncelleme
- `GET /api/bakim-kontrol` — Üretim planı için bakım uyarısı API'si

### [B-003] CLAUDE — Template'ler + Navigasyon `[✅ TAMAMLANDI — 2026-05-02]`
- `bakim/program.html` — Planlı bakım listesi + ekle modal
- `bakim/ariza_tamir.html` — Arıza tamir kayıt formu + özet istatistikler
- `bakim/periyodik.html` — Periyodik kontrol listesi + 30 gün uyarısı
- `base.html` navigasyona 3 yeni bakım linki eklendi
- `planlama/yeni_plan.html` — İstasyon seçilince bakım uyarısı (JS fetch)

### [B-004] CLAUDE — Bakım Dashboard Zenginleştirme `[✅ TAMAMLANDI — 2026-05-02]`
- 4 istatistik kartı: bu ay arıza (trend ok ile), bakım süresi (saat), arıza oranı (%), periyodik kontrol uyarısı
- En sık arıza yapan makineler widget'ı (son 30 gün, top 5, bar chart)
- Periyodik kontrol uyarıları (30 gün içinde, gecikmiş olanlar kırmızı)
- `bakim_dashboard()` route'una yeni SQL sorguları eklendi
- `bakim/dashboard.html` tamamen yeniden tasarlandı

### [B-005] CLAUDE — Admin Sunucu Dashboard `[✅ TAMAMLANDI — 2026-05-02]`
- CPU / RAM / disk kullanımı — renk kodlu progress bar, 5 sn'de bir otomatik AJAX güncelleme
- Aktif kullanıcılar (son 30 dk `son_giris` bazlı, avatar + rol + giriş saati)
- Şifreli restart butonu — admin şifresi doğrulanınca `systemctl restart erlau`
- `psutil==7.2.2` requirements.txt'e eklendi
- `/admin/sunucu` route + `/admin/sunucu/durum` (AJAX) + `/admin/sunucu/restart` (POST)
- `admin/sunucu_dashboard.html` oluşturuldu
- Sol menüye admin rolü için "Sunucu Durumu" linki eklendi

### [B-006] — Ek Gereksinim: can.otu Admin `[✅ TAMAMLANDI — 2026-05-02]`
- `can.otu@erlau.com.tr` → `admin` rolüne yükseltildi

---

## TAM GÖREV TABLOSU (B serisi)

| # | Görev | Sorumlu | Durum |
|---|---|---|---|
| B-001 | DB Modelleri + 127 Makine Import | Claude | ✅ |
| B-002 | Backend Routes | Claude | ✅ |
| B-003 | Template'ler + Navigasyon | Claude | ✅ |
| B-004 | Bakım Dashboard Zenginleştirme | Claude | ✅ |
| B-005 | Admin Sunucu Dashboard | Claude | ✅ |
| B-006 | can.otu → admin yetki | Claude | ✅ |

---

## FAZ 8 — Yetki ve Talep Kriterleri Yönetimi

### [Y-001] CODEX — Admin Yetki Matrisi + Gelişmiş Kullanıcı Yönetimi `[✅ TAMAMLANDI — 2026-05-03]`
- Admin kullanıcı ekranı rol, departman, ünvan, telefon, durum ve özel yetkileri düzenleyebilir.
- Özel yetkiler görünür hale getirildi: `liste_yetki`, `teknik_resim_yetki`, `bildirim_email`, `unvan_pdf_goster`.
- `/admin/yetki-matrisi` ekranı eklendi: satırlarda yapılabilen işlemler, sütunlarda kullanıcılar, izinli olanlar X ile gösterilir.
- Matris düzenlenebilir hale getirildi: checkbox ile kişi bazlı izin aç/kapat yapılır, `/admin/yetki-matrisi/kaydet` ile `user_permission` tablosuna yazılır.
- Route erişimleri merkezi `app/permissions.py` kataloğu ve kişi bazlı izinlerle kontrol edilir.

### [Y-002] CODEX — Yeni Talep Malzeme Kriterleri Admin Yönetimi `[TODO]`
**Gereksinim:** Admin hesabı, yeni satın alma talebi ekranındaki Malzeme Listesi kriterlerini ekleyebilmeli, çıkarabilmeli ve düzenleyebilmelidir.

**Kapsam:**
- `malzeme_turu[]`, `birim[]`, `hedef[]`, `kullanim_amaci[]`, `kullanilan_alan[]` gibi select seçenekleri veritabanından yönetilebilir hale getirilecek.
- Admin panelinde “Talep Kriterleri” ekranı oluşturulacak.
- Kriter tipi, görünen ad, değer, sıralama, aktif/pasif durumu yönetilecek.
- `yeni_talep.html` hardcoded option değerleri yerine route context’inden gelen kriterleri kullanacak.
- Mevcut kayıtların eski değerleri bozulmayacak; kriter silme fiziksel silme yerine pasife alma olarak yapılacak.
