# MASTER_PROJECT_CONTEXT.md
# Erlau Satın Alma Sistemi — Tek Referans Doküman
# Son Güncelleme: 26 Nisan 2026

## 1. PROJE KİMLİĞİ
- Şirket: Erlau (RUD Gruppe markası)
- Geliştirici: Can Otu (can.otu@erlau.com.tr)
- GitHub: https://github.com/Erlau-Proje/erlau-app
- Amaç: Kağıt/Excel tabanlı satın alma talep sürecini dijitalleştirme

## 2. SUNUCU
- IP: 178.104.49.105 (Hetzner CPX22, Nuremberg)
- SSH: root@178.104.49.105
- Uygulama: http://178.104.49.105:5000
- Coolify: http://178.104.49.105:8000
- Kod: /root/erlau-app
- Veritabanı: /root/erlau-app/instance/erlau.db
- Faturalar: /root/erlau-app/faturalar/
- Yedekler: /root/erlau-backups/
- Güncelleme: bash /root/guncelle.sh
- Log: journalctl -u erlau -n 50 --no-pager

## 3. TEKNOLOJİLER
- Python 3.12, Flask 3.1.3
- SQLAlchemy 2.0, Flask-SQLAlchemy 3.1.1, Flask-Migrate 4.1.0
- Flask-Login 0.6.3
- SQLite (instance/erlau.db)
- Gunicorn 2 worker, timeout 120s
- ReportLab 4.4.10 (PDF)
- openpyxl 3.1.5 (Excel)
- anthropic 0.97.0 (Claude Haiku — fatura AI)
- Tailwind CSS CDN + Inter font
- Chart.js CDN (raporlar)
- systemd (erlau.service)

## 4. KULLANICILAR (13 kişi)
- admin@erlau.com | admin | Satınalma
- gurbet.filiz@erlau.com.tr | personel | Planlama ve Tedarik Zinciri
- nilufer.guler@erlau.com.tr | personel | Planlama ve Tedarik Zinciri
- nesim.gok@erlau.com.tr | departman_yoneticisi | Planlama ve Tedarik Zinciri
- ali.solak@erlau.com.tr | satinalma | Satınalma
- can.otu@erlau.com.tr | satinalma | Satınalma
- mehmet.turk@erlau.com.tr | gm | Genel Müdür
- batuhan.konur@erlau.com.tr | personel | Üretim
- ali.aslan@erlau.com.tr | departman_yoneticisi | Üretim
- kubra.dere@erlau.com.tr | personel | Proje
- caner.cinar@erlau.com.tr | departman_yoneticisi | Proje
- kerim.bilgili@erlau.com.tr | muhasebe | Muhasebe
- simay.pehlivan@erlau.com.tr | departman_yoneticisi | Muhasebe

## 5. ROLLER VE YETKİLER
- admin: Her şey
- satinalma: Panel, raporlar, tedarikçi, fatura görüntüleme+eşleştirme+onaylama
- muhasebe: Fatura yükleme/düzenleme/silme/ödeme takibi
- gm: Panel, raporlar (salt okunur)
- departman_yoneticisi: Departmanının talepleri, sipariş raporu
- personel: Kendi talepleri, sipariş raporu (sadece kendi)

## 6. DURUM AKIŞI
bekliyor → onaylandi → yolda → teslim_alindi
bekliyor → iptal

Fatura: bekliyor → onaylandi (satınalma) → odendi (muhasebe) | iptal | iade

## 7. TAMAMLANAN ÖZELLİKLER
- Login, dashboard, yeni talep, talep düzenleme/silme
- Satınalma paneli (onay/iptal/yolda/teslim)
- Fiyatlandırma ekranı (tedarikçi, fiyat, vade, termin)
- Sipariş özeti (tedarikçi bazlı Excel + mailto CC)
- PDF export (ReportLab, Türkçe, logo)
- Tedarikçi yönetimi + Excel toplu aktarım
- Kullanıcı yönetimi + şifre sıfırlama
- Profil sayfası (unvan, telefon, doğum tarihi, istatistikler, PIN)
- Rapor ekranı (Chart.js grafikleri)
- Sipariş raporu (detaylı filtreler + Excel export)
- Muhasebe/fatura modülü (Claude AI, iskonto, öğrenen eşleştirme)
- Flask-Migrate, Error handling, Logging
- Yedekleme (cron gece 02:00, /root/erlau-backups/)
- UI yenileme (sidebar, Inter font, kurumsal)
- Ürün arama

## 8. ERTELENENLER
- Departman yöneticisi ve GM online onay (~1 ay sonra)
- Email/bildirim sistemi
- PostgreSQL geçişi (ileride)
- Günlük üretim takibi (tablet)
- CNC takım takibi (tablet)

## 9. API ANAHTARLARI
- Anthropic API: systemd service'te ANTHROPIC_API_KEY env var
- Model: claude-haiku-4-5-20251001

## 10. ÖNEMLİ KOMUTLAR
systemctl restart erlau
systemctl status erlau
journalctl -u erlau -n 50 --no-pager
bash /root/guncelle.sh
FLASK_APP=run.py venv/bin/flask db migrate -m "açıklama"
FLASK_APP=run.py venv/bin/flask db upgrade
cat /root/erlau-backups/yedek.log
