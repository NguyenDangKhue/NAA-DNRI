@echo off
echo ========================================
echo    TAT TAM THOI FIREWALL
echo ========================================
echo.
echo ⚠️  CANH BAO: Script nay se TAT Windows Firewall
echo    Chi nen su dung de test, nho BAT LAI sau!
echo.
pause

echo Dang tat Windows Firewall...
netsh advfirewall set allprofiles state off

echo.
echo ========================================
echo    FIREWALL DA TAT
echo ========================================
echo.
echo ✅ Windows Firewall da duoc tat
echo.
echo 🧪 Bay gio hay test:
echo    1. Khoi dong server: python -m app  
echo    2. Test tu thiet bi khac: http://192.168.1.201:5000
echo.
echo ⚠️  NHO BAT LAI FIREWALL SAU KHI TEST XONG!
echo    Chay: enable_firewall.bat
echo.

pause
