#!/usr/bin/env python3
"""
Script hiển thị thông tin mạng để chia sẻ ứng dụng LabManage
"""

import socket
import subprocess
import platform
import sys

def get_local_ip():
    """Lấy địa chỉ IP local của máy tính"""
    try:
        # Tạo socket để kết nối với một địa chỉ bên ngoài
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Không thể xác định"

def get_network_info():
    """Lấy thông tin mạng chi tiết"""
    system = platform.system()
    
    if system == "Windows":
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp1252')
            return result.stdout
        except:
            return "Không thể lấy thông tin mạng"
    else:
        try:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            return result.stdout
        except:
            return "Không thể lấy thông tin mạng"

def main():
    print("=" * 60)
    print("    THÔNG TIN CHIA SẺ ỨNG DỤNG LAB MANAGE")
    print("=" * 60)
    print()
    
    # Lấy địa chỉ IP
    local_ip = get_local_ip()
    port = 5000
    
    print(f"🌐 Địa chỉ IP của máy tính: {local_ip}")
    print(f"🔌 Port: {port}")
    print()
    
    print("📱 Cách truy cập từ thiết bị khác:")
    print(f"   • URL: http://{local_ip}:{port}")
    print(f"   • Hoặc: http://{local_ip}:{port}/login")
    print()
    
    print("💻 Cách truy cập từ máy tính này:")
    print("   • URL: http://localhost:5000")
    print("   • Hoặc: http://127.0.0.1:5000")
    print()
    
    print("🚀 Để khởi động server:")
    print("   • Windows: Double-click start_server.bat")
    print("   • Linux/Mac: ./start_server.sh")
    print("   • Thủ công: python -m app")
    print()
    
    print("⚠️  Lưu ý:")
    print("   • Đảm bảo tất cả thiết bị cùng mạng WiFi")
    print("   • Kiểm tra Firewall nếu không truy cập được")
    print("   • Địa chỉ IP có thể thay đổi khi khởi động lại")
    print()
    
    print("=" * 60)
    print("Thông tin mạng chi tiết:")
    print("=" * 60)
    network_info = get_network_info()
    print(network_info)

if __name__ == "__main__":
    main()
