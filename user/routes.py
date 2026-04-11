"""
user/routes.py — Module giao diện sinh viên (Thành viên B đảm nhận)
Routes: /   /equipment/<id>   /my-requests   /request/new   /api/suggestions
"""
from datetime import date as dt_date
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from . import user_bp
from extensions import db
from models import Equipment, Category, Request


# ─────────────────────────────────────────────
#  /  — Trang chủ (danh sách thiết bị)
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

    eq_query = Equipment.query.order_by(Equipment.status.asc())
    if category_id:
        eq_query = eq_query.filter_by(category_id=category_id)
    if search_q:
        eq_query = eq_query.filter(Equipment.name.ilike(f'%{search_q}%'))

    pagination = eq_query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.all()

    return render_template('user/index.html',
                           equipments=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           selected_category=category_id,
                           query=search_q)


# ─────────────────────────────────────────────
#  /api/suggestions  — Gợi ý tìm kiếm (AJAX)
# ─────────────────────────────────────────────
@user_bp.route('/api/suggestions')
@login_required
def suggestions():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])

    results = Equipment.query\
        .filter(Equipment.name.ilike(f'%{q}%'))\
        .limit(6)\
        .all()

    return jsonify([{
        'id':       eq.id,
        'name':     eq.name,
        'category': eq.category.name,
        'status':   eq.status
    } for eq in results])


# ─────────────────────────────────────────────
#  /equipment/<id>  — Chi tiết + form đăng ký mượn
# ─────────────────────────────────────────────
@user_bp.route('/equipment/<int:equipment_id>')
@login_required
def equipment_detail(equipment_id):
    student_guard = _ensure_student()
    if student_guard:
        return student_guard

    equipment = Equipment.query.get_or_404(equipment_id)

    # Lịch sử mượn của thiết bị (Approved + Returned, 5 lần gần nhất)
    borrow_history = Request.query\
        .filter_by(equipment_id=equipment_id)\
        .filter(Request.status.in_(['Approved', 'Returned']))\
        .order_by(Request.created_at.desc())\
        .limit(5)\
        .all()

    return render_template('user/equipment_detail.html',
                           equipment=equipment,
                           today=dt_date.today(),
                           borrow_history=borrow_history)


# ─────────────────────────────────────────────
#  /my-requests  — Lịch sử mượn cá nhân
# ─────────────────────────────────────────────
@user_bp.route('/my-requests')
@login_required
def my_requests():
    student_guard = _ensure_student()
    if student_guard:
        return student_guard

    # Lọc theo user_id — chỉ thấy lịch sử của chính mình (Ràng buộc quyền hạn)
    requests = Request.query\
        .filter_by(user_id=current_user.id)\
        .order_by(Request.created_at.desc())\
        .all()
    return render_template('user/my_requests.html', requests=requests)


# ─────────────────────────────────────────────
#  /request/new  — Gửi yêu cầu mượn mới
# ─────────────────────────────────────────────
@user_bp.route('/request/new', methods=['POST'])
@login_required
def new_request():
    student_guard = _ensure_student()
    if student_guard:
        return student_guard

    """
    TODO (Thành viên B + C): Hoàn thiện form và validation
    Logic nghiệp vụ (Ràng buộc từ spec):
    1. return_date phải > borrow_date
    2. Equipment phải ở trạng thái Available
    """
    equipment_id = request.form.get('equipment_id', type=int)
    borrow_date  = request.form.get('borrow_date')
    return_date  = request.form.get('return_date')

    # Validation cơ bản
    if not equipment_id or not borrow_date or not return_date:
        flash('Vui lòng điền đầy đủ thông tin.', 'danger')
        return redirect(url_for('user.index'))

    try:
        bd = dt_date.fromisoformat(borrow_date)
        rd = dt_date.fromisoformat(return_date)
    except ValueError:
        flash('Định dạng ngày không hợp lệ.', 'danger')
        return redirect(url_for('user.index'))

    # Ràng buộc 1: ngày trả > ngày mượn
    if rd <= bd:
        flash('Ngày trả phải sau ngày mượn.', 'danger')
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))

    # Ràng buộc 2: thiết bị phải Available
    equipment = Equipment.query.get_or_404(equipment_id)
    if equipment.status != 'Available':
        flash('Thiết bị này hiện không khả dụng để mượn.', 'danger')
        return redirect(url_for('user.equipment_detail', equipment_id=equipment_id))

    # Tạo Request mới
    new_req = Request(
        user_id      = current_user.id,
        equipment_id = equipment_id,
        borrow_date  = bd,
        return_date  = rd,
        status       = 'Pending'
    )
    db.session.add(new_req)
    db.session.commit()

    flash(f'Gửi yêu cầu mượn "{equipment.name}" thành công! Vui lòng chờ Admin duyệt.', 'success')
    return redirect(url_for('user.my_requests'))


def _ensure_student():
    if current_user.role == 'admin':
        flash('Admin không thao tác ở khu vực người dùng.', 'warning')
        return redirect(url_for('admin.dashboard'))
    return None


