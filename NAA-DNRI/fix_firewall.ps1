# Script mở Firewall cho LabManage
# Cần chạy với quyền Administrator

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    CAP HINH FIREWALL CHO LAB MANAGE" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra quyền Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Script này cần quyền Administrator!" -ForegroundColor Red
    Write-Host "Vui lòng chạy PowerShell với quyền Administrator" -ForegroundColor Yellow
    Write-Host "Nhấn Windows + X, chọn 'Windows PowerShell (Admin)'" -ForegroundColor Yellow
    Read-Host "Nhấn Enter để thoát"
    exit 1
}

Write-Host "✅ Đang cấu hình Firewall..." -ForegroundColor Green

try {
    # Mở port 5000 cho LabManage
    Write-Host "1. Mở port 5000..." -ForegroundColor Yellow
    New-NetFirewallRule -DisplayName "LabManage Port 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Any
    
    # Cho phép Python qua Firewall
    Write-Host "2. Cho phép Python..." -ForegroundColor Yellow
    $pythonPath = (Get-Command python).Source
    New-NetFirewallRule -DisplayName "Python LabManage" -Direction Inbound -Program $pythonPath -Action Allow -Profile Any
    
    Write-Host ""
    Write-Host "✅ Đã cấu hình Firewall thành công!" -ForegroundColor Green
    Write-Host ""
    
    # Hiển thị các rule đã tạo
    Write-Host "📋 Các rule đã tạo:" -ForegroundColor Cyan
    Get-NetFirewallRule -DisplayName "*LabManage*" | Format-Table DisplayName, Direction, Action, Protocol, LocalPort
    
} catch {
    Write-Host "❌ Lỗi khi cấu hình Firewall: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Hướng dẫn thủ công:" -ForegroundColor Yellow
    Write-Host "1. Mở Windows Defender Firewall" -ForegroundColor White
    Write-Host "2. Chọn 'Inbound Rules' → 'New Rule'" -ForegroundColor White
    Write-Host "3. Chọn 'Port' → TCP → Port 5000 → Allow" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    HƯỚNG DẪN TIẾP THEO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Khởi động lại server: python -m app" -ForegroundColor White
Write-Host "2. Test từ thiết bị khác: http://192.168.1.201:5000" -ForegroundColor White
Write-Host "3. Nếu vẫn không được, thử tắt tạm thời Firewall" -ForegroundColor White
Write-Host ""

Read-Host "Nhấn Enter để thoát"
