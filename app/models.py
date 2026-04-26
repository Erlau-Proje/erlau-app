from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
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
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    unvan = db.Column(db.String(100))
    telefon = db.Column(db.String(20))
    dogum_tarihi = db.Column(db.Date)
    unvan_pdf_goster = db.Column(db.Boolean, default=False)
    son_giris = db.Column(db.DateTime)
    sifre_degisim_tarihi = db.Column(db.DateTime)
    tablet_pin = db.Column(db.String(6))
    bildirim_email = db.Column(db.Boolean, default=True)
    talepler = db.relationship('TalepFormu', backref='talep_eden', lazy=True)

class Tedarikci(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
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
    siparis_no = db.Column(db.String(50), unique=True, nullable=False)
    talep_eden_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    durum = db.Column(db.String(30), default='bekliyor')
    yolda_tarihi = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    kalemler = db.relationship('TalepKalem', backref='talep', lazy=True, cascade='all, delete-orphan')
    department = db.relationship('Department', foreign_keys=[department_id])

class TalepKalem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    talep_id = db.Column(db.Integer, db.ForeignKey('talep_formu.id'))
    malzeme_adi = db.Column(db.String(200), nullable=False)
    marka_model = db.Column(db.String(200))
    malzeme_turu = db.Column(db.String(50))
    birim = db.Column(db.String(20))
    miktar = db.Column(db.Float)
    hedef = db.Column(db.String(20), default='siparis')
    kullanim_amaci = db.Column(db.String(100))
    kullanilan_alan = db.Column(db.String(50))
    proje_makine = db.Column(db.String(200))
    kw = db.Column(db.String(10))
    aciklama = db.Column(db.Text)
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
    fatura_no = db.Column(db.String(100))
    fatura_tarihi = db.Column(db.Date)
    vade_tarihi = db.Column(db.Date)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'))
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    tedarikci_adi_ham = db.Column(db.String(200))  # AI'dan gelen ham isim
    ara_toplam = db.Column(db.Float)
    kdv_tutari = db.Column(db.Float)
    genel_toplam = db.Column(db.Float)
    para_birimi = db.Column(db.String(10), default='TL')
    durum = db.Column(db.String(30), default='bekliyor')  # bekliyor, onaylandi, odendi, iptal, iade
    dosya_yolu = db.Column(db.String(300))
    ai_ham_veri = db.Column(db.Text)  # AI'dan gelen raw JSON
    ai_guvenskoru = db.Column(db.Float)  # 0-1 arası güven skoru
    notlar = db.Column(db.Text)
    yukleme_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    yukleyen_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    yukleyen = db.relationship('User', foreign_keys=[yukleyen_id])
    talep_id = db.Column(db.Integer, db.ForeignKey('talep_formu.id'))
    talep = db.relationship('TalepFormu', foreign_keys=[talep_id])
    kalemler = db.relationship('FaturaKalem', backref='fatura', lazy=True, cascade='all, delete-orphan')
    odeme_tarihi = db.Column(db.Date)

class FaturaKalem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'))
    malzeme_adi = db.Column(db.String(300))
    miktar = db.Column(db.Float)
    birim = db.Column(db.String(20))
    br_fiyat = db.Column(db.Float)
    kdv_orani = db.Column(db.Float)
    toplam_fiyat = db.Column(db.Float)
    talep_kalem_id = db.Column(db.Integer, db.ForeignKey('talep_kalem.id'))
    eslesme_durumu = db.Column(db.String(20))  # eslesti, fiyat_farki, urun_farki, eslesmiyor
    eslesme_notu = db.Column(db.Text)

class TedarikciSablon(db.Model):
    """Her tedarikçi için AI düzeltme hafızası"""
    id = db.Column(db.Integer, primary_key=True)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'))
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    ornek_json = db.Column(db.Text)  # Onaylanmış fatura JSON örneği
    guncelleme_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
