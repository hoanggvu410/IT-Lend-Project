"""
admin/routes.py — Module quản trị
Routes (prefix /admin): /dashboard  /equipments  /categories  /approve  /history
"""
from datetime import datetime, timezone, timedelta
from functools import wraps
from collections import defaultdict

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from . import admin_bp
from extensions import db
from models import Equipment, Category, Request, User


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

PER_PAGE = 10


# ─────────────────────────────────────────────
#  Decorator kiểm tra quyền Admin
# ─────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
#  /admin  hoặc  /admin/dashboard
# ─────────────────────────────────────────────
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    now = _now()
    total_equipment   = Equipment.query.count()
    maintenance_count = Equipment.query.filter_by(status='Maintenance').count()

    # IDs đang được mượn (Approved + đang trong khoảng thời gian)
    active_eq_ids_q = db.session.query(Request.equipment_id).filter(
        Request.status == 'Approved',
        Request.borrow_date <= now,
        Request.return_date >= now
    ).distinct()

    borrowed_count = db.session.query(Equipment.id).filter(
        Equipment.id.in_(active_eq_ids_q)
    ).count()

    # Sẵn sàng = Available status + không đang bị mượn
    available_count = Equipment.query.filter(
        Equipment.status == 'Available',
        ~Equipment.id.in_(active_eq_ids_q)
    ).count()

    pending_requests = Request.query.filter_by(status='Pending').count()
    total_users      = User.query.filter_by(role='student').count()
    recent_requests  = Request.query.order_by(Request.created_at.desc()).limit(8).all()

    # ── Thống kê theo loại thiết bị ──
    categories = Category.query.all()
    category_stats = []
    for cat in categories:
        eqs    = cat.equipments
        eq_ids = [e.id for e in eqs]
        if not eq_ids:
            continue
        total = len(eq_ids)
        maint = sum(1 for e in eqs if e.status == 'Maintenance')

        cat_borrowed = db.session.query(Request.equipment_id).filter(
            Request.equipment_id.in_(eq_ids),
            Request.status == 'Approved',
            Request.borrow_date <= now,
            Request.return_date >= now
        ).distinct().count()

        cat_available = total - maint - cat_borrowed
        if cat_available < 0:
            cat_available = 0

        cat_pending = Request.query.filter(
            Request.equipment_id.in_(eq_ids),
            Request.status == 'Pending'
        ).count()

        category_stats.append({
            'name':        cat.name,
            'total':       total,
            'available':   cat_available,
            'maintenance': maint,
            'borrowed':    cat_borrowed,
            'pending':     cat_pending,
        })

    return render_template('admin/dashboard.html',
                           total_equipment=total_equipment,
                           available_count=available_count,
                           borrowed_count=borrowed_count,
                           maintenance_count=maintenance_count,
                           pending_requests=pending_requests,
                           total_users=total_users,
                           recent_requests=recent_requests,
                           category_stats=category_stats)


# ─────────────────────────────────────────────
#  /admin/equipments  — Quản lý thiết bị
# ─────────────────────────────────────────────
@admin_bp.route('/equipments')
@login_required
@admin_required
def equipments():
    search          = request.args.get('search', '').strip()
    status_filter   = request.args.get('status', '')
    category_filter = request.args.get('category_id', 0, type=int)
    page            = request.args.get('page', 1, type=int)

    query = Equipment.query

    if status_filter in ('Available', 'Maintenance'):
        query = query.filter_by(status=status_filter)
    else:
        status_filter = ''

    if category_filter:
        query = query.filter_by(category_id=category_filter)

    if search:
        query = query.filter(
            db.or_(
                Equipment.name.ilike(f'%{search}%'),
                Equipment.serial_number.ilike(f'%{search}%'),
                Equipment.description.ilike(f'%{search}%'),
            )
        )

    pagination     = query.order_by(Equipment.id.desc()).paginate(
                        page=page, per_page=PER_PAGE, error_out=False)
    all_categories = Category.query.order_by(Category.name).all()

    return render_template('admin/equipments.html',
                           equipments=pagination.items,
                           pagination=pagination,
                           categories=all_categories,
                           status_filter=status_filter,
                           category_filter=category_filter,
                           search=search)


