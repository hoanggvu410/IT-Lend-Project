"""
seed.py — Tạo dữ liệu mẫu để test giao diện.
Chạy một lần:  python seed.py
WARNING: Sẽ xóa toàn bộ dữ liệu cũ!
"""
from app import create_app
from extensions import db, bcrypt
from models import User, Category, Equipment


def seed():
    app = create_app()
    with app.app_context():
        print("🗑️  Xóa dữ liệu cũ...")
        db.drop_all()
        db.create_all()

        # ── Users ──────────────────────────────────────────────────────────
        admin = User(
            username='admin',
            email='admin@itlend.vn',
            password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin'
        )
        sv001 = User(
            username='sv001',
            email='sv001@student.edu.vn',
            password_hash=bcrypt.generate_password_hash('student123').decode('utf-8'),
            role='student'
        )
        sv002 = User(
            username='sv002',
            email='sv002@student.edu.vn',
            password_hash=bcrypt.generate_password_hash('student123').decode('utf-8'),
            role='student'
        )
        db.session.add_all([admin, sv001, sv002])
        db.session.commit()

        # ── Categories ─────────────────────────────────────────────────────
        categories = [
            Category(name='Laptop',        description='Máy tính xách tay phục vụ thực hành'),
            Category(name='Máy chiếu',     description='Projector dùng cho giảng dạy và thuyết trình'),
            Category(name='Kit IoT',       description='Bộ kit thực hành IoT, Arduino, Raspberry Pi'),
            Category(name='Máy tính bảng', description='Tablet dùng cho thực hành và thuyết trình'),
        ]
        db.session.add_all(categories)
        db.session.commit()

        # ── Equipment ──────────────────────────────────────────────────────
        equipments = [
            Equipment(name='Laptop Dell Latitude 5420',   serial_number='DELL-001', category_id=1, status='Available'),
            Equipment(name='Laptop Dell Latitude 5420',   serial_number='DELL-002', category_id=1, status='Borrowed'),
            Equipment(name='Laptop HP ProBook 450 G9',    serial_number='HP-001',   category_id=1, status='Available'),
            Equipment(name='Laptop Lenovo ThinkPad E14',  serial_number='LEN-001',  category_id=1, status='Available'),
            Equipment(name='Laptop Asus VivoBook 15',     serial_number='ASUS-001', category_id=1, status='Maintenance'),
            Equipment(name='Máy chiếu Epson EB-X41',      serial_number='EPS-001',  category_id=2, status='Available'),
            Equipment(name='Máy chiếu BenQ MH550',        serial_number='BEN-001',  category_id=2, status='Available'),
            Equipment(name='Máy chiếu ViewSonic PA503W',  serial_number='VIEW-001', category_id=2, status='Borrowed'),
            Equipment(name='Kit Arduino Uno R3',           serial_number='ARD-001',  category_id=3, status='Available'),
            Equipment(name='Kit Arduino Mega 2560',        serial_number='ARD-002',  category_id=3, status='Available'),
            Equipment(name='Raspberry Pi 4B 4GB',          serial_number='RPI-001',  category_id=3, status='Available'),
            Equipment(name='ESP32 DevKit V1',              serial_number='ESP-001',  category_id=3, status='Borrowed'),
            Equipment(name='iPad Air 5th Gen (Wi-Fi)',     serial_number='IPAD-001', category_id=4, status='Available'),
            Equipment(name='Samsung Galaxy Tab S8',        serial_number='SAM-001',  category_id=4, status='Available'),
        ]
        db.session.add_all(equipments)
        db.session.commit()

        print("✅ Seed hoàn tất!")
        print("─" * 40)
        print("  Tài khoản Admin  : admin / admin123")
        print("  Tài khoản SV #1  : sv001 / student123")
        print("  Tài khoản SV #2  : sv002 / student123")
        print("─" * 40)
        print(f"  Categories : {Category.query.count()}")
        print(f"  Equipments : {Equipment.query.count()}")
        print(f"  Users      : {User.query.count()}")


if __name__ == '__main__':
    seed()

