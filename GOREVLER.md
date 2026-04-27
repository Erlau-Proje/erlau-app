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

### [G-009] CLAUDE — AI Teklif Analizi `[BEKLIYOR — G-005 SONRASI]`
**Durum:** `[✓] Claude üstlendi`

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
| G-009 | AI Teklif Analizi | Claude | ⬜ Bekliyor (G-005 sonrası) |