# ── API lấy thông tin thiết bị để nhân bản ──
@admin_bp.route('/equipments/<int:eq_id>/info')
@login_required
@admin_required
def equipment_info(eq_id):
    eq = Equipment.query.get_or_404(eq_id)

    # Tự động tăng serial: tách prefix và số
    serial = eq.serial_number
    if '-' in serial:
        parts  = serial.rsplit('-', 1)
        prefix = parts[0]
        # Tìm số lớn nhất hiện có với cùng prefix
        similar = Equipment.query.filter(
            Equipment.serial_number.like(f'{prefix}-%')
        ).all()
        max_num = 0
        for s in similar:
            try:
                num = int(s.serial_number.rsplit('-', 1)[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
        suggested_serial = f'{prefix}-{max_num + 1:03d}'
    else:
        suggested_serial = f'{serial}-002'

    return jsonify({
        'name':             eq.name,
        'category_id':      eq.category_id,
        'image_url':        eq.image_url or '',
        'description':      eq.description or '',
        'usage':            eq.usage or '',
        'functions':        eq.functions or '',
        'specs':            eq.specs or '',
        'suggested_serial': suggested_serial,
    })


@admin_bp.route('/equipments/<int:eq_id>/clone', methods=['POST'])
@login_required
@admin_required
def clone_equipment(eq_id):
    """Tạo bản sao thiết bị — serial tự động tăng (số lớn nhất + 1)."""
    eq = Equipment.query.get_or_404(eq_id)
    serial = eq.serial_number

    if '-' in serial:
        prefix = serial.rsplit('-', 1)[0]
        similar = Equipment.query.filter(
            Equipment.serial_number.like(f'{prefix}-%')
        ).all()
        max_num = 0
        for s in similar:
            try:
                num = int(s.serial_number.rsplit('-', 1)[1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                pass
        new_serial = f'{prefix}-{max_num + 1:03d}'
    else:
        # Serial không có dấu '-': tìm số ở cuối chuỗi
        import re as _re
        similar = Equipment.query.filter(
            Equipment.name == eq.name
        ).all()
        max_num = 0
        for s in similar:
            m = _re.search(r'(\d+)$', s.serial_number)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
        new_serial = f'{serial}{max_num + 1:03d}' if max_num else f'{serial}-002'

    if Equipment.query.filter_by(serial_number=new_serial).first():
        flash(
            f'Serial "{new_serial}" đã tồn tại. '
            f'Vui lòng thêm thiết bị thủ công để tự chọn serial.',
            'warning'
        )
        return redirect(url_for('admin.equipments'))

    new_eq = Equipment(
        name=eq.name,
        serial_number=new_serial,
        category_id=eq.category_id,
        status='Available',
        image_url=eq.image_url,
        description=eq.description,
        usage=eq.usage,
        functions=eq.functions,
        specs=eq.specs,
    )
    db.session.add(new_eq)
    db.session.commit()
    flash(
        f'Đã tạo bản sao thiết bị "{new_eq.name}" '
        f'với serial <strong>{new_serial}</strong>.',
        'success'
    )
    return redirect(url_for('admin.equipments'))


@admin_bp.route('/equipments/add', methods=['POST'])
@login_required
@admin_required
def add_equipment():
    name          = request.form.get('name', '').strip()
    serial_number = request.form.get('serial_number', '').strip()
    category_id   = request.form.get('category_id', type=int)
    image_url     = request.form.get('image_url', '').strip() or None
    description   = request.form.get('description', '').strip() or None
    usage         = request.form.get('usage', '').strip() or None
    functions     = request.form.get('functions', '').strip() or None
    specs         = request.form.get('specs', '').strip() or None

    if not name or not serial_number or not category_id:
        flash('Vui lòng điền đầy đủ thông tin thiết bị.', 'danger')
        return redirect(url_for('admin.equipments'))

    if Equipment.query.filter_by(serial_number=serial_number).first():
        flash('Serial number đã tồn tại.', 'danger')
        return redirect(url_for('admin.equipments'))

    eq = Equipment(name=name, serial_number=serial_number,
                   category_id=category_id, status='Available',
                   image_url=image_url, description=description,
                   usage=usage, functions=functions, specs=specs)
    db.session.add(eq)
    db.session.commit()
    flash(f'Đã thêm thiết bị "{name}".', 'success')
    return redirect(url_for('admin.equipments'))


@admin_bp.route('/equipments/<int:eq_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_equipment(eq_id):
    eq         = Equipment.query.get_or_404(eq_id)
    old_status = eq.status

    eq.name        = request.form.get('name', eq.name).strip()
    new_status     = request.form.get('status', eq.status)
    if new_status in ('Available', 'Maintenance'):
        eq.status  = new_status
    eq.image_url   = request.form.get('image_url', '') or None
    eq.category_id = request.form.get('category_id', eq.category_id, type=int)
    eq.description = request.form.get('description', '').strip() or None
    eq.usage       = request.form.get('usage', '').strip() or None
    eq.functions   = request.form.get('functions', '').strip() or None
    eq.specs       = request.form.get('specs', '').strip() or None

    # ── Nếu chuyển sang Bảo trì → huỷ các yêu cầu tương lai ──
    if old_status != 'Maintenance' and eq.status == 'Maintenance':
        now = _now()
        future_reqs = Request.query.filter(
            Request.equipment_id == eq_id,
            Request.status.in_(['Pending', 'Approved']),
            Request.return_date > now
        ).all()
        cancelled_count = len(future_reqs)
        for r in future_reqs:
            r.status     = 'Rejected'
            r.admin_note = (
                f'⚠️ Thiết bị "{eq.name}" cần bảo trì đột xuất. '
                f'Yêu cầu mượn của bạn đã bị huỷ tự động. '
                f'Vui lòng liên hệ admin để được hỗ trợ.'
            )
        if cancelled_count:
            flash(
                f'Đã huỷ {cancelled_count} yêu cầu mượn (tương lai) '
                f'do thiết bị chuyển sang bảo trì. '
                f'Người dùng đã được thông báo trong lịch sử mượn.',
                'warning'
            )

    db.session.commit()
    flash(f'Đã cập nhật thiết bị "{eq.name}".', 'success')
    return redirect(url_for('admin.equipments'))


@admin_bp.route('/equipments/<int:eq_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_equipment(eq_id):
    eq = Equipment.query.get_or_404(eq_id)

    # Ràng buộc: không xoá khi có bất kỳ lịch mượn nào
    any_request = Request.query.filter_by(equipment_id=eq_id).first()
    if any_request:
        flash(
            f'Không thể xóa thiết bị "{eq.name}" vì đã có lịch sử mượn. '
            f'Hãy chuyển thiết bị sang trạng thái Bảo trì thay vì xóa.',
            'danger'
        )
        return redirect(url_for('admin.equipments'))

    db.session.delete(eq)
    db.session.commit()
    flash(f'Đã xóa thiết bị "{eq.name}".', 'success')
    return redirect(url_for('admin.equipments'))


# ─────────────────────────────────────────────
#  /admin/categories  — Quản lý danh mục (CRUD)
# ─────────────────────────────────────────────
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    all_categories = Category.query.all()
    return render_template('admin/categories.html', categories=all_categories)


@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip() or None
    if not name:
        flash('Tên danh mục không được để trống.', 'danger')
        return redirect(url_for('admin.categories'))
    if Category.query.filter_by(name=name).first():
        flash('Danh mục này đã tồn tại.', 'danger')
        return redirect(url_for('admin.categories'))
    db.session.add(Category(name=name, description=description))
    db.session.commit()
    flash(f'Đã thêm danh mục "{name}".', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:cat_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_category(cat_id):
    cat      = Category.query.get_or_404(cat_id)
    new_name = request.form.get('name', '').strip()
    new_desc = request.form.get('description', '').strip() or None
    if not new_name:
        flash('Tên danh mục không được để trống.', 'danger')
        return redirect(url_for('admin.categories'))
    existing = Category.query.filter_by(name=new_name).first()
    if existing and existing.id != cat_id:
        flash('Tên danh mục đã tồn tại.', 'danger')
        return redirect(url_for('admin.categories'))
    cat.name        = new_name
    cat.description = new_desc
    db.session.commit()
    flash(f'Đã cập nhật danh mục "{cat.name}".', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.equipments:
        flash(
            f'Không thể xóa danh mục "{cat.name}" vì còn '
            f'{len(cat.equipments)} thiết bị liên quan.',
            'danger'
        )
        return redirect(url_for('admin.categories'))
    db.session.delete(cat)
    db.session.commit()
    flash(f'Đã xóa danh mục "{cat.name}".', 'success')
    return redirect(url_for('admin.categories'))


# ─────────────────────────────────────────────
#  /admin/approve  — Duyệt yêu cầu mượn
# ─────────────────────────────────────────────
@admin_bp.route('/approve')
@login_required
@admin_required
def approve_requests():
    # ── Pending: nhóm theo user ──
    pending_all = Request.query.filter_by(status='Pending')\
                               .order_by(Request.user_id, Request.created_at.asc()).all()
    pending_groups_dict = defaultdict(list)
    for req in pending_all:
        pending_groups_dict[req.user_id].append(req)
    pending_groups = [
        {'user': reqs[0].user, 'requests': reqs}
        for reqs in pending_groups_dict.values()
    ]

    approved_list = Request.query.filter_by(status='Approved')\
                                 .order_by(Request.borrow_date.asc()).all()
    rejected_list = Request.query.filter_by(status='Rejected')\
                                 .order_by(Request.created_at.desc()).all()
    returned_list = Request.query.filter_by(status='Returned')\
                                 .order_by(Request.actual_return_date.desc()).all()

    # ── Lịch sử mượn với bộ lọc ──
    hist_user      = request.args.get('hist_user', '').strip()
    hist_equipment = request.args.get('hist_equipment', '').strip()
    hist_date_from = request.args.get('hist_date_from', '').strip()
    hist_date_to   = request.args.get('hist_date_to', '').strip()

    hist_query = Request.query\
        .join(User,      Request.user_id      == User.id)\
        .join(Equipment, Request.equipment_id == Equipment.id)

    if hist_user:
        hist_query = hist_query.filter(User.username.ilike(f'%{hist_user}%'))
    if hist_equipment:
        hist_query = hist_query.filter(Equipment.name.ilike(f'%{hist_equipment}%'))
    if hist_date_from:
        try:
            d_from = datetime.strptime(hist_date_from, '%Y-%m-%d')
            hist_query = hist_query.filter(Request.borrow_date >= d_from)
        except ValueError:
            pass
    if hist_date_to:
        try:
            d_to = datetime.strptime(hist_date_to, '%Y-%m-%d') + timedelta(days=1)
            hist_query = hist_query.filter(Request.borrow_date < d_to)
        except ValueError:
            pass

    history_list = hist_query.order_by(Request.created_at.desc()).limit(200).all()

    # Tab đang active (để JS mở đúng tab sau redirect)
    active_tab = request.args.get('tab', 'pending')

    return render_template('admin/approve_requests.html',
                           pending_groups=pending_groups,
                           pending_count=len(pending_all),
                           approved_list=approved_list,
                           rejected_list=rejected_list,
                           returned_list=returned_list,
                           history_list=history_list,
                           hist_user=hist_user,
                           hist_equipment=hist_equipment,
                           hist_date_from=hist_date_from,
                           hist_date_to=hist_date_to,
                           active_tab=active_tab)


@admin_bp.route('/approve/<int:req_id>/action', methods=['POST'])
@login_required
@admin_required
def request_action(req_id):
    req        = Request.query.get_or_404(req_id)
    action     = request.form.get('action')
    admin_note = request.form.get('admin_note', '').strip() or None

    if action == 'approve' and req.status == 'Pending':
        conflict = Request.query.filter(
            Request.id           != req.id,
            Request.equipment_id == req.equipment_id,
            Request.status       == 'Approved',
            Request.borrow_date  < req.return_date,
            Request.return_date  > req.borrow_date
        ).first()
        if conflict:
            flash(
                f'Không thể duyệt: xung đột với yêu cầu #{conflict.id} '
                f'[{conflict.borrow_date.strftime("%d/%m %H:%M")} – '
                f'{conflict.return_date.strftime("%d/%m %H:%M")}].',
                'danger'
            )
            return redirect(url_for('admin.approve_requests'))
        req.status     = 'Approved'
        req.admin_note = admin_note
        flash(f'Đã duyệt yêu cầu #{req.id}.', 'success')

    elif action == 'reject' and req.status == 'Pending':
        req.status     = 'Rejected'
        req.admin_note = admin_note
        flash(f'Đã từ chối yêu cầu #{req.id}.', 'warning')

    elif action == 'confirm_return' and req.status == 'Approved':
        req.status             = 'Returned'
        req.actual_return_date = _now()
        flash(f'Đã xác nhận trả thiết bị cho yêu cầu #{req.id}.', 'success')

    else:
        flash('Hành động không hợp lệ.', 'danger')
        return redirect(url_for('admin.approve_requests'))

    db.session.commit()
    return redirect(url_for('admin.approve_requests'))


# ── Duyệt TẤT CẢ yêu cầu Pending của 1 user ──
@admin_bp.route('/approve/user/<int:user_id>/approve-all', methods=['POST'])
@login_required
@admin_required
def approve_all_for_user(user_id):
    user = User.query.get_or_404(user_id)
    admin_note = request.form.get('admin_note', '').strip() or None
    pending = Request.query.filter_by(user_id=user_id, status='Pending')\
                           .order_by(Request.borrow_date.asc()).all()
    approved_count = 0
    skipped        = []

    for req in pending:
        conflict = Request.query.filter(
            Request.id           != req.id,
            Request.equipment_id == req.equipment_id,
            Request.status       == 'Approved',
            Request.borrow_date  < req.return_date,
            Request.return_date  > req.borrow_date
        ).first()
        if conflict:
            skipped.append(req.id)
        else:
            req.status     = 'Approved'
            req.admin_note = admin_note
            approved_count += 1

    db.session.commit()
    if approved_count:
        flash(f'Đã duyệt {approved_count} yêu cầu cho {user.username}.', 'success')
    if skipped:
        flash(
            f'{len(skipped)} yêu cầu bị bỏ qua do xung đột lịch mượn '
            f'(#{", #".join(map(str, skipped))}).',
            'warning'
        )
    return redirect(url_for('admin.approve_requests'))


# ── Từ chối TẤT CẢ yêu cầu Pending của 1 user ──
@admin_bp.route('/approve/user/<int:user_id>/reject-all', methods=['POST'])
@login_required
@admin_required
def reject_all_for_user(user_id):
    user = User.query.get_or_404(user_id)
    admin_note = request.form.get('admin_note', '').strip() or 'Từ chối hàng loạt bởi admin.'
    pending = Request.query.filter_by(user_id=user_id, status='Pending').all()
    count = len(pending)
    for req in pending:
        req.status     = 'Rejected'
        req.admin_note = admin_note
    db.session.commit()
    flash(f'Đã từ chối {count} yêu cầu của {user.username}.', 'warning')
    return redirect(url_for('admin.approve_requests'))

