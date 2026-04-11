"""
user/routes.py — Module giao diện sinh viên
Routes: /  /equipment/<id>  /my-requests  /request/new
        /cart  /cart/add  /cart/remove/<id>  /cart/clear  /cart/checkout
        /api/suggestions  /api/equipment/<id>/slots  /api/cart/count
"""
from datetime import datetime, timedelta, timezone
from math import ceil
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user

from . import user_bp
from extensions import db
from models import Equipment, Category, Request


# ── Helper ────────────────────────────────────────────────────────────────
def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class GroupPagination:
    """Pagination object dùng cho grouped equipment."""
    def __init__(self, total, page, per_page):
        self.total    = total
        self.page     = page
        self.per_page = per_page
        self.pages    = max(1, ceil(total / per_page)) if total > 0 else 1
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1

    def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge
                    or self.page - left_current - 1 < num < self.page + right_current
                    or num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num


def _group_equipments(eq_list):
    """Nhóm danh sách Equipment theo tên, trả về list of dict."""
    groups = {}
    for eq in eq_list:
        key = eq.name
        if key not in groups:
            groups[key] = {
                'name':              eq.name,
                'category':          eq.category,
                'image_url':         None,
                'total':             0,
                'maintenance_count': 0,
                'units':             [],
            }
        g = groups[key]
        g['units'].append(eq)
        g['total'] += 1
        if eq.image_url and not g['image_url']:
            g['image_url'] = eq.image_url
        if eq.status == 'Maintenance':
            g['maintenance_count'] += 1
    return list(groups.values())


# ─────────────────────────────────────────────
#  /  — Trang chủ (danh sách thiết bị — grouped)
# ─────────────────────────────────────────────
@user_bp.route('/')
@login_required
def index():
    student_guard = _ensure_student()
    if student_guard:
        return student_guard

    page        = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search_q    = request.args.get('q', '').strip()
    per_page    = 8

    eq_query = Equipment.query.order_by(Equipment.name.asc(), Equipment.serial_number.asc())
    if category_id:
        eq_query = eq_query.filter_by(category_id=category_id)
    if search_q:
        eq_query = eq_query.filter(Equipment.name.ilike(f'%{search_q}%'))

    all_eq     = eq_query.all()
    all_groups = _group_equipments(all_eq)

    # Phân trang trên groups
    start      = (page - 1) * per_page
    paged_grps = all_groups[start:start + per_page]
    pagination = GroupPagination(len(all_groups), page, per_page)

    categories = Category.query.all()
    cart_ids   = session.get('cart', [])

    return render_template('user/index.html',
                           groups=paged_grps,
                           pagination=pagination,
                           categories=categories,
                           selected_category=category_id,
                           query=search_q,
                           cart_ids=cart_ids)


# ─────────────────────────────────────────────
#  /api/suggestions  — Gợi ý tìm kiếm (AJAX)
# ─────────────────────────────────────────────
@user_bp.route('/api/suggestions')
@login_required
def suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    results = Equipment.query.filter(Equipment.name.ilike(f'%{q}%')).limit(6).all()
    return jsonify([{
        'id': eq.id, 'name': eq.name,
        'category': eq.category.name, 'status': eq.status
    } for eq in results])


# ─────────────────────────────────────────────
#  /api/equipment/<id>/slots  — Khung giờ đã đặt
# ─────────────────────────────────────────────
@user_bp.route('/api/equipment/<int:equipment_id>/slots')
@login_required
def equipment_slots(equipment_id):
    now    = _now()
    cutoff = now + timedelta(days=14)
    booked = Request.query.filter(
        Request.equipment_id == equipment_id,
        Request.status.in_(['Pending', 'Approved']),
        Request.return_date  >= now,
        Request.borrow_date  <= cutoff
    ).order_by(Request.borrow_date.asc()).all()
    return jsonify([{
        'id':          r.id,
        'status':      r.status,
        'borrow_date': r.borrow_date.strftime('%Y-%m-%dT%H:%M'),
        'return_date': r.return_date.strftime('%Y-%m-%dT%H:%M'),
        'user':        r.user.username if r.user_id == current_user.id else '—'
    } for r in booked])


# ─────────────────────────────────────────────
#  /api/cart/count  — Số lượng trong giỏ (AJAX)
# ─────────────────────────────────────────────
@user_bp.route('/api/cart/count')
@login_required
def cart_count_api():
    return jsonify({'count': len(session.get('cart', []))})


