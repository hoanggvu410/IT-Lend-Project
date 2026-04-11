# IT-Lend 🖥️
### Hệ thống quản lý mượn thiết bị Lab/Khoa

---

## 🚀 Cài đặt & Chạy nhanh

```bash
# 1. Clone repo
git clone <repo-url>
cd IT-Lending-Project

# 2. Tạo môi trường ảo & cài thư viện
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 3. Tạo DB + seed dữ liệu mẫu (chạy 1 lần)
python seed.py

# 4. Chạy ứng dụng
python app.py
```

Truy cập: **http://127.0.0.1:5000**

---

## 👤 Tài khoản mẫu (sau khi seed)

| Role    | Username | Password   |
|---------|----------|------------|
| Admin   | admin    | admin123   |
| Student | sv001    | student123 |

---

## 📁 Cấu trúc dự án

```
IT-Lending-Project/
├── app.py              ← Flask app factory (entry point)
├── models.py           ← DB models dùng chung (User, Equipment, Category, Request)
├── extensions.py       ← Flask extensions (db, bcrypt, login_manager)
├── seed.py             ← Script tạo dữ liệu mẫu
├── requirements.txt
├── .gitignore
│
├── auth/               ← Module Auth (Thành viên C)
│   ├── __init__.py
│   └── routes.py       ← /login, /register, /logout, /search
│
├── admin/              ← Module Admin (Thành viên A)
│   ├── __init__.py
│   └── routes.py       ← /admin/*, CRUD thiết bị, duyệt yêu cầu
│
├── user/               ← Module User (Thành viên B)
│   ├── __init__.py
│   └── routes.py       ← /, /equipment/<id>, /my-requests
│
├── templates/
│   ├── base.html       ← Layout dùng chung (sidebar + Bootstrap 5)
│   ├── auth/           ← login.html, register.html
│   ├── admin/          ← dashboard.html, equipments.html, ...
│   └── user/           ← index.html, equipment_detail.html, my_requests.html
│
└── static/
    ├── css/style.css
    ├── js/main.js
    └── images/
```

---

## 🗂️ Phân chia công việc

| Thành viên | Module | Branch |
|---|---|---|
| **Thành viên A** | Admin Dashboard, CRUD thiết bị, duyệt yêu cầu | `feature/admin` |
| **Thành viên B** | Giao diện người dùng, form mượn, lịch sử | `feature/user` |
| **Thành viên C** | Auth, Đăng nhập/Đăng ký, Tìm kiếm, Validation | `feature/logic-core` |

---

## 🗃️ Database Schema

| Bảng | Các trường chính |
|---|---|
| **User** | id, username, email, password_hash, role (admin/student) |
| **Category** | id, name, description |
| **Equipment** | id, name, serial_number, category_id, status (Available/Borrowed/Maintenance), image_url |
| **Request** | id, user_id, equipment_id, borrow_date, return_date, actual_return_date, status (Pending/Approved/Rejected/Returned), admin_note |

---

## 🎨 Bảng màu chuẩn

| Vai trò | Mã màu |
|---|---|
| Chủ đạo (Sidebar) | `#2C3E50` Midnight Blue |
| Hành động (Button) | `#3498DB` Sky Blue |
| Thành công | `#27AE60` Green |
| Cảnh báo / Lỗi | `#E74C3C` Red |

---

## ⚙️ Quy tắc làm việc nhóm

1. Mỗi thành viên làm việc trên **branch riêng** (`feature/admin`, `feature/user`, `feature/logic-core`).
2. **Không sửa** `models.py`, `extensions.py`, `base.html` nếu không thông qua nhóm.
3. Merge về `develop` khi hoàn thành từng tính năng, merge về `main` khi hoàn thiện.
4. Commit message theo format: `feat(module): mô tả ngắn` — ví dụ: `feat(admin): add equipment CRUD`

