from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, date, time
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    users = db.relationship('User', backref='department', lazy=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='personel')
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_active = db.Column(db.Boolean, default=True)
    unvan = db.Column(db.String(100))
    telefon = db.Column(db.String(20))
    dogum_tarihi = db.Column(db.Date)
    unvan_pdf_goster = db.Column(db.Boolean, default=False)
    son_giris = db.Column(db.DateTime)
    sifre_degisim_tarihi = db.Column(db.DateTime)
    tablet_pin = db.Column(db.String(6))
    bildirim_email = db.Column(db.Boolean, default=True)
    teknik_resim_yetki = db.Column(db.Boolean, default=False)
    liste_yetki = db.Column(db.Boolean, default=False)
    user_type = db.Column(db.String(30), default='office', index=True)
    job_profile = db.Column(db.String(60), default='sadece_goruntuleme', index=True)
    scope_type = db.Column(db.String(40), default='self', index=True)
    uretim_personeli_id = db.Column(db.Integer, db.ForeignKey('uretim_personeli.id'), nullable=True, index=True)
    uretim_personeli = db.relationship('UretimPersoneli', foreign_keys=[uretim_personeli_id])
    talepler = db.relationship('TalepFormu', backref='talep_eden', lazy=True)
    yetkiler = db.relationship('UserPermission', foreign_keys='UserPermission.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    kapsam_departmanlari = db.relationship('UserScopeDepartment', backref='user', lazy=True, cascade='all, delete-orphan')
    kapsam_istasyonlari = db.relationship('UserScopeStation', backref='user', lazy=True, cascade='all, delete-orphan')

class UserPermission(db.Model):
    __tablename__ = 'user_permission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    permission_code = db.Column(db.String(80), nullable=False, index=True)
    allowed = db.Column(db.Boolean, default=False, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'permission_code', name='uq_user_permission_code'),)

class UserScopeDepartment(db.Model):
    __tablename__ = 'user_scope_department'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False, index=True)
    department = db.relationship('Department', foreign_keys=[department_id])
    __table_args__ = (db.UniqueConstraint('user_id', 'department_id', name='uq_user_scope_department'),)

class UserScopeStation(db.Model):
    __tablename__ = 'user_scope_station'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    station_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'), nullable=False, index=True)
    station = db.relationship('IsIstasyonu', foreign_keys=[station_id])
    __table_args__ = (db.UniqueConstraint('user_id', 'station_id', name='uq_user_scope_station'),)

class Tedarikci(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    unvan = db.Column(db.String(200))
    vergi_no = db.Column(db.String(50))
    email = db.Column(db.String(120))
    telefon = db.Column(db.String(20))
    adres = db.Column(db.Text)
    iletisim_kisi = db.Column(db.String(100))
    para_birimi = db.Column(db.String(10), default='TL')
    vade_gun = db.Column(db.Integer, default=30)
    kategori = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TalepFormu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    siparis_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    talep_eden_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), index=True)
    durum = db.Column(db.String(30), default='bekliyor', index=True)
    yolda_tarihi = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    kalemler = db.relationship('TalepKalem', backref='talep', lazy=True, cascade='all, delete-orphan')
    department = db.relationship('Department', foreign_keys=[department_id])

class TalepKalem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    talep_id = db.Column(db.Integer, db.ForeignKey('talep_formu.id'), index=True)
    parent_kalem_id = db.Column(db.Integer, db.ForeignKey('talep_kalem.id'), nullable=True)
    malzeme_adi = db.Column(db.String(200), nullable=False, index=True)
    marka_model = db.Column(db.String(200))
    malzeme_turu = db.Column(db.String(50), index=True)
    birim = db.Column(db.String(20))
    miktar = db.Column(db.Float)
    hedef = db.Column(db.String(20), default='siparis')
    kullanim_amaci = db.Column(db.String(100))
    kullanilan_alan = db.Column(db.String(50))
    proje_makine = db.Column(db.String(200))
    kw = db.Column(db.String(10))
    aciklama = db.Column(db.Text)
    anlik_stok = db.Column(db.String(50))
    teknik_resim_kodu = db.Column(db.String(100))
    standart = db.Column(db.String(100))
    br_fiyat = db.Column(db.Float)
    toplam_fiyat = db.Column(db.Float)
    para_birimi = db.Column(db.String(10))
    vade_gun = db.Column(db.Integer)
    termin_gun = db.Column(db.Integer)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'))
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    son_alinma_tarihi = db.Column(db.DateTime)
    son_siparis_no = db.Column(db.String(50))

class Fatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fatura_no = db.Column(db.String(100), index=True)
    fatura_tarihi = db.Column(db.Date)
    vade_tarihi = db.Column(db.Date)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'), index=True)
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    tedarikci_adi_ham = db.Column(db.String(200))  # AI'dan gelen ham isim
    ara_toplam = db.Column(db.Float)
    kdv_tutari = db.Column(db.Float)
    genel_toplam = db.Column(db.Float)
    para_birimi = db.Column(db.String(10), default='TL')
    durum = db.Column(db.String(30), default='bekliyor', index=True)  # bekliyor, onaylandi, odendi, iptal, iade
    dosya_yolu = db.Column(db.String(300))
    ai_ham_veri = db.Column(db.Text)  # AI'dan gelen raw JSON
    ai_guvenskoru = db.Column(db.Float)  # 0-1 arası güven skoru
    notlar = db.Column(db.Text)
    yukleme_tarihi = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    yukleyen = db.relationship('User', foreign_keys=[yukleyen_id])
    talep_id = db.Column(db.Integer, db.ForeignKey('talep_formu.id'), index=True)
    talep = db.relationship('TalepFormu', foreign_keys=[talep_id])
    kalemler = db.relationship('FaturaKalem', backref='fatura', lazy=True, cascade='all, delete-orphan')
    odeme_tarihi = db.Column(db.Date)
    fatura_turu  = db.Column(db.String(20), default='normal')  # normal | kur_farki
    ana_fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'))
    ana_fatura   = db.relationship('Fatura', remote_side='Fatura.id', foreign_keys=[ana_fatura_id])
    fatura_kuru  = db.Column(db.Float)   # fatura tarihindeki TCMB kuru
    odeme_kuru   = db.Column(db.Float)   # ödeme anındaki kur
    tl_karsiligi = db.Column(db.Float)   # genel_toplam * fatura_kuru
    odenen_tl    = db.Column(db.Float)   # genel_toplam * odeme_kuru (gerçek ödeme)

class FaturaKalem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), index=True)
    malzeme_adi = db.Column(db.String(300))
    miktar = db.Column(db.Float)
    birim = db.Column(db.String(20))
    liste_fiyati = db.Column(db.Float)
    iskonto_orani = db.Column(db.Float)
    iskonto_tutari = db.Column(db.Float)
    br_fiyat = db.Column(db.Float)
    kdv_orani = db.Column(db.Float)
    toplam_fiyat = db.Column(db.Float)
    talep_kalem_id = db.Column(db.Integer, db.ForeignKey('talep_kalem.id'), index=True)
    eslesme_durumu = db.Column(db.String(20))  # eslesti, fiyat_farki, urun_farki, eslesmiyor
    eslesme_notu = db.Column(db.Text)

class TedarikciSablon(db.Model):
    """Her tedarikçi için AI düzeltme hafızası"""
    id = db.Column(db.Integer, primary_key=True)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'))
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    ornek_json = db.Column(db.Text)
    guncelleme_tarihi = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# MALZEME LİSTESİ
# ---------------------------------------------------------------------------

class Malzeme(db.Model):
    __tablename__ = 'malzeme'
    id = db.Column(db.Integer, primary_key=True)
    stok_kodu = db.Column(db.String(20), unique=True, nullable=False)
    malzeme_adi = db.Column(db.String(200), nullable=False)
    birim = db.Column(db.String(20))
    kategori = db.Column(db.String(100))
    aciklama = db.Column(db.Text)
    kullanim_notu = db.Column(db.Text)   # AI öğrenilen proje/makine kullanım bilgisi
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# ÜRÜN LİSTESİ
# ---------------------------------------------------------------------------

