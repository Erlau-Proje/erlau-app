# Erlau Satın Alma Yönetim Sistemi — CLAUDE.md

## Proje Özeti

Flask tabanlı kurumsal satın alma, teklif, sipariş ve muhasebe yönetim sistemi.

- **Sunucu:** 178.104.49.105:5000
- **Servis:** `systemctl restart erlau` (Gunicorn + systemd)
- **Git:** github.com/Erlau-Proje/erlau-app (main branch)
- **DB:** SQLite (`instance/erlau.db`) — ileride PostgreSQL'e geçiş planlanıyor

## Teknoloji

- Python 3.12, Flask, SQLAlchemy, Flask-Login, Flask-Migrate
- Tailwind CSS (CDN), vanilla JS
- ReportLab (PDF), openpyxl (Excel), Anthropic Claude Haiku (AI özellikler)

## Klasör Yapısı

```
app/
  __init__.py       # create_app, blueprint kayıtları
  models.py         # SQLAlchemy modeller
  routes.py         # Tüm route'lar (main, satin_alma, admin, muhasebe, api blueprints)
  utils.py          # Yardımcı fonksiyonlar
  static/
    teknik_resimler/  # 1640 PDF teknik resim
  templates/          # Jinja2 HTML şablonları
instance/
  erlau.db
migrations/           # Flask-Migrate (Alembic)
logs/
  erlau.log
```

## Veritabanı Modelleri

| Model | Açıklama | Kayıt |
|---|---|---|
| `User` | Kullanıcılar, rol + boolean yetkiler | 18 |
| `TalepFormu` | Satın alma talep formları | 1321 |
| `TalepKalem` | Talep kalemleri (malzeme satırları) | — |
| `Tedarikci` | Tedarikçi firmaları | 54 |
| `TeklifGrubu` | Teklif grupları (batch_id ile toplu teklif) | — |
| `TeklifKalem` | Tedarikçiden gelen teklif kalemleri | — |
| `Malzeme` | Malzeme listesi (Türkçe + Almanca) | 940 |
| `Urun` | Ürün listesi | 268 |
| `TeknikResim` | Teknik resim PDF katalog | 1640 |
| `Fatura` / `FaturaKalem` | Muhasebe fatura modülü | — |
| `Makine`, `BakimPlani`, `BakimKaydi` | Bakım modülü | — |
| `UretimPlani`, `UretimKaydi` | Üretim takip | — |

## Kullanıcı Rolleri ve Yetkiler

**Roller:** `admin`, `satinalma`, `muhasebe`, `personel`, `uretim`

**Boolean yetkiler (User modeli):**
- `teknik_resim_yetki` — Teknik resim ekle/sil
- `liste_yetki` — Malzeme + Ürün listesi CRUD

**Yetkili kullanıcılar:**
- `teknik_resim_yetki`: Gurbet, Nilüfer, Kübra, Batuhan, Nesim, Caner, Mehmet Türk, Can, Ali Solak, Ali Aslan, Göktürk, Özlem ÖZ
- `liste_yetki`: Gurbet, Nilüfer, Ali Solak, Can, Admin

**Aktif kullanıcılar (@erlau.com.tr):**
admin, ali.aslan, caner.cinar, nesim.gok, simay.pehlivan, mehmet.turk, kerim.bilgili,
batuhan.konur, gurbet.filiz, gokturk.senel, kubra.dere, melike.kivrak, nilufer.guler,
orhan.ipsir, rusen.bahtisen, ali.solak, can.otu, ozlem.oz

Varsayılan şifre (yeni kullanıcı): `123456*`

## Blueprint'ler ve Ana Route'lar

| Blueprint | Prefix | Açıklama |
|---|---|---|
| `auth` | — | Login/logout |
| `main` | — | Dashboard, talep CRUD, portal |
| `satin_alma` | `/satinalma/` | Panel, fiyatlandırma, teklif, sipariş, raporlar |
| `admin` | `/admin/` | Kullanıcı, tedarikçi, malzeme, ürün yönetimi |
| `muhasebe` | `/muhasebe/` | Fatura yükleme, eşleştirme, PDF |
| `api` | `/api/` | Malzeme önerisi (AI), arama, kullanım sıklığı |
| `teknik_resim` | `/teknik-resim/` | PDF katalog, accordion lazy load |
| `uretim` | `/uretim/` | Üretim girişi, raporlar |
| `planlama` | `/planlama/` | Üretim planları |
| `bakim` | `/bakim/` | Makine bakım takvimi |

## Temel İş Akışı

```
Personel → Yeni Talep (yeni_talep.html)
         → Talep Detay (talep_detay.html)
         ↓
Satınalma → Fiyatlandır (fiyatlandir.html)
          → Teklif Al (teklif_detay.html) veya Toplu Teklif (toplu_teklif.html)
          → Teklif Seç → Sipariş (PO PDF + Outlook EML)
          ↓
Muhasebe → Fatura Yükle → Siparişle Eşleştir
```

## Önemli Özellikler

### Teklif Ekosistemi
- Tekil teklif: `/satinalma/teklif/yeni/<kalem_id>`
- **Toplu teklif:** Birden çok kalemi aynı anda teklif grubuna alma (`batch_id` ile gruplandırma)
- Excel RFQ çıktısı (tedarikçiye gönderim)
- Outlook mailto linki (tarayıcıdan mail taslağı)
- AI mail parse: Gelen teklif mailini yapıştır → kalem otomatik doldurulur
- AI tavsiye: Teklif karşılaştırma analizi (Claude Haiku)

### Sipariş (PO)
- PO PDF: ReportLab ile Türkçe sipariş formu
- PO EML: PDF ekli Outlook taslağı (`.eml` dosyası)
- Direkt fiyatlandırmadan sipariş gönderim

### Teknik Resim Modülü
- 1640 PDF, accordion + lazy AJAX yükleme
- Klasör bazlı gruplandırma, arama modu
- `teknik_resim_yetki` boolean ile erişim kontrolü

### AI Özellikleri
- `/api/malzeme-oneri`: Yeni talep sırasında malzeme önerisi (1.5sn debounce)
- `/api/malzeme-ara`: Stok kodu + isim + açıklama arama
- Teklif mail parse, teklif karşılaştırma analizi

## Kod Kuralları

- Değişken/sütun adlarında Türkçe karakter KULLANMA (ı, ş, ğ, ü, ö, ç) — bug riski
- Modal gizle/göster için `element.style.display='none'/'flex'` kullan, Tailwind `hidden` class'ı KULLANMA
- Sunucuyu yeniden başlatmak için: `systemctl restart erlau`
- 1000+ kayıtlı listeler için accordion + AJAX lazy load kullan

## Bekleyen / Planlanan Özellikler

- Departman yöneticisi + GM online onay akışı (~1 ay sonra)
- Email/bildirim sistemi (ertelendi)
- PostgreSQL geçişi (ileride)
- Günlük üretim takibi (tablet)
- CNC takım takibi (tablet)
