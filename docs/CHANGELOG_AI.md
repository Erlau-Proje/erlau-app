# CHANGELOG_AI.md — AI Destekli Geliştirme Geçmişi

## ÖNCEKİ KONUŞMA (Tarih: uncertain)

### Yapılanlar
- Hetzner CPX22 sunucu kurulumu (Ubuntu 24.04 LTS)
- Coolify kurulumu (dpkg lock sorunu: kill 2271 && dpkg --configure -a)
- Flask uygulaması sıfırdan yazıldı
- systemd servisi oluşturuldu (erlau.service)
- Gunicorn 2 worker ile yapılandırıldı
- GitHub entegrasyonu (token URL gömme yöntemi)
- /root/guncelle.sh scripti oluşturuldu
- yeni_talep form yapısı değiştirildi: form genelinden satır bazına
- TalepKalem modeline fiyat ve tedarikçi alanları eklendi

### Yaşanan Hatalar ve Çözümler
- Login route Method Not Allowed → methods=['GET','POST'] eklendi (sed ile)
- base.html iki kez yazıldı → python3 -c ile üstüne yazıldı
- Coolify terminal websocket hatası → SSH key authorized_keys'e eklendi
- git push token sorunu → URL'ye token gömüldü
- ~ karakteri Hetzner console'da bozuluyor → tam path kullanıldı

---

## 25 NİSAN 2026

### Sorun: /dashboard Internal Server Error
- Hata: sqlalchemy.exc.OperationalError: no such column: talep_kalem.kullanim_amaci
- Neden: TalepKalem modeline yeni kolonlar eklendi ama SQLite'a uygulanmadı
- Çözüm: Manuel ALTER TABLE (SQLAlchemy 2.0 text() API ile)
  - kullanim_amaci VARCHAR(100)
  - kullanilan_alan VARCHAR(50)
  - proje_makine VARCHAR(200)
  - kw VARCHAR(10)
- Sonuç: Dashboard çalışır hale geldi

### Altyapı
- Claude Code Windows'a kuruldu (v2.1.119, PowerShell native installer)
- GitHub repo public yapıldı
- Coolify GitHub App bağlandı (erlau-github, Erlau-Proje org)
- Coolify Docker deploy denendi → SQLite uyumsuzluğu → iptal edildi
- .gitignore güncellendi (instance/, __pycache__/, *.pyc, *.db)
- docs/ klasörü oluşturuldu, dokümantasyon dosyaları yazıldı

### Bilinen Açık Sorunlar
- TalepFormu'nda eski 3 alan hala duruyor (model temizlenmedi)
- routes.py yeni_talep → TalepFormu'na hala 3 eski alan yazılıyor
- talep_pdf → TalepFormu'ndan okuyor, TalepKalem'e geçirilmeli
