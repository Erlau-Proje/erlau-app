from app import db
from app.models import TalepFormu, TalepKalem, Department, Tedarikci
from sqlalchemy import func, extract
from datetime import datetime, timedelta, date
import json

def get_gm_dashboard_stats():
    """GM Dashboard için gerekli tüm ağır istatistikleri hesaplar."""
    bugun = date.today()
    ay_baslangic = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    alti_ay_once = datetime.utcnow() - timedelta(days=182)

    # KPI Verileri
    durum_sayilari = dict(db.session.query(
        TalepFormu.durum, func.count(TalepFormu.id)
    ).group_by(TalepFormu.durum).all())

    gm_stats = {
        'bu_ay': TalepFormu.query.filter(TalepFormu.created_at >= ay_baslangic).count(),
        'bekleyen': durum_sayilari.get('bekliyor', 0) + durum_sayilari.get('fiyatlandirildi', 0),
        'yolda': durum_sayilari.get('yolda', 0),
        'bu_ay_teslim': TalepFormu.query.filter(
            TalepFormu.created_at >= ay_baslangic, TalepFormu.durum == 'teslim_alindi'
        ).count(),
    }

    # Departman Dağılımı
    dept_rows = db.session.query(
        TalepFormu.department_id, TalepFormu.durum, func.count(TalepFormu.id)
    ).group_by(TalepFormu.department_id, TalepFormu.durum).all()

    dept_map = {}
    for d_id, durum, sayi in dept_rows:
        dm = dept_map.setdefault(d_id, {'toplam': 0, 'bekleyen': 0, 'yolda': 0, 'teslim': 0})
        dm['toplam'] += sayi
        if durum in ('bekliyor', 'fiyatlandirildi'): dm['bekleyen'] += sayi
        elif durum == 'yolda': dm['yolda'] += sayi
        elif durum == 'teslim_alindi': dm['teslim'] += sayi

    departmanlar = Department.query.order_by(Department.name).all()
    dept_stats = [
        {'dept': d, **dept_map.get(d.id, {'toplam': 0, 'bekleyen': 0, 'yolda': 0, 'teslim': 0})}
        for d in departmanlar if d.id in dept_map
    ]

    # Trend Analizi (Son 6 Ay)
    ay_adlari = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
    son_6_ay = []
    for i in range(5, -1, -1):
        d = datetime.utcnow() - timedelta(days=30 * i)
        son_6_ay.append((d.year, d.month))

    trend_labels = [f"{ay_adlari[m-1]} {y}" for y, m in son_6_ay]
    
    trend_rows = db.session.query(
        extract('year', TalepFormu.created_at).label('yil'),
        extract('month', TalepFormu.created_at).label('ay'),
        TalepFormu.department_id,
        func.count(TalepFormu.id)
    ).filter(TalepFormu.created_at >= alti_ay_once).group_by('yil', 'ay', TalepFormu.department_id).all()

    trend_data_map = {}
    for y, m, d_id, sayi in trend_rows:
        trend_data_map.setdefault(d_id, {})[(int(y), int(m))] = sayi

    renkler = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
    datasets = []
    for i, ds in enumerate(dept_stats):
        d_id = ds['dept'].id
        datasets.append({
            'label': ds['dept'].name,
            'data': [trend_data_map.get(d_id, {}).get((y, m), 0) for y, m in son_6_ay],
            'backgroundColor': renkler[i % len(renkler)],
        })

    return {
        'gm_stats': gm_stats,
        'dept_stats': dept_stats,
        'trend_json': json.dumps({'labels': trend_labels, 'datasets': datasets}),
        'top_tedarikci': db.session.query(
            Tedarikci.name,
            func.count(TalepKalem.id).label('kalem_sayi'),
            func.count(func.distinct(TalepKalem.talep_id)).label('siparis_sayi')
        ).join(TalepKalem, TalepKalem.tedarikci_id == Tedarikci.id
        ).group_by(Tedarikci.id, Tedarikci.name
        ).order_by(func.count(TalepKalem.id).desc()).limit(10).all(),
        'bekleyen_talepler': TalepFormu.query.filter(
            TalepFormu.durum.in_(['bekliyor', 'fiyatlandirildi'])
        ).order_by(TalepFormu.created_at.asc()).limit(8).all(),
        'bekleme_stats': _bekleme_stats_hesapla(dept_stats),
    }

def _bekleme_stats_hesapla(dept_stats):
    bekleme_rows = db.session.query(
        TalepFormu.department_id,
        func.avg(func.julianday('now') - func.julianday(TalepFormu.created_at)).label('ort_gun'),
        func.count(TalepFormu.id).label('sayi')
    ).filter(TalepFormu.durum.in_(['bekliyor', 'fiyatlandirildi'])
    ).group_by(TalepFormu.department_id).all()

    bekleme_map = {r.department_id: {'gun': round(r.ort_gun or 0), 'sayi': r.sayi}
                   for r in bekleme_rows}
    result = [
        {'dept': ds['dept'], **bekleme_map[ds['dept'].id]}
        for ds in dept_stats if ds['dept'].id in bekleme_map
    ]
    result.sort(key=lambda x: x['gun'], reverse=True)
    return result

def get_user_stats(user_id):
    """Kullanıcı profil sayfası için performanslı istatistikler döndürür."""
    return dict(
        db.session.query(TalepFormu.durum, func.count(TalepFormu.id))
        .filter_by(talep_eden_id=user_id)
        .group_by(TalepFormu.durum).all()
    )