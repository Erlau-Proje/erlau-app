from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import date, timedelta
import os

from app import db
from app.models import (
    KaliteKontrol, DOF, DOFAksiyon, DOFEk, SekizD,
    IsAkisiSurec, IsAkisiAdim, UretimKaydi, UretimPlaniSatir,
    UretimPlani, Urun, IsIstasyonu, Tedarikci, User
)
from app.utils import generate_dof_no, generate_sekizd_no, generate_surec_kodu
from app.permissions import ENDPOINT_PERMISSIONS, has_permission

kalite = Blueprint('kalite', __name__, url_prefix='/kalite')

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'static', 'dof_ekler')


def kalite_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        endpoint_permission = ENDPOINT_PERMISSIONS.get(request.endpoint, 'quality.dashboard')
        if not current_user.is_authenticated or (current_user.role not in ('kalite', 'departman_yoneticisi', 'admin') and not has_permission(current_user, endpoint_permission)):
            flash('Kalite modülüne erişim yetkiniz yok.', 'danger')
            return redirect(url_for('auth.portal'))
        return f(*args, **kwargs)
    return decorated


def _dept_dof_sayilari(departman):
    """Bir departmana açık ve geciken DÖF/aksiyon sayılarını döndürür."""
    bugun = date.today()
    acik = DOF.query.filter(
        DOF.hedef_departman == departman,
        DOF.durum.in_(['acik', 'isleniyor', 'gecikti'])
    ).count()
    geciken_aksiyon = (
        DOFAksiyon.query
        .join(DOF)
        .filter(
            DOF.hedef_departman == departman,
            DOFAksiyon.durum == 'bekliyor',
            DOFAksiyon.planlanan_tarih < bugun
        ).count()
    )
    return acik, geciken_aksiyon


def _can_view_dof(dof):
    if current_user.role in ('admin', 'kalite', 'gm'):
        return True
    dept_adi = current_user.department.name if current_user.department else ''
    if dof.acan_kullanici_id and dof.acan_kullanici_id == current_user.id:
        return True
    if dof.hedef_kullanici_id and dof.hedef_kullanici_id == current_user.id:
        return True
    if dof.hedef_departman and dept_adi and dof.hedef_departman == dept_adi:
        return True
    return False


def _can_manage_dof_actions(dof):
    if current_user.role in ('admin', 'kalite'):
        return True
    dept_adi = current_user.department.name if current_user.department else ''
    if dof.hedef_kullanici_id and dof.hedef_kullanici_id == current_user.id:
        return True
    if dof.hedef_departman and dept_adi and dof.hedef_departman == dept_adi:
        return True
    return False


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@kalite.route('/')
@login_required
def kalite_dashboard():
    bugun = date.today()
    yedi_gun_once = bugun - timedelta(days=6)

    bugun_kayitlar = UretimKaydi.query.filter_by(tarih=bugun).all()
    bugun_kontroller = KaliteKontrol.query.filter_by(tarih=bugun).all()
    bugun_ok = sum(k.ok_adet for k in bugun_kontroller)
    bugun_nok = sum(k.nok_adet for k in bugun_kontroller)
    bugun_kontrol_edilen = bugun_ok + bugun_nok
    bugun_nok_orani = round((bugun_nok / bugun_kontrol_edilen * 100), 1) if bugun_kontrol_edilen else 0

    trend_7gun = []
    for i in range(7):
        gun = yedi_gun_once + timedelta(days=i)
        kayitlar = KaliteKontrol.query.filter_by(tarih=gun).all()
        trend_7gun.append({
            'tarih': gun.strftime('%d.%m'),
            'ok_adet': sum(k.ok_adet for k in kayitlar),
            'nok_adet': sum(k.nok_adet for k in kayitlar),
        })

    istasyonlar = IsIstasyonu.query.filter_by(is_active=True).all()
    istasyon_kalite = []
    for ist in istasyonlar:
        kayitlar = KaliteKontrol.query.filter(
            KaliteKontrol.istasyon_id == ist.id,
            KaliteKontrol.tarih >= yedi_gun_once,
            KaliteKontrol.tarih <= bugun
        ).all()
        ok = sum(k.ok_adet for k in kayitlar)
        nok = sum(k.nok_adet for k in kayitlar)
        toplam = ok + nok
        istasyon_kalite.append({
            'istasyon_adi': ist.istasyon_adi,
            'ok': ok, 'nok': nok,
            'oran': round(ok / toplam * 100, 1) if toplam else 100,
        })

    nok_nedenler = {
        'hammadde_hatasi': {'label': 'Hammadde Hatası', 'adet': 0, 'hurda': 0, 'tamir': 0},
        'isleme_hatasi': {'label': 'İşleme Hatası', 'adet': 0, 'hurda': 0, 'tamir': 0},
        'olcu_hatasi': {'label': 'Ölçü Hatası', 'adet': 0, 'hurda': 0, 'tamir': 0},
        'diger': {'label': 'Diğer', 'adet': 0, 'hurda': 0, 'tamir': 0},
    }
    hafta_nok = KaliteKontrol.query.filter(
        KaliteKontrol.tarih >= bugun - timedelta(days=6),
        KaliteKontrol.nok_adet > 0
    ).all()
    toplam_nok = sum(k.nok_adet for k in hafta_nok) or 1
    for k in hafta_nok:
        neden = k.nok_neden or 'diger'
        if neden not in nok_nedenler:
            neden = 'diger'
        nok_nedenler[neden]['adet'] += k.nok_adet
        if k.nok_akibet == 'hurda':
            nok_nedenler[neden]['hurda'] += k.nok_adet
        elif k.nok_akibet == 'tamir':
            nok_nedenler[neden]['tamir'] += k.nok_adet
    nok_neden_dagilim = []
    for key, val in nok_nedenler.items():
        if val['adet'] > 0:
            val['oran'] = round(val['adet'] / toplam_nok * 100, 1)
            nok_neden_dagilim.append(val)

    tamir_kuyrugu = UretimPlaniSatir.query.join(UretimPlani).filter(
        UretimPlaniSatir.kaynak == 'tamir',
        UretimPlani.durum == 'aktif'
    ).all()

    acik_dof = DOF.query.filter(DOF.durum.in_(['acik', 'isleniyor', 'gecikti'])).count()

    return render_template('kalite/dashboard.html',
        bugun=bugun,
        bugun_ok=bugun_ok, bugun_nok=bugun_nok,
        bugun_kontrol_edilen=bugun_kontrol_edilen,
        bugun_nok_orani=bugun_nok_orani,
        trend_7gun=trend_7gun,
        istasyon_kalite=istasyon_kalite,
        nok_neden_dagilim=nok_neden_dagilim,
        tamir_kuyrugu=tamir_kuyrugu,
        acik_dof_sayisi=acik_dof,
    )