# ─────────────────────────────────────────────
#  /equipment/<id>  — Chi tiết + form mượn
# ─────────────────────────────────────────────
@user_bp.route('/equipment/<int:equipment_id>')
@login_required
def equipment_detail(equipment_id):
    student_guard = _ensure_student()
    if student_guard:
        return student_guard

    equipment = Equipment.query.get_or_404(equipment_id)
    borrow_history = Request.query\
        .filter_by(equipment_id=equipment_id)\
        .filter(Request.status.in_(['Approved', 'Returned']))\
        .order_by(Request.created_at.desc()).limit(5).all()

    now    = _now()
    cutoff = now + timedelta(days=7)
    booked_slots = Request.query.filter(
        Request.equipment_id == equipment_id,
        Request.status.in_(['Pending', 'Approved']),
        Request.return_date  >= now,
        Request.borrow_date  <= cutoff
    ).order_by(Request.borrow_date.asc()).all()

    in_cart = equipment_id in session.get('cart', [])

    return render_template('user/equipment_detail.html',
                           equipment=equipment,
                           now=now,
                           booked_slots=booked_slots,
                           borrow_history=borrow_history,
                           in_cart=in_cart)


# ─────────────────────────────────────────────
#  /my-requests  — Lịch sử mượn cá nhân
# ─────────────────────────────────────────────
@user_bp.route('/my-requests')
@login_required
def my_requests():
    student_guard = _ensure_student()
    if student_guard:
        return student_guard
    reqs = Request.query.filter_by(user_id=current_user.id)\
                        .order_by(Request.created_at.desc()).all()
    return render_template('user/my_requests.html', requests=reqs)


# ─────────────────────────────────────────────
#  /request/new  — Gửi yêu cầu mượn đơn lẻ
# ─────────────────────────────────────────────
@user_bp.route('/request/new', methods=['POST'])
@login_required
def new_request():
    student_guard = _ensure_student()
    if student_guard:
        return student_guard

    equipment_id = request.form.get('equipment_id', type=int)
    borrow_str   = request.form.get('borrow_date', '').strip()
    return_str   = request.form.get('return_date', '').strip()

    if not equipment_id or not borrow_str or not return_str:
        flash('Vui lòng điền đầy đủ thông tin.', 'danger')
        return redirect(url_for('user.index'))

    try:
        borrow_dt = datetime.fromisoformat(borrow_str)
        return_dt = datetime.fromisoformat(return_str)
    except ValueError:
        flash('Định dạng ngày giờ không hợp lệ.', 'danger')
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))

    now = _now()
    if borrow_dt < now:
        flash('Thời gian bắt đầu mượn phải là thời điểm trong tương lai.', 'danger')
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))

    duration = return_dt - borrow_dt
    if duration < timedelta(hours=1):
        flash('Thời gian mượn tối thiểu là 1 tiếng.', 'danger')
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))
    if duration > timedelta(days=3):
        flash('Thời gian mượn tối đa là 3 ngày.', 'danger')
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))

    equipment = Equipment.query.get_or_404(equipment_id)
    if equipment.status == 'Maintenance':
        flash('Thiết bị này hiện đang bảo trì, không thể đặt mượn.', 'danger')
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))

    if not equipment.is_available_for(borrow_dt, return_dt):
        conflict = Request.query.filter(
            Request.equipment_id == equipment_id,
            Request.status.in_(['Pending', 'Approved']),
            Request.borrow_date  < return_dt,
            Request.return_date  > borrow_dt
        ).first()
        if conflict:
            flash(
                f'Khung giờ bị trùng với yêu cầu '
                f'[{conflict.borrow_date.strftime("%d/%m %H:%M")} – '
                f'{conflict.return_date.strftime("%d/%m %H:%M")}] '
                f'({conflict.status}). Vui lòng chọn khung giờ khác.',
                'danger'
            )
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))

    own_conflict = Request.query.filter(
        Request.user_id      == current_user.id,
        Request.equipment_id == equipment_id,
        Request.status.in_(['Pending', 'Approved']),
        Request.borrow_date  < return_dt,
        Request.return_date  > borrow_dt
    ).first()
    if own_conflict:
        flash('Bạn đã có yêu cầu mượn thiết bị này trong khung giờ đó rồi.', 'warning')
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))

    new_req = Request(user_id=current_user.id, equipment_id=equipment_id,
                      borrow_date=borrow_dt, return_date=return_dt, status='Pending')
    db.session.add(new_req)
    db.session.commit()
    flash(
        f'Gửi yêu cầu mượn "{equipment.name}" thành công! '
        f'({borrow_dt.strftime("%d/%m/%Y %H:%M")} – {return_dt.strftime("%d/%m/%Y %H:%M")}) '
        f'Chờ Admin duyệt.',
        'success'
    )
    return redirect(url_for('user.my_requests'))


# ─────────────────────────────────────────────
#  GIỎ MƯỢN ĐỒ (CART)
# ─────────────────────────────────────────────

