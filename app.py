"""
app.py — Flask Application Factory (Entry Point)
Chạy:  python app.py
"""
import os
from flask import Flask, session
from extensions import db, bcrypt, login_manager, migrate


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
    migrate.init_app(app, db)

    # ── Đăng ký Blueprints ────────────────────────────────────────────────
    from auth import auth_bp
    from admin import admin_bp
    from user import user_bp

    app.register_blueprint(auth_bp)                        # /login, /register, /logout
    app.register_blueprint(admin_bp, url_prefix='/admin')  # /admin/*
    app.register_blueprint(user_bp)                        # /, /equipment/<id>, /my-requests

    # ── Context processor: inject cart_count vào mọi template ────────────
    @app.context_processor
    def inject_cart():
        from flask_login import current_user
        if current_user.is_authenticated and current_user.role == 'student':
            return {'cart_count': len(session.get('cart', []))}
        return {'cart_count': 0}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