# ─── KALİTE KONTROL GİRİŞ ───────────────────────────────────────────────────

@kalite.route('/kontrol', methods=['GET', 'POST'])
@login_required
@kalite_required
def kontrol_giris():
    bugun = date.today()
    if request.method == 'POST':
        kayitlar = UretimKaydi.query.filter_by(
            tarih=date.fromisoformat(request.form.get('tarih', str(bugun)))
        ).all()
        for kayit in kayitlar:
            ok = int(request.form.get(f'ok_{kayit.id}', 0) or 0)
            nok = int(request.form.get(f'nok_{kayit.id}', 0) or 0)
            if ok == 0 and nok == 0:
                continue
            nok_neden = request.form.get(f'nok_neden_{kayit.id}') or None
            nok_aciklama = request.form.get(f'nok_aciklama_{kayit.id}') or None
            nok_akibet = request.form.get(f'nok_akibet_{kayit.id}') or None

            tamir_satir_id = None
            if nok > 0 and nok_akibet == 'tamir' and kayit.urun_id and kayit.istasyon_id:
                aktif_plan = UretimPlani.query.filter_by(durum='aktif').order_by(UretimPlani.id.desc()).first()
                if aktif_plan:
                    from app.utils import devir_gunu
                    tamir_satir = UretimPlaniSatir(
                        plan_id=aktif_plan.id,
                        urun_id=kayit.urun_id,
                        istasyon_id=kayit.istasyon_id,
                        tarih=devir_gunu(bugun),
                        planlanan_adet=nok,
                        kaynak='tamir',
                    )
                    db.session.add(tamir_satir)
                    db.session.flush()
                    tamir_satir_id = tamir_satir.id

            kk = KaliteKontrol(
                tarih=date.fromisoformat(request.form.get('tarih', str(bugun))),
                uretim_kaydi_id=kayit.id,
                urun_id=kayit.urun_id,
                istasyon_id=kayit.istasyon_id,
                kontrol_eden_id=current_user.id,
                ok_adet=ok, nok_adet=nok,
                nok_neden=nok_neden,
                nok_neden_aciklama=nok_aciklama,
                nok_akibet=nok_akibet if nok > 0 else None,
                tamir_plan_satir_id=tamir_satir_id,
            )
            db.session.add(kk)
        db.session.commit()
        flash('Kalite kontrol kayıtları kaydedildi.', 'success')
        return redirect(url_for('kalite.kalite_dashboard'))

    tarih_str = request.args.get('tarih', str(bugun))
    try:
        tarih = date.fromisoformat(tarih_str)
    except ValueError:
        tarih = bugun
    bugun_kayitlar = UretimKaydi.query.filter_by(tarih=tarih).all()
    mevcut_kontroller = {k.uretim_kaydi_id: k for k in KaliteKontrol.query.filter_by(tarih=tarih).all()}
    return render_template('kalite/kontrol_giris.html',
        bugun_kayitlar=bugun_kayitlar, tarih=tarih,
        mevcut_kontroller=mevcut_kontroller)


