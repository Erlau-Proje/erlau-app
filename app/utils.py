import random, string
from app.models import Department, User, db
from werkzeug.security import generate_password_hash

def create_default_data():
    departmanlar = [
        'Üretim', 'Bakım', 'Planlama ve Tedarik Zinciri',
        'Proje', 'İnsan Kaynakları', 'Muhasebe',
        'Kalite', 'Satınalma', 'Genel Müdür'
    ]
    for dep_name in departmanlar:
        if not Department.query.filter_by(name=dep_name).first():
            dep = Department(name=dep_name)
            db.session.add(dep)
    db.session.commit()

    if not User.query.filter_by(email='admin@erlau.com').first():
        admin_dep = Department.query.filter_by(name='Satınalma').first()
        admin = User(
            name='Admin',
            email='admin@erlau.com',
            password=generate_password_hash('Erlau2026!'),
            role='admin',
            department_id=admin_dep.id if admin_dep else None
        )
        db.session.add(admin)
        db.session.commit()

import datetime

def generate_siparis_no():
    now = datetime.datetime.now()
    rastgele = ''.join(random.choices(string.digits, k=4))
    return f"SP-{now.strftime('%Y%m%d%H%M%S')}-{rastgele}"

def generate_stok_kodu():
    from app.models import Malzeme
    son = Malzeme.query.order_by(Malzeme.id.desc()).first()
    sonraki = (son.id + 1) if son else 1
    return f"MLZ-{sonraki:05d}"

def generate_urun_kodu():
    from app.models import Urun
    son = Urun.query.order_by(Urun.id.desc()).first()
    sonraki = (son.id + 1) if son else 1
    return f"URN-{sonraki:05d}"

def generate_makine_kodu():
    from app.models import Makine
    son = Makine.query.order_by(Makine.id.desc()).first()
    sonraki = (son.id + 1) if son else 1
    return f"MKN-{sonraki:05d}"

def generate_teklif_no():
    from app.models import TeklifGrubu
    yil = datetime.datetime.now().year
    son = TeklifGrubu.query.filter(
        TeklifGrubu.teklif_no.like(f"TKL-{yil}-%")
    ).order_by(TeklifGrubu.id.desc()).first()
    if son:
        sonraki = int(son.teklif_no.split('-')[-1]) + 1
    else:
        sonraki = 1
    return f"TKL-{yil}-{sonraki:05d}"

def generate_istasyon_kodu():
    from app.models import IsIstasyonu
    son = IsIstasyonu.query.order_by(IsIstasyonu.id.desc()).first()
    sonraki = (son.id + 1) if son else 1
    return f"IST-{sonraki:05d}"

def generate_plan_no():
    from app.models import UretimPlani
    now = datetime.datetime.now()
    hafta = now.isocalendar()[1]
    yil = now.year
    son = UretimPlani.query.filter_by(hafta=hafta, yil=yil).count()
    return f"PLN-{yil}-W{hafta:02d}-{son+1:02d}"

def generate_dof_no():
    from app.models import DOF
    yil = datetime.datetime.now().year
    son = DOF.query.filter(DOF.dof_no.like(f"DOF-{yil}-%")).count()
    return f"DOF-{yil}-{son+1:05d}"

def generate_sekizd_no():
    from app.models import SekizD
    yil = datetime.datetime.now().year
    son = SekizD.query.filter(SekizD.sekizd_no.like(f"8D-{yil}-%")).count()
    return f"8D-{yil}-{son+1:05d}"

def generate_surec_kodu():
    from app.models import IsAkisiSurec
    yil = datetime.datetime.now().year
    son = IsAkisiSurec.query.filter(IsAkisiSurec.surec_kodu.like(f"SRC-{yil}-%")).count()
    return f"SRC-{yil}-{son+1:03d}"

def devir_gunu(tarih):
    """Hafta sonu atlayarak bir sonraki çalışma gününü döndürür."""
    sonraki = tarih + datetime.timedelta(days=1)
    while sonraki.weekday() >= 5:  # 5=Cumartesi, 6=Pazar
        sonraki += datetime.timedelta(days=1)
    return sonraki

def haftalik_gunden_gune_dagit(haftalik_adet: int, gun_sayisi: int = 5) -> list:
    """Haftalık adet hedefini günlere eşit böler; kalan ilk güne eklenir."""
    if gun_sayisi <= 0 or haftalik_adet <= 0:
        return [0] * max(gun_sayisi, 1)
    gun_basi = haftalik_adet // gun_sayisi
    kalan = haftalik_adet % gun_sayisi
    dagitim = [gun_basi] * gun_sayisi
    dagitim[0] += kalan
    return dagitim
