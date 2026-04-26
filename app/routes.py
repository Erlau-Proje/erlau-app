from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import selectinload
from app import db
from app.models import User, Department, TalepFormu, TalepKalem, Tedarikci, Fatura, FaturaKalem, TedarikciSablon
from app.utils import generate_siparis_no
from datetime import datetime, date, timedelta
from functools import wraps

auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)
satin_alma = Blueprint('satin_alma', __name__, url_prefix='/satinalma')
admin = Blueprint('admin', __name__, url_prefix='/admin')
muhasebe = Blueprint('muhasebe', __name__, url_prefix='/muhasebe')

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password) and user.is_active:
            login_user(user)
            user.son_giris = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('main.dashboard'))
        flash('E-posta veya şifre hatalı.', 'danger')
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    from app.services import get_gm_dashboard_stats
    if current_user.role in ['satinalma', 'admin']:
        return redirect(url_for('satin_alma.panel'))

    bugun = date.today()

    if current_user.role == 'gm':
        stats_data = get_gm_dashboard_stats()

        # ── GECİKMİŞ SİPARİŞLER ──────────────────────────────────────────────
        yolda_talepler = TalepFormu.query.options(
            selectinload(TalepFormu.kalemler)
        ).filter(
            TalepFormu.durum == 'yolda',
            TalepFormu.yolda_tarihi != None
        ).all()

        gecikis_listesi = []
        for t in yolda_talepler:
            if not t.kalemler:
                continue
            termin = max((k.termin_gun or 0) for k in t.kalemler)
            if termin > 0:
                bitis = t.yolda_tarihi.date() + timedelta(days=termin)
                if bitis < bugun:
                    gecikis_listesi.append({'talep': t, 'gecikme': (bugun - bitis).days})
        gecikis_listesi.sort(key=lambda x: x['gecikme'], reverse=True)

        return render_template('dashboard.html',
            gm_stats=stats_data['gm_stats'],
            dept_stats=stats_data['dept_stats'],
            bekleyen_talepler=stats_data['bekleyen_talepler'],
            trend_json=stats_data['trend_json'],
            bekleme_stats=stats_data['bekleme_stats'],
            gecikis_listesi=gecikis_listesi,
            top_tedarikci=stats_data['top_tedarikci'],
            talepler=[], kalan_gunler={}, pagination=None)

    page = request.args.get('page', 1, type=int)
    if current_user.role == 'departman_yoneticisi':
        pagination = TalepFormu.query.options(
            selectinload(TalepFormu.kalemler),
            selectinload(TalepFormu.talep_eden),
        ).filter_by(
            department_id=current_user.department_id
        ).order_by(TalepFormu.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    else:
        pagination = TalepFormu.query.options(
            selectinload(TalepFormu.kalemler),
        ).filter_by(
            talep_eden_id=current_user.id
        ).order_by(TalepFormu.created_at.desc()).paginate(page=page, per_page=20, error_out=False)

    talepler = pagination.items
    kalan_gunler = {}
    for talep in talepler:
        if talep.durum == 'yolda' and talep.yolda_tarihi:
            termin = max((k.termin_gun or 0) for k in talep.kalemler) if talep.kalemler else 0
            if termin > 0:
                bitis = talep.yolda_tarihi.date() + timedelta(days=termin)
                kalan_gunler[talep.id] = (bitis - bugun).days

    # İstatistikleri tüm kayıtlar üzerinden hesapla (sadece bu sayfadaki 20 üzerinden değil)
    if current_user.role == 'departman_yoneticisi':
        stats_q = TalepFormu.query.filter_by(department_id=current_user.department_id)
    else:
        stats_q = TalepFormu.query.filter_by(talep_eden_id=current_user.id)

    stats = {
        'toplam': stats_q.count(),
        'bekleyen': stats_q.filter(TalepFormu.durum.in_(('bekliyor', 'fiyatlandirildi'))).count(),
        'yolda': stats_q.filter_by(durum='yolda').count(),
        'onaylandi': stats_q.filter_by(durum='onaylandi').count(),
        'teslim': stats_q.filter_by(durum='teslim_alindi').count(),
    }

    return render_template('dashboard.html',
        talepler=talepler,
        kalan_gunler=kalan_gunler,
        pagination=pagination,
        stats=stats,
        gm_stats=None)

@main.route('/arama')
@login_required
def arama():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    sonuclar = []
    pagination = None
    if q:
        from sqlalchemy import or_
        kalem_query = TalepKalem.query.join(TalepFormu).filter(
            or_(
                TalepKalem.malzeme_adi.ilike(f'%{q}%'),
                TalepKalem.marka_model.ilike(f'%{q}%'),
                TalepKalem.malzeme_turu.ilike(f'%{q}%'),
                TalepKalem.aciklama.ilike(f'%{q}%'),
                TalepKalem.kullanim_amaci.ilike(f'%{q}%'),
                TalepKalem.teknik_resim_kodu.ilike(f'%{q}%'),
                TalepKalem.standart.ilike(f'%{q}%'),
                TalepFormu.siparis_no.ilike(f'%{q}%'),
            )
        )
        if current_user.role not in ['satinalma', 'admin', 'gm']:
            if current_user.role == 'departman_yoneticisi':
                kalem_query = kalem_query.filter(TalepFormu.department_id == current_user.department_id)
            else:
                kalem_query = kalem_query.filter(TalepFormu.talep_eden_id == current_user.id)
        
        pagination = kalem_query.order_by(TalepFormu.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
        sonuclar = pagination.items
        
    return render_template('arama.html', q=q, sonuclar=sonuclar, pagination=pagination)

@main.route('/talep/yeni', methods=['GET', 'POST'])
@login_required
def yeni_talep():
    if request.method == 'POST':
        talep = TalepFormu(
            siparis_no=generate_siparis_no(),
            talep_eden_id=current_user.id,
            department_id=current_user.department_id,
            durum='bekliyor'
        )
        db.session.add(talep)
        db.session.flush()

        malzeme_adlari = request.form.getlist('malzeme_adi[]')
        marka_modeller = request.form.getlist('marka_model[]')
        malzeme_turleri = request.form.getlist('malzeme_turu[]')
        birimler = request.form.getlist('birim[]')
        miktarlar = request.form.getlist('miktar[]')
        hedefler = request.form.getlist('hedef[]')
        kwler = request.form.getlist('kw[]')
        aciklamalar = request.form.getlist('aciklama[]')
        kullanim_amaclari = request.form.getlist('kullanim_amaci[]')
        kullanilan_alanlar = request.form.getlist('kullanilan_alan[]')
        proje_makineler = request.form.getlist('proje_makine[]')

        for i, ad in enumerate(malzeme_adlari):
            if ad.strip():
                kalem = TalepKalem(
                    talep_id=talep.id,
                    malzeme_adi=ad,
                    marka_model=marka_modeller[i] if i < len(marka_modeller) else '',
                    malzeme_turu=malzeme_turleri[i] if i < len(malzeme_turleri) else '',
                    birim=birimler[i] if i < len(birimler) else 'Adet',
                    miktar=float(miktarlar[i]) if i < len(miktarlar) and miktarlar[i] else 0,
                    hedef=hedefler[i] if i < len(hedefler) else 'siparis',
                    kullanim_amaci=kullanim_amaclari[i] if i < len(kullanim_amaclari) else '',
                    kullanilan_alan=kullanilan_alanlar[i] if i < len(kullanilan_alanlar) else '',
                    proje_makine=proje_makineler[i] if i < len(proje_makineler) else '',
                    kw=kwler[i] if i < len(kwler) else '',
                    aciklama=aciklamalar[i] if i < len(aciklamalar) else ''
                )
                db.session.add(kalem)

        db.session.commit()
        flash(f'Talep {talep.siparis_no} başarıyla oluşturuldu!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('yeni_talep.html')

@main.route('/talep/<int:talep_id>')
@login_required
def talep_detay(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    return render_template('talep_detay.html', talep=talep)

@main.route('/talep/<int:talep_id>/duzenle', methods=['GET', 'POST'])
@login_required
def talep_duzenle(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    if talep.talep_eden_id != current_user.id and current_user.role != 'admin':
        flash('Bu talebi düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('main.dashboard'))
    if talep.durum != 'bekliyor':
        flash('Sadece bekleyen talepler düzenlenebilir.', 'danger')
        return redirect(url_for('main.talep_detay', talep_id=talep_id))
    if request.method == 'POST':
        for kalem in list(talep.kalemler):
            db.session.delete(kalem)
        db.session.flush()
        malzeme_adlari = request.form.getlist('malzeme_adi[]')
        marka_modeller = request.form.getlist('marka_model[]')
        malzeme_turleri = request.form.getlist('malzeme_turu[]')
        birimler = request.form.getlist('birim[]')
        miktarlar = request.form.getlist('miktar[]')
        hedefler = request.form.getlist('hedef[]')
        kullanim_amaclari = request.form.getlist('kullanim_amaci[]')
        kullanilan_alanlar = request.form.getlist('kullanilan_alan[]')
        proje_makineler = request.form.getlist('proje_makine[]')
        kwler = request.form.getlist('kw[]')
        aciklamalar = request.form.getlist('aciklama[]')
        for i, ad in enumerate(malzeme_adlari):
            if ad.strip():
                db.session.add(TalepKalem(
                    talep_id=talep.id,
                    malzeme_adi=ad,
                    marka_model=marka_modeller[i] if i < len(marka_modeller) else '',
                    malzeme_turu=malzeme_turleri[i] if i < len(malzeme_turleri) else '',
                    birim=birimler[i] if i < len(birimler) else 'Adet',
                    miktar=float(miktarlar[i]) if i < len(miktarlar) and miktarlar[i] else 0,
                    hedef=hedefler[i] if i < len(hedefler) else 'siparis',
                    kullanim_amaci=kullanim_amaclari[i] if i < len(kullanim_amaclari) else '',
                    kullanilan_alan=kullanilan_alanlar[i] if i < len(kullanilan_alanlar) else '',
                    proje_makine=proje_makineler[i] if i < len(proje_makineler) else '',
                    kw=kwler[i] if i < len(kwler) else '',
                    aciklama=aciklamalar[i] if i < len(aciklamalar) else ''
                ))
        db.session.commit()
        flash('Talep güncellendi.', 'success')
        return redirect(url_for('main.talep_detay', talep_id=talep_id))
    return render_template('talep_duzenle.html', talep=talep)

@main.route('/talep/<int:talep_id>/sil', methods=['POST'])
@login_required
def talep_sil(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    if talep.talep_eden_id != current_user.id and current_user.role != 'admin':
        flash('Bu talebi silme yetkiniz yok.', 'danger')
        return redirect(url_for('main.dashboard'))
    if talep.durum != 'bekliyor':
        flash('Sadece bekleyen talepler silinebilir.', 'danger')
        return redirect(url_for('main.dashboard'))
    db.session.delete(talep)
    db.session.commit()
    flash('Talep silindi.', 'success')
    return redirect(url_for('main.dashboard'))

@satin_alma.route('/siparis-raporu')
@login_required
def siparis_raporu():
    from sqlalchemy import func

    # Filtreler — tarih boşsa son 6 ay varsayılan
    _varsayilan_bas = (datetime.utcnow() - timedelta(days=182)).strftime('%Y-%m-%d')
    bas_str = request.args.get('bas_tarih', _varsayilan_bas)
    bit_str = request.args.get('bit_tarih', '')
    tur_filtre = request.args.get('malzeme_turu', '')
    ted_filtre = request.args.get('tedarikci_id', '')
    durum_filtre = request.args.get('durum', '')
    hedef_filtre = request.args.get('hedef', '')
    amac_filtre = request.args.get('kullanim_amaci', '')
    alan_filtre = request.args.get('kullanilan_alan', '')
    proje_filtre = request.args.get('proje_makine', '').strip()
    export = request.args.get('export', '')
    page = request.args.get('page', 1, type=int)

    query = TalepKalem.query.join(TalepFormu).options(
        selectinload(TalepKalem.talep).selectinload(TalepFormu.talep_eden),
        selectinload(TalepKalem.talep).selectinload(TalepFormu.department),
        selectinload(TalepKalem.tedarikci)
    )

    # Rol bazlı kapsam
    if current_user.role in ['satinalma', 'admin', 'gm']:
        pass  # hepsini görür
    elif current_user.role == 'departman_yoneticisi':
        query = query.filter(TalepFormu.department_id == current_user.department_id)
    else:
        query = query.filter(TalepFormu.talep_eden_id == current_user.id)

    if bas_str:
        try:
            bas = datetime.strptime(bas_str, '%Y-%m-%d')
            query = query.filter(TalepFormu.created_at >= bas)
        except ValueError:
            pass
    if bit_str:
        try:
            bit = datetime.strptime(bit_str, '%Y-%m-%d')
            bit = bit.replace(hour=23, minute=59, second=59)
            query = query.filter(TalepFormu.created_at <= bit)
        except ValueError:
            pass
    if tur_filtre:
        query = query.filter(TalepKalem.malzeme_turu == tur_filtre)
    if ted_filtre:
        query = query.filter(TalepKalem.tedarikci_id == int(ted_filtre))
    if durum_filtre:
        query = query.filter(TalepFormu.durum == durum_filtre)
    if hedef_filtre:
        query = query.filter(TalepKalem.hedef == hedef_filtre)
    if amac_filtre:
        query = query.filter(TalepKalem.kullanim_amaci == amac_filtre)
    if alan_filtre:
        query = query.filter(TalepKalem.kullanilan_alan == alan_filtre)
    if proje_filtre:
        query = query.filter(TalepKalem.proje_makine.ilike(f'%{proje_filtre}%'))

    # Excel export
    if export == 'excel':
        kalemler = query.order_by(TalepFormu.created_at.desc()).all()
        import io
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        from flask import make_response
        wb = Workbook()
        ws = wb.active
        ws.title = 'Sipariş Raporu'
        basliklar = ['Sipariş No', 'Tarih', 'Talep Eden', 'Departman', 'Malzeme Adı',
                     'Marka/Model', 'Malzeme Türü', 'Kullanım Amacı', 'Kullanılan Alan',
                     'Proje/Makine', 'Miktar', 'Birim', 'Br. Fiyat', 'Toplam', 'Para Birimi',
                     'Tedarikçi', 'Vade (gün)', 'Termin (gün)', 'Durum']
        yesil = PatternFill(fill_type='solid', fgColor='2d7a3a')
        for col, b in enumerate(basliklar, 1):
            c = ws.cell(row=1, column=col, value=b)
            c.font = Font(bold=True, color='FFFFFF')
            c.fill = yesil
            c.alignment = Alignment(horizontal='center')
            ws.column_dimensions[c.column_letter].width = 18
        for i, k in enumerate(kalemler, 2):
            t = k.talep
            ws.append([
                t.siparis_no,
                t.created_at.strftime('%d.%m.%Y'),
                t.talep_eden.name if t.talep_eden else '',
                t.department.name if t.department else '',
                k.malzeme_adi, k.marka_model or '',
                k.malzeme_turu or '', k.kullanim_amaci or '',
                k.kullanilan_alan or '', k.proje_makine or '',
                k.miktar or '', k.birim or '',
                k.br_fiyat or '', k.toplam_fiyat or '',
                k.para_birimi or '',
                k.tedarikci.name if k.tedarikci else '',
                k.vade_gun or '', k.termin_gun or '',
                t.durum
            ])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        from flask import make_response
        tarih = datetime.utcnow().strftime('%Y%m%d')
        resp = make_response(buf.read())
        resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        resp.headers['Content-Disposition'] = f'attachment; filename="siparis_raporu_{tarih}.xlsx"'
        return resp

    # Normal sayfa görünümü için pagination
    pagination = query.order_by(TalepFormu.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    kalemler = pagination.items

    # Özet: türe göre
    tur_ozet = {}
    for k in kalemler:
        tur = k.malzeme_turu or 'Belirtilmemiş'
        if tur not in tur_ozet:
            tur_ozet[tur] = {'adet': 0, 'toplam': 0, 'para': ''}
        tur_ozet[tur]['adet'] += 1
        if k.toplam_fiyat:
            tur_ozet[tur]['toplam'] += k.toplam_fiyat
            tur_ozet[tur]['para'] = k.para_birimi or ''

    # Özet: tedarikçiye göre
    ted_ozet = {}
    for k in kalemler:
        if k.tedarikci:
            ad = k.tedarikci.name
            if ad not in ted_ozet:
                ted_ozet[ad] = {'adet': 0, 'toplam': 0, 'para': ''}
            ted_ozet[ad]['adet'] += 1
            if k.toplam_fiyat:
                ted_ozet[ad]['toplam'] += k.toplam_fiyat
                ted_ozet[ad]['para'] = k.para_birimi or ''

    def distinct_vals(col):
        return [v[0] for v in db.session.query(col).filter(col != None, col != '').distinct().order_by(col).all()]

    turler = distinct_vals(TalepKalem.malzeme_turu)
    hedefler = distinct_vals(TalepKalem.hedef)
    amaclar = distinct_vals(TalepKalem.kullanim_amaci)
    alanlar = distinct_vals(TalepKalem.kullanilan_alan)
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()

    return render_template('siparis_raporu.html',
        kalemler=kalemler, pagination=pagination, tur_ozet=tur_ozet, ted_ozet=ted_ozet,
        turler=turler, hedefler=hedefler, amaclar=amaclar, alanlar=alanlar,
        tedarikciler=tedarikciler,
        bas_str=bas_str, bit_str=bit_str,
        tur_filtre=tur_filtre, ted_filtre=ted_filtre, durum_filtre=durum_filtre,
        hedef_filtre=hedef_filtre, amac_filtre=amac_filtre,
        alan_filtre=alan_filtre, proje_filtre=proje_filtre
    )

@satin_alma.route('/raporlar')
@login_required
@role_required('satinalma', 'admin', 'gm')
def raporlar():
    from sqlalchemy import func, extract
    from datetime import date

    # Durum özeti
    durum_rows = db.session.query(TalepFormu.durum, func.count(TalepFormu.id)).group_by(TalepFormu.durum).all()
    durum_map = dict(durum_rows)

    # Son 6 ay — talep sayısı
    bugun = date.today()
    aylar, ay_sayilari = [], []
    for i in range(5, -1, -1):
        ay = bugun.month - i
        yil = bugun.year
        while ay <= 0:
            ay += 12
            yil -= 1
        sayi = TalepFormu.query.filter(
            extract('month', TalepFormu.created_at) == ay,
            extract('year', TalepFormu.created_at) == yil
        ).count()
        aylar.append(f"{ay:02d}/{yil}")
        ay_sayilari.append(sayi)

    # Departmana göre talep sayısı
    dept_rows = db.session.query(Department.name, func.count(TalepFormu.id))\
        .join(TalepFormu, TalepFormu.department_id == Department.id)\
        .group_by(Department.name).order_by(func.count(TalepFormu.id).desc()).all()

    # Malzeme türüne göre
    tur_rows = db.session.query(TalepKalem.malzeme_turu, func.count(TalepKalem.id))\
        .filter(TalepKalem.malzeme_turu != None)\
        .group_by(TalepKalem.malzeme_turu).order_by(func.count(TalepKalem.id).desc()).all()

    # Tedarikçiye göre harcama (TL)
    ted_rows = db.session.query(Tedarikci.name, func.coalesce(func.sum(TalepKalem.toplam_fiyat), 0))\
        .join(TalepKalem, TalepKalem.tedarikci_id == Tedarikci.id)\
        .filter(TalepKalem.para_birimi == 'TL')\
        .group_by(Tedarikci.name).order_by(func.sum(TalepKalem.toplam_fiyat).desc()).limit(10).all()

    toplam_talep = TalepFormu.query.count()
    toplam_kalem = TalepKalem.query.count()
    toplam_tutar = db.session.query(func.coalesce(func.sum(TalepKalem.toplam_fiyat), 0))\
        .filter(TalepKalem.para_birimi == 'TL').scalar() or 0

    return render_template('raporlar.html',
        durum_map=durum_map,
        aylar=aylar, ay_sayilari=ay_sayilari,
        dept_rows=dept_rows, tur_rows=tur_rows, ted_rows=ted_rows,
        toplam_talep=toplam_talep, toplam_kalem=toplam_kalem, toplam_tutar=toplam_tutar
    )

@satin_alma.route('/panel')
@login_required
@role_required('satinalma', 'admin', 'gm')
def panel():
    durum = request.args.get('durum', 'hepsi')
    dept = request.args.get('dept', '')
    arama = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    q = TalepFormu.query.options(
        selectinload(TalepFormu.kalemler),
        selectinload(TalepFormu.talep_eden),
        selectinload(TalepFormu.department),
    )
    if durum != 'hepsi':
        q = q.filter_by(durum=durum)
    if dept:
        q = q.filter_by(department_id=dept)
    if arama:
        from sqlalchemy import or_
        q = q.filter(or_(
            TalepFormu.siparis_no.ilike(f'%{arama}%'),
            TalepFormu.kalemler.any(TalepKalem.malzeme_adi.ilike(f'%{arama}%'))
        ))
    pagination = q.order_by(TalepFormu.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    departmanlar = Department.query.all()
    return render_template('satinalma_panel.html',
        talepler=pagination.items,
        pagination=pagination,
        departmanlar=departmanlar,
        secili_durum=durum,
        arama=arama,
        dept_filtre=dept)

@satin_alma.route('/onayla/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def onayla(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    talep.durum = 'onaylandi'
    db.session.commit()
    flash('Talep onaylandı.', 'success')
    return redirect(url_for('satin_alma.panel'))

@satin_alma.route('/iptal/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def iptal(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    talep.durum = 'iptal'
    db.session.commit()
    flash('Talep iptal edildi.', 'warning')
    return redirect(url_for('satin_alma.panel'))

@admin.route('/kullanicilar')
@login_required
@role_required('admin')
def kullanicilar():
    users = User.query.all()
    departmanlar = Department.query.all()
    return render_template('admin_kullanicilar.html', users=users, departmanlar=departmanlar)

@admin.route('/kullanici/ekle', methods=['POST'])
@login_required
@role_required('admin')
def kullanici_ekle():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    department_id = request.form.get('department_id')
    if User.query.filter_by(email=email).first():
        flash('Bu e-posta zaten kayıtlı.', 'danger')
        return redirect(url_for('admin.kullanicilar'))
    user = User(
        name=name, email=email,
        password=generate_password_hash(password),
        role=role, department_id=department_id
    )
    db.session.add(user)
    db.session.commit()
    flash(f'{name} başarıyla eklendi.', 'success')
    return redirect(url_for('admin.kullanicilar'))

@admin.route('/kullanici/<int:user_id>/duzenle', methods=['POST'])
@login_required
@role_required('admin')
def kullanici_duzenle(user_id):
    user = db.get_or_404(User, user_id)
    user.name = request.form.get('name')
    user.role = request.form.get('role')
    user.department_id = request.form.get('department_id') or None
    user.is_active = request.form.get('is_active') == '1'
    db.session.commit()
    flash(f'{user.name} güncellendi.', 'success')
    return redirect(url_for('admin.kullanicilar'))

@admin.route('/kullanici/<int:user_id>/sil', methods=['POST'])
@login_required
@role_required('admin')
def kullanici_sil(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash('Kendi hesabınızı silemezsiniz.', 'danger')
        return redirect(url_for('admin.kullanicilar'))
    user.is_active = False
    db.session.commit()
    flash(f'{user.name} pasife alındı.', 'warning')
    return redirect(url_for('admin.kullanicilar'))

@admin.route('/tedarikci')
@login_required
@role_required('admin', 'satinalma')
def tedarikci_listesi():
    tedarikciler = Tedarikci.query.all()
    return render_template('tedarikci.html', tedarikciler=tedarikciler)

@admin.route('/tedarikci/sablonu-indir')
@login_required
@role_required('admin', 'satinalma')
def tedarikci_sablon_indir():
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from flask import make_response
    wb = Workbook()
    ws = wb.active
    ws.title = 'Tedarikçiler'
    basliklar = ['Firma Adı*', 'Unvan', 'Vergi No', 'E-posta', 'Telefon', 'İletişim Kişisi', 'Adres', 'Para Birimi (TL/USD/EUR)', 'Vade Gün', 'Kategori']
    for col, baslik in enumerate(basliklar, 1):
        hucre = ws.cell(row=1, column=col, value=baslik)
        hucre.font = Font(bold=True, color='FFFFFF')
        hucre.fill = PatternFill(fill_type='solid', fgColor='2d7a3a')
        hucre.alignment = Alignment(horizontal='center')
        ws.column_dimensions[hucre.column_letter].width = 20
    ornek = ['Örnek A.Ş.', 'Makine Tedarikçisi', '1234567890', 'info@ornek.com', '0212 000 00 00', 'Ahmet Yılmaz', 'İstanbul', 'TL', '30', 'Makine']
    for col, deger in enumerate(ornek, 1):
        ws.cell(row=2, column=col, value=deger)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    resp.headers['Content-Disposition'] = 'attachment; filename=tedarikci_sablonu.xlsx'
    return resp

@admin.route('/tedarikci/excel-yukle', methods=['POST'])
@login_required
@role_required('admin', 'satinalma')
def tedarikci_excel_yukle():
    from openpyxl import load_workbook
    dosya = request.files.get('excel_dosya')
    if not dosya or not dosya.filename.endswith('.xlsx'):
        flash('Geçerli bir .xlsx dosyası seçin.', 'danger')
        return redirect(url_for('admin.tedarikci_listesi'))
    try:
        wb = load_workbook(dosya)
        ws = wb.active
        eklenen, atlanan = 0, 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            name = str(row[0]).strip()
            vergi_no = str(row[2]).strip() if row[2] else None
            if Tedarikci.query.filter_by(name=name).first():
                atlanan += 1
                continue
            t = Tedarikci(
                name=name,
                unvan=str(row[1]).strip() if row[1] else None,
                vergi_no=vergi_no,
                email=str(row[3]).strip() if row[3] else None,
                telefon=str(row[4]).strip() if row[4] else None,
                iletisim_kisi=str(row[5]).strip() if row[5] else None,
                adres=str(row[6]).strip() if row[6] else None,
                para_birimi=str(row[7]).strip() if row[7] else 'TL',
                vade_gun=int(row[8]) if row[8] else 30,
                kategori=str(row[9]).strip() if row[9] else None,
            )
            db.session.add(t)
            eklenen += 1
        db.session.commit()
        flash(f'{eklenen} tedarikçi eklendi. {atlanan} kayıt zaten mevcut olduğu için atlandı.', 'success')
    except Exception as e:
        flash(f'Dosya okunamadı: {e}', 'danger')
    return redirect(url_for('admin.tedarikci_listesi'))

@admin.route('/tedarikci/ekle', methods=['POST'])
@login_required
@role_required('admin', 'satinalma')
def tedarikci_ekle():
    t = Tedarikci(
        name=request.form.get('name'),
        unvan=request.form.get('unvan'),
        vergi_no=request.form.get('vergi_no'),
        email=request.form.get('email'),
        telefon=request.form.get('telefon'),
        adres=request.form.get('adres'),
        iletisim_kisi=request.form.get('iletisim_kisi'),
        para_birimi=request.form.get('para_birimi', 'TL'),
        vade_gun=int(request.form.get('vade_gun', 30)),
        kategori=request.form.get('kategori')
    )
    db.session.add(t)
    db.session.commit()
    flash('Tedarikçi eklendi.', 'success')
    return redirect(url_for('admin.tedarikci_listesi'))

@admin.route('/tedarikci/<int:t_id>/duzenle', methods=['POST'])
@login_required
@role_required('admin', 'satinalma')
def tedarikci_duzenle(t_id):
    t = db.get_or_404(Tedarikci, t_id)
    t.name = request.form.get('name')
    t.unvan = request.form.get('unvan')
    t.vergi_no = request.form.get('vergi_no')
    t.iletisim_kisi = request.form.get('iletisim_kisi')
    t.email = request.form.get('email')
    t.telefon = request.form.get('telefon')
    t.kategori = request.form.get('kategori')
    t.para_birimi = request.form.get('para_birimi', 'TL')
    t.vade_gun = int(request.form.get('vade_gun', 30))
    t.is_active = request.form.get('is_active') == '1'
    db.session.commit()
    flash(f'{t.name} güncellendi.', 'success')
    return redirect(url_for('admin.tedarikci_listesi'))

@admin.route('/tedarikci/<int:t_id>/sil', methods=['POST'])
@login_required
@role_required('admin', 'satinalma')
def tedarikci_sil(t_id):
    t = db.get_or_404(Tedarikci, t_id)
    t.is_active = False
    db.session.commit()
    flash(f'{t.name} pasife alındı.', 'warning')
    return redirect(url_for('admin.tedarikci_listesi'))

from flask import make_response
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.graphics.shapes import Drawing, String, Line
from reportlab.graphics import renderPDF
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, os

_fonts_registered = False
def _register_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    base = os.path.join(os.path.dirname(__file__), 'static')
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', os.path.join(base, 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', os.path.join(base, 'DejaVuSans-Bold.ttf')))
        _fonts_registered = True
    except Exception:
        pass

@main.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    if request.method == 'POST':
        aksiyon = request.form.get('aksiyon')
        if aksiyon == 'profil_guncelle':
            current_user.name = request.form.get('name') or current_user.name
            current_user.unvan = request.form.get('unvan') or None
            current_user.telefon = request.form.get('telefon') or None
            dogum_str = request.form.get('dogum_tarihi')
            if dogum_str:
                try:
                    from datetime import date
                    current_user.dogum_tarihi = date.fromisoformat(dogum_str)
                except ValueError:
                    pass
            current_user.unvan_pdf_goster = request.form.get('unvan_pdf_goster') == '1'
            current_user.bildirim_email = request.form.get('bildirim_email') == '1'
            pin = request.form.get('tablet_pin', '').strip()
            if pin and pin.isdigit() and len(pin) == 4:
                current_user.tablet_pin = pin
            elif pin == '':
                current_user.tablet_pin = None
            db.session.commit()
            flash('Profil güncellendi.', 'success')
        elif aksiyon == 'sifre_degistir':
            mevcut = request.form.get('mevcut_sifre')
            yeni = request.form.get('yeni_sifre')
            tekrar = request.form.get('yeni_sifre_tekrar')
            if not check_password_hash(current_user.password, mevcut):
                flash('Mevcut şifre hatalı.', 'danger')
            elif len(yeni) < 6:
                flash('Yeni şifre en az 6 karakter olmalıdır.', 'danger')
            elif yeni != tekrar:
                flash('Yeni şifreler eşleşmiyor.', 'danger')
            else:
                current_user.password = generate_password_hash(yeni)
                current_user.sifre_degisim_tarihi = datetime.utcnow()
                db.session.commit()
                flash('Şifreniz başarıyla değiştirildi.', 'success')
    from sqlalchemy import func
    toplam = TalepFormu.query.filter_by(talep_eden_id=current_user.id).count()
    durum_sayilari = dict(
        db.session.query(TalepFormu.durum, func.count(TalepFormu.id))
        .filter_by(talep_eden_id=current_user.id)
        .group_by(TalepFormu.durum).all()
    )
    bu_ay_baslangic = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    bu_ay = TalepFormu.query.filter(
        TalepFormu.talep_eden_id == current_user.id,
        TalepFormu.created_at >= bu_ay_baslangic
    ).count()
    return render_template('profil.html', toplam=toplam, durum_sayilari=durum_sayilari, bu_ay=bu_ay)

@admin.route('/kullanici/<int:user_id>/sifre-sifirla', methods=['POST'])
@login_required
@role_required('admin')
def kullanici_sifre_sifirla(user_id):
    user = db.get_or_404(User, user_id)
    yeni = request.form.get('yeni_sifre')
    if not yeni or len(yeni) < 6:
        flash('Şifre en az 6 karakter olmalıdır.', 'danger')
    else:
        user.password = generate_password_hash(yeni)
        user.sifre_degisim_tarihi = datetime.utcnow()
        db.session.commit()
        flash(f'{user.name} şifresi sıfırlandı.', 'success')
    return redirect(url_for('admin.kullanicilar'))

@main.route('/talep/<int:talep_id>/pdf')
@login_required
def talep_pdf(talep_id):
    _register_fonts()
    FONT = 'DejaVu' if _fonts_registered else 'Helvetica'
    FONT_BOLD = 'DejaVu-Bold' if _fonts_registered else 'Helvetica-Bold'

    talep = db.get_or_404(TalepFormu, talep_id)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    elements = []

    header_style = ParagraphStyle('header', fontSize=11, fontName=FONT_BOLD, spaceAfter=4)
    normal_style = ParagraphStyle('normal', fontSize=9, fontName=FONT)
    small_style = ParagraphStyle('small', fontSize=8, fontName=FONT)

    logo_drawing = Drawing(140, 40)
    logo_drawing.add(String(0, 14, 'ERLAU', fontSize=28, fontName='Helvetica-Bold', fillColor=colors.HexColor('#3a8a00')))
    logo_drawing.add(String(2, 4, 'EINE MARKE DER RUD GRUPPE', fontSize=7, fontName='Helvetica-Bold', fillColor=colors.black))

    header_data = [[logo_drawing, Paragraph('SATIN ALMA TALEP FORMU', header_style)]]
    header_table = Table(header_data, colWidths=[6*cm, None])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*cm))
    
    info_data = [
        ['Sipariş No:', talep.siparis_no, 'Tarih:', talep.created_at.strftime('%d.%m.%Y')],
        ['Departman:', talep.department.name if talep.department else '-', 'Talep Eden:', talep.talep_eden.name if talep.talep_eden else '-'],
    ]

    info_table = Table(info_data, colWidths=[3*cm, 7*cm, 3*cm, 7*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (0,-1), FONT_BOLD),
        ('FONTNAME', (2,0), (2,-1), FONT_BOLD),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('BACKGROUND', (2,0), (2,-1), colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.5*cm))

    table_data = [['#', 'Malzeme Adı', 'Marka/Model', 'Tür', 'Birim', 'Miktar', 'Hedef', 'KW', 'Açıklama', 'Son Alım']]
    for i, kalem in enumerate(talep.kalemler):
        son_alim = kalem.son_alinma_tarihi.strftime('%d.%m.%Y') if kalem.son_alinma_tarihi else '-'
        table_data.append([
            str(i+1),
            kalem.malzeme_adi or '',
            kalem.marka_model or '',
            kalem.malzeme_turu or '',
            kalem.birim or '',
            str(kalem.miktar or ''),
            kalem.hedef or '',
            kalem.kw or '',
            kalem.aciklama or '',
            son_alim,
        ])

    col_widths = [0.8*cm, 4.5*cm, 3.5*cm, 2.2*cm, 1.3*cm, 1.3*cm, 1.6*cm, 1.3*cm, 3.5*cm, 2*cm]
    main_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    main_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d7a3a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 1*cm))

    imza_data = [
        ['Talebi Oluşturan', 'Departman Müdürü Onayı', 'Genel Müdür Onayı'],
        ['\n\n\n' + (talep.talep_eden.name if talep.talep_eden else '') + ('\n' + talep.talep_eden.unvan if talep.talep_eden and talep.talep_eden.unvan and talep.talep_eden.unvan_pdf_goster else ''), '\n\n\nAd Soyad', '\n\n\nAd Soyad'],
        ['İmza / Tarih', 'İmza / Tarih', 'İmza / Tarih'],
    ]
    imza_table = Table(imza_data, colWidths=[8*cm, 8*cm, 8*cm])
    imza_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(imza_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=talep_{talep.siparis_no}.pdf'
    return response

@satin_alma.route('/fiyatlandir/<int:talep_id>', methods=['GET', 'POST'])
@login_required
@role_required('satinalma', 'admin')
def fiyatlandir(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()
    if request.method == 'POST':
        for kalem in talep.kalemler:
            prefix = f'kalem_{kalem.id}_'
            br_fiyat = request.form.get(prefix + 'br_fiyat')
            miktar = request.form.get(prefix + 'miktar')
            kalem.tedarikci_id = request.form.get(prefix + 'tedarikci_id') or None
            kalem.br_fiyat = float(br_fiyat) if br_fiyat else None
            if miktar:
                kalem.miktar = float(miktar)
            kalem.toplam_fiyat = round(kalem.br_fiyat * kalem.miktar, 2) if kalem.br_fiyat and kalem.miktar else None
            kalem.para_birimi = request.form.get(prefix + 'para_birimi', 'TL')
            vade = request.form.get(prefix + 'vade_gun')
            termin = request.form.get(prefix + 'termin_gun')
            kalem.vade_gun = int(vade) if vade else None
            kalem.termin_gun = int(termin) if termin else None
        talep.durum = 'fiyatlandirildi'
        db.session.commit()
        flash('Fiyatlandırma kaydedildi.', 'success')
        return redirect(url_for('satin_alma.panel'))
    return render_template('fiyatlandir.html', talep=talep, tedarikciler=tedarikciler)

@satin_alma.route('/kalem/<int:kalem_id>/duzenle', methods=['POST'])
@login_required
def kalem_duzenle(kalem_id):
    kalem = db.get_or_404(TalepKalem, kalem_id)
    talep = kalem.talep
    is_satinalma = current_user.role in ['satinalma', 'admin']
    is_talep_eden = talep.talep_eden_id == current_user.id

    if not is_satinalma and not is_talep_eden:
        flash('Bu işlem için yetkiniz yok.', 'danger')
        return redirect(url_for('main.talep_detay', talep_id=talep.id))

    if is_satinalma:
        br_fiyat_str = request.form.get('br_fiyat', '').strip()
        if br_fiyat_str:
            try:
                kalem.br_fiyat = float(br_fiyat_str)
            except ValueError:
                flash('Geçersiz birim fiyat.', 'danger')
                return redirect(url_for('main.talep_detay', talep_id=talep.id))

    miktar_str = request.form.get('miktar', '').strip()
    if miktar_str:
        try:
            kalem.miktar = float(miktar_str)
        except ValueError:
            flash('Geçersiz miktar.', 'danger')
            return redirect(url_for('main.talep_detay', talep_id=talep.id))

    if kalem.br_fiyat and kalem.miktar:
        kalem.toplam_fiyat = round(kalem.br_fiyat * kalem.miktar, 2)

    db.session.commit()
    flash('Kalem güncellendi.', 'success')
    next_url = request.form.get('next', '')
    return redirect(next_url if next_url else url_for('main.talep_detay', talep_id=talep.id))

@satin_alma.route('/siparis/<int:talep_id>')
@login_required
@role_required('satinalma', 'admin')
def siparis_ozet(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    gruplar = {}
    atamasiz = []
    for kalem in talep.kalemler:
        if kalem.tedarikci:
            tid = kalem.tedarikci_id
            if tid not in gruplar:
                gruplar[tid] = {'tedarikci': kalem.tedarikci, 'kalemler': [], 'toplam': 0}
            gruplar[tid]['kalemler'].append(kalem)
            if kalem.toplam_fiyat:
                gruplar[tid]['toplam'] += kalem.toplam_fiyat
        else:
            atamasiz.append(kalem)
    cc_emails = [u.email for u in User.query.filter(
        User.role == 'satinalma', User.id != current_user.id, User.is_active == True
    ).all()]
    cc = ','.join(cc_emails)
    return render_template('siparis_ozet.html', talep=talep, gruplar=gruplar, atamasiz=atamasiz, cc=cc)

@satin_alma.route('/siparis/<int:talep_id>/excel/<int:tedarikci_id>')
@login_required
@role_required('satinalma', 'admin')
def siparis_excel(talep_id, tedarikci_id):
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    talep = db.get_or_404(TalepFormu, talep_id)
    tedarikci = db.get_or_404(Tedarikci, tedarikci_id)
    kalemler = [k for k in talep.kalemler if k.tedarikci_id == tedarikci_id]

    wb = Workbook()
    ws = wb.active
    ws.title = 'Sipariş'

    yesil = PatternFill(fill_type='solid', fgColor='2d7a3a')
    acik = PatternFill(fill_type='solid', fgColor='f0f7f1')
    kalin = Font(bold=True)
    beyaz_kalin = Font(bold=True, color='FFFFFF')
    ince = Border(
        left=Side(style='thin', color='CCCCCC'), right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'), bottom=Side(style='thin', color='CCCCCC')
    )
    orta = Alignment(horizontal='center', vertical='center')

    # Başlık
    ws.merge_cells('A1:J1')
    ws['A1'] = 'ERLAU — SİPARİŞ FORMU'
    ws['A1'].font = Font(bold=True, size=14, color='2d7a3a')
    ws['A1'].alignment = orta
    ws.row_dimensions[1].height = 28

    # Bilgi satırları
    bilgiler = [
        ('Sipariş No', talep.siparis_no), ('Tarih', datetime.utcnow().strftime('%d.%m.%Y')),
        ('Tedarikçi', tedarikci.name), ('İletişim Kişisi', tedarikci.iletisim_kisi or '-'),
        ('E-posta', tedarikci.email or '-'), ('Telefon', tedarikci.telefon or '-'),
    ]
    for i, (label, val) in enumerate(bilgiler, 2):
        ws.cell(row=i, column=1, value=label).font = kalin
        ws.cell(row=i, column=2, value=val)
    ws.row_dimensions[8].height = 8

    # Tablo başlığı
    basliklar = ['#', 'Malzeme Adı', 'Marka/Model', 'Tür', 'Birim', 'Miktar', 'Br. Fiyat', 'Toplam', 'Para Birimi', 'Termin (gün)']
    for col, b in enumerate(basliklar, 1):
        c = ws.cell(row=9, column=col, value=b)
        c.font = beyaz_kalin
        c.fill = yesil
        c.alignment = orta
        c.border = ince

    genislikler = [4, 30, 20, 15, 8, 8, 12, 12, 12, 12]
    for i, g in enumerate(genislikler, 1):
        ws.column_dimensions[get_column_letter(i)].width = g

    # Kalemler
    toplam_genel = 0
    for idx, k in enumerate(kalemler, 1):
        row = 9 + idx
        fill = acik if idx % 2 == 0 else PatternFill()
        satirlar = [idx, k.malzeme_adi, k.marka_model or '', k.malzeme_turu or '',
                    k.birim or '', k.miktar or '', k.br_fiyat or '', k.toplam_fiyat or '', k.para_birimi or '', k.termin_gun or '']
        for col, val in enumerate(satirlar, 1):
            c = ws.cell(row=row, column=col, value=val)
            c.border = ince
            if fill.fill_type:
                c.fill = fill
        if k.toplam_fiyat:
            toplam_genel += k.toplam_fiyat

    # Toplam satırı
    t_row = 9 + len(kalemler) + 1
    ws.cell(row=t_row, column=7, value='TOPLAM').font = kalin
    ws.cell(row=t_row, column=8, value=toplam_genel).font = kalin
    ws.cell(row=t_row, column=9, value=kalemler[0].para_birimi if kalemler else '').font = kalin

    # Not alanı
    ws.cell(row=t_row+2, column=1, value='Not / Açıklama:').font = kalin
    ws.merge_cells(f'B{t_row+2}:J{t_row+3}')

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    from flask import make_response
    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    tr_map = str.maketrans('çğıöşüÇĞİÖŞÜ', 'cgiosucgiosu')
    guvenli_ad = tedarikci.name.translate(tr_map).replace(' ', '_')
    from urllib.parse import quote
    utf8_ad = quote(f'siparis_{talep.siparis_no}_{tedarikci.name}.xlsx')
    resp.headers['Content-Disposition'] = f"attachment; filename=\"siparis_{talep.siparis_no}_{guvenli_ad}.xlsx\"; filename*=UTF-8''{utf8_ad}"
    return resp

@satin_alma.route('/yolda/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def yolda(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    talep.durum = 'yolda'
    db.session.commit()
    flash('Sipariş yolda olarak işaretlendi.', 'success')
    return redirect(url_for('satin_alma.panel'))

@satin_alma.route('/teslim/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def teslim(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    talep.durum = 'teslim_alindi'
    db.session.commit()
    flash('Sipariş teslim alındı olarak işaretlendi.', 'success')
    return redirect(url_for('satin_alma.panel'))

@satin_alma.route('/durum/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def durum_guncelle(talep_id):
    talep = db.get_or_404(TalepFormu, talep_id)
    yeni_durum = request.form.get('durum')
    gecerli_durumlar = ['bekliyor', 'fiyatlandirildi', 'onaylandi', 'yolda', 'teslim_alindi', 'iptal']
    if yeni_durum in gecerli_durumlar:
        talep.durum = yeni_durum
        if yeni_durum == 'yolda' and not talep.yolda_tarihi:
            talep.yolda_tarihi = datetime.utcnow()
        if yeni_durum == 'teslim_alindi':
            now = datetime.utcnow()
            for kalem in talep.kalemler:
                kalem.son_alinma_tarihi = now
                kalem.son_siparis_no = talep.siparis_no
        db.session.commit()
        flash('Durum güncellendi.', 'success')
    return redirect(url_for('satin_alma.panel'))

@main.route('/api/son-alim')
@login_required
def son_alim_api():
    malzeme_adi = request.args.get('malzeme_adi', '').strip()
    if not malzeme_adi:
        return jsonify(None)
    from sqlalchemy import func
    kalem = (TalepKalem.query
             .filter(func.lower(TalepKalem.malzeme_adi) == func.lower(malzeme_adi))
             .filter(TalepKalem.son_alinma_tarihi.isnot(None))
             .order_by(TalepKalem.son_alinma_tarihi.desc())
             .first())
    if kalem:
        return jsonify({
            'tarih': kalem.son_alinma_tarihi.strftime('%d.%m.%Y'),
            'siparis_no': kalem.son_siparis_no or ''
        })
    return jsonify(None)

@main.route('/api/kullanim-sikligi')
@login_required
def kullanim_sikligi_api():
    from sqlalchemy import func
    malzeme_adi = request.args.get('malzeme_adi', '').strip()
    if not malzeme_adi:
        return jsonify(None)
    toplam = (TalepKalem.query
              .join(TalepFormu)
              .filter(func.lower(TalepKalem.malzeme_adi) == func.lower(malzeme_adi))
              .filter(TalepFormu.durum == 'teslim_alindi')
              .count())
    return jsonify({'toplam': toplam})

# ─── MUHASEBE ────────────────────────────────────────────────────────────────

IZINLI_MUHASEBE = ['muhasebe', 'satinalma', 'admin']

@muhasebe.route('/faturalar')
@login_required
@role_required('muhasebe', 'satinalma', 'admin')
def fatura_listesi():
    durum_filtre = request.args.get('durum', '')
    q = request.args.get('q', '').strip()
    query = Fatura.query
    if durum_filtre:
        query = query.filter_by(durum=durum_filtre)
    if q:
        from sqlalchemy import or_
        query = query.filter(or_(
            Fatura.fatura_no.ilike(f'%{q}%'),
            Fatura.tedarikci_adi_ham.ilike(f'%{q}%'),
        ))
    faturalar = query.order_by(Fatura.yukleme_tarihi.desc()).all()
    ozet = {
        'toplam': len(faturalar),
        'bekliyor': sum(1 for f in faturalar if f.durum == 'bekliyor'),
        'odendi': sum(1 for f in faturalar if f.durum == 'odendi'),
        'iptal_iade': sum(1 for f in faturalar if f.durum in ['iptal', 'iade']),
        'toplam_tutar': sum(f.genel_toplam or 0 for f in faturalar if f.durum not in ['iptal', 'iade']),
    }
    return render_template('fatura_listesi.html', faturalar=faturalar, ozet=ozet,
                           durum_filtre=durum_filtre, q=q, today=date.today())

@muhasebe.route('/fatura/yukle', methods=['GET', 'POST'])
@login_required
@role_required('muhasebe', 'admin')
def fatura_yukle():
    if request.method == 'POST':
        dosya = request.files.get('pdf_dosya')
        if not dosya or not dosya.filename.endswith('.pdf'):
            flash('Geçerli bir PDF dosyası seçin.', 'danger')
            return redirect(request.url)
        import os
        from werkzeug.utils import secure_filename
        dosya_adi = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{secure_filename(dosya.filename)}"
        kayit_dizini = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'faturalar')
        os.makedirs(kayit_dizini, exist_ok=True)
        tam_yol = os.path.join(kayit_dizini, dosya_adi)
        dosya.save(tam_yol)

        try:
            from app.fatura_ai import pdf_oku
            # Tedarikçi hafızası var mı kontrol et
            ted_id = request.form.get('tedarikci_id')
            ornek = None
            if ted_id:
                sablon = TedarikciSablon.query.filter_by(tedarikci_id=int(ted_id)).first()
                if sablon:
                    ornek = sablon.ornek_json
            ai_sonuc = pdf_oku(tam_yol, ornek)
        except Exception as e:
            os.remove(tam_yol)
            flash(f'AI analizi başarısız: {e}', 'danger')
            return redirect(request.url)

        import json
        from app.tcmb import get_kur
        para_birimi = ai_sonuc.get('para_birimi', 'TL')
        genel_toplam = ai_sonuc.get('genel_toplam')
        fatura_turu = request.form.get('fatura_turu', 'normal')
        ana_fatura_id = request.form.get('ana_fatura_id') or None

        # TCMB kuru otomatik çek
        fatura_kuru = None
        tl_karsiligi = None
        if para_birimi != 'TL':
            fatura_kuru = get_kur(para_birimi)
            if fatura_kuru and genel_toplam:
                tl_karsiligi = round(float(genel_toplam) * fatura_kuru, 2)

        fatura = Fatura(
            fatura_no=ai_sonuc.get('fatura_no'),
            tedarikci_adi_ham=ai_sonuc.get('tedarikci_adi'),
            ara_toplam=ai_sonuc.get('ara_toplam'),
            iskonto_tutari=ai_sonuc.get('iskonto_tutari'),
            iskonto_orani=ai_sonuc.get('iskonto_orani'),
            kdv_tutari=ai_sonuc.get('kdv_tutari'),
            genel_toplam=genel_toplam,
            para_birimi=para_birimi,
            dosya_yolu=dosya_adi,
            ai_ham_veri=json.dumps(ai_sonuc, ensure_ascii=False),
            ai_guvenskoru=ai_sonuc.get('guven_skoru', 0.5),
            yukleyen_id=current_user.id,
            durum='bekliyor',
            fatura_turu=fatura_turu,
            ana_fatura_id=int(ana_fatura_id) if ana_fatura_id else None,
            fatura_kuru=fatura_kuru,
            tl_karsiligi=tl_karsiligi,
        )
        if ai_sonuc.get('fatura_tarihi'):
            try:
                from datetime import date
                fatura.fatura_tarihi = date.fromisoformat(ai_sonuc['fatura_tarihi'])
            except: pass
        if ai_sonuc.get('vade_tarihi'):
            try:
                from datetime import date
                fatura.vade_tarihi = date.fromisoformat(ai_sonuc['vade_tarihi'])
            except: pass
        if ted_id:
            fatura.tedarikci_id = int(ted_id)
        db.session.add(fatura)
        db.session.flush()

        for k in ai_sonuc.get('kalemler', []):
            fk = FaturaKalem(
                fatura_id=fatura.id,
                malzeme_adi=k.get('malzeme_adi'),
                miktar=k.get('miktar'),
                birim=k.get('birim'),
                liste_fiyati=k.get('liste_fiyati'),
                iskonto_orani=k.get('iskonto_orani'),
                iskonto_tutari=k.get('iskonto_tutari'),
                br_fiyat=k.get('br_fiyat'),
                kdv_orani=k.get('kdv_orani'),
                toplam_fiyat=k.get('toplam_fiyat'),
            )
            db.session.add(fk)

        db.session.commit()
        flash(f'Fatura yüklendi ve AI analiz etti. Lütfen kontrol edin.', 'success')
        return redirect(url_for('muhasebe.fatura_detay', fatura_id=fatura.id))

    from app.tcmb import kur_listesi
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()
    diger_faturalar = Fatura.query.filter_by(fatura_turu='normal').order_by(Fatura.yukleme_tarihi.desc()).limit(100).all()
    return render_template('fatura_yukle.html', tedarikciler=tedarikciler,
                           guncel_kurlar=kur_listesi(), diger_faturalar=diger_faturalar)

@muhasebe.route('/fatura/<int:fatura_id>')
@login_required
@role_required('muhasebe', 'satinalma', 'admin')
def fatura_detay(fatura_id):
    fatura = db.get_or_404(Fatura, fatura_id)
    talepler = TalepFormu.query.filter(
        TalepFormu.durum.in_(['onaylandi', 'yolda', 'teslim_alindi'])
    ).order_by(TalepFormu.created_at.desc()).limit(50).all()
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()
    talep_kalemleri = fatura.talep.kalemler if fatura.talep else []
    from datetime import date
    return render_template('fatura_detay.html', fatura=fatura, talepler=talepler,
                           tedarikciler=tedarikciler, today=date.today(),
                           talep_kalemleri=talep_kalemleri)

@muhasebe.route('/fatura/<int:fatura_id>/kalem-esles', methods=['POST'])
@login_required
@role_required('muhasebe', 'satinalma', 'admin')
def fatura_kalem_esles_manuel(fatura_id):
    fatura = db.get_or_404(Fatura, fatura_id)
    from app.models import TalepKalem
    from app.fatura_ai import net_birim_fiyat, hafizaya_kaydet

    for fk in fatura.kalemler:
        tk_id_str = request.form.get(f'kalem_{fk.id}_talep_kalem_id', '')
        tk_id = int(tk_id_str) if tk_id_str.isdigit() else None
        fk.talep_kalem_id = tk_id

        if tk_id:
            tk = TalepKalem.query.get(tk_id)
            if tk:
                fatura_net = net_birim_fiyat({
                    'br_fiyat': fk.br_fiyat,
                    'liste_fiyati': fk.liste_fiyati,
                    'iskonto_orani': fk.iskonto_orani,
                    'iskonto_tutari': fk.iskonto_tutari,
                    'miktar': fk.miktar,
                    'toplam_fiyat': fk.toplam_fiyat,
                    'kdv_orani': fk.kdv_orani,
                })
                siparis_net = tk.br_fiyat or 0
                if siparis_net > 0 and fatura_net > 0:
                    fark = abs(fatura_net - siparis_net)
                    yuzde = fark / siparis_net * 100
                    if yuzde > 5:
                        fk.eslesme_durumu = 'fiyat_farki'
                        fk.eslesme_notu = (f"Siparişteki net br. fiyat: {siparis_net:.2f} | "
                                           f"Faturadaki net br. fiyat: {fatura_net:.2f} | Fark: %{yuzde:.1f}")
                    else:
                        fk.eslesme_durumu = 'eslesti'
                        fk.eslesme_notu = 'Manuel eşleştirme'
                else:
                    fk.eslesme_durumu = 'eslesti'
                    fk.eslesme_notu = 'Manuel eşleştirme'
                if fk.malzeme_adi and tk.malzeme_adi:
                    hafizaya_kaydet(fk.malzeme_adi, tk.malzeme_adi)
        else:
            fk.eslesme_durumu = 'eslesmiyor'
            fk.eslesme_notu = ''

    db.session.commit()
    flash('Kalem eşleştirmeleri kaydedildi ve hafızaya öğretildi.', 'success')
    return redirect(url_for('muhasebe.fatura_detay', fatura_id=fatura_id))


@muhasebe.route('/fatura/<int:fatura_id>/guncelle', methods=['POST'])
@login_required
@role_required('muhasebe', 'satinalma', 'admin')
def fatura_guncelle(fatura_id):
    fatura = db.get_or_404(Fatura, fatura_id)
    fatura.fatura_no = request.form.get('fatura_no')
    fatura.tedarikci_adi_ham = request.form.get('tedarikci_adi_ham')
    fatura.ara_toplam = request.form.get('ara_toplam') or None
    fatura.kdv_tutari = request.form.get('kdv_tutari') or None
    fatura.genel_toplam = request.form.get('genel_toplam') or None
    fatura.para_birimi = request.form.get('para_birimi', 'TL')
    fatura.notlar = request.form.get('notlar')
    ted_id = request.form.get('tedarikci_id')
    fatura.tedarikci_id = int(ted_id) if ted_id else None
    tarih_str = request.form.get('fatura_tarihi')
    vade_str = request.form.get('vade_tarihi')
    if tarih_str:
        try:
            from datetime import date
            fatura.fatura_tarihi = date.fromisoformat(tarih_str)
        except: pass
    if vade_str:
        try:
            from datetime import date
            fatura.vade_tarihi = date.fromisoformat(vade_str)
        except: pass

    # Kalemleri güncelle
    for kalem in fatura.kalemler:
        prefix = f'kalem_{kalem.id}_'
        kalem.malzeme_adi = request.form.get(prefix + 'malzeme_adi', kalem.malzeme_adi)
        kalem.miktar = request.form.get(prefix + 'miktar') or kalem.miktar
        kalem.br_fiyat = request.form.get(prefix + 'br_fiyat') or kalem.br_fiyat
        kalem.toplam_fiyat = request.form.get(prefix + 'toplam_fiyat') or kalem.toplam_fiyat

    # Tedarikçi hafızasını güncelle
    if fatura.tedarikci_id:
        import json
        sablon = TedarikciSablon.query.filter_by(tedarikci_id=fatura.tedarikci_id).first()
        if not sablon:
            sablon = TedarikciSablon(tedarikci_id=fatura.tedarikci_id)
            db.session.add(sablon)
        sablon.ornek_json = json.dumps({
            'fatura_no': fatura.fatura_no,
            'fatura_tarihi': str(fatura.fatura_tarihi),
            'tedarikci_adi': fatura.tedarikci_adi_ham,
            'genel_toplam': fatura.genel_toplam,
            'para_birimi': fatura.para_birimi,
            'kalemler': [{'malzeme_adi': k.malzeme_adi, 'miktar': k.miktar,
                          'birim': k.birim, 'br_fiyat': k.br_fiyat} for k in fatura.kalemler]
        }, ensure_ascii=False)
        sablon.guncelleme_tarihi = datetime.utcnow()

    db.session.commit()
    flash('Fatura güncellendi ve tedarikçi hafızası iyileştirildi.', 'success')
    return redirect(url_for('muhasebe.fatura_detay', fatura_id=fatura.id))

@muhasebe.route('/fatura/<int:fatura_id>/durum', methods=['POST'])
@login_required
@role_required('muhasebe', 'satinalma', 'admin')
def fatura_durum(fatura_id):
    fatura = db.get_or_404(Fatura, fatura_id)
    yeni_durum = request.form.get('durum')
    if yeni_durum in ['bekliyor', 'onaylandi', 'odendi', 'iptal', 'iade']:
        fatura.durum = yeni_durum
        if yeni_durum == 'odendi':
            from datetime import date
            fatura.odeme_tarihi = date.today()
            # Ödeme kuru işle (döviz faturalar için)
            odeme_kuru_str = request.form.get('odeme_kuru', '').strip()
            if odeme_kuru_str and fatura.para_birimi != 'TL':
                try:
                    fatura.odeme_kuru = float(odeme_kuru_str.replace(',', '.'))
                    if fatura.genel_toplam:
                        fatura.odenen_tl = round(fatura.genel_toplam * fatura.odeme_kuru, 2)
                except ValueError:
                    pass
            elif fatura.para_birimi == 'TL':
                fatura.odenen_tl = fatura.genel_toplam
        # Onaylanan faturalarda eşleşmeleri hafızaya kaydet
        if yeni_durum in ['onaylandi', 'odendi']:
            from app.fatura_ai import hafizaya_kaydet
            from app.models import TalepKalem
            for kalem in fatura.kalemler:
                if kalem.eslesme_durumu in ['eslesti', 'fiyat_farki'] and kalem.talep_kalem_id and kalem.malzeme_adi:
                    tk = TalepKalem.query.get(kalem.talep_kalem_id)
                    if tk:
                        hafizaya_kaydet(kalem.malzeme_adi, tk.malzeme_adi)
        db.session.commit()
        flash(f'Fatura durumu güncellendi: {yeni_durum}', 'success')
    return redirect(url_for('muhasebe.fatura_detay', fatura_id=fatura.id))

@muhasebe.route('/fatura/<int:fatura_id>/esles', methods=['POST'])
@login_required
@role_required('muhasebe', 'satinalma', 'admin')
def fatura_esles(fatura_id):
    fatura = db.get_or_404(Fatura, fatura_id)
    talep_id = request.form.get('talep_id')
    if talep_id:
        talep = db.get_or_404(TalepFormu, int(talep_id))
        fatura.talep_id = talep.id
        from app.fatura_ai import siparis_eslestir
        eslesme = siparis_eslestir(
            [{
                'malzeme_adi': k.malzeme_adi,
                'miktar': k.miktar,
                'birim': k.birim,
                'liste_fiyati': k.liste_fiyati,
                'iskonto_orani': k.iskonto_orani,
                'iskonto_tutari': k.iskonto_tutari,
                'br_fiyat': k.br_fiyat,
                'kdv_orani': k.kdv_orani,
                'toplam_fiyat': k.toplam_fiyat,
            } for k in fatura.kalemler],
            talep.kalemler
        )
        from app.fatura_ai import hafizaya_kaydet
        for i, kalem in enumerate(fatura.kalemler):
            if i < len(eslesme):
                kalem.talep_kalem_id = eslesme[i]['talep_kalem_id']
                kalem.eslesme_durumu = eslesme[i]['eslesme_durumu']
                kalem.eslesme_notu = eslesme[i]['eslesme_notu']
                # Eşleşen kalemleri hafızaya kaydet
                if eslesme[i]['talep_kalem_id'] and kalem.malzeme_adi:
                    from app.models import TalepKalem
                    tk = TalepKalem.query.get(eslesme[i]['talep_kalem_id'])
                    if tk:
                        hafizaya_kaydet(kalem.malzeme_adi, tk.malzeme_adi)
        db.session.commit()
        eslesen = sum(1 for e in eslesme if e['eslesme_durumu'] in ['eslesti', 'fiyat_farki'])
        toplam = len(eslesme)
        if eslesen == 0:
            flash(f'{talep.siparis_no} ile eşleştirildi — ancak hiçbir kalem uyuşmadı. Doğru siparişi seçtiğinizden emin olun.', 'warning')
        elif eslesen == toplam:
            flash(f'{talep.siparis_no} ile eşleştirildi. Tüm kalemler uyuştu ✓', 'success')
        else:
            flash(f'{talep.siparis_no} ile eşleştirildi. {eslesen}/{toplam} kalem uyuştu.', 'warning')
    return redirect(url_for('muhasebe.fatura_detay', fatura_id=fatura.id))

@muhasebe.route('/fatura/<int:fatura_id>/sil', methods=['POST'])
@login_required
@role_required('muhasebe', 'satinalma', 'admin')
def fatura_sil(fatura_id):
    fatura = db.get_or_404(Fatura, fatura_id)
    import os
    if fatura.dosya_yolu:
        tam_yol = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'faturalar', fatura.dosya_yolu)
        if os.path.exists(tam_yol):
            os.remove(tam_yol)
    db.session.delete(fatura)
    db.session.commit()
    flash('Fatura silindi.', 'warning')
    return redirect(url_for('muhasebe.fatura_listesi'))

@muhasebe.route('/fatura/<int:fatura_id>/pdf')
@login_required
@role_required('muhasebe', 'satinalma', 'admin')
def fatura_pdf_indir(fatura_id):
    fatura = db.get_or_404(Fatura, fatura_id)
    import os
    from flask import send_file
    tam_yol = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'faturalar', fatura.dosya_yolu)
    return send_file(tam_yol, as_attachment=False, mimetype='application/pdf')
