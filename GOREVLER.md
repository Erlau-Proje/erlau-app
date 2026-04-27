# GÖREVLER — AI Koordinasyon Dosyası

## Nasıl Çalışır
1. **Claude** bu dosyaya görev yazar — kime, ne yapacak, hangi dosyada
2. **Codex veya Gemini** görevi okur, uygular, durumu `[TAMAMLANDI]` yapar
3. **Claude** değişiklikleri kontrol eder, onaylar veya düzeltir

> **NOT:** Tüm görevler `ONAY BEKLENİYOR` durumundadır. Kullanıcı onayından sonra aktive edilecektir.

---

## FAZ 1 — Portal ve Mimari Altyapı

### [G-001] CODEX — Portal Landing Page `[ONAY BEKLENİYOR]`
**Dosya:** `app/templates/portal.html` (YENİ)
**Açıklama:**
- IP:5000 adresine gelen kullanıcı bu sayfayı görür (login gerekmez)
- 5 büyük buton: Satınalma, Üretim, Bakım, Sevkiyat, Planlama
- **Tasarım:** Koyu/parlak gradient arka plan (siyah-lacivert-mor), cam efekti (glassmorphism) butonlar, her butonun simgesi ve kısa açıklaması olacak
- **Sevkiyat butonu:** Disabled görünüm + "Yakında" etiketi, tıklanamaz
- Tailwind CSS kullan (CDN zaten var)
- Mobil uyumlu olmalı

**Bağlantılar:**
- Satınalma → `/login` (mevcut)
- Üretim → `/uretim/login`
- Bakım → `/bakim/login`
- Sevkiyat → `#` (disabled)
- Planlama → `/planlama/login`

**Durum:** `[ ] Bekliyor`

---

### [G-002] GEMINI — Veritabanı Modelleri Genişletme `[ONAY BEKLENİYOR]`
**Dosya:** `app/models.py`
**Açıklama:** Aşağıdaki yeni modelleri mevcut `models.py`'ye ekle. Mevcut modellere dokunma.

**Eklenecek Modeller:**