@kalite.route('/gecmis')
@login_required
def kontrol_gecmis():
    baslangic = request.args.get('bas', str(date.today() - timedelta(days=6)))
    bitis = request.args.get('bit', str(date.today()))
    istasyon_id = request.args.get('istasyon_id', '')
    try:
        bas = date.fromisoformat(baslangic)
        bit = date.fromisoformat(bitis)
    except ValueError:
        bas = date.today() - timedelta(days=6)
        bit = date.today()
    q = KaliteKontrol.query.filter(KaliteKontrol.tarih >= bas, KaliteKontrol.tarih <= bit)
    if istasyon_id:
        q = q.filter(KaliteKontrol.istasyon_id == istasyon_id)
    kontroller = q.order_by(KaliteKontrol.tarih.desc()).all()
    istasyonlar = IsIstasyonu.query.filter_by(is_active=True).all()
    return render_template('kalite/kontrol_gecmis.html',
        kontroller=kontroller, istasyonlar=istasyonlar,
        baslangic=baslangic, bitis=bitis, istasyon_id=istasyon_id)


# ─── DÖF ─────────────────────────────────────────────────────────────────────

@kalite.route('/dof')
@login_required
def dof_listesi():
    durum = request.args.get('durum', '')
    dept = request.args.get('dept', '')
    tip = request.args.get('tip', '')
    bas = request.args.get('bas', '')
    bit = request.args.get('bit', '')
    q = DOF.query
    if durum:
        q = q.filter_by(durum=durum)
    if dept:
        q = q.filter_by(hedef_departman=dept)
    if tip:
        q = q.filter_by(tip=tip)
    if bas:
        try:
            q = q.filter(DOF.tarih >= date.fromisoformat(bas))
        except ValueError:
            bas = ''
    if bit:
        try:
            q = q.filter(DOF.tarih <= date.fromisoformat(bit))
        except ValueError:
            bit = ''
    doflar = q.order_by(DOF.id.desc()).all()
    departmanlar = db.session.query(DOF.hedef_departman).distinct().all()
    departmanlar = [d[0] for d in departmanlar]
    return render_template('kalite/dof_listesi.html',
        doflar=doflar, departmanlar=departmanlar,
        secili_durum=durum, secili_dept=dept, secili_tip=tip,
        secili_bas=bas, secili_bit=bit)


@kalite.route('/dof/benim')
@login_required
def dof_benim():
    bugun = date.today()
    dept_adi = current_user.department.name if current_user.department else ''
    q = DOF.query
    if current_user.role not in ('admin', 'kalite', 'gm'):
        q = q.filter(
            (DOF.hedef_departman == dept_adi) |
            (DOF.hedef_kullanici_id == current_user.id) |
            (DOF.acan_kullanici_id == current_user.id)
        )
    doflar = q.order_by(DOF.id.desc()).all()
    acik_dof, geciken = _dept_dof_sayilari(dept_adi)
    return render_template('kalite/dof_listesi.html',
        doflar=doflar, departmanlar=[], secili_durum='', secili_dept=dept_adi, secili_tip='',
        acik_dof_sayisi=acik_dof, geciken_aksiyon_sayisi=geciken, sadece_benim=True)


@kalite.route('/dof/yeni', methods=['GET', 'POST'])
@login_required
@kalite_required
def dof_yeni():
    if request.method == 'POST':
        tip = request.form.get('tip', 'ic')
        dof = DOF(
            dof_no=generate_dof_no(),
            tarih=date.today(),
            hedef_departman=request.form.get('hedef_departman', ''),
            hedef_kullanici_id=request.form.get('hedef_kullanici_id') or None,
            acan_kullanici_id=current_user.id,
            problem_tanimi=request.form.get('problem_tanimi', ''),
            kok_neden=request.form.get('kok_neden') or None,
            planlanan_kapatma_tarihi=date.fromisoformat(request.form['planlanan_kapatma_tarihi']) if request.form.get('planlanan_kapatma_tarihi') else None,
            tip=tip,
            tedarikci_id=request.form.get('tedarikci_id') or None,
        )
        db.session.add(dof)
        db.session.flush()

        tanimlar = request.form.getlist('aksiyon_tanimi[]')
        sorumlular = request.form.getlist('sorumlu_id[]')
        tarihler = request.form.getlist('planlanan_tarih[]')
        for tanim, sor, tar in zip(tanimlar, sorumlular, tarihler):
            if tanim.strip() and tar:
                a = DOFAksiyon(
                    dof_id=dof.id,
                    aksiyon_tanimi=tanim.strip(),
                    sorumlu_id=sor or None,
                    planlanan_tarih=date.fromisoformat(tar),
                )
                db.session.add(a)
        db.session.commit()
        flash(f'DÖF {dof.dof_no} oluşturuldu.', 'success')
        return redirect(url_for('kalite.dof_detay', id=dof.id))

    kullanicilar = User.query.filter_by(is_active=True).order_by(User.name).all()
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()
    departmanlar = [
        'Satınalma', 'Üretim', 'Bakım', 'Planlama ve Tedarik Zinciri',
        'Muhasebe', 'Kalite', 'İnsan Kaynakları', 'Genel Müdür'
    ]
    return render_template('kalite/dof_yeni.html',
        kullanicilar=kullanicilar, tedarikciler=tedarikciler, departmanlar=departmanlar)


