"""
main.py — Entry point (alias cho app.py)
Chạy:  python main.py   hoặc   python app.py
"""
from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
