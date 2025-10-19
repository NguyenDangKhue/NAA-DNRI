@echo off
echo ========================================
echo    CAP HINH FIREWALL CHO LAB MANAGE
echo ========================================
echo.

echo Dang cap hinh Windows Firewall...
echo.

REM Mở port 5000 cho Python
echo 1. Mo port 5000 cho Python...
netsh advfirewall firewall add rule name="LabManage Python Server" dir=in action=allow protocol=TCP localport=5000

REM Mở port 5000 cho tất cả ứng dụng
echo 2. Mo port 5000 cho tat ca ung dung...
netsh advfirewall firewall add rule name="LabManage Port 5000" dir=in action=allow protocol=TCP localport=5000

REM Cho phép Python qua Firewall
echo 3. Cho phep Python qua Firewall...
netsh advfirewall firewall add rule name="Python LabManage" dir=in action=allow program="%PYTHON%" enable=yes

echo.
echo ========================================
echo    KET QUA
echo ========================================
echo.

echo Kiem tra cac rule da tao:
netsh advfirewall firewall show rule name="LabManage Python Server"
echo.
netsh advfirewall firewall show rule name="LabManage Port 5000"
echo.

echo ========================================
echo    HUONG DAN TIEP THEO
echo ========================================
echo.
echo 1. Khoi dong lai server: start_server.bat
echo 2. Test tu thiet bi khac: http://192.168.1.201:5000
echo 3. Neu van khong vao duoc, thu tat tam thoi Windows Firewall
echo.

pause
