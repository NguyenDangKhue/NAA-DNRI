@echo off
echo ========================================
echo    KIEM TRA NHANH LAB MANAGE
echo ========================================
echo.

echo 1. Kiem tra server co dang chay khong...
netstat -an | findstr :5000
if %errorlevel% == 0 (
    echo ✅ Server dang chay
) else (
    echo ❌ Server chua chay - Hay chay: python -m app
    pause
    exit
)

echo.
echo 2. Kiem tra IP hien tai...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    set ip=%%a
    goto :found
)
:found
echo IP hien tai: %ip%

echo.
echo 3. Test ket noi local...
python -c "import requests; print('✅ Local OK' if requests.get('http://localhost:5000').status_code == 200 else '❌ Local Loi')" 2>nul || echo ❌ Khong the test local

echo.
echo ========================================
echo    KET QUA
echo ========================================
echo.
echo 🌐 URL de chia se: http://%ip%:5000
echo.
echo 🔧 Neu nguoi khac khong vao duoc:
echo    1. Chay: disable_firewall_temp.bat (tat tam thoi Firewall)
echo    2. Hoac lam theo: HUONG_DAN_FIREWALL.md
echo.

pause
