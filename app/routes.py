from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Department, TalepFormu, TalepKalem, Tedarikci
from app.utils import generate_siparis_no
from datetime import datetime
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
    return render_template('dashboard.html', talepler=talepler)

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
    
    header_style = ParagraphStyle('header', fontSize=14, fontName='Helvetica-Bold', spaceAfter=6)
    normal_style = ParagraphStyle('normal', fontSize=9, fontName='Helvetica')
    small_style = ParagraphStyle('small', fontSize=8, fontName='Helvetica')
    
    elements.append(Paragraph('ERLAU - SATIN ALMA TALEP FORMU', header_style))
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
    
    table_data = [['#', 'Malzeme Adi', 'Marka/Model', 'Tur', 'Birim', 'Miktar', 'Hedef', 'KW', 'Aciklama']]
    for i, kalem in enumerate(talep.kalemler):
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
        ])
    
    col_widths = [0.8*cm, 5*cm, 4*cm, 2.5*cm, 1.5*cm, 1.5*cm, 1.8*cm, 1.5*cm, 4*cm]
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
