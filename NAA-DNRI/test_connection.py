#!/usr/bin/env python3
"""
Script test kết nối mạng cho LabManage
"""

import socket
import requests
import time
import threading
from urllib.parse import urljoin

def test_port_open(host, port, timeout=3):
    """Test xem port có mở không"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def test_http_response(url, timeout=5):
    """Test HTTP response"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200, response.status_code
    except requests.exceptions.ConnectionError:
        return False, "Connection Error"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 50)
    print("    TEST KẾT NỐI LAB MANAGE")
    print("=" * 50)
    print()
    
    # Thông tin server
    local_ip = "192.168.1.201"
    port = 5000
    local_url = f"http://localhost:{port}"
    network_url = f"http://{local_ip}:{port}"
    
    print(f"🔍 Đang test kết nối...")
    print(f"   • Local: {local_url}")
    print(f"   • Network: {network_url}")
    print()
    
    # Test port local
    print("1️⃣ Test port local (localhost:5000)...")
    if test_port_open("localhost", port):
        print("   ✅ Port local mở")
        
        # Test HTTP response
        success, status = test_http_response(local_url)
        if success:
            print(f"   ✅ HTTP response OK (Status: {status})")
        else:
            print(f"   ❌ HTTP response lỗi: {status}")
    else:
        print("   ❌ Port local không mở")
    print()
    
    # Test port network
    print("2️⃣ Test port network (192.168.1.201:5000)...")
    if test_port_open(local_ip, port):
        print("   ✅ Port network mở")
        
        # Test HTTP response
        success, status = test_http_response(network_url)
        if success:
            print(f"   ✅ HTTP response OK (Status: {status})")
        else:
            print(f"   ❌ HTTP response lỗi: {status}")
    else:
        print("   ❌ Port network không mở")
    print()
    
    print("=" * 50)
    print("KẾT QUẢ:")
    print("=" * 50)
    
    local_ok = test_port_open("localhost", port)
    network_ok = test_port_open(local_ip, port)
    
    if local_ok and network_ok:
        print("🎉 Server hoạt động tốt!")
        print(f"   • Truy cập từ máy này: {local_url}")
        print(f"   • Truy cập từ thiết bị khác: {network_url}")
    elif local_ok:
        print("⚠️  Server chỉ hoạt động local")
        print("   • Cần kiểm tra Firewall")
        print("   • Cần kiểm tra cấu hình network")
    else:
        print("❌ Server chưa khởi động")
        print("   • Chạy: python -m app")
        print("   • Hoặc: start_server.bat")

if __name__ == "__main__":
    main()
