@echo off
echo ================================================
echo 🚀 KHỞI ĐỘNG ỨNG DỤNG LAB MANAGEMENT
echo ================================================
echo 📁 Thư mục làm việc: %CD%
echo 🌐 Server sẽ chạy tại: http://localhost:5000
echo ⏹️  Nhấn Ctrl+C để dừng server
echo ================================================
echo.

REM Kiểm tra Python có tồn tại không
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không được tìm thấy!
    echo 💡 Hãy cài đặt Python và thêm vào PATH
    pause
    exit /b 1
)

REM Chạy ứng dụng
python start_app.py

REM Nếu có lỗi, hiển thị thông báo
if errorlevel 1 (
    echo.
    echo ❌ Có lỗi xảy ra khi khởi động ứng dụng
    echo 💡 Kiểm tra lại dependencies: pip install -r requirements.txt
    pause
)