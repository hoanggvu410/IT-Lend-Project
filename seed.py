"""
seed.py — Tạo dữ liệu mẫu để test giao diện.
Chạy một lần:  python seed.py
WARNING: Sẽ xóa toàn bộ dữ liệu cũ!
"""
from datetime import datetime, timedelta, timezone
from app import create_app
from extensions import db, bcrypt
from models import User, Category, Equipment, Request


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
            Equipment(
                name='Laptop Dell Latitude 5420', serial_number='DELL-001', category_id=1,
                status='Available',
                description='Laptop doanh nghiệp Dell Latitude 5420, phù hợp lập trình và đồ hoạ nhẹ.',
                functions='Lập trình, soạn thảo văn bản, xử lý dữ liệu, trình chiếu.',
                usage='Bật nguồn, đăng nhập tài khoản sinh viên. Tắt máy và bàn giao đầy đủ phụ kiện khi trả.',
                specs='CPU: Intel Core i5-1135G7\nRAM: 8GB DDR4\nSSD: 256GB NVMe\nMàn hình: 14" FHD\nHĐH: Windows 11 Pro'
            ),
            Equipment(
                name='Laptop Dell Latitude 5420', serial_number='DELL-002', category_id=1,
                status='Available',
                description='Laptop doanh nghiệp Dell Latitude 5420.',
                specs='CPU: Intel Core i5-1135G7\nRAM: 8GB DDR4\nSSD: 256GB NVMe\nMàn hình: 14" FHD'
            ),
            Equipment(
                name='Laptop HP ProBook 450 G9', serial_number='HP-001', category_id=1,
                status='Available',
                description='Laptop HP ProBook 450 G9, thiết kế bền bỉ cho môi trường học tập.',
                functions='Lập trình web, xử lý văn bản, họp online, đồ hoạ cơ bản.',
                usage='Sạc pin trước khi mượn. Không tự ý cài thêm phần mềm. Trả máy với pin còn trên 20%.',
                specs='CPU: Intel Core i5-1235U\nRAM: 8GB DDR4\nSSD: 512GB\nMàn hình: 15.6" FHD\nHĐH: Windows 11'
            ),
            Equipment(
                name='Laptop Lenovo ThinkPad E14', serial_number='LEN-001', category_id=1,
                status='Available',
                description='ThinkPad E14 — dòng laptop bền nổi tiếng của Lenovo.',
                specs='CPU: AMD Ryzen 5 5500U\nRAM: 16GB DDR4\nSSD: 512GB\nMàn hình: 14" FHD IPS'
            ),
            Equipment(
                name='Laptop Asus VivoBook 15', serial_number='ASUS-001', category_id=1,
                status='Maintenance',
                description='Laptop Asus VivoBook 15 đang trong quá trình bảo trì.'
            ),
            Equipment(
                name='Máy chiếu Epson EB-X41', serial_number='EPS-001', category_id=2,
                status='Available',
                description='Máy chiếu Epson EB-X41 độ sáng 3600 lumens, phù hợp phòng học.',
                functions='Trình chiếu slide, video, màn hình máy tính qua HDMI/VGA.',
                usage='Kết nối nguồn điện 220V. Bật Remote → nhấn Power. Chỉnh zoom và focus. Sau dùng tắt Remote trước khi rút nguồn.',
                specs='Độ sáng: 3600 lumens\nĐộ phân giải: XGA (1024×768)\nKết nối: HDMI, VGA, USB\nTỉ lệ tương phản: 15000:1'
            ),
            Equipment(
                name='Máy chiếu BenQ MH550', serial_number='BEN-001', category_id=2,
                status='Available',
                description='Máy chiếu BenQ MH550 Full HD, lý tưởng cho hội nghị và lớp học.',
                specs='Độ sáng: 3500 lumens\nĐộ phân giải: 1080p Full HD\nKết nối: HDMI×2, VGA'
            ),
            Equipment(
                name='Máy chiếu ViewSonic PA503W', serial_number='VIEW-001', category_id=2,
                status='Available',
                description='Máy chiếu ViewSonic PA503W WXGA nhỏ gọn.',
                specs='Độ sáng: 3800 lumens\nĐộ phân giải: WXGA (1280×800)\nKết nối: HDMI, VGA'
            ),
            Equipment(
                name='Kit Arduino Uno R3', serial_number='ARD-001', category_id=3,
                status='Available',
                description='Bộ kit Arduino Uno R3 đầy đủ linh kiện thực hành IoT cơ bản.',
                functions='Lập trình vi điều khiển, giao tiếp cảm biến, điều khiển thiết bị ngoại vi.',
                usage='Cài Arduino IDE. Kết nối USB. Nạp code qua IDE. Không cấp nguồn vượt 5V vào chân GPIO.',
                specs='Vi điều khiển: ATmega328P\nXung nhịp: 16 MHz\nRAM: 2KB\nFlash: 32KB\nGiao tiếp: USB, I2C, SPI, UART'
            ),
            Equipment(
                name='Kit Arduino Mega 2560', serial_number='ARD-002', category_id=3,
                status='Available',
                description='Arduino Mega 2560 với nhiều chân GPIO hơn, phù hợp dự án phức tạp.',
                specs='Vi điều khiển: ATmega2560\nXung nhịp: 16 MHz\nRAM: 8KB\nFlash: 256KB\nSố chân I/O: 54'
            ),
            Equipment(
                name='Raspberry Pi 4B 4GB', serial_number='RPI-001', category_id=3,
                status='Available',
                description='Máy tính nhúng Raspberry Pi 4B RAM 4GB, chạy Linux đầy đủ.',
                functions='Máy chủ web nhúng, xử lý ảnh, AI/ML edge, IoT gateway.',
                usage='Cắm thẻ nhớ có sẵn OS. Cấp nguồn USB-C 5V/3A. Kết nối qua SSH hoặc màn hình HDMI.',
                specs='CPU: ARM Cortex-A72 (4 nhân)\nRAM: 4GB LPDDR4\nHệ điều hành: Raspberry Pi OS\nKết nối: WiFi, Bluetooth, Gigabit Ethernet, USB 3.0'
            ),
            Equipment(
                name='ESP32 DevKit V1', serial_number='ESP-001', category_id=3,
                status='Available',
                description='Module ESP32 tích hợp WiFi + Bluetooth, lý tưởng cho dự án IoT.',
                specs='CPU: Xtensa LX6 dual-core\nXung: 240 MHz\nWiFi: 802.11 b/g/n\nBluetooth: BT 4.2 + BLE\nGPIO: 30 chân'
            ),
            Equipment(
                name='iPad Air 5th Gen (Wi-Fi)', serial_number='IPAD-001', category_id=4,
                status='Available',
                description='iPad Air thế hệ 5, màn hình Liquid Retina 10.9 inch.',
                functions='Trình chiếu, vẽ kỹ thuật số (kết hợp Apple Pencil), họp online.',
                usage='Unlock bằng mã PIN được cấp. Sạc đầy trước khi trả. Không cài app cá nhân.',
                specs='CPU: Apple M1\nMàn hình: 10.9" Liquid Retina\nRAM: 8GB\nBộ nhớ: 64GB\nHĐH: iPadOS 16'
            ),
            Equipment(
                name='Samsung Galaxy Tab S8', serial_number='SAM-001', category_id=4,
                status='Available',
                description='Samsung Galaxy Tab S8 màn hình AMOLED 11 inch, kèm S Pen.',
                specs='CPU: Snapdragon 8 Gen 1\nMàn hình: 11" LTPS TFT 120Hz\nRAM: 8GB\nBộ nhớ: 128GB\nHĐH: Android 12'
            ),
        ]
        db.session.add_all(equipments)
        db.session.commit()

        # ── Sample Requests (datetime) ─────────────────────────────────────
        # Tạo vài request mẫu để test timeline
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sv1 = User.query.filter_by(username='sv001').first()
        sv2 = User.query.filter_by(username='sv002').first()
        hp  = Equipment.query.filter_by(serial_number='HP-001').first()
        eps = Equipment.query.filter_by(serial_number='EPS-001').first()

        sample_requests = [
            # sv001 đặt Laptop HP ProBook ngày mai 8h-12h (Approved)
            Request(user_id=sv1.id, equipment_id=hp.id,
                    borrow_date=now.replace(hour=8, minute=0, second=0) + timedelta(days=1),
                    return_date=now.replace(hour=12, minute=0, second=0) + timedelta(days=1),
                    status='Approved'),
            # sv002 đặt Laptop HP ProBook ngày mai 14h-17h (Pending)
            Request(user_id=sv2.id, equipment_id=hp.id,
                    borrow_date=now.replace(hour=14, minute=0, second=0) + timedelta(days=1),
                    return_date=now.replace(hour=17, minute=0, second=0) + timedelta(days=1),
                    status='Pending'),
            # sv001 đặt Máy chiếu ngày kia cả ngày (Pending)
            Request(user_id=sv1.id, equipment_id=eps.id,
                    borrow_date=now.replace(hour=9, minute=0, second=0) + timedelta(days=2),
                    return_date=now.replace(hour=18, minute=0, second=0) + timedelta(days=2),
                    status='Pending'),
        ]
        db.session.add_all(sample_requests)
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
        print(f"  Requests   : {Request.query.count()}")


if __name__ == '__main__':
    seed()

