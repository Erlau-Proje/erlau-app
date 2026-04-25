# ARCHITECTURE.md — Kod Yapısı

## KLASÖR YAPISI
/root/erlau-app/
├── app/
│   ├── __init__.py        # Flask app factory, DB init, blueprint kayıt
│   ├── models.py          # SQLAlchemy modelleri
│   ├── routes.py          # Tüm route'lar
│   ├── utils.py           # siparis_no, create_default_data
│   ├── forms.py           # BOŞ
│   └── templates/
│       ├── base.html              # Navbar, Tailwind CDN, flash mesajları
│       ├── login.html
│       ├── dashboard.html
│       ├── yeni_talep.html        # Dinamik satır ekleme (satirEkle JS)
│       ├── talep_detay.html
│       ├── satinalma_panel.html
│       ├── admin_kullanicilar.html
│       └── tedarikci.html
├── instance/erlau.db      # gitignore'da
├── venv/                  # gitignore'da
├── docs/                  # Bu dokümantasyon klasörü
├── run.py
├── requirements.txt
└── .gitignore

## MODELLER
Department: id, name(unique)
User: id, name, email, password(hash), role, department_id, is_active, created_at
Tedarikci: id, name, unvan, vergi_no, email, telefon, adres, iletisim_kisi, para_birimi, vade_gun, kategori
TalepFormu: id, siparis_no(unique), talep_eden_id, department_id, kullanim_amaci(*), kullanilan_alan(*), proje_makine(*), durum, created_at, updated_at
  (*) = GECİS DONEMİ — TalepKalem'e taşındı ama model temizlenmedi
TalepKalem: id, talep_id, malzeme_adi, marka_model, malzeme_turu, birim, miktar, hedef, kullanim_amaci, kullanilan_alan, proje_makine, kw, aciklama, teknik_resim_kodu, standart, br_fiyat, toplam_fiyat, para_birimi, vade_gun, termin_gun, tedarikci_id, son_alinma_tarihi, son_siparis_no

## BLUEPRINT'LER
auth (/) → login, logout
main (/) → dashboard, yeni_talep, talep_detay, talep_pdf
satin_alma (/satinalma) → panel, onayla, iptal, yolda, teslim
admin (/admin) → kullanicilar, kullanici_ekle, tedarikci_listesi, tedarikci_ekle

## YENI_TALEP FORM YAPISI
- Üstte sadece departman seçimi
- Her malzeme satırında: malzeme_adi, marka_model, malzeme_turu, birim, miktar, hedef, kullanim_amaci, kullanilan_alan, proje_makine, kw, aciklama
- JavaScript satirEkle() ile dinamik satır ekleme
- X butonu ile satır silme

## BASE.HTML MENU
- satinalma/admin → panel + tedarikci menüsü görünür
- Diğer roller bu menü öğelerini görmez