@kalite.route('/dof/<int:id>')
@login_required
def dof_detay(id):
    dof = DOF.query.get_or_404(id)
    if not _can_view_dof(dof):
        flash('Bu DÖF kaydını görüntüleme yetkiniz yok.', 'danger')
        return redirect(url_for('main.dashboard'))
    kullanicilar = User.query.filter_by(is_active=True).order_by(User.name).all()
    can_manage_actions = _can_manage_dof_actions(dof)
    can_close = current_user.role in ('admin', 'kalite')
    can_upload = can_manage_actions
    return render_template('kalite/dof_detay.html',
        dof=dof, kullanicilar=kullanicilar, today=date.today(),
        can_manage_actions=can_manage_actions, can_close=can_close, can_upload=can_upload)


@kalite.route('/dof/<int:id>/aksiyon-ekle', methods=['POST'])
@login_required
def dof_aksiyon_ekle(id):
    dof = DOF.query.get_or_404(id)
    if not _can_manage_dof_actions(dof):
        flash('Bu DÖF için aksiyon ekleme yetkiniz yok.', 'danger')
        return redirect(url_for('kalite.dof_detay', id=id))
    a = DOFAksiyon(
        dof_id=dof.id,
        aksiyon_tanimi=request.form.get('aksiyon_tanimi', ''),
        sorumlu_id=request.form.get('sorumlu_id') or None,
        planlanan_tarih=date.fromisoformat(request.form['planlanan_tarih']),
    )
    db.session.add(a)
    if dof.durum == 'acik':
        dof.durum = 'isleniyor'
    db.session.commit()
    flash('Aksiyon eklendi.', 'success')
    return redirect(url_for('kalite.dof_detay', id=id))


@kalite.route('/dof/aksiyon/<int:aksiyon_id>/tamamla', methods=['POST'])
@login_required
def aksiyon_tamamla(aksiyon_id):
    a = DOFAksiyon.query.get_or_404(aksiyon_id)
    dof = DOF.query.get_or_404(a.dof_id)
    if current_user.role not in ('admin', 'kalite') and current_user.id != a.sorumlu_id and not _can_manage_dof_actions(dof):
        flash('Bu aksiyonu tamamlama yetkiniz yok.', 'danger')
        return redirect(url_for('kalite.dof_detay', id=a.dof_id))
    tarih_str = request.form.get('tamamlama_tarihi', str(date.today()))
    a.tamamlama_tarihi = date.fromisoformat(tarih_str)
    a.durum = 'tamamlandi'
    db.session.commit()
    flash('Aksiyon tamamlandı olarak işaretlendi.', 'success')
    return redirect(url_for('kalite.dof_detay', id=a.dof_id))


@kalite.route('/dof/<int:id>/kapat', methods=['POST'])
@login_required
@kalite_required
def dof_kapat(id):
    dof = DOF.query.get_or_404(id)
    if current_user.role not in ('admin', 'kalite'):
        flash('DÖF kapatma yetkiniz yok.', 'danger')
        return redirect(url_for('kalite.dof_detay', id=id))
    dof.durum = 'kapali'
    dof.kapatma_notu = request.form.get('kapatma_notu', '')
    tarih_str = request.form.get('gercek_kapatma_tarihi', str(date.today()))
    dof.gercek_kapatma_tarihi = date.fromisoformat(tarih_str)
    dof.kapatan_kullanici_id = current_user.id
    db.session.commit()
    flash(f'DÖF {dof.dof_no} kapatıldı.', 'success')
    return redirect(url_for('kalite.dof_detay', id=id))


