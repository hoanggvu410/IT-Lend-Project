"""
models.py — Định nghĩa toàn bộ bảng DB dùng chung.
KHÔNG sửa file này nếu không thống nhất với cả nhóm.
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db, login_manager


def _now():
    """Trả về datetime UTC hiện tại (naive) — dùng thay cho datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


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
    # status: 'Available' | 'Maintenance'
    # Trạng thái 'Borrowed' không còn dùng — tính động qua Request
    status        = db.Column(db.String(20), nullable=False, default='Available')
    image_url     = db.Column(db.String(300), nullable=True)

    # ── Thông tin chi tiết thiết bị (toggle hiển thị) ──
    description   = db.Column(db.Text, nullable=True)   # Mô tả tổng quan
    usage         = db.Column(db.Text, nullable=True)   # Hướng dẫn sử dụng
    functions     = db.Column(db.Text, nullable=True)   # Tác dụng & chức năng
    specs         = db.Column(db.Text, nullable=True)   # Thông số kỹ thuật / cấu hình

    requests = db.relationship('Request', backref='equipment', lazy=True)

    def is_available_for(self, start_dt, end_dt):
        """
        Trả về True nếu thiết bị không có request Pending/Approved
        nào chồng lấp với khung giờ [start_dt, end_dt).
        Logic: xung đột khi existing.start < end_dt AND existing.end > start_dt
        """
        if self.status == 'Maintenance':
            return False
        conflict = Request.query.filter(
            Request.equipment_id == self.id,
            Request.status.in_(['Pending', 'Approved']),
            Request.borrow_date < end_dt,
            Request.return_date > start_dt
        ).first()
        return conflict is None

    def get_current_display_status(self):
        """
        Trạng thái hiển thị động tại thời điểm hiện tại:
        - 'Maintenance' nếu đang bảo trì
        - 'Busy'        nếu có Approved đang chạy ngay lúc này
        - 'Pending'     nếu có Pending đang chờ duyệt (không có Approved chạy)
        - 'Available'   nếu trống
        """
        if self.status == 'Maintenance':
            return 'Maintenance'
        now = _now()
        active = Request.query.filter(
            Request.equipment_id == self.id,
            Request.status == 'Approved',
            Request.borrow_date <= now,
            Request.return_date >= now
        ).first()
        if active:
            return 'Busy'
        pending = Request.query.filter(
            Request.equipment_id == self.id,
            Request.status == 'Pending'
        ).first()
        if pending:
            return 'Pending'
        return 'Available'

    def __repr__(self):
        return f'<Equipment {self.name} [{self.status}]>'


# ──────────────────────────────────────────────
#  Request — Theo dõi quy trình mượn/trả
# ──────────────────────────────────────────────
class Request(db.Model):
    __tablename__ = 'request'

    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('user.id'),      nullable=False)
    equipment_id        = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    # Dùng DateTime để hỗ trợ đặt lịch theo giờ
    borrow_date         = db.Column(db.DateTime, nullable=False)
    return_date         = db.Column(db.DateTime, nullable=False)
    actual_return_date  = db.Column(db.DateTime, nullable=True)  # Ghi nhận khi Admin bấm "Confirm Return"
    # status: 'Pending' | 'Approved' | 'Rejected' | 'Returned'
    status              = db.Column(db.String(20), nullable=False, default='Pending')
    admin_note          = db.Column(db.Text, nullable=True)
    created_at          = db.Column(db.DateTime, default=_now)

    @property
    def is_overdue(self):
        """Trả về True nếu đang mượn và đã quá giờ trả dự kiến."""
        return self.status == 'Approved' and self.return_date < _now()

    def __repr__(self):
        return f'<Request #{self.id} [{self.status}]>'

