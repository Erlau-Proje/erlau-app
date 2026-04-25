# TODO.md — Eksik ve Geliştirilmesi Gerekenler

## KRİTİK (Düzeltilmesi Gereken)
- [ ] TalepFormu'ndan kullanim_amaci, kullanilan_alan, proje_makine kaldırılmalı
- [ ] routes.py yeni_talep → TalepFormu oluştururken bu 3 alan hala yazılıyor
- [ ] talep_pdf → talep.kullanim_amaci yerine TalepKalem'den okunmalı
- [ ] SECRET_KEY hardcoded → environment variable'a alınmalı
- [ ] forms.py boş ama Flask-WTF kurulu → ya kullanılmalı ya kaldırılmalı
- [ ] guncelle.sh var mı doğrula: cat /root/guncelle.sh

## ÖNEMLİ EKSİKLER
- [ ] Kullanıcı silme/düzenleme yok
- [ ] Tedarikçi silme/düzenleme yok
- [ ] Talep düzenleme yok
- [ ] Talep silme yok
- [ ] departman_yoneticisi onay yetkisi yok (iş akışı belirsiz)
- [ ] gm onay yetkisi yok
- [ ] PDF Türkçe karakter sorunu (Helvetica → Türkçe desteklemiyor)
- [ ] Fiyat alanları (br_fiyat, toplam_fiyat) hiçbir formda dolmuyor

## GELİŞTİRİLECEKLER
- [ ] Fiyatlandırma ekranı (tedarikçi seç, fiyat, vade, termin)
- [ ] Tedarikçi atama arayüzü
- [ ] Departman yöneticisi onay adımı
- [ ] GM online onay adımı
- [ ] Filtreleme ve arama
- [ ] Email/bildirim sistemi
- [ ] Rapor ekranı (harcama istatistikleri)
- [ ] Flask-Migrate kurulumu
- [ ] PostgreSQL geçişi (SQLite production için yetersiz kalacak)
- [ ] Kullanıcı şifre değiştirme
- [ ] Tedarikçi Excel toplu aktarım
- [ ] Outlook mail taslağı (Excel formatında sipariş)
- [ ] PDF logo ekleme (Erlau_Eine_Marke_der_RUD_Gruppe_color.jpg)
- [ ] Günlük üretim takibi (tablet arayüzü)
- [ ] CNC takım takibi (tablet arayüzü)
- [ ] Muhasebe/fatura modülü

## TEKNİK BORÇ
- [ ] TalepFormu.query.get_or_404() → db.get_or_404() kullanılmalı
- [ ] Error handling yok (500 hataları ham görünüyor)
- [ ] Logging yok
