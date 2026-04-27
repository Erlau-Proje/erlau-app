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
    from app.models import TalepFormu
    now = datetime.datetime.now()
    prefix = f"SP-{now.strftime('%Y%m%d%H%M%S')}"
    count = TalepFormu.query.filter(
        TalepFormu.siparis_no.like(f"{prefix}%")
    ).count()
    return f"{prefix}-{count+1:03d}"

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
