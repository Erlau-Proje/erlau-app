# TODO.md — Eksik ve Geliştirilmesi Gerekenler

## KRİTİK (Düzeltilmesi Gereken)
- [x] TalepFormu'ndan kullanim_amaci, kullanilan_alan, proje_makine kaldırılmalı → zaten TalepKalem'de
- [x] routes.py yeni_talep → TalepKalem objesine yazılıyor, TalepFormu'na değil
- [x] talep_pdf → kalem.* ile okunuyor, talep.kullanim_amaci kullanılmıyor
- [x] SECRET_KEY hardcoded → os.environ.get ile alınıyor
- [x] forms.py boş ama Flask-WTF kurulu → hata vermiyor, ileride kullanılabilir, bırakıldı
- [x] guncelle.sh → /root/guncelle.sh mevcut

## ÖNEMLİ EKSİKLER
- [x] Kullanıcı silme/düzenleme yok
- [x] Tedarikçi silme/düzenleme yok
- [x] Talep düzenleme yok
- [x] Talep silme yok
- [ ] ~~departman_yoneticisi online onay~~ → ERTELENDI: Şimdilik ıslak imza ile onay, ~1 ay sonra online onay akışı eklenecek
- [ ] ~~gm online onay~~ → ERTELENDI: Şimdilik ıslak imza ile onay, ~1 ay sonra online onay akışı eklenecek
- [x] PDF Türkçe karakter sorunu (Helvetica → Türkçe desteklemiyor)
- [x] Fiyat alanları (br_fiyat, toplam_fiyat) hiçbir formda dolmuyor

## GELİŞTİRİLECEKLER
- [x] Portal'a geri dönüş navigasyonu (`/portal`, sidebar linki, logo linki)
- [x] Fiyatlandırma ekranı (tedarikçi seç, fiyat, vade, termin)
- [x] Tedarikçi atama arayüzü
- [x] Filtreleme ve arama
- [ ] Email/bildirim sistemi
- [x] Rapor ekranı (harcama istatistikleri)
- [x] Flask-Migrate kurulumu
- [ ] PostgreSQL geçişi (SQLite production için yetersiz kalacak)
- [x] Kullanıcı şifre değiştirme + profil sayfası (unvan, telefon, doğum tarihi, istatistikler, son giriş, tablet PIN, bildirim tercihi)
- [x] Tedarikçi Excel toplu aktarım
- [x] Outlook mail taslağı (Excel formatında sipariş)
- [x] PDF logo ekleme (vektör çizim ile yapıldı)
- [ ] Günlük üretim takibi (tablet arayüzü)
- [ ] CNC takım takibi (tablet arayüzü)
- [ ] Muhasebe/fatura modülü

## TEKNİK BORÇ
- [x] TalepFormu.query.get_or_404() → db.get_or_404() kullanılmalı
- [x] Error handling (404, 403, 500 özel hata sayfaları)
- [x] Logging (logs/erlau.log, RotatingFileHandler, WARNING+)
