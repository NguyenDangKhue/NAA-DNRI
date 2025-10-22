# 🚀 HƯỚNG DẪN KHỞI ĐỘNG ỨNG DỤNG

## Cách 1: Sử dụng file batch (Windows)
```bash
# Double-click vào file này hoặc chạy trong Command Prompt
start_server.bat
```

## Cách 2: Sử dụng Python script
```bash
python start_app.py
```

## Cách 3: Sử dụng wsgi.py trực tiếp
```bash
python wsgi.py
```

## Cách 4: Sử dụng Flask CLI
```bash
# Set environment variable
set FLASK_APP=wsgi.py
set FLASK_ENV=development

# Run Flask
flask run --host=0.0.0.0 --port=5000
```

## 🌐 Truy cập ứng dụng
Sau khi khởi động thành công, mở trình duyệt và truy cập:
- **Local**: http://localhost:5000
- **Network**: http://[IP_ADDRESS]:5000

## 🔧 Xử lý lỗi thường gặp

### Lỗi "Module not found"
```bash
pip install -r requirements.txt
```

### Lỗi "Permission denied"
- Chạy Command Prompt với quyền Administrator
- Hoặc sử dụng port khác: `python start_app.py --port 8080`

### Lỗi "Port already in use"
- Thay đổi port trong file start_app.py
- Hoặc tìm và kill process đang sử dụng port 5000

## 📁 Cấu trúc thư mục quan trọng
```
NAA-DNRI/
├── app/                 # Mã nguồn ứng dụng
├── data/               # Dữ liệu JSON
├── uploads/            # Files đã upload
├── static/             # CSS, JS, images
├── templates/          # HTML templates
├── wsgi.py            # Entry point chính
├── start_app.py       # Script khởi động Python
├── start_server.bat   # Script khởi động Windows
└── requirements.txt   # Dependencies
```

## 🛠️ Development Mode
Để phát triển, sử dụng:
```bash
python start_app.py
```
Server sẽ tự động reload khi có thay đổi code.

## 🚀 Production Mode
Để deploy production, sử dụng:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```