@kalite.route('/dof/<int:id>/ek-yukle', methods=['POST'])
@login_required
def dof_ek_yukle(id):
    dof = DOF.query.get_or_404(id)
    if not _can_manage_dof_actions(dof):
        flash('Bu DÖF için ek dosya yükleme yetkiniz yok.', 'danger')
        return redirect(url_for('kalite.dof_detay', id=id))
    dosya = request.files.get('dosya')
    if not dosya or not dosya.filename:
        flash('Dosya seçilmedi.', 'danger')
        return redirect(url_for('kalite.dof_detay', id=id))
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    import uuid
    ext = os.path.splitext(dosya.filename)[1].lower()
    yeni_ad = f"{dof.dof_no}_{uuid.uuid4().hex[:8]}{ext}"
    yol = os.path.join(UPLOAD_DIR, yeni_ad)
    dosya.save(yol)
    tur = 'resim' if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp') else ('pdf' if ext == '.pdf' else 'diger')
    ek = DOFEk(
        dof_id=dof.id,
        dosya_adi=dosya.filename,
        dosya_yolu=f'dof_ekler/{yeni_ad}',
        dosya_turu=tur,
        yukleyen_id=current_user.id,
    )
    db.session.add(ek)
    db.session.commit()
    flash('Dosya yüklendi.', 'success')
    return redirect(url_for('kalite.dof_detay', id=id))


# ─── DÖF API (bildirim) ──────────────────────────────────────────────────────

@kalite.route('/api/dof-uyarilar')
@login_required
def api_dof_uyarilar():
    bugun = date.today()
    uc_gun_sonra = bugun + timedelta(days=3)
    dept_adi = current_user.department.name if current_user.department else ''

    geciken_dof = DOF.query.filter(
        DOF.hedef_departman == dept_adi,
        DOF.planlanan_kapatma_tarihi < bugun,
        DOF.durum.in_(['acik', 'isleniyor'])
    ).all()

    yaklasan_aksiyonlar = (
        DOFAksiyon.query.join(DOF)
        .filter(
            DOF.hedef_departman == dept_adi,
            DOFAksiyon.durum == 'bekliyor',
            DOFAksiyon.planlanan_tarih <= uc_gun_sonra,
            DOFAksiyon.planlanan_tarih >= bugun,
        ).all()
    )

    geciken_aksiyonlar = (
        DOFAksiyon.query.join(DOF)
        .filter(
            DOF.hedef_departman == dept_adi,
            DOFAksiyon.durum == 'bekliyor',
            DOFAksiyon.planlanan_tarih < bugun,
        ).all()
    )

    return jsonify({
        'geciken_dof': [{'dof_no': d.dof_no, 'id': d.id} for d in geciken_dof],
        'yaklasan_aksiyon': [{'id': a.id, 'tanim': a.aksiyon_tanimi[:60], 'tarih': str(a.planlanan_tarih)} for a in yaklasan_aksiyonlar],
        'geciken_aksiyon': [{'id': a.id, 'tanim': a.aksiyon_tanimi[:60], 'tarih': str(a.planlanan_tarih)} for a in geciken_aksiyonlar],
        'toplam': len(geciken_dof) + len(geciken_aksiyonlar),
    })


# ─── DÖF PERFORMANS ──────────────────────────────────────────────────────────

@kalite.route('/performans')
@login_required
def dof_performans():
    gun = int(request.args.get('gun', 30))
    bas = date.today() - timedelta(days=gun)
    tum_doflar = DOF.query.filter(DOF.tarih >= bas).all()

    dept_map = {}
    for d in tum_doflar:
        dept = d.hedef_departman or 'Belirtilmemiş'
        row = dept_map.setdefault(dept, {'departman': dept, 'acik': 0, 'geciken': 0, 'kapali': 0, 'kapali_sure': []})
        if d.durum == 'kapali':
            row['kapali'] += 1
            if d.gercek_kapatma_tarihi and d.tarih:
                row['kapali_sure'].append((d.gercek_kapatma_tarihi - d.tarih).days)
        elif d.durum in ('acik', 'isleniyor'):
            row['acik'] += 1
        elif d.durum == 'gecikti':
            row['geciken'] += 1

    dept_performans = []
    for dept, row in dept_map.items():
        toplam = row['acik'] + row['geciken'] + row['kapali']
        ort = round(sum(row['kapali_sure']) / len(row['kapali_sure']), 1) if row['kapali_sure'] else 0
        perf = round(row['kapali'] / toplam * 100) if toplam else 0
        dept_performans.append({
            'departman': dept,
            'acik': row['acik'], 'geciken': row['geciken'], 'kapali': row['kapali'],
            'ort_kapat_gun': ort, 'performans_yuzdesi': perf,
        })

    return render_template('kalite/dof_performans.html',
        dept_performans=dept_performans,
        filtre_gun=gun,
        toplam_acik=sum(r['acik'] for r in dept_performans),
        toplam_geciken=sum(r['geciken'] for r in dept_performans),
        toplam_kapali=sum(r['kapali'] for r in dept_performans),
    )


