"""
app.py — Flask Application Factory (Entry Point)
Chạy:  python app.py
"""
import os
from flask import Flask
from extensions import db, bcrypt, login_manager


def create_app():
    app = Flask(__name__)

    # ── Cấu hình ──────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'it-lend-dev-secret-2024-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///it_lend.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Khởi tạo extensions ───────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # ── Đăng ký Blueprints ────────────────────────────────────────────────
    from auth import auth_bp
    from admin import admin_bp
    from user import user_bp

    app.register_blueprint(auth_bp)                    # /login, /register, /logout, /search
    app.register_blueprint(admin_bp, url_prefix='/admin')  # /admin/*, /admin/equipments, ...
    app.register_blueprint(user_bp)                    # /, /equipment/<id>, /my-requests

    # ── Tạo bảng DB nếu chưa có ──────────────────────────────────────────
    with app.app_context():
        import models  # noqa: F401 — đảm bảo models được nạp trước db.create_all()
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

