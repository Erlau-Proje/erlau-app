# Kullanici, Gorev Profili ve Kapsam Mimarisi - Audit

Bu dokuman, yetki matrisini ana yonetim araci olmaktan cikarip kullanici tanimlama ekranini merkeze almak icin ilk sistem taramasidir.

## Mevcut Durum

### Kullanici modeli

`User` su alanlarla yonetiliyor:

- `role`
- `department_id`
- `unvan`
- `telefon`
- `tablet_pin`
- `bildirim_email`
- `teknik_resim_yetki`
- `liste_yetki`
- `UserPermission` override kayitlari

Ana sorun: `role`, `department_id`, ozel boolean yetkiler ve `UserPermission` ayni anda calisiyor. Bu, admin icin "bu kisi gercekte ne yapabiliyor?" sorusunu zorlastiriyor.

### Uretim personeli modeli

Uretim tarafinda ayrica `UretimPersoneli` var:

- `ad`
- `soyad`
- `sicil_no`
- `istasyon_id`
- `is_active`

Ana sorun: `UretimPersoneli` sistem kullanicisi degil. Uretim kaydinda iki farkli kisi kavrami var:

- `uretim_personeli_id`: isi yapan operator/personel
- `giren_personel_id`: sisteme giris yapip kaydi giren `User`

Bu ayrim dogru olabilir, ama su an admin ekraninda baglanmiyor. CNC veya istasyon operatoru sisteme giris yapacaksa `User` ile `UretimPersoneli` arasinda iliski kurulmasi gerekiyor.

### Veritabani ozeti

Aktif sistem kullanicilari:

- `admin`: 2
- `departman_yoneticisi`: 5
- `gm`: 1
- `kalite`: 1
- `muhasebe`: 1
- `personel`: 7
- `satinalma`: 1

Uretim personeli ayrica 14 kayit olarak duruyor. Bunlar istasyonlara dagilmis, fakat sistem kullanicisi olmak zorunda degiller.

Yetki matrisi su anda her kullanici icin tum permission kayitlarini override olarak saklamis durumda: `1440` satir. Bu da matrisin "debug tablosu" gibi degil, ana karar tablosu gibi davranmasina yol aciyor.

## Mevcut Modul Envanteri

Sistemde ana modul gruplari:

- Genel / Portal / Dashboard
- Talep
- Satinalma
- Tedarikci
- Muhasebe / Fatura
- Malzeme ve Urun listeleri
- Teknik Resim
- Uretim
- Planlama
- Bakim
- Kalite
- Admin / Sunucu

`permissions.py` bu moduller icin kodlari iceriyor ve `ENDPOINT_PERMISSIONS` ile endpoint eslesmesi yapiliyor.

## Tespit Edilen Mimarik Sorunlar

### 1. Rol ve permission kontrolu karisik

Bazi yerlerde `has_permission(...)`, bazi yerlerde `current_user.role`, bazi yerlerde `role_required(...)` kullaniliyor.

Ornekler:

- Satinalma ve muhasebe route'lari cogunlukla `role_required(...)` kullaniyor.
- Uretim, planlama ve kalite tarafinda hala rol bypass kosullari var.
- Bakim tarafinda bir kisim permission'a cekildi, ama tum alt ekranlar tamamen ayni standarda gelmis degil.

Hedef: menü, sayfa, buton ve POST islemi ayni permission/scope helper'indan beslenmeli.

### 2. Kapsam bilgisi tabloda yok

Permission su anda sadece "yapabilir/yapamaz" diyor. Ama gercek ihtiyac iki parca:

- Ne yapabilir?
- Nerede yapabilir?

Ornek:

- Departman yoneticisi kendi departman taleplerini gormeli.
- Kalite, uretime DÖF acip takip edebilmeli.
- Muhasebe, uretim operasyon ekranlarini gormemeli.
- Operator sadece atandigi istasyonda veri girebilmeli.

### 3. Kullanici ekleme ekrani isi bitirmiyor

Admin kullanici olustururken sadece rol, departman ve iki ozel checkbox seciyor. Halbuki asil ihtiyac:

- Gorev profili
- Departman
- Bagli istasyonlar
- Veri kapsami
- Operator/personel baglantisi
- Varsayilan menü ve islem yetkileri

### 4. Yetki matrisi kullanici deneyimi icin fazla dusuk seviyeli

Matris debug ve ileri seviye duzeltme icin kalmali. Gunluk admin akisi "Kullanici Ekle/Duzenle" uzerinden bitmeli.

## Onerilen Yeni Model

### Kullanici tipi

`User` icin `user_type` benzeri bir alan dusunulmeli:

- `office`: ofis kullanicisi
- `operator`: uretim/bakim/kalite veri giren saha kullanicisi
- `manager`: departman yoneticisi
- `executive`: GM/yonetim
- `admin`: sistem yoneticisi
- `external`: ileride tedarikci/dis paydas

### Gorev profili

Yeni ana karar alani `job_profile` olmali.

Baslangic profilleri:

- `admin`
- `gm`
- `satinalma_uzmani`
- `satinalma_yoneticisi`
- `muhasebe_personeli`
- `muhasebe_yoneticisi`
- `planlama_personeli`
- `planlama_yoneticisi`
- `uretim_operatoru`
- `cnc_operatoru`
- `uretim_sorumlusu`
- `uretim_yoneticisi`
- `bakim_personeli`
- `bakim_yoneticisi`
- `kalite_personeli`
- `kalite_sorumlusu`
- `proje_personeli`
- `departman_yoneticisi`
- `sadece_goruntuleme`

### Kapsam

Kapsam, permission'dan ayri tutulmali.

Onerilen kapsam tipleri:

- `self`: sadece kendi kayitlari
- `own_department`: kendi departmani
- `assigned_station`: atandigi istasyonlar
- `assigned_departments`: secilen departmanlar
- `target_department`: DÖF gibi hedef departmana gore
- `all_company`: tum sirket

### Operator/istasyon baglantisi

`User` ile `UretimPersoneli` iliskisi kurulmasi gerekiyor.

Minimum model:

- `User.uretim_personeli_id` nullable FK
- `UserProfileStation` veya benzeri coklu istasyon tablosu

Tek istasyon yetmezse:

- `user_station_scope`
  - `user_id`
  - `station_id`

Bu sayede operator giris yaptiginda sadece kendi istasyonlari icin veri girebilir.

## Kullanici Ekrani V2 Taslagi

Admin kullanici eklerken su bolumler olmali:

1. Kimlik
   - Ad Soyad
   - E-posta
   - Sifre
   - Telefon
   - Unvan

2. Organizasyon
   - Departman
   - Kullanici tipi
   - Gorev profili
   - Yonetici mi?

3. Kapsam
   - Kendi departmani
   - Tum sirket
   - Secili departmanlar
   - Secili istasyonlar

4. Uretim/Saha baglantisi
   - Uretim personeli kaydina bagla
   - Yeni uretim personeli olarak olustur
   - Istasyon sec

5. Varsayilan yetkiler
   - Gorev profiline gore otomatik gelsin
   - Admin isterse gelismis ayarlari acsin

6. Gelismis
   - Teknik resim yonetimi
   - Liste yonetimi
   - PDF unvan gosterimi
   - E-posta bildirimi
   - Yetki matrisi override linki

## Yetki Matrisi Ne Olacak?

Yetki matrisi kaldirilmamali, ama rolu degismeli:

- Ana yonetim araci degil
- Debug / ileri seviye override ekrani
- Kullanici profili uzerinden olusan efektif yetkileri gosteren kontrol ekrani

Yeni matris ekrani su ayrimi gostermeli:

- Profil varsayilani
- Kullanici override
- Kapsam sonucu
- Efektif sonuc

## Uygulama Sirasi

### Faz 1 - Audit ve profil sozlesmesi

- Bu dokuman baz alinacak.
- Gorev profilleri ve kapsamlar netlestirilecek.
- Mevcut roller yeni profillere eslenecek.

### Faz 2 - Model ve migration

Yeni alanlar/tablolari ekle:

- `User.user_type`
- `User.job_profile`
- `User.scope_type`
- `User.uretim_personeli_id`
- `UserScopeDepartment`
- `UserScopeStation`

Mevcut veriyi bozmadan default mapping yap:

- `admin` -> `admin`, `all_company`
- `gm` -> `gm`, `all_company`
- `satinalma` -> `satinalma_uzmani`, `all_company`
- `muhasebe` -> `muhasebe_personeli`, `own_department`
- `kalite` -> `kalite_personeli`, `assigned_departments`
- `uretim` -> `uretim_sorumlusu`, `own_department`
- `bakim` -> `bakim_personeli`, `own_department`
- `planlama` -> `planlama_personeli`, `own_department`
- `departman_yoneticisi` -> departmana gore ilgili yonetici profili
- `personel` -> departmana gore ilgili personel profili

### Faz 3 - Permission helper teklesmesi

Tek helper hedefi:

- `can_access(user, action, resource=None)`
- `can_view_menu(user, menu_key)`
- `can_submit(user, action, resource=None)`

### Faz 4 - Kullanici ekrani V2

Admin ekrani yenilenecek:

- Sol/ust kisimda kullanici listesi
- Sagda sade kullanici formu
- Gorev profili secimi
- Kapsam secimi
- Istasyon/departman baglantisi
- Gelismis override bolumu

### Faz 5 - Modul modul uygulama

Sira:

1. Uretim
2. Bakim
3. Kalite / DÖF
4. Satinalma / Talep
5. Muhasebe
6. Planlama
7. Teknik resim ve listeler

## Ilk Uygulama Onerisi

En dogru ilk kod adimi:

1. Yeni profil/kapsam sabitlerini olustur: `app/access_profiles.py`
2. `User` modeline yeni alanlari ekle.
3. Kullanici ekranina `Gorev Profili`, `Kapsam`, `Istasyonlar` alanlarini ekle.
4. Henuz route davranisini komple degistirmeden once admin ekraninda efektif yetki onizlemesi goster.

Bu yaklasim mevcut sistemi bozmaz; once gorunurluk ve veri modeli netlesir, sonra route/buton davranislari adim adim yeni modele baglanir.
