# MASTER_PROJECT_CONTEXT.md
# Erlau Satın Alma Sistemi — Tek Referans Doküman
# Son Güncelleme: 25 Nisan 2026

## 1. PROJE KİMLİĞİ
- Şirket: Erlau (RUD Gruppe markası)
- Geliştirici: Can Otu (can.otu@erlau.com.tr)
- GitHub: https://github.com/Erlau-Proje/erlau-app
- Amaç: Kağıt/Excel tabanlı satın alma talep sürecini dijitalleştirme

## 2. SUNUCU
- IP: 178.104.49.105 (Hetzner CPX22, Nuremberg DC Park 1)
- Plan: 2 vCPU, 4GB RAM, 80GB SSD, Ubuntu 24.04 LTS, ~10 EUR/ay
- SSH: root@178.104.49.105
- Uygulama: http://178.104.49.105:5000
- Coolify: http://178.104.49.105:8000
- Kod: /root/erlau-app
- Veritabanı: /root/erlau-app/instance/erlau.db
- Güncelleme: bash /root/guncelle.sh
- Log: journalctl -u erlau -n 50 --no-pager

## 3. TEKNOLOJİLER
- Python 3.12, Flask 3.1.3
- SQLAlchemy 2.0.49, Flask-SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- SQLite (instance/erlau.db)
- Gunicorn 25.3.0 (2 worker)
- ReportLab 4.4.10
- Jinja2 + Tailwind CSS CDN
- systemd (erlau.service)
- Coolify v4.0.0-beta.474 (kurulu ama kullanılmıyor)

## 4. MEVCUT KULLANICILAR
- Admin | admin@erlau.com | admin | Satınalma
- Gurbet Filiz | gurbet.filiz@erlau.com.tr | personel | Planlama ve Tedarik Zinciri
- Nilufer Guler | nilufer.guler@erlau.com.tr | personel | Planlama ve Tedarik Zinciri
- Nesim Gok | nesim.gok@erlau.com.tr | departman_yoneticisi | Planlama ve Tedarik Zinciri
- Ali Solak | ali.solak@erlau.com.tr | personel | Satinalma
- Can Otu | can.otu@erlau.com.tr | satinalma | Satinalma

## 5. DURUM AKIŞI
bekliyor → onaylandi → yolda → teslim_alindi
bekliyor → iptal

## 6. MEVCUT DURUM (25 Nisan 2026)
- CALISIYOR: Login, dashboard, yeni talep, satinalma paneli
- CALISIYOR: PDF export, tedarikci yonetimi, kullanici yonetimi
- SORUN: TalepFormu'nda eski alanlar hala duruyor (temizlenmedi)
- EKSIK: Fiyatlandirma ekrani, tedarikci atama, mail taslagi

## 7. PLANLANAN OZELLIKLER
1. Fiyatlandirma ekrani (tedarikci, fiyat, vade, termin)
2. Tedarikci Excel toplu aktarim
3. Outlook mail taslagi (Excel formatinda siparis)
4. PDF logo ekleme (Erlau_Eine_Marke_der_RUD_Gruppe_color.jpg)
5. Departman yoneticisi onay adimi
6. GM online onay
7. Muhasebe/fatura modulu
8. Gunluk uretim takibi (tablet)
9. CNC takim takibi (tablet)

## 8. ONEMLI KOMUTLAR
systemctl restart erlau
bash /root/guncelle.sh
journalctl -u erlau -n 50 --no-pager
cd /root/erlau-app && source venv/bin/activate && python3 run.py
