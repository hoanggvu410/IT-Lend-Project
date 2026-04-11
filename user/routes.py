"""
user/routes.py — Module giao diện sinh viên (Thành viên B đảm nhận)
Routes: /   /equipment/<id>   /my-requests   /request/new
"""
from datetime import date as dt_date
from flask import render_template, redirect, url_for, flash, request
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
    # Admin chuyển thẳng sang dashboard
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    # TODO (Thành viên B): Thêm phân trang, lazy load ảnh
    equipments = Equipment.query.order_by(Equipment.status.asc()).all()
    categories = Category.query.all()
    return render_template('user/index.html',
                           equipments=equipments,
                           categories=categories,
                           query='')


# ─────────────────────────────────────────────
#  /equipment/<id>  — Chi tiết + form đăng ký mượn
# ─────────────────────────────────────────────
@user_bp.route('/equipment/<int:equipment_id>')
@login_required
def equipment_detail(equipment_id):
    # TODO (Thành viên B): Hiển thị lịch sử mượn của thiết bị
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template('user/equipment_detail.html',
                           equipment=equipment,
                           today=dt_date.today())


# ─────────────────────────────────────────────
#  /my-requests  — Lịch sử mượn cá nhân
# ─────────────────────────────────────────────
@user_bp.route('/my-requests')
@login_required
def my_requests():
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

    from datetime import date as parse_date
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