# ─── 8D ──────────────────────────────────────────────────────────────────────

@kalite.route('/8d')
@login_required
def sekizd_listesi():
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()
    durum = request.args.get('durum', '')
    tdr = request.args.get('tedarikci_id', '')
    q = SekizD.query
    if durum:
        q = q.filter_by(durum=durum)
    if tdr:
        q = q.filter_by(tedarikci_id=int(tdr))
    sekizd_listesi = q.order_by(SekizD.id.desc()).all()
    return render_template('kalite/sekizd_listesi.html',
        sekizd_listesi=sekizd_listesi, tedarikciler=tedarikciler,
        secili_durum=durum, secili_tdr=tdr)


@kalite.route('/8d/yeni', methods=['GET', 'POST'])
@login_required
@kalite_required
def sekizd_yeni():
    if request.method == 'POST':
        s = SekizD(
            sekizd_no=generate_sekizd_no(),
            tarih=date.today(),
            tedarikci_id=request.form.get('tedarikci_id'),
            urun_kodu=request.form.get('urun_kodu') or None,
            urun_adi=request.form.get('urun_adi') or None,
            revizyon_no=request.form.get('revizyon_no', '1'),
            durum='taslak' if request.form.get('eylem') == 'taslak' else 'gonderildi',
            d1_ekip_lideri=request.form.get('d1_ekip_lideri') or None,
            d1_ekip_uyeleri=request.form.get('d1_ekip_uyeleri') or None,
            d2_problem_ozeti=request.form.get('d2_problem_ozeti') or None,
            d2_kim=request.form.get('d2_kim') or None,
            d2_ne=request.form.get('d2_ne') or None,
            d2_nerede=request.form.get('d2_nerede') or None,
            d2_ne_zaman=request.form.get('d2_ne_zaman') or None,
            d2_neden=request.form.get('d2_neden') or None,
            d2_nasil=request.form.get('d2_nasil') or None,
            d2_ne_kadar=request.form.get('d2_ne_kadar') or None,
            d2_ilk_tespit=request.form.get('d2_ilk_tespit') or None,
            d3_onlem=request.form.get('d3_onlem') or None,
            d3_sorumlu=request.form.get('d3_sorumlu') or None,
            d3_tarih=date.fromisoformat(request.form['d3_tarih']) if request.form.get('d3_tarih') else None,
            d3_etkinlik=request.form.get('d3_etkinlik') or None,
            d4_kok_neden=request.form.get('d4_kok_neden') or None,
            d4_analiz_metod=request.form.get('d4_analiz_metod') or None,
            d5_aksiyon=request.form.get('d5_aksiyon') or None,
            d6_uygulama=request.form.get('d6_uygulama') or None,
            d6_tarih=date.fromisoformat(request.form['d6_tarih']) if request.form.get('d6_tarih') else None,
            d6_dogrulama=request.form.get('d6_dogrulama') or None,
            d7_onleyici=request.form.get('d7_onleyici') or None,
            d8_tadir=request.form.get('d8_tadir') or None,
            acan_kullanici_id=current_user.id,
        )
        db.session.add(s)
        db.session.commit()
        flash(f'8D {s.sekizd_no} oluşturuldu.', 'success')
        return redirect(url_for('kalite.sekizd_detay', id=s.id))
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()
    return render_template('kalite/sekizd_form.html',
        sekizd=None, tedarikciler=tedarikciler,
        form_action=url_for('kalite.sekizd_yeni'), baslik='Yeni 8D Raporu')


@kalite.route('/8d/<int:id>')
@login_required
def sekizd_detay(id):
    s = SekizD.query.get_or_404(id)
    return render_template('kalite/sekizd_detay.html', sekizd=s, tedarikci=s.tedarikci)


@kalite.route('/8d/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@kalite_required
def sekizd_duzenle(id):
    s = SekizD.query.get_or_404(id)
    if request.method == 'POST':
        for alan in ['d1_ekip_lideri','d1_ekip_uyeleri','d2_problem_ozeti','d2_kim','d2_ne',
                     'd2_nerede','d2_ne_zaman','d2_neden','d2_nasil','d2_ne_kadar','d2_ilk_tespit',
                     'd3_onlem','d3_sorumlu','d3_etkinlik','d4_kok_neden','d4_analiz_metod',
                     'd5_aksiyon','d6_uygulama','d6_dogrulama','d7_onleyici','d8_tadir',
                     'urun_kodu','urun_adi','revizyon_no']:
            setattr(s, alan, request.form.get(alan) or None)
        if request.form.get('tedarikci_id'):
            s.tedarikci_id = request.form.get('tedarikci_id')
        for tarih_alan in ['d3_tarih', 'd6_tarih']:
            val = request.form.get(tarih_alan)
            setattr(s, tarih_alan, date.fromisoformat(val) if val else None)
        if request.form.get('eylem') == 'kapali':
            s.durum = 'kapali'
        elif request.form.get('eylem') == 'gonderildi':
            s.durum = 'gonderildi'
        db.session.commit()
        flash('8D güncellendi.', 'success')
        return redirect(url_for('kalite.sekizd_detay', id=id))
    tedarikciler = Tedarikci.query.filter_by(is_active=True).order_by(Tedarikci.name).all()
    return render_template('kalite/sekizd_form.html',
        sekizd=s, tedarikciler=tedarikciler,
        form_action=url_for('kalite.sekizd_duzenle', id=id), baslik='8D Düzenle')


@kalite.route('/8d/<int:id>/pdf')
@login_required
def sekizd_pdf(id):
    s = SekizD.query.get_or_404(id)
    from app.sekizd_pdf import build_sekizd_pdf
    pdf_bytes = build_sekizd_pdf(s)
    import io
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=False,
                     download_name=f'{s.sekizd_no}.pdf')


@kalite.route('/8d/<int:id>/excel')
@login_required
def sekizd_excel(id):
    s = SekizD.query.get_or_404(id)
    from app.sekizd_excel import build_sekizd_excel
    excel_bytes = build_sekizd_excel(s)
    import io
    return send_file(io.BytesIO(excel_bytes),
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name=f'{s.sekizd_no}.xlsx')


@kalite.route('/8d/<int:id>/eml')
@login_required
def sekizd_eml(id):
    s = SekizD.query.get_or_404(id)
    from app.sekizd_pdf import build_sekizd_pdf
    import base64, email.utils
    pdf_bytes = build_sekizd_pdf(s)
    pdf_b64 = base64.b64encode(pdf_bytes).decode()
    dosya_adi = f'{s.sekizd_no}.pdf'
    konu = f'8D Raporu — {s.sekizd_no} — {s.tedarikci.name if s.tedarikci else ""}'
    alici = s.tedarikci.email if s.tedarikci and s.tedarikci.email else ''
    eml = (
        f"To: {alici}\r\n"
        f"Subject: {konu}\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: multipart/mixed; boundary=\"ERLAU_BOUND\"\r\n\r\n"
        f"--ERLAU_BOUND\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
        f"Sayın ilgili,\n\n8D raporumuz ekte sunulmuştur.\n\nERLAU Kalite Departmanı\r\n\r\n"
        f"--ERLAU_BOUND\r\n"
        f"Content-Type: application/pdf; name=\"{dosya_adi}\"\r\n"
        f"Content-Transfer-Encoding: base64\r\n"
        f"Content-Disposition: attachment; filename=\"{dosya_adi}\"\r\n\r\n"
        f"{pdf_b64}\r\n--ERLAU_BOUND--"
    )
    import io
    return send_file(io.BytesIO(eml.encode('utf-8')), mimetype='message/rfc822',
                     as_attachment=True, download_name=f'{s.sekizd_no}.eml')


# ─── İŞ AKIŞI ────────────────────────────────────────────────────────────────

@kalite.route('/surecler')
@login_required
def surec_listesi():
    durum = request.args.get('durum', '')
    dept = request.args.get('dept', '')
    q = IsAkisiSurec.query
    if durum:
        q = q.filter_by(durum=durum)
    if dept:
        q = q.filter_by(departman=dept)
    surecler = q.order_by(IsAkisiSurec.id.desc()).all()
    departmanlar = db.session.query(IsAkisiSurec.departman).distinct().all()
    departmanlar = [d[0] for d in departmanlar]
    return render_template('kalite/surec_listesi.html',
        surecler=surecler, departmanlar=departmanlar, secili_durum=durum, secili_dept=dept)


@kalite.route('/surecler/yeni', methods=['GET', 'POST'])
@login_required
@kalite_required
def surec_yeni():
    if request.method == 'POST':
        s = IsAkisiSurec(
            surec_kodu=generate_surec_kodu(),
            surec_adi=request.form.get('surec_adi', ''),
            departman=request.form.get('departman', ''),
            aciklama=request.form.get('aciklama') or None,
            versiyon=request.form.get('versiyon', '1.0'),
            olusturan_id=current_user.id,
        )
        db.session.add(s)
        db.session.commit()
        flash(f'Süreç {s.surec_kodu} oluşturuldu.', 'success')
        return redirect(url_for('kalite.surec_duzenle', id=s.id))
    departmanlar = ['Satınalma', 'Üretim', 'Bakım', 'Planlama ve Tedarik Zinciri',
                    'Muhasebe', 'Kalite', 'İnsan Kaynakları', 'Genel Müdür']
    return render_template('kalite/surec_yeni.html', departmanlar=departmanlar)


