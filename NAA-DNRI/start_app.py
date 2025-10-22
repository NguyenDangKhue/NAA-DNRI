#!/usr/bin/env python3
"""
Script khởi động ứng dụng Flask
Sử dụng: python start_app.py
"""

import sys
import os

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    
    print("=" * 50)
    print("🚀 KHỞI ĐỘNG ỨNG DỤNG LAB MANAGEMENT")
    print("=" * 50)
    print("📁 Thư mục làm việc:", os.getcwd())
    print("🌐 Server sẽ chạy tại: http://localhost:5000")
    print("⏹️  Nhấn Ctrl+C để dừng server")
    print("=" * 50)
    
    app = create_app()
    
    # Chạy ứng dụng
    app.run(
        host='0.0.0.0',  # Cho phép truy cập từ các IP khác
        port=5000,       # Port 5000
        debug=True,      # Chế độ debug để dễ phát triển
        threaded=True    # Hỗ trợ multi-threading
    )
    
except ImportError as e:
    print("❌ Lỗi import:", str(e))
    print("💡 Hãy đảm bảo bạn đã cài đặt Flask và các dependencies")
    print("   Chạy: pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print("❌ Lỗi khởi động:", str(e))
    print("💡 Kiểm tra lại cấu hình và dependencies")
    sys.exit(1)
