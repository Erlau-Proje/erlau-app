# Erlau Satın Alma Sistemi - Kritik Hatalar ve Geliştirme Yol Haritası

Bu doküman, mevcut Python/Flask uygulamasının performans, ölçeklenebilirlik ve kod kalitesi açısından yapılan analizi sonucunda ortaya çıkan iyileştirme kalemlerini içerir.

## 1. Veritabanı ve Performans Sorunları (Kritik)
- **Eksik İndeksler:** `TalepFormu` ve `TalepKalem` tablolarında `durum`, `department_id`, `siparis_no` ve `created_at` kolonlarında veritabanı indeksi bulunmuyor. Bu durum, veri seti büyüdüğünde dashboard ve rapor sayfalarının yavaşlamasına neden olacaktır.
- **SQLite Kilitleme Riski:** Production ortamında Gunicorn (multi-worker) ile SQLite kullanımı, eşzamanlı yazma işlemlerinde "Database is locked" hatalarına yol açabilir. Kısa vadede `timeout` ayarı artırılmalı, orta vadede PostgreSQL'e geçilmelidir.
- **Dashboard Yükü:** GM Dashboard'daki istatistiksel hesaplamalar (6 aylık trend, departman bazlı dağılım) her sayfa yenilemesinde sıfırdan hesaplanıyor. Bu, veritabanı üzerinde gereksiz yük oluşturuyor.
- **Bellek Yönetimi:** Excel ve PDF dışa aktarma işlemlerinde tüm kayıtlar `.all()` ile belleğe çekiliyor. Binlerce satırlık veri setlerinde RAM tüketimi kritik seviyeye ulaşabilir.

## 2. Mimari ve Kod Kalitesi
- **Monolitik Routes:** Tüm business logic (iş mantığı) `routes.py` içerisinde yer alıyor. Özellikle sipariş eşleştirme, Excel üretimi ve dosya işlemleri gibi ağır mantıkların `services/` veya `utils/` klasörüne taşınması gerekiyor.
- **Legacy Kolonlar:** `TalepFormu` modelinde hala duran `kullanim_amaci`, `kullanilan_alan` ve `proje_makine` kolonları veri tutarsızlığı riskidir. Bu alanlar `TalepKalem`'e taşındığı için modelden temizlenmelidir.
- **Dinamik Arama Performansı:** Ürün arama fonksiyonu 8-10 kolonda birden `ilike` operatörü kullanıyor. SQLite'da bu işlem full-table scan demektir ve çok maliyetlidir.

## 3. Güvenlik ve Altyapı
- **Secret Key:** `SECRET_KEY` hala hardcoded olarak duruyor. Production ortamında mutlaka environment variable üzerinden okunmalıdır.
- **Migrate Eksikliği:** Flask-Migrate kurulu olmasına rağmen manuel `ALTER TABLE` süreçleri devam ediyor. Veritabanı şemasının tam yönetimi için `flask db migrate` akışına geçilmelidir.

## 4. Önerilen Geliştirme Planı

### Faz 1: Performans ve Stabilite (Hemen)
1. **İndeksleme:** Sık sorgulanan kolonlara (durum, tarih, id) veritabanı indeksleri eklenmesi.
2. **Caching:** GM Dashboard ve Rapor verileri için 10-15 dakikalık basit bir `Flask-Caching` mekanizmasının kurulması.
3. **Veri Temizliği:** Model seviyesinde legacy kolonların (TalepFormu) temizlenmesi ve migration'ın tamamlanması.

### Faz 2: Mimari Refactoring
1. **Service Layer:** `routes.py` içindeki ağır SQL sorgularının ve veri işleme mantığının `app/services/` altına taşınması.
2. **Pagination:** Sipariş raporu ve admin listeleri gibi sayfalarda server-side pagination (sayfalama) uygulanması.
3. **Fatura AI Geliştirmesi:** Claude AI'dan dönen verilerin daha güvenli bir şekilde `schema validation` (Pydantic vb.) ile doğrulanması.

### Faz 3: Ölçekleme
1. **PostgreSQL Geçişi:** SQLite'tan PostgreSQL'e geçiş için altyapı hazırlığının yapılması.
2. **Async İşlemler:** PDF/Excel üretimi ve AI analiz süreçlerinin (uzun süren işlemler) `Celery` veya `Redis Queue` ile arka plana (background task) alınması.

---
*Not: Bu liste projenin sürdürülebilirliği için öncelik sırasına göre dizilmiştir.*