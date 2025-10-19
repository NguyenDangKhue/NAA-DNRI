# 🔥 HƯỚNG DẪN MỞ FIREWALL CHO LAB MANAGE

## 🚨 VẤN ĐỀ: Người khác không truy cập được http://192.168.1.201:5000

**Nguyên nhân chính**: Windows Firewall đang chặn kết nối từ bên ngoài.

---

## ✅ GIẢI PHÁP 1: Mở Firewall thủ công (Khuyến nghị)

### Bước 1: Mở Windows Defender Firewall
1. Nhấn `Windows + R`
2. Gõ `wf.msc` và nhấn Enter
3. Chọn "Inbound Rules" ở bên trái

### Bước 2: Tạo rule mới
1. Click chuột phải vào "Inbound Rules" → "New Rule..."
2. Chọn "Port" → Next
3. Chọn "TCP" → "Specific local ports" → Gõ `5000` → Next
4. Chọn "Allow the connection" → Next
5. Tick tất cả 3 ô (Domain, Private, Public) → Next
6. Đặt tên: "LabManage Port 5000" → Finish

### Bước 3: Tạo rule cho Python
1. Click chuột phải vào "Inbound Rules" → "New Rule..."
2. Chọn "Program" → Next
3. Chọn "This program path" → Browse đến file Python.exe
4. Chọn "Allow the connection" → Next
5. Tick tất cả 3 ô → Next
6. Đặt tên: "Python LabManage" → Finish

---

## ✅ GIẢI PHÁP 2: Tắt tạm thời Firewall (Nhanh nhất)

### Cách 1: Qua Control Panel
1. Mở Control Panel → System and Security → Windows Defender Firewall
2. Click "Turn Windows Defender Firewall on or off"
3. Tắt "Private network settings" và "Public network settings"
4. Click OK

### Cách 2: Qua PowerShell (Chạy với quyền Admin)
```powershell
# Tắt Firewall cho Private network
Set-NetFirewallProfile -Profile Private -Enabled False

# Tắt Firewall cho Public network  
Set-NetFirewallProfile -Profile Public -Enabled False
```

**⚠️ Lưu ý**: Nhớ bật lại Firewall sau khi test xong!

---

## ✅ GIẢI PHÁP 3: Chạy script với quyền Admin

1. **Chạy PowerShell với quyền Administrator**:
   - Nhấn `Windows + X`
   - Chọn "Windows PowerShell (Admin)"

2. **Chạy các lệnh sau**:
```powershell
# Mở port 5000
netsh advfirewall firewall add rule name="LabManage Port 5000" dir=in action=allow protocol=TCP localport=5000

# Cho phép Python
netsh advfirewall firewall add rule name="Python LabManage" dir=in action=allow program="python.exe"
```

---

## 🧪 KIỂM TRA SAU KHI SỬA

### Bước 1: Khởi động lại server
```bash
python -m app
```

### Bước 2: Test từ máy khác
- Mở trình duyệt trên máy khác
- Truy cập: `http://192.168.1.201:5000`
- Nếu thấy trang đăng nhập → Thành công! 🎉

### Bước 3: Nếu vẫn không được
1. **Kiểm tra IP có đúng không**:
   ```bash
   ipconfig
   ```

2. **Test ping từ máy khác**:
   ```bash
   ping 192.168.1.201
   ```

3. **Kiểm tra router có chặn không**

---

## 🔧 XỬ LÝ SỰ CỐ KHÁC

### Vấn đề: "Connection refused"
- **Nguyên nhân**: Server chưa chạy hoặc Firewall chặn
- **Giải pháp**: Làm theo hướng dẫn trên

### Vấn đề: "Timeout"
- **Nguyên nhân**: Router chặn hoặc mạng khác nhau
- **Giải pháp**: Kiểm tra tất cả thiết bị cùng mạng WiFi

### Vấn đề: "Page not found"
- **Nguyên nhân**: Server chạy nhưng không đúng cấu hình
- **Giải pháp**: Kiểm tra server có chạy `host='0.0.0.0'` không

---

## 📞 HỖ TRỢ

Nếu vẫn gặp vấn đề, hãy:
1. Chụp ảnh lỗi
2. Gửi thông tin mạng: `ipconfig`
3. Gửi kết quả: `netstat -an | findstr :5000`
