# Portal Navigasyonu

## Amaç
Kullanıcılar satın alma talebi açmak için Satınalma modülüne girse bile, asıl işlerini yapmak için Üretim, Bakım veya Planlama gibi başka modüllere geçebilmelidir.

## Karar
- `/` dış giriş kapısı olarak kalır; kullanıcı giriş yaptıysa kendi ana sayfasına yönlenir.
- `/portal` her zaman portal ekranını gösterir.
- Sol menüde "Uygulama Portalı" linki bulunur.
- Sidebar'daki Erlau logosu `/portal` adresine gider.
- Portal kartları kullanıcı giriş yapmışsa ilgili modül paneline, giriş yapmamışsa login ekranına yönlendirir.

## Kullanıcı Akışı
1. Kullanıcı sisteme girer.
2. Satınalma, Üretim, Bakım veya Planlama modülünde çalışır.
3. Başka bir modüle geçmek isterse sol menüden "Uygulama Portalı"na tıklar.
4. Portal ekranından yeni modülü seçer.

## Not
Sevkiyat kartı şimdilik pasiftir ve "Yakında" etiketiyle gösterilir.