@kalite.route('/surecler/<int:id>')
@login_required
def surec_goruntur(id):
    surec = IsAkisiSurec.query.get_or_404(id)
    return render_template('kalite/surec_goruntur.html', surec=surec)


@kalite.route('/surecler/<int:id>/duzenle', methods=['GET', 'POST'])
@login_required
@kalite_required
def surec_duzenle(id):
    surec = IsAkisiSurec.query.get_or_404(id)
    if request.method == 'POST':
        eylem = request.form.get('eylem', 'meta')
        if eylem == 'meta':
            surec.surec_adi = request.form.get('surec_adi', surec.surec_adi)
            surec.departman = request.form.get('departman', surec.departman)
            surec.aciklama = request.form.get('aciklama') or None
            surec.versiyon = request.form.get('versiyon', surec.versiyon)
            db.session.commit()
            flash('Süreç bilgileri güncellendi.', 'success')
        return redirect(url_for('kalite.surec_duzenle', id=id))
    kullanicilar = User.query.filter_by(is_active=True).order_by(User.name).all()
    departmanlar = ['Satınalma', 'Üretim', 'Bakım', 'Planlama ve Tedarik Zinciri',
                    'Muhasebe', 'Kalite', 'İnsan Kaynakları', 'Genel Müdür']
    return render_template('kalite/surec_duzenle.html',
        surec=surec, kullanicilar=kullanicilar, departmanlar=departmanlar)


@kalite.route('/surecler/<int:id>/adim-ekle', methods=['POST'])
@login_required
@kalite_required
def adim_ekle(id):
    surec = IsAkisiSurec.query.get_or_404(id)
    max_sira = db.session.query(db.func.max(IsAkisiAdim.sira)).filter_by(surec_id=id).scalar() or 0
    adim = IsAkisiAdim(
        surec_id=id,
        sira=max_sira + 1,
        adim_tipi=request.form.get('adim_tipi', 'islem'),
        adim_adi=request.form.get('adim_adi', ''),
        aciklama=request.form.get('aciklama') or None,
        sorumlu_departman=request.form.get('sorumlu_departman') or None,
        sure_hedef_saat=int(request.form['sure_hedef_saat']) if request.form.get('sure_hedef_saat') else None,
        evet_sonraki_sira=int(request.form['evet_sonraki_sira']) if request.form.get('evet_sonraki_sira') else None,
        hayir_sonraki_sira=int(request.form['hayir_sonraki_sira']) if request.form.get('hayir_sonraki_sira') else None,
    )
    db.session.add(adim)
    db.session.commit()
    flash('Adım eklendi.', 'success')
    return redirect(url_for('kalite.surec_duzenle', id=id))


@kalite.route('/surecler/<int:id>/adim-sil', methods=['POST'])
@login_required
@kalite_required
def adim_sil(id):
    adim_id = int(request.form.get('adim_id'))
    adim = IsAkisiAdim.query.get_or_404(adim_id)
    db.session.delete(adim)
    db.session.commit()
    flash('Adım silindi.', 'success')
    return redirect(url_for('kalite.surec_duzenle', id=id))


@kalite.route('/surecler/<int:id>/adim-sira', methods=['POST'])
@login_required
@kalite_required
def adim_sira_degistir(id):
    adim_id = int(request.form.get('adim_id'))
    yon = request.form.get('yon', 'yukari')
    adim = IsAkisiAdim.query.get_or_404(adim_id)
    if yon == 'yukari' and adim.sira > 1:
        onceki = IsAkisiAdim.query.filter_by(surec_id=id, sira=adim.sira - 1).first()
        if onceki:
            onceki.sira, adim.sira = adim.sira, onceki.sira
    elif yon == 'asagi':
        sonraki = IsAkisiAdim.query.filter_by(surec_id=id, sira=adim.sira + 1).first()
        if sonraki:
            sonraki.sira, adim.sira = adim.sira, sonraki.sira
    db.session.commit()
    return redirect(url_for('kalite.surec_duzenle', id=id))


@kalite.route('/surecler/<int:id>/durum', methods=['POST'])
@login_required
@kalite_required
def surec_durum(id):
    surec = IsAkisiSurec.query.get_or_404(id)
    surec.durum = request.form.get('durum', surec.durum)
    db.session.commit()
    flash('Süreç durumu güncellendi.', 'success')
    return redirect(url_for('kalite.surec_goruntur', id=id))
