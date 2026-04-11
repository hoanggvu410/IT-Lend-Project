"""
admin/routes.py — Module quản trị (Thành viên A đảm nhận)
Routes (prefix /admin): /  /dashboard  /equipments  /categories  /approve
"""
from functools import wraps
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import admin_bp
from extensions import db
from models import Equipment, Category, Request, User


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
    total_equipment   = Equipment.query.count()
    available_count   = Equipment.query.filter_by(status='Available').count()
    borrowed_count    = Equipment.query.filter_by(status='Borrowed').count()
    maintenance_count = Equipment.query.filter_by(status='Maintenance').count()
    pending_requests  = Request.query.filter_by(status='Pending').count()
    total_users       = User.query.filter_by(role='student').count()
    recent_requests   = Request.query.order_by(Request.created_at.desc()).limit(8).all()

    return render_template('admin/dashboard.html',
                           total_equipment=total_equipment,
                           available_count=available_count,
                           borrowed_count=borrowed_count,
                           maintenance_count=maintenance_count,
                           pending_requests=pending_requests,
                           total_users=total_users,
                           recent_requests=recent_requests)


# ─────────────────────────────────────────────
#  /admin/equipments  — Quản lý thiết bị (CRUD)
# ─────────────────────────────────────────────
@admin_bp.route('/equipments')
@login_required
@admin_required
def equipments():
    status_filter  = request.args.get('status', '')
    valid_statuses = ['Available', 'Borrowed', 'Maintenance']
    if status_filter in valid_statuses:
        all_equipments = Equipment.query.filter_by(status=status_filter)\
                                        .order_by(Equipment.id.desc()).all()
    else:
        status_filter  = ''
        all_equipments = Equipment.query.order_by(Equipment.id.desc()).all()
    categories = Category.query.all()
    return render_template('admin/equipments.html',
                           equipments=all_equipments,
                           categories=categories,
                           status_filter=status_filter)


@admin_bp.route('/equipments/add', methods=['POST'])
@login_required
@admin_required
def add_equipment():
    # TODO (Thành viên A): Hoàn thiện form thêm thiết bị
    name          = request.form.get('name', '').strip()
    serial_number = request.form.get('serial_number', '').strip()
    category_id   = request.form.get('category_id', type=int)
    image_url     = request.form.get('image_url', '').strip() or None

    if not name or not serial_number or not category_id:
        flash('Vui lòng điền đầy đủ thông tin thiết bị.', 'danger')
        return redirect(url_for('admin.equipments'))

    if Equipment.query.filter_by(serial_number=serial_number).first():
        flash('Serial number đã tồn tại.', 'danger')
        return redirect(url_for('admin.equipments'))

    eq = Equipment(name=name, serial_number=serial_number,
                   category_id=category_id, status='Available',
                   image_url=image_url)
    db.session.add(eq)
    db.session.commit()
    flash(f'Đã thêm thiết bị "{name}".', 'success')
    return redirect(url_for('admin.equipments'))


@admin_bp.route('/equipments/<int:eq_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_equipment(eq_id):
    # TODO (Thành viên A): Hoàn thiện chỉnh sửa thiết bị
    eq = Equipment.query.get_or_404(eq_id)
    eq.name        = request.form.get('name', eq.name).strip()
    eq.status      = request.form.get('status', eq.status)
    eq.image_url   = request.form.get('image_url', eq.image_url) or None
    eq.category_id = request.form.get('category_id', eq.category_id, type=int)
    db.session.commit()
    flash(f'Đã cập nhật thiết bị "{eq.name}".', 'success')
    return redirect(url_for('admin.equipments'))


@admin_bp.route('/equipments/<int:eq_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_equipment(eq_id):
    # TODO (Thành viên A): Kiểm tra ràng buộc trước khi xóa
    eq = Equipment.query.get_or_404(eq_id)
    if eq.status == 'Borrowed':
        flash('Không thể xóa thiết bị đang được mượn.', 'danger')
        return redirect(url_for('admin.equipments'))
    db.session.delete(eq)
    db.session.commit()
    flash(f'Đã xóa thiết bị "{eq.name}".', 'success')
    return redirect(url_for('admin.equipments'))


# ─────────────────────────────────────────────
#  /admin/categories  — Quản lý danh mục
# ─────────────────────────────────────────────
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    # TODO (Thành viên A): Thêm CRUD cho Category
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
    cat = Category.query.get_or_404(cat_id)
    new_name = request.form.get('name', '').strip()
    new_desc = request.form.get('description', '').strip() or None
    if not new_name:
        flash('Tên danh mục không được để trống.', 'danger')
        return redirect(url_for('admin.categories'))
    # Kiểm tra trùng tên với danh mục khác
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
    # Ràng buộc: không xóa nếu còn thiết bị thuộc danh mục này
    if cat.equipments:
        flash(f'Không thể xóa danh mục "{cat.name}" vì còn {len(cat.equipments)} thiết bị liên quan.', 'danger')
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
    pending_list  = Request.query.filter_by(status='Pending')\
                                 .order_by(Request.created_at.asc()).all()
    approved_list = Request.query.filter_by(status='Approved')\
                                 .order_by(Request.borrow_date.asc()).all()
    rejected_list = Request.query.filter_by(status='Rejected')\
                                 .order_by(Request.created_at.desc()).all()
    returned_list = Request.query.filter_by(status='Returned')\
                                 .order_by(Request.actual_return_date.desc()).all()
    return render_template('admin/approve_requests.html',
                           pending_list=pending_list,
                           approved_list=approved_list,
                           rejected_list=rejected_list,
                           returned_list=returned_list)


@admin_bp.route('/approve/<int:req_id>/action', methods=['POST'])
@login_required
@admin_required
def request_action(req_id):
    """
    Xử lý nút Approve / Reject / Confirm Return
    TODO (Thành viên A): Hoàn thiện logic cập nhật trạng thái
    """
    from datetime import date
    req        = Request.query.get_or_404(req_id)
    action     = request.form.get('action')
    admin_note = request.form.get('admin_note', '').strip() or None

    if action == 'approve' and req.status == 'Pending':
        req.status           = 'Approved'
        req.admin_note       = admin_note
        req.equipment.status = 'Borrowed'   # Ràng buộc nghiệp vụ
        flash(f'Đã duyệt yêu cầu #{req.id}.', 'success')

    elif action == 'reject' and req.status == 'Pending':
        req.status     = 'Rejected'
        req.admin_note = admin_note
        flash(f'Đã từ chối yêu cầu #{req.id}.', 'warning')

    elif action == 'confirm_return' and req.status == 'Approved':
        req.status               = 'Returned'
        req.actual_return_date   = date.today()
        req.equipment.status     = 'Available'  # Ràng buộc nghiệp vụ
        flash(f'Đã xác nhận trả thiết bị cho yêu cầu #{req.id}.', 'success')

    else:
        flash('Hành động không hợp lệ.', 'danger')
        return redirect(url_for('admin.approve_requests'))

    db.session.commit()
    return redirect(url_for('admin.approve_requests'))

