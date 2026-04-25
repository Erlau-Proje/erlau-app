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
    talepler = TalepFormu.query.filter_by(
        talep_eden_id=current_user.id
    ).order_by(TalepFormu.created_at.desc()).limit(10).all()
    return render_template('dashboard.html', talepler=talepler)

@main.route('/talep/yeni', methods=['GET', 'POST'])
@login_required
def yeni_talep():
    departmanlar = Department.query.all()
    if request.method == 'POST':
        talep = TalepFormu(
            siparis_no=generate_siparis_no(),
            talep_eden_id=current_user.id,
            department_id=request.form.get('department_id'),
            kullanim_amaci=request.form.get('kullanim_amaci'),
            kullanilan_alan=request.form.get('kullanilan_alan'),
            proje_makine=request.form.get('proje_makine'),
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
                    kw=kwler[i] if i < len(kwler) else '',
                    aciklama=aciklamalar[i] if i < len(aciklamalar) else ''
                )
                db.session.add(kalem)

        db.session.commit()
        flash(f'Talep {talep.siparis_no} başarıyla oluşturuldu!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('yeni_talep.html', departmanlar=departmanlar)

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
