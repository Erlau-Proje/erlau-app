from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Department, TalepFormu, TalepKalem, Tedarikci
from app.utils import generate_siparis_no
from datetime import datetime, date, timedelta
from functools import wraps

auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)
satin_alma = Blueprint('satin_alma', __name__, url_prefix='/satinalma')
admin = Blueprint('admin', __name__, url_prefix='/admin')

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
    if current_user.role in ['satinalma', 'admin']:
        return redirect(url_for('satin_alma.panel'))
    if current_user.role == 'departman_yoneticisi':
        talepler = TalepFormu.query.filter_by(
            department_id=current_user.department_id
        ).order_by(TalepFormu.created_at.desc()).all()
    else:
        talepler = TalepFormu.query.filter_by(
            talep_eden_id=current_user.id
        ).order_by(TalepFormu.created_at.desc()).limit(10).all()

    bugun = date.today()
    kalan_gunler = {}
    for talep in talepler:
        if talep.durum == 'yolda' and talep.yolda_tarihi:
            termin = max((k.termin_gun or 0) for k in talep.kalemler) if talep.kalemler else 0
            if termin > 0:
                bitis = talep.yolda_tarihi.date() + timedelta(days=termin)
                kalan_gunler[talep.id] = (bitis - bugun).days

    return render_template('dashboard.html', talepler=talepler, kalan_gunler=kalan_gunler)

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
    talep = TalepFormu.query.get_or_404(talep_id)
    return render_template('talep_detay.html', talep=talep)

@satin_alma.route('/panel')
@login_required
@role_required('satinalma', 'admin', 'gm')
def panel():
    durum = request.args.get('durum', 'hepsi')
    dept = request.args.get('dept', '')
    q = TalepFormu.query
    if durum != 'hepsi':
        q = q.filter_by(durum=durum)
    if dept:
        q = q.filter_by(department_id=dept)
    talepler = q.order_by(TalepFormu.created_at.desc()).all()
    departmanlar = Department.query.all()
    return render_template('satinalma_panel.html', talepler=talepler, departmanlar=departmanlar, secili_durum=durum)

@satin_alma.route('/onayla/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def onayla(talep_id):
    talep = TalepFormu.query.get_or_404(talep_id)
    talep.durum = 'onaylandi'
    db.session.commit()
    flash('Talep onaylandı.', 'success')
    return redirect(url_for('satin_alma.panel'))

@satin_alma.route('/iptal/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def iptal(talep_id):
    talep = TalepFormu.query.get_or_404(talep_id)
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
    user = User.query.get_or_404(user_id)
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
    user = User.query.get_or_404(user_id)
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
    t = Tedarikci.query.get_or_404(t_id)
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
    t = Tedarikci.query.get_or_404(t_id)
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
import io

@main.route('/talep/<int:talep_id>/pdf')
@login_required
def talep_pdf(talep_id):
    talep = TalepFormu.query.get_or_404(talep_id)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    elements = []

    header_style = ParagraphStyle('header', fontSize=11, fontName='Helvetica-Bold', spaceAfter=4)
    normal_style = ParagraphStyle('normal', fontSize=9, fontName='Helvetica')
    small_style = ParagraphStyle('small', fontSize=8, fontName='Helvetica')

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
        ['Siparis No:', talep.siparis_no, 'Tarih:', talep.created_at.strftime('%d.%m.%Y')],
        ['Departman:', talep.department.name if talep.department else '-', 'Talep Eden:', talep.talep_eden.name if talep.talep_eden else '-'],
    ]
    
    info_table = Table(info_data, colWidths=[3*cm, 7*cm, 3*cm, 7*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('BACKGROUND', (2,0), (2,-1), colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.5*cm))
    
    table_data = [['#', 'Malzeme Adi', 'Marka/Model', 'Tur', 'Birim', 'Miktar', 'Hedef', 'KW', 'Aciklama', 'Son Alim']]
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
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
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
        ['Talebi Olusturan', 'Departman Muduru Onayi', 'Genel Mudur Onayi'],
        ['\n\n\n' + (talep.talep_eden.name if talep.talep_eden else ''), '\n\n\nAd Soyad', '\n\n\nAd Soyad'],
        ['Imza / Tarih', 'Imza / Tarih', 'Imza / Tarih'],
    ]
    imza_table = Table(imza_data, colWidths=[8*cm, 8*cm, 8*cm])
    imza_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
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
    talep = TalepFormu.query.get_or_404(talep_id)
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()
    if request.method == 'POST':
        for kalem in talep.kalemler:
            prefix = f'kalem_{kalem.id}_'
            br_fiyat = request.form.get(prefix + 'br_fiyat')
            kalem.tedarikci_id = request.form.get(prefix + 'tedarikci_id') or None
            kalem.br_fiyat = float(br_fiyat) if br_fiyat else None
            kalem.toplam_fiyat = kalem.br_fiyat * kalem.miktar if kalem.br_fiyat and kalem.miktar else None
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

@satin_alma.route('/yolda/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def yolda(talep_id):
    talep = TalepFormu.query.get_or_404(talep_id)
    talep.durum = 'yolda'
    db.session.commit()
    flash('Sipariş yolda olarak işaretlendi.', 'success')
    return redirect(url_for('satin_alma.panel'))

@satin_alma.route('/teslim/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def teslim(talep_id):
    talep = TalepFormu.query.get_or_404(talep_id)
    talep.durum = 'teslim_alindi'
    db.session.commit()
    flash('Sipariş teslim alındı olarak işaretlendi.', 'success')
    return redirect(url_for('satin_alma.panel'))

@satin_alma.route('/durum/<int:talep_id>', methods=['POST'])
@login_required
@role_required('satinalma', 'admin')
def durum_guncelle(talep_id):
    talep = TalepFormu.query.get_or_404(talep_id)
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
