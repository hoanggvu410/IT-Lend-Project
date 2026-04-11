"""
models.py — Định nghĩa toàn bộ bảng DB dùng chung.
KHÔNG sửa file này nếu không thống nhất với cả nhóm.
"""
from datetime import datetime, date
from flask_login import UserMixin
from extensions import db, login_manager


# ──────────────────────────────────────────────
#  User loader (bắt buộc cho Flask-Login)
# ──────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ──────────────────────────────────────────────
#  User — Tài khoản & phân quyền
# ──────────────────────────────────────────────
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # role: 'admin' hoặc 'student'
    role          = db.Column(db.String(20),  nullable=False, default='student')

    requests = db.relationship('Request', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'


# ──────────────────────────────────────────────
#  Category — Phân loại thiết bị
# ──────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = 'category'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    equipments = db.relationship('Equipment', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


# ──────────────────────────────────────────────
#  Equipment — Thông tin thiết bị
# ──────────────────────────────────────────────
class Equipment(db.Model):
    __tablename__ = 'equipment'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(200), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    category_id   = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    # status: 'Available' | 'Borrowed' | 'Maintenance'
    status        = db.Column(db.String(20), nullable=False, default='Available')
    image_url     = db.Column(db.String(300), nullable=True)

    requests = db.relationship('Request', backref='equipment', lazy=True)

    def __repr__(self):
        return f'<Equipment {self.name} [{self.status}]>'


# ──────────────────────────────────────────────
#  Request — Theo dõi quy trình mượn/trả
# ──────────────────────────────────────────────
class Request(db.Model):
    __tablename__ = 'request'

    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, db.ForeignKey('user.id'),      nullable=False)
    equipment_id       = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    borrow_date        = db.Column(db.Date, nullable=False)
    return_date        = db.Column(db.Date, nullable=False)
    actual_return_date = db.Column(db.Date, nullable=True)   # Ghi nhận khi Admin bấm "Confirm Return"
    # status: 'Pending' | 'Approved' | 'Rejected' | 'Returned'
    status             = db.Column(db.String(20), nullable=False, default='Pending')
    admin_note         = db.Column(db.Text, nullable=True)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_overdue(self):
        """Trả về True nếu đang mượn và đã quá ngày trả dự kiến."""
        return self.status == 'Approved' and self.return_date < date.today()

    def __repr__(self):
        return f'<Request #{self.id} [{self.status}]>'

