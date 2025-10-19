# Hướng dẫn chia sẻ ứng dụng qua mạng LAN WiFi

## 🚀 Cách khởi động server

### Phương pháp 1: Sử dụng script tự động (Khuyến nghị)
- **Windows**: Double-click vào file `start_server.bat`
- **Linux/Mac**: Chạy lệnh `chmod +x start_server.sh && ./start_server.sh`

### Phương pháp 2: Chạy thủ công
```bash
python -m app
```

## 🌐 Truy cập ứng dụng

### Từ máy tính hiện tại:
- URL: `http://localhost:5000`

### Từ các thiết bị khác trong mạng LAN:
- URL: `http://192.168.1.201:5000`
- **Lưu ý**: Thay `192.168.1.201` bằng địa chỉ IP thực tế của máy tính

## 📱 Cách tìm địa chỉ IP của máy tính

### Windows:
```cmd
ipconfig
```
Tìm dòng "IPv4 Address" trong phần adapter đang kết nối WiFi

### Linux/Mac:
```bash
ifconfig
```
hoặc
```bash
ip addr show
```

## 🔧 Cấu hình Firewall (nếu cần)

### Windows:
1. Mở Windows Defender Firewall
2. Chọn "Allow an app or feature through Windows Defender Firewall"
3. Click "Change settings" → "Allow another app"
4. Thêm Python.exe và cho phép qua cả Private và Public networks

### Linux:
```bash
sudo ufw allow 5000
```

## 📋 Kiểm tra kết nối

### Từ máy tính khác:
1. Mở trình duyệt web
2. Truy cập `http://192.168.1.201:5000`
3. Nếu thấy trang đăng nhập của LabManage thì thành công!

### Kiểm tra từ dòng lệnh:
```bash
# Windows
telnet 192.168.1.201 5000

# Linux/Mac
nc -zv 192.168.1.201 5000
```

## ⚠️ Lưu ý quan trọng

1. **Bảo mật**: Ứng dụng hiện tại chạy ở chế độ debug, không nên sử dụng trong môi trường production
2. **Mạng**: Đảm bảo tất cả thiết bị đều kết nối cùng mạng WiFi
3. **Firewall**: Có thể cần tắt tạm thời Windows Firewall nếu gặp vấn đề kết nối
4. **Port**: Port 5000 phải không bị sử dụng bởi ứng dụng khác

## 🛠️ Xử lý sự cố

### Không thể truy cập từ thiết bị khác:
1. Kiểm tra Firewall
2. Kiểm tra địa chỉ IP có đúng không
3. Thử ping từ thiết bị khác: `ping 192.168.1.201`
4. Kiểm tra port có bị chặn không

### Lỗi "Address already in use":
1. Tìm và tắt process đang sử dụng port 5000
2. Hoặc thay đổi port trong file `app/__main__.py`

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Địa chỉ IP có đúng không
2. Firewall có chặn không
3. Các thiết bị có cùng mạng không
4. Port 5000 có bị sử dụng không
