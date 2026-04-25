# CLAUDE.md — Erlau Satın Alma Sistemi

Bu dosya, Claude'un bu projede nasıl çalışması gerektiğini tanımlar.

## Sunucu Bilgileri
- **IP:** 178.104.49.105
- **Uygulama portu:** 5000
- **Coolify paneli:** 178.104.49.105:8000
- **Proje klasörü:** /root/erlau-app
- **Servis adı:** erlau (systemctl)
- **GitHub:** https://github.com/Erlau-Proje/erlau-app

## Çalışma Akışı
1. Kod değişikliği → sunucuda /root/erlau-app/app/ içinde düzenle
2. Test et: journalctl -u erlau -n 20 --no-pager
3. GitHub'a push et: git add app/ && git commit -m "açıklama" && git push origin main
4. Servisi restart et: systemctl restart erlau

## Güncelleme Komutu
bash /root/guncelle.sh

## Veritabanı
- Tip: SQLite — /root/erlau-app/instance/erlau.db
- Flask-Migrate KURULU DEĞİL
- Yeni kolon = Manuel ALTER TABLE
- instance/ gitignore'da, commit edilmez

## SQLAlchemy 2.0 — Kritik
db.engine.execute() ÇALIŞMAZ. Doğru kullanım:
from sqlalchemy import text
with db.engine.connect() as conn:
    conn.execute(text('ALTER TABLE ...'))
    conn.commit()

## Roller
- admin: Tüm yetkiler
- satinalma: Panel, onay/iptal/yolda/teslim
- gm: Paneli görüntüler (salt okunur)
- departman_yoneticisi: Kendi departmanının taleplerini görür
- personel: Sadece kendi taleplerini görür

## Varsayılan Admin
- Email: admin@erlau.com
- Şifre: Erlau2026!

## Kritik Notlar
- forms.py boş, kullanılmıyor
- TalepFormu'nda kullanim_amaci, kullanilan_alan, proje_makine hâlâ var (temizlenmedi)
- PDF Türkçe karakter desteklemiyor (Helvetica)
- SECRET_KEY hardcoded — production için env variable'a alınmalı
- db.create_all() mevcut tabloları güncellemez, manuel ALTER TABLE gerekir
