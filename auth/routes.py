"""
auth/routes.py — Module xác thực (Thành viên C đảm nhận)
Routes: /login  /register  /logout  /search
"""
from urllib.parse import urlparse, urljoin

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from . import auth_bp
from extensions import db, bcrypt
from models import User, Equipment, Category


# ─────────────────────────────────────────────
#  /login  — Đăng nhập
# ─────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role()

    if request.method == 'POST':
        # TODO (Thành viên C): Hoàn thiện logic đăng nhập
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not username or not password:
            flash('Vui lòng nhập tên đăng nhập và mật khẩu.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f'Xin chào, {user.username}! 👋', 'success')
            next_page = request.args.get('next', '').strip()
            if not _is_safe_next_url(next_page):
                next_page = ''
            return redirect(next_page) if next_page else _redirect_by_role()
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')

    return render_template('auth/login.html')


# ─────────────────────────────────────────────
#  /register  — Đăng ký tài khoản mới
# ─────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role()

    if request.method == 'POST':
        # TODO (Thành viên C): Hoàn thiện validation đăng ký
        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Basic validation
        if not username or not email or not password:
            flash('Vui lòng điền đầy đủ thông tin.', 'danger')
        elif len(username) < 3:
            flash('Tên đăng nhập phải có ít nhất 3 ký tự.', 'danger')
        elif '@' not in email or '.' not in email.split('@')[-1]:
            flash('Email không hợp lệ.', 'danger')
        elif password != confirm_password:
            flash('Mật khẩu xác nhận không khớp.', 'danger')
        elif len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng.', 'danger')
        else:
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email,
                            password_hash=hashed, role='student')
            db.session.add(new_user)
            db.session.commit()
            flash('Tạo tài khoản thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# ─────────────────────────────────────────────
#  /logout  — Đăng xuất
# ─────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất thành công.', 'info')
    return redirect(url_for('auth.login'))


# ─────────────────────────────────────────────
#  /search  — Tìm kiếm & lọc thiết bị
# ─────────────────────────────────────────────
@auth_bp.route('/search')
@login_required
def search():
    # Route tìm kiếm dành cho student; admin dùng dashboard riêng
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))

    q           = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)

    query = Equipment.query
    if q:
        query = query.filter(Equipment.name.ilike(f'%{q}%'))
    if category_id:
        query = query.filter_by(category_id=category_id)

    equipments = query.all()
    categories = Category.query.all()
    return render_template('user/index.html',
                           equipments=equipments,
                           categories=categories,
                           query=q,
                           selected_category=category_id)


# ─────────────────────────────────────────────
#  Helper
# ─────────────────────────────────────────────
def _redirect_by_role():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('user.index'))


def _is_safe_next_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