@user_bp.route('/cart')
@login_required
def cart():
    student_guard = _ensure_student()
    if student_guard:
        return student_guard
    cart_ids   = session.get('cart', [])
    cart_items = [eq for eq_id in cart_ids
                  if (eq := Equipment.query.get(eq_id)) is not None]
    return render_template('user/cart.html', cart_items=cart_items, now=_now())


@user_bp.route('/cart/add', methods=['POST'])
@login_required
def cart_add():
    student_guard = _ensure_student()
    if student_guard:
        return jsonify({'error': 'Forbidden'}), 403

    data         = request.get_json(silent=True) or {}
    equipment_id = data.get('equipment_id') or request.form.get('equipment_id', type=int)
    if isinstance(equipment_id, str):
        equipment_id = int(equipment_id)

    if not equipment_id:
        return jsonify({'error': 'Thiếu equipment_id'}), 400

    eq = Equipment.query.get(equipment_id)
    if not eq:
        return jsonify({'error': 'Không tìm thấy thiết bị'}), 404
    if eq.status == 'Maintenance':
        return jsonify({'error': 'Thiết bị đang bảo trì, không thể thêm vào giỏ.'}), 400

    cart = session.get('cart', [])
    if equipment_id in cart:
        return jsonify({'message': 'already_in_cart', 'count': len(cart),
                        'name': eq.name, 'serial': eq.serial_number})

    cart.append(equipment_id)
    session['cart']    = cart
    session.modified   = True
    return jsonify({'message': 'added', 'count': len(cart),
                    'name': eq.name, 'serial': eq.serial_number})


@user_bp.route('/cart/remove/<int:equipment_id>', methods=['POST'])
@login_required
def cart_remove(equipment_id):
    cart = session.get('cart', [])
    if equipment_id in cart:
        cart.remove(equipment_id)
        session['cart']  = cart
        session.modified = True
    return redirect(url_for('user.cart'))


@user_bp.route('/cart/clear', methods=['POST'])
@login_required
def cart_clear():
    session['cart']  = []
    session.modified = True
    flash('Đã xóa toàn bộ giỏ mượn.', 'info')
    return redirect(url_for('user.cart'))


@user_bp.route('/cart/checkout', methods=['POST'])
@login_required
def cart_checkout():
    student_guard = _ensure_student()
    if student_guard:
        return student_guard

    cart_ids = session.get('cart', [])
    if not cart_ids:
        flash('Giỏ mượn đồ đang trống.', 'warning')
        return redirect(url_for('user.cart'))

    now         = _now()
    errors      = []
    new_requests = []

    for eq_id in cart_ids:
        eq = Equipment.query.get(eq_id)
        if not eq:
            errors.append(f'Thiết bị #{eq_id} không tồn tại.')
            continue

        borrow_str = request.form.get(f'borrow_{eq_id}', '').strip()
        return_str = request.form.get(f'return_{eq_id}', '').strip()

        if not borrow_str or not return_str:
            errors.append(f'"{eq.name}" ({eq.serial_number}): Chưa chọn thời gian mượn.')
            continue

        try:
            borrow_dt = datetime.fromisoformat(borrow_str)
            return_dt = datetime.fromisoformat(return_str)
        except ValueError:
            errors.append(f'"{eq.name}": Định dạng thời gian không hợp lệ.')
            continue

        if borrow_dt < now:
            errors.append(f'"{eq.name}": Thời gian bắt đầu phải trong tương lai.')
            continue

        duration = return_dt - borrow_dt
        if duration < timedelta(hours=1):
            errors.append(f'"{eq.name}": Tối thiểu 1 tiếng.')
            continue
        if duration > timedelta(days=3):
            errors.append(f'"{eq.name}": Tối đa 3 ngày.')
            continue

        if eq.status == 'Maintenance':
            errors.append(f'"{eq.name}": Đang bảo trì, không thể mượn.')
            continue

        if not eq.is_available_for(borrow_dt, return_dt):
            errors.append(f'"{eq.name}" ({eq.serial_number}): Khung giờ bị trùng lịch đã đặt.')
            continue

        new_requests.append(Request(
            user_id=current_user.id, equipment_id=eq_id,
            borrow_date=borrow_dt, return_date=return_dt, status='Pending'
        ))

    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('user.cart'))

    for req in new_requests:
        db.session.add(req)
    db.session.commit()

    session['cart']  = []
    session.modified = True
    flash(f'Đã gửi {len(new_requests)} yêu cầu mượn thành công! Vui lòng chờ Admin duyệt.', 'success')
    return redirect(url_for('user.my_requests'))


def _ensure_student():
    if current_user.role == 'admin':
        flash('Admin không thao tác ở khu vực người dùng.', 'warning')
        return redirect(url_for('admin.dashboard'))
    return None

