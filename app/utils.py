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
