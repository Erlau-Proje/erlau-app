from app.permissions import has_permission


def _dept_key(user):
    name = (getattr(getattr(user, 'department', None), 'name', '') or '').strip().lower()
    return name


def _is_cross_role(user):
    return getattr(user, 'role', '') in ('admin', 'gm', 'satinalma')


def _profile(user):
    return getattr(user, 'job_profile', '') or ''


def _is_own_or_cross(user, dept_keywords):
    if _is_cross_role(user):
        return True
    dept = _dept_key(user)
    return any(k in dept for k in dept_keywords)


def menu_visible(user, key):
    # Genel erişim (oturum açmış tüm kullanıcılar)
    if key in ('portal', 'dashboard'):
        return True

    # Satın alma alanı
    if key == 'purchase.section':
        return any([
            has_permission(user, 'talep.create'),
            has_permission(user, 'purchase.order_report'),
            has_permission(user, 'purchase.panel'),
            has_permission(user, 'purchase.reports'),
            has_permission(user, 'offer.view'),
        ])

    # Departman tabanlı modüller
    if key == 'planning.section':
        return _is_own_or_cross(user, ('planlama',)) and (
            has_permission(user, 'planning.dashboard') or has_permission(user, 'planning.create')
        )
    if key == 'maintenance.section':
        return _is_own_or_cross(user, ('bakım', 'bakim')) and any([
            has_permission(user, 'maintenance.dashboard'),
            has_permission(user, 'maintenance.program'),
            has_permission(user, 'maintenance.repair'),
            has_permission(user, 'maintenance.periodic'),
            has_permission(user, 'maintenance.calendar_report'),
        ])
    if key == 'production.section':
        if _profile(user) in ('uretim_operatoru', 'cnc_operatoru', 'uretim_sorumlusu', 'uretim_yoneticisi'):
            return True
        return _is_own_or_cross(user, ('üretim', 'uretim')) and any([
            has_permission(user, 'production.dashboard'),
            has_permission(user, 'production.reports'),
            has_permission(user, 'production.staff_view'),
        ])
    if key == 'quality.section':
        return _is_own_or_cross(user, ('kalite',)) and any([
            has_permission(user, 'quality.dashboard'),
            has_permission(user, 'quality.dof_view'),
            has_permission(user, 'quality.8d_view'),
            has_permission(user, 'quality.process_view'),
            has_permission(user, 'quality.control_entry'),
            has_permission(user, 'quality.dof_performance'),
        ])

    # Muhasebe sadece ilgili yetki + muhasebe/satınalma/admin/gm
    if key == 'invoice.section':
        return has_permission(user, 'invoice.view') and (
            _is_cross_role(user) or _is_own_or_cross(user, ('muhasebe',))
        )

    if key == 'management.section':
        return has_permission(user, 'supplier.manage')

    if key == 'admin.section':
        return any([
            has_permission(user, 'admin.users'),
            has_permission(user, 'admin.permissions'),
            has_permission(user, 'admin.server'),
        ])

    if key == 'list.section':
        return has_permission(user, 'list.view')

    if key == 'technical.section':
        return has_permission(user, 'technical.view')

    return False
