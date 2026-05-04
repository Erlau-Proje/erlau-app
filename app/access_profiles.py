USER_TYPES = [
    ('office', 'Ofis kullanicisi'),
    ('operator', 'Operator / saha kullanicisi'),
    ('manager', 'Yonetici'),
    ('executive', 'Yonetim'),
    ('admin', 'Sistem yoneticisi'),
    ('external', 'Dis paydas'),
]

SCOPE_TYPES = [
    ('self', 'Sadece kendi kayitlari'),
    ('own_department', 'Kendi departmani'),
    ('assigned_station', 'Atandigi istasyonlar'),
    ('assigned_departments', 'Secili departmanlar'),
    ('target_department', 'Hedef departman'),
    ('all_company', 'Tum sirket'),
]

JOB_PROFILES = [
    ('admin', 'Admin'),
    ('gm', 'Genel Mudur'),
    ('satinalma_uzmani', 'Satinalma Uzmani'),
    ('satinalma_yoneticisi', 'Satinalma Yoneticisi'),
    ('muhasebe_personeli', 'Muhasebe Personeli'),
    ('muhasebe_yoneticisi', 'Muhasebe Yoneticisi'),
    ('planlama_personeli', 'Planlama Personeli'),
    ('planlama_yoneticisi', 'Planlama Yoneticisi'),
    ('uretim_operatoru', 'Uretim Operatoru'),
    ('cnc_operatoru', 'CNC Operatoru'),
    ('uretim_sorumlusu', 'Uretim Sorumlusu'),
    ('uretim_yoneticisi', 'Uretim Yoneticisi'),
    ('bakim_personeli', 'Bakim Personeli'),
    ('bakim_yoneticisi', 'Bakim Yoneticisi'),
    ('kalite_personeli', 'Kalite Personeli'),
    ('kalite_sorumlusu', 'Kalite Sorumlusu'),
    ('proje_personeli', 'Proje Personeli'),
    ('departman_yoneticisi', 'Departman Yoneticisi'),
    ('sadece_goruntuleme', 'Sadece Goruntuleme'),
]

PROFILE_LABELS = dict(JOB_PROFILES)
USER_TYPE_LABELS = dict(USER_TYPES)
SCOPE_LABELS = dict(SCOPE_TYPES)


def _dept_name(user):
    return (getattr(getattr(user, 'department', None), 'name', '') or '').lower()


def infer_profile(user):
    role = getattr(user, 'role', '') or 'personel'
    dept = _dept_name(user)

    if role == 'admin':
        return 'admin', 'admin', 'all_company'
    if role == 'gm':
        return 'gm', 'executive', 'all_company'
    if role == 'satinalma':
        return 'satinalma_uzmani', 'office', 'all_company'
    if role == 'muhasebe':
        return 'muhasebe_personeli', 'office', 'own_department'
    if role == 'kalite':
        return 'kalite_personeli', 'office', 'assigned_departments'
    if role == 'bakim':
        return 'bakim_personeli', 'office', 'own_department'
    if role == 'planlama':
        return 'planlama_personeli', 'office', 'own_department'
    if role == 'uretim':
        return 'uretim_sorumlusu', 'office', 'own_department'

    if role == 'departman_yoneticisi':
        if 'uretim' in dept or 'üretim' in dept:
            return 'uretim_yoneticisi', 'manager', 'own_department'
        if 'bakim' in dept or 'bakım' in dept:
            return 'bakim_yoneticisi', 'manager', 'own_department'
        if 'kalite' in dept:
            return 'kalite_sorumlusu', 'manager', 'assigned_departments'
        if 'planlama' in dept:
            return 'planlama_yoneticisi', 'manager', 'own_department'
        if 'muhasebe' in dept:
            return 'muhasebe_yoneticisi', 'manager', 'own_department'
        if 'sat' in dept:
            return 'satinalma_yoneticisi', 'manager', 'all_company'
        return 'departman_yoneticisi', 'manager', 'own_department'

    if 'uretim' in dept or 'üretim' in dept:
        return 'uretim_operatoru', 'operator', 'assigned_station'
    if 'bakim' in dept or 'bakım' in dept:
        return 'bakim_personeli', 'office', 'own_department'
    if 'kalite' in dept:
        return 'kalite_personeli', 'office', 'assigned_departments'
    if 'planlama' in dept:
        return 'planlama_personeli', 'office', 'own_department'
    if 'muhasebe' in dept:
        return 'muhasebe_personeli', 'office', 'own_department'
    if 'proje' in dept:
        return 'proje_personeli', 'office', 'own_department'
    return 'sadece_goruntuleme', 'office', 'self'