```python
# Malzeme Listesi (admin yönetir)
class Malzeme(db.Model):
    __tablename__ = 'malzeme'
    id = db.Column(db.Integer, primary_key=True)
    stok_kodu = db.Column(db.String(20), unique=True)  # otomatik üretilecek: MLZ-00001
    malzeme_adi = db.Column(db.String(200), nullable=False)
    birim = db.Column(db.String(20))
    kategori = db.Column(db.String(100))
    aciklama = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Ürün Listesi
class Urun(db.Model):
    __tablename__ = 'urun'
    id = db.Column(db.Integer, primary_key=True)
    urun_kodu = db.Column(db.String(20), unique=True)  # otomatik: URN-00001
    urun_adi = db.Column(db.String(200), nullable=False)
    proje = db.Column(db.String(100))
    makine = db.Column(db.String(100))
    aciklama = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Çoklu Tedarikçi Teklifi
class TeklifGrubu(db.Model):
    __tablename__ = 'teklif_grubu'
    id = db.Column(db.Integer, primary_key=True)
    teklif_no = db.Column(db.String(30), unique=True)  # otomatik: TKL-2026-00001
    talep_kalem_id = db.Column(db.Integer, db.ForeignKey('talep_kalem.id'))
    durum = db.Column(db.String(30), default='bekliyor')  # bekliyor, teklif_alindi, secildi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    kalemler = db.relationship('TeklifKalem', backref='grup', lazy=True)

class TeklifKalem(db.Model):
    __tablename__ = 'teklif_kalem'
    id = db.Column(db.Integer, primary_key=True)
    grup_id = db.Column(db.Integer, db.ForeignKey('teklif_grubu.id'))
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'))
    birim_fiyat = db.Column(db.Float)
    para_birimi = db.Column(db.String(10))
    vade_gun = db.Column(db.Integer)
    kaynak = db.Column(db.String(20))  # 'mail', 'excel', 'pdf', 'manuel'
    teklif_dosyasi = db.Column(db.String(500))  # dosya yolu
    mail_referans = db.Column(db.String(100))  # outlook mail ID
    secildi = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# İş İstasyonu (Üretim)
class IsIstasyonu(db.Model):
    __tablename__ = 'is_istasyonu'
    id = db.Column(db.Integer, primary_key=True)
    istasyon_kodu = db.Column(db.String(20), unique=True)
    istasyon_adi = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Üretim Planı (Planlama departmanı girer)
class UretimPlani(db.Model):
    __tablename__ = 'uretim_plani'
    id = db.Column(db.Integer, primary_key=True)
    plan_no = db.Column(db.String(30), unique=True)
    hafta = db.Column(db.Integer)
    yil = db.Column(db.Integer)
    baslangic_tarihi = db.Column(db.Date)
    bitis_tarihi = db.Column(db.Date)
    planlayan_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    durum = db.Column(db.String(20), default='taslak')  # taslak, aktif, tamamlandi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    satirlar = db.relationship('UretimPlaniSatir', backref='plan', lazy=True)

class UretimPlaniSatir(db.Model):
    __tablename__ = 'uretim_plani_satir'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('uretim_plani.id'))
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'))
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'))
    tarih = db.Column(db.Date)
    planlanan_adet = db.Column(db.Integer)

# Günlük Üretim Kaydı
class UretimKaydi(db.Model):
    __tablename__ = 'uretim_kaydi'
    id = db.Column(db.Integer, primary_key=True)
    plan_satir_id = db.Column(db.Integer, db.ForeignKey('uretim_plani_satir.id'), nullable=True)
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'))
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'))
    tarih = db.Column(db.Date)
    gerceklesen_adet = db.Column(db.Integer, default=0)
    fire_adet = db.Column(db.Integer, default=0)
    giren_personel_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    aciklama = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Arıza Kaydı
class ArizaKaydi(db.Model):
    __tablename__ = 'ariza_kaydi'
    id = db.Column(db.Integer, primary_key=True)
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'))
    tarih = db.Column(db.Date)
    baslangic_saati = db.Column(db.Time)
    bitis_saati = db.Column(db.Time)
    aciklama = db.Column(db.Text)
    durum = db.Column(db.String(20), default='acik')  # acik, kapalı
    giren_personel_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Makine / Ekipman
class Makine(db.Model):
    __tablename__ = 'makine'
    id = db.Column(db.Integer, primary_key=True)
    makine_kodu = db.Column(db.String(20), unique=True)
    makine_adi = db.Column(db.String(200))
    marka = db.Column(db.String(100))
    model = db.Column(db.String(100))
    seri_no = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)

# Bakım Planı
class BakimPlani(db.Model):
    __tablename__ = 'bakim_plani'
    id = db.Column(db.Integer, primary_key=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id'))
    bakim_adi = db.Column(db.String(200))
    periyot_gun = db.Column(db.Integer)  # kaç günde bir
    son_bakim_tarihi = db.Column(db.Date)
    sonraki_bakim_tarihi = db.Column(db.Date)
    aciklama = db.Column(db.Text)

# Bakım Kaydı
class BakimKaydi(db.Model):
    __tablename__ = 'bakim_kaydi'
    id = db.Column(db.Integer, primary_key=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id'))
    bakim_plani_id = db.Column(db.Integer, db.ForeignKey('bakim_plani.id'), nullable=True)
    bakim_turu = db.Column(db.String(30))  # periyodik, ariza, gunluk
    tarih = db.Column(db.Date)
    yapilan_isler = db.Column(db.Text)
    sure_dakika = db.Column(db.Integer)
    giren_personel_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**KRITIK:** `stok_kodu` ve `urun_kodu` için `utils.py`'de otomatik üretim fonksiyonu yaz:
```python
def generate_stok_kodu():  # MLZ-00001 formatı
def generate_urun_kodu():  # URN-00001 formatı
def generate_teklif_no():  # TKL-2026-00001 formatı
def generate_plan_no():    # PLN-2026-W01 formatı (hafta numaralı)
```

**Durum:** `[ ] Bekliyor`

---

## FAZ 2 — Satınalma İyileştirmeleri

### [G-003] CODEX — Malzeme ve Ürün Autocomplete `[ONAY BEKLENİYOR]`
**Dosya:** `app/templates/yeni_talep.html`
**Açıklama:**
- Malzeme adı alanına 3 harf/rakam girildiğinde `/api/malzeme-ara?q=xxx` endpoint'ini çağır
- Açılan dropdown'dan seçince birim alanı otomatik dolsun
- Ürün/Proje/Makine alanı: 3 karakter sonrası `/api/urun-ara?q=xxx` çağır
- Eğer girilen ürün listede yoksa otomatik kaydet (arka planda `POST /api/urun-ekle`)
- JavaScript ile yap, harici kütüphane kullanma

**Durum:** `[ ] Bekliyor`

---

### [G-004] GEMINI — Malzeme ve Ürün CRUD Sayfaları `[ONAY BEKLENİYOR]`
**Dosya:** `app/routes.py` (admin blueprint'e ekle) + yeni template'ler
**Açıklama:**
- `/admin/malzemeler` → Malzeme listesi, ekle/düzenle/sil (inline edit veya modal)
- `/admin/urunler` → Ürün listesi, ekle/düzenle/sil
- `/api/malzeme-ara` → GET, `q` parametresi, JSON döndür
- `/api/urun-ara` → GET, `q` parametresi, JSON döndür
- `/api/urun-ekle` → POST, yeni ürünü kaydet, `urun_kodu` otomatik üretilsin
- Sol menüde admin rolüne "Malzeme Listesi" ve "Ürün Listesi" linkleri ekle

**Durum:** `[ ] Bekliyor`

---

### [G-005] GEMINI — Çoklu Tedarikçi Teklif Sistemi `[ONAY BEKLENİYOR]`
**Dosya:** `app/routes.py` + `app/templates/teklif_yonetimi.html` (YENİ)
**Açıklama:**
- Satınalma panelinde her talep kalemine "Teklif İste" butonu ekle
- Tıklanınca tedarikçi seçim modalı açılsın (çoklu seçim, 2-3 tedarikçi)
- `TeklifGrubu` oluşturulsun, her tedarikçi için `TeklifKalem` kaydı
- Teklif karşılaştırma sayfası: tedarikçilerin fiyatları yan yana görünsün
- "Seç" butonu ile en uygun teklif seçilsin, `TalepKalem`'e işlensin

**Durum:** `[ ] Bekliyor`

---

## FAZ 3 — Üretim Modülü

### [G-006] GEMINI — Üretim Blueprint ve Sayfalar `[ONAY BEKLENİYOR]`
**Dosya:** `app/routes.py` (uretim blueprint) + template'ler
**Açıklama:**
- `/uretim/dashboard` → İş istasyonları + bugünün planı
- `/uretim/giris` → Günlük üretim adedi girişi (planlanan gösterilsin, gerçekleşen girilsin)
- `/uretim/ariza` → Arıza kaydı oluştur
- `/uretim/raporlar` → Planlanan vs Gerçekleşen raporu, tarih aralığı filtresi
- `/uretim/istasyonlar` → İstasyon tanımla/düzenle (sadece üretim DY)
- Sol menüde "Üretim Raporları" linki → tüm DY ve GM görebilir

**Durum:** `[ ] Bekliyor`

---

## FAZ 4 — Bakım Modülü

### [G-007] GEMINI — Bakım Blueprint ve Sayfalar `[ONAY BEKLENİYOR]`
**Dosya:** `app/routes.py` (bakim blueprint) + template'ler
**Açıklama:**
- `/bakim/dashboard` → Bugünkü bakımlar + yaklaşan periyodik bakımlar
- `/bakim/kayit` → Günlük bakım kaydı gir
- `/bakim/plan` → Makine periyodik bakım planı görüntüle/ekle
- `/bakim/takvim` → Aylık bakım takvimi (Calendar view)
- `/bakim/raporlar` → Bakım geçmişi, makine bazlı rapor
- `/bakim/makineler` → Makine listesi CRUD

**Durum:** `[ ] Bekliyor`

---

## FAZ 5 — Planlama Modülü

### [G-008] CODEX — Planlama Arayüzü `[ONAY BEKLENİYOR]`
**Dosya:** `app/templates/planlama/` (YENİ klasör) + route'lar
**Açıklama:**
- `/planlama/dashboard` → Haftalık plan takvimi görünümü (7 kolon = 7 gün)
- `/planlama/yeni-plan` → Yeni haftalık plan oluştur
  - Ürün seç, iş istasyonu seç, günlere adet dağıt
  - Planı "Aktif Et" ile yayınla
- `/planlama/planlar` → Geçmiş planlar listesi
- Üretim bölümünde aktif planın satırları gözüksün

**Durum:** `[ ] Bekliyor`

---

## FAZ 6 — AI: Teklif Okuma (Claude Yapacak)

### [G-009] CLAUDE — AI Teklif Analizi `[ONAY BEKLENİYOR]`
**Dosya:** `app/fatura_ai.py` (genişletilecek) + yeni `app/teklif_ai.py`
**Açıklama:**
- PDF/Excel teklif dosyası yükleme
- Claude Haiku ile dosyadan: tedarikçi, birim fiyat, para birimi, vade, geçerlilik tarihi çıkar
- Çıkarılan bilgiyi `TeklifKalem`'e kaydet, kaynak='pdf' veya kaynak='excel'
- Outlook entegrasyonu: özel teklif numarası (TKL-2026-00001) içeren mailleri eşleştir
  - **NOT:** Outlook API kurulumu gerekecek (Microsoft Graph API) — ayrı değerlendirme

**Durum:** `[ ] Bekliyor`

---

## GÖREV DURUMU ÖZETİ

| Görev | Sorumlu | Durum |
|-------|---------|-------|
| G-001 Portal Landing Page | Codex | Bekliyor |
| G-002 DB Modelleri | Gemini | Bekliyor |
| G-003 Autocomplete | Codex | Bekliyor |
| G-004 Malzeme/Ürün CRUD | Gemini | Bekliyor |
| G-005 Çoklu Teklif | Gemini | Bekliyor |
| G-006 Üretim Modülü | Gemini | Bekliyor |
| G-007 Bakım Modülü | Gemini | Bekliyor |
| G-008 Planlama Arayüzü | Codex | Bekliyor |
| G-009 AI Teklif Analizi | Claude | Bekliyor |
