# CLAUDE.md — Erlau Satın Alma Sistemi

Bu dosya, Claude'un bu projede nasıl çalışması gerektiğini tanımlar.

## Sunucu Bilgileri
- **IP:** 178.104.49.105 (Hetzner CPX22, Nuremberg)
- **SSH alias:** `ssh erlau` (config kurulduysa)
- **SSH direkt:** `ssh root@178.104.49.105`
- **Uygulama:** http://178.104.49.105:5000
- **Coolify paneli:** http://178.104.49.105:8000
- **Proje klasörü:** /root/erlau-app
- **Servis adı:** erlau (systemctl)
- **GitHub:** https://github.com/Erlau-Proje/erlau-app

## Yeni Bilgisayar / Yeni AI Ortamı Kurulumu

### 1. GitHub Auth
```bash
gh auth login
# GitHub.com → HTTPS → Login with a web browser
```

### 2. SSH Key Kurulumu (sunucuya şifresiz erişim)
```bash
# Mevcut key yoksa oluştur:
ssh-keygen -t ed25519 -C "can.otu@gmail.com" -f ~/.ssh/id_ed25519 -N ""

# Sunucuya public key'i yükle (bir kerelik şifre gerekir):
ssh-keyscan -H 178.104.49.105 >> ~/.ssh/known_hosts
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@178.104.49.105

# SSH config oluştur (alias için):
cat >> ~/.ssh/config << 'EOF'
Host erlau
    HostName 178.104.49.105
    User root
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
EOF
chmod 600 ~/.ssh/config

# Test et:
ssh erlau "echo Bağlantı başarılı"
```

### 3. Projeyi GitHub'dan çek
```bash
git clone https://github.com/Erlau-Proje/erlau-app.git
cd erlau-app
```

### 4. Çalışmaya başlamadan önce her zaman
```bash
git pull  # GitHub'daki son değişiklikleri al
```

## Çalışma Akışı
1. `git pull` — önce güncel hali al
2. Kod değişikliği → lokal `app/` içinde düzenle
3. Test et: `ssh erlau "journalctl -u erlau -n 20 --no-pager"`
4. GitHub'a push et: `git add app/ && git commit -m "açıklama" && git push origin main`
5. Sunucuyu güncelle: `ssh erlau "bash /root/guncelle.sh"`

## Güncelleme Komutu
bash /root/guncelle.sh

## Veritabanı
- Tip: SQLite — /root/erlau-app/instance/erlau.db
- Flask-Migrate KURULU ve AKTİF
- Yeni kolon = flask db migrate -m "mesaj" && flask db upgrade
- instance/ gitignore'da, commit edilmez
- SQLite timeout=30s olarak güncellendi (concurrency için)

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