class Urun(db.Model):
    __tablename__ = 'urun'
    id = db.Column(db.Integer, primary_key=True)
    urun_kodu = db.Column(db.String(20), unique=True, nullable=False)
    urun_adi = db.Column(db.String(200), nullable=False)
    proje = db.Column(db.String(100))
    makine = db.Column(db.String(100))
    aciklama = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# ÇOKLU TEDARİKÇİ TEKLİF SİSTEMİ
# ---------------------------------------------------------------------------

class TeklifGrubu(db.Model):
    __tablename__ = 'teklif_grubu'
    id = db.Column(db.Integer, primary_key=True)
    teklif_no = db.Column(db.String(30), unique=True, nullable=False)
    talep_kalem_id = db.Column(db.Integer, db.ForeignKey('talep_kalem.id'), nullable=False)
    batch_id = db.Column(db.String(36), nullable=True, index=True)
    talep_kalem = db.relationship('TalepKalem', foreign_keys=[talep_kalem_id], backref='teklif_gruplari')
    durum = db.Column(db.String(30), default='bekliyor')  # bekliyor, teklif_alindi, secildi
    konu_basligi = db.Column(db.Text)
    po_no = db.Column(db.String(30))
    po_tarihi = db.Column(db.DateTime)
    po_gonderen_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    po_gonderen = db.relationship('User', foreign_keys=[po_gonderen_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    kalemler = db.relationship('TeklifKalem', backref='grup', lazy=True, cascade='all, delete-orphan')


class TeklifKalem(db.Model):
    __tablename__ = 'teklif_kalem'
    id = db.Column(db.Integer, primary_key=True)
    grup_id = db.Column(db.Integer, db.ForeignKey('teklif_grubu.id'), nullable=False)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'))
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    birim_fiyat = db.Column(db.Float)
    para_birimi = db.Column(db.String(10), default='TL')
    vade_gun = db.Column(db.Integer)
    kaynak = db.Column(db.String(20), default='manuel')  # manuel, pdf, excel, mail
    teklif_dosyasi = db.Column(db.String(500))
    mail_referans = db.Column(db.String(100))
    notlar = db.Column(db.Text)
    red_nedeni = db.Column(db.Text)
    secildi = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# ÜRETİM MODÜLܽ
# ---------------------------------------------------------------------------

class IsIstasyonu(db.Model):
    __tablename__ = 'is_istasyonu'
    id = db.Column(db.Integer, primary_key=True)
    istasyon_kodu = db.Column(db.String(20), unique=True, nullable=False)
    istasyon_adi = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uretim_kayitlari = db.relationship('UretimKaydi', backref='istasyon', lazy=True)
    personeller = db.relationship('UretimPersoneli', backref='istasyon', lazy=True)


class UretimPersoneli(db.Model):
    __tablename__ = 'uretim_personeli'
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    soyad = db.Column(db.String(100))
    sicil_no = db.Column(db.String(20), unique=True, nullable=True)
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uretim_kayitlari = db.relationship('UretimKaydi', backref='uretim_personeli', lazy=True)

    @property
    def tam_ad(self):
        return f"{self.ad} {self.soyad or ''}".strip()


class UretimPlani(db.Model):
    __tablename__ = 'uretim_plani'
    id = db.Column(db.Integer, primary_key=True)
    plan_no = db.Column(db.String(30), unique=True, nullable=False)
    hafta = db.Column(db.Integer, nullable=False)
    yil = db.Column(db.Integer, nullable=False)
    baslangic_tarihi = db.Column(db.Date)
    bitis_tarihi = db.Column(db.Date)
    planlayan_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    planlayan = db.relationship('User', foreign_keys=[planlayan_id])
    durum = db.Column(db.String(20), default='taslak')  # taslak, aktif, tamamlandi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    satirlar = db.relationship('UretimPlaniSatir', backref='plan', lazy=True, cascade='all, delete-orphan')


class UretimPlaniSatir(db.Model):
    __tablename__ = 'uretim_plani_satir'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('uretim_plani.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'))
    urun = db.relationship('Urun', foreign_keys=[urun_id])
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'))
    istasyon = db.relationship('IsIstasyonu', foreign_keys=[istasyon_id])
    tarih = db.Column(db.Date, nullable=False)
    planlanan_adet = db.Column(db.Integer, default=0)
    devir_adet = db.Column(db.Integer, default=0)
    kaynak = db.Column(db.String(20), default='plan')  # plan | devir | tamir
    uretim_kayitlari = db.relationship('UretimKaydi', backref='plan_satir', lazy=True)


class UretimKaydi(db.Model):
    __tablename__ = 'uretim_kaydi'
    id = db.Column(db.Integer, primary_key=True)
    plan_satir_id = db.Column(db.Integer, db.ForeignKey('uretim_plani_satir.id'), nullable=True)
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'))
    urun = db.relationship('Urun', foreign_keys=[urun_id])
    tarih = db.Column(db.Date, nullable=False, default=date.today)
    gerceklesen_adet = db.Column(db.Integer, default=0)
    fire_adet = db.Column(db.Integer, default=0)
    uretim_personeli_id = db.Column(db.Integer, db.ForeignKey('uretim_personeli.id'), nullable=True)
    giren_personel_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    giren_personel = db.relationship('User', foreign_keys=[giren_personel_id])
    aciklama = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ArizaKaydi(db.Model):
    __tablename__ = 'ariza_kaydi'
    id = db.Column(db.Integer, primary_key=True)
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'), nullable=False)
    istasyon = db.relationship('IsIstasyonu', foreign_keys=[istasyon_id])
    tarih = db.Column(db.Date, nullable=False, default=date.today)
    baslangic_saati = db.Column(db.Time)
    bitis_saati = db.Column(db.Time)
    aciklama = db.Column(db.Text)
    durum = db.Column(db.String(20), default='acik')  # acik, kapali
    giren_personel_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    giren_personel = db.relationship('User', foreign_keys=[giren_personel_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# BAKIM MODÜLܽ
# ---------------------------------------------------------------------------

class Makine(db.Model):
    __tablename__ = 'makine'
    id = db.Column(db.Integer, primary_key=True)
    makine_kodu = db.Column(db.String(20), unique=True, nullable=False)
    makine_adi = db.Column(db.String(200), nullable=False)
    marka = db.Column(db.String(100))
    model = db.Column(db.String(100))
    seri_no = db.Column(db.String(100))
    islev = db.Column(db.String(200))
    lokasyon = db.Column(db.String(200))
    guc_kw = db.Column(db.String(30))
    uretim_yili = db.Column(db.Integer)
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'), nullable=True)
    istasyon = db.relationship('IsIstasyonu', foreign_keys=[istasyon_id])
    aciklama = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bakim_planlari = db.relationship('BakimPlani', backref='makine', lazy=True)
    bakim_kayitlari = db.relationship('BakimKaydi', backref='makine', lazy=True)
    planli_bakimlar = db.relationship('PlanliBakim', backref='makine', lazy=True)
    periyodik_kontroller = db.relationship('PeriyodikKontrol', backref='makine', lazy=True)


class BakimPlani(db.Model):
    __tablename__ = 'bakim_plani'
    id = db.Column(db.Integer, primary_key=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id'), nullable=False)
    bakim_adi = db.Column(db.String(200), nullable=False)
    periyot_gun = db.Column(db.Integer, nullable=False)
    son_bakim_tarihi = db.Column(db.Date)
    sonraki_bakim_tarihi = db.Column(db.Date)
    aciklama = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)


class BakimKaydi(db.Model):
    __tablename__ = 'bakim_kaydi'
    id = db.Column(db.Integer, primary_key=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id'), nullable=False)
    bakim_plani_id = db.Column(db.Integer, db.ForeignKey('bakim_plani.id'), nullable=True)
    bakim_plani = db.relationship('BakimPlani', foreign_keys=[bakim_plani_id])
    bakim_turu = db.Column(db.String(30), default='gunluk')  # gunluk, periyodik, ariza
    tarih = db.Column(db.Date, nullable=False, default=date.today)
    yapilan_isler = db.Column(db.Text)
    sure_dakika = db.Column(db.Integer)
    baslangic_saati = db.Column(db.Time, nullable=True)
    bitis_saati = db.Column(db.Time, nullable=True)
    parca_kullanildi = db.Column(db.Boolean, default=False)
    kullanilan_parcalar = db.Column(db.Text)
    giren_personel_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    giren_personel = db.relationship('User', foreign_keys=[giren_personel_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PlanliBakim(db.Model):
    """Bakım departmanının oluşturduğu tarihli bakım penceresi."""
    __tablename__ = 'planli_bakim'
    id = db.Column(db.Integer, primary_key=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id'), nullable=False)
    bakim_adi = db.Column(db.String(200), nullable=False)
    baslangic_tarihi = db.Column(db.Date, nullable=False)
    bitis_tarihi = db.Column(db.Date, nullable=False)
    baslangic_saati = db.Column(db.Time, nullable=True)
    bitis_saati = db.Column(db.Time, nullable=True)
    sure_saat = db.Column(db.Float, nullable=True)
    # planli | devam_ediyor | tamamlandi | iptal
    durum = db.Column(db.String(20), default='planli', index=True)
    planlayan_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    planlayan = db.relationship('User', foreign_keys=[planlayan_id])
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PeriyodikKontrol(db.Model):
    """Dış kaynaklı firma tarafından yapılan periyodik kontroller."""
    __tablename__ = 'periyodik_kontrol'
    id = db.Column(db.Integer, primary_key=True)
    makine_id = db.Column(db.Integer, db.ForeignKey('makine.id'), nullable=True)
    kontrol_adi = db.Column(db.String(200), nullable=False)
    kontrol_turu = db.Column(db.String(50))  # elektrik, toprak, basinc, diger
    periyot_ay = db.Column(db.Integer, nullable=False, default=12)  # 6 veya 12
    son_kontrol_tarihi = db.Column(db.Date, nullable=True)
    sonraki_kontrol_tarihi = db.Column(db.Date, nullable=True)
    kontrol_eden_firma = db.Column(db.String(200))
    son_kontrol_notu = db.Column(db.Text)
    # aktif | pasif
    durum = db.Column(db.String(20), default='aktif', index=True)
    olusturan_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    olusturan = db.relationship('User', foreign_keys=[olusturan_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# TEKNİK RESİM
# ---------------------------------------------------------------------------

class TeknikResim(db.Model):
    __tablename__ = 'teknik_resim'
    id = db.Column(db.Integer, primary_key=True)
    klasor = db.Column(db.String(500), index=True)   # relative folder path, e.g. "MakineA/Alt"
    dosya_adi_gosterim = db.Column(db.String(300), nullable=False, index=True)  # original filename stem
    dosya_adi = db.Column(db.String(400), nullable=False)  # filename on disk
    aciklama = db.Column(db.Text)
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    yukleyen = db.relationship('User', foreign_keys=[yukleyen_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


# ---------------------------------------------------------------------------
# KALİTE KONTROL
# ---------------------------------------------------------------------------

class KaliteKontrol(db.Model):
    __tablename__ = 'kalite_kontrol'
    id = db.Column(db.Integer, primary_key=True)
    tarih = db.Column(db.Date, nullable=False, default=date.today, index=True)
    uretim_kaydi_id = db.Column(db.Integer, db.ForeignKey('uretim_kaydi.id'), nullable=True)
    uretim_kaydi = db.relationship('UretimKaydi', foreign_keys=[uretim_kaydi_id])
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    urun = db.relationship('Urun', foreign_keys=[urun_id])
    istasyon_id = db.Column(db.Integer, db.ForeignKey('is_istasyonu.id'), nullable=False)
    kontrol_eden_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    kontrol_eden = db.relationship('User', foreign_keys=[kontrol_eden_id])
    ok_adet = db.Column(db.Integer, default=0)
    nok_adet = db.Column(db.Integer, default=0)
    # hammadde_hatasi | isleme_hatasi | olcu_hatasi | diger
    nok_neden = db.Column(db.String(50), nullable=True)
    nok_neden_aciklama = db.Column(db.Text, nullable=True)
    # hurda | tamir
    nok_akibet = db.Column(db.String(20), nullable=True)
    tamir_plan_satir_id = db.Column(db.Integer, db.ForeignKey('uretim_plani_satir.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# DÖF — DÜZELTİCİ VE ÖNLEYİCİ FAALİYET
# ---------------------------------------------------------------------------

class DOF(db.Model):
    __tablename__ = 'dof'
    id = db.Column(db.Integer, primary_key=True)
    dof_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    tarih = db.Column(db.Date, nullable=False, default=date.today)
    # acik | isleniyor | kapali | gecikti | iptal
    durum = db.Column(db.String(20), default='acik', index=True)
    hedef_departman = db.Column(db.String(50), nullable=False)
    hedef_kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    hedef_kullanici = db.relationship('User', foreign_keys=[hedef_kullanici_id])
    acan_kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    acan_kullanici = db.relationship('User', foreign_keys=[acan_kullanici_id])
    problem_tanimi = db.Column(db.Text, nullable=False)
    kok_neden = db.Column(db.Text, nullable=True)
    planlanan_kapatma_tarihi = db.Column(db.Date, nullable=True)
    gercek_kapatma_tarihi = db.Column(db.Date, nullable=True)
    kapatan_kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    kapatan_kullanici = db.relationship('User', foreign_keys=[kapatan_kullanici_id])
    kapatma_notu = db.Column(db.Text, nullable=True)
    # ic | tedis (tedarikçi)
    tip = db.Column(db.String(10), default='ic')
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'), nullable=True)
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    aksiyonlar = db.relationship('DOFAksiyon', backref='dof', lazy=True, cascade='all, delete-orphan')
    ekler = db.relationship('DOFEk', backref='dof', lazy=True, cascade='all, delete-orphan')


class DOFAksiyon(db.Model):
    __tablename__ = 'dof_aksiyon'
    id = db.Column(db.Integer, primary_key=True)
    dof_id = db.Column(db.Integer, db.ForeignKey('dof.id'), nullable=False)
    aksiyon_tanimi = db.Column(db.Text, nullable=False)
    sorumlu_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sorumlu = db.relationship('User', foreign_keys=[sorumlu_id])
    planlanan_tarih = db.Column(db.Date, nullable=False)
    tamamlama_tarihi = db.Column(db.Date, nullable=True)
    # bekliyor | tamamlandi | gecikti
    durum = db.Column(db.String(20), default='bekliyor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DOFEk(db.Model):
    __tablename__ = 'dof_ek'
    id = db.Column(db.Integer, primary_key=True)
    dof_id = db.Column(db.Integer, db.ForeignKey('dof.id'), nullable=False)
    dosya_adi = db.Column(db.String(200), nullable=False)
    dosya_yolu = db.Column(db.String(500), nullable=False)
    # resim | pdf | diger
    dosya_turu = db.Column(db.String(20), default='diger')
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    yukleyen = db.relationship('User', foreign_keys=[yukleyen_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# 8D RAPORU
# ---------------------------------------------------------------------------

class SekizD(db.Model):
    __tablename__ = 'sekiz_d'
    id = db.Column(db.Integer, primary_key=True)
    sekizd_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    tarih = db.Column(db.Date, nullable=False, default=date.today)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'), nullable=False)
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    urun_kodu = db.Column(db.String(50), nullable=True)
    urun_adi = db.Column(db.String(200), nullable=True)
    revizyon_no = db.Column(db.String(10), default='1')
    # taslak | gonderildi | kapali
    durum = db.Column(db.String(20), default='taslak')
    # D1
    d1_ekip_lideri = db.Column(db.String(100), nullable=True)
    d1_ekip_uyeleri = db.Column(db.Text, nullable=True)
    # D2 - Problem (5W2H)
    d2_problem_ozeti = db.Column(db.Text, nullable=True)
    d2_kim = db.Column(db.String(200), nullable=True)
    d2_ne = db.Column(db.String(200), nullable=True)
    d2_nerede = db.Column(db.String(200), nullable=True)
    d2_ne_zaman = db.Column(db.String(200), nullable=True)
    d2_neden = db.Column(db.String(200), nullable=True)
    d2_nasil = db.Column(db.String(200), nullable=True)
    d2_ne_kadar = db.Column(db.String(200), nullable=True)
    d2_ilk_tespit = db.Column(db.String(100), nullable=True)
    # D3 - Geçici Önlem
    d3_onlem = db.Column(db.Text, nullable=True)
    d3_sorumlu = db.Column(db.String(100), nullable=True)
    d3_tarih = db.Column(db.Date, nullable=True)
    d3_etkinlik = db.Column(db.String(200), nullable=True)
    # D4 - Kök Neden
    d4_kok_neden = db.Column(db.Text, nullable=True)
    # 5why | balik_kilcigi | diger
    d4_analiz_metod = db.Column(db.String(50), nullable=True)
    # D5 - Kalıcı Düzeltici
    d5_aksiyon = db.Column(db.Text, nullable=True)
    # D6 - Uygulama
    d6_uygulama = db.Column(db.Text, nullable=True)
    d6_tarih = db.Column(db.Date, nullable=True)
    d6_dogrulama = db.Column(db.String(200), nullable=True)
    # D7 - Önleyici
    d7_onleyici = db.Column(db.Text, nullable=True)
    # D8
    d8_tadir = db.Column(db.Text, nullable=True)
    acan_kullanici_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    acan_kullanici = db.relationship('User', foreign_keys=[acan_kullanici_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# İŞ AKIŞI SÜREÇLERİ
# ---------------------------------------------------------------------------

class IsAkisiSurec(db.Model):
    __tablename__ = 'is_akisi_surec'
    id = db.Column(db.Integer, primary_key=True)
    surec_kodu = db.Column(db.String(20), unique=True, nullable=False)
    surec_adi = db.Column(db.String(200), nullable=False)
    departman = db.Column(db.String(50), nullable=False)
    aciklama = db.Column(db.Text, nullable=True)
    versiyon = db.Column(db.String(10), default='1.0')
    # taslak | aktif | arsiv
    durum = db.Column(db.String(20), default='taslak')
    olusturan_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    olusturan = db.relationship('User', foreign_keys=[olusturan_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    adimlar = db.relationship('IsAkisiAdim', backref='surec', lazy=True,
                              order_by='IsAkisiAdim.sira', cascade='all, delete-orphan')


class IsAkisiAdim(db.Model):
    __tablename__ = 'is_akisi_adim'
    id = db.Column(db.Integer, primary_key=True)
    surec_id = db.Column(db.Integer, db.ForeignKey('is_akisi_surec.id'), nullable=False)
    sira = db.Column(db.Integer, nullable=False, default=1)
    # baslangic | islem | karar | belge | bitis
    adim_tipi = db.Column(db.String(20), default='islem')
    adim_adi = db.Column(db.String(200), nullable=False)
    aciklama = db.Column(db.Text, nullable=True)
    sorumlu_departman = db.Column(db.String(50), nullable=True)
    sure_hedef_saat = db.Column(db.Integer, nullable=True)
    evet_sonraki_sira = db.Column(db.Integer, nullable=True)
    hayir_sonraki_sira = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
