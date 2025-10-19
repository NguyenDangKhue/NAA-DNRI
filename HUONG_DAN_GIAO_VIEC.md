# Module Giao việc - Hướng dẫn sử dụng

## Tổng quan
Module "Giao việc" được thiết kế để giúp trưởng phòng và các thành viên trong phòng quản lý, phân công và bàn giao công việc một cách hiệu quả.

## Tính năng chính

### 1. Tạo công việc mới
- **Người có quyền**: Tất cả người dùng có quyền `task_assignment`
- **Chức năng**: 
  - Tạo công việc mới với tiêu đề, mô tả chi tiết
  - Giao việc cho người dùng cụ thể
  - Thiết lập độ ưu tiên (Cao/Trung bình/Thấp)
  - Đặt hạn hoàn thành
  - Phân loại công việc theo danh mục
  - Thêm ghi chú bổ sung

### 2. Quản lý công việc
- **Danh sách tất cả công việc**: Xem tất cả công việc trong hệ thống
- **Công việc của tôi**: Xem và quản lý các công việc được giao cho bạn
- **Tìm kiếm và lọc**: Tìm kiếm theo từ khóa, lọc theo trạng thái, độ ưu tiên, người được giao
- **Phân trang**: Hiển thị công việc theo trang để dễ quản lý

### 3. Cập nhật trạng thái công việc
- **Chờ xử lý** → **Đang xử lý**: Người được giao có thể bắt đầu công việc
- **Đang xử lý** → **Hoàn thành**: Đánh dấu công việc đã hoàn thành
- **Hủy**: Hủy công việc nếu không cần thiết

### 4. Bàn giao công việc
- **Chức năng**: Cho phép người được giao việc bàn giao cho người khác
- **Lịch sử bàn giao**: Lưu trữ toàn bộ lịch sử bàn giao với ghi chú
- **Quyền hạn**: Chỉ người được giao việc mới có thể bàn giao

### 5. Thống kê và báo cáo
- **Thống kê cá nhân**: Số lượng công việc theo từng trạng thái
- **Thống kê tổng quan**: Tổng quan về tất cả công việc trong hệ thống
- **Xuất Excel**: Xuất danh sách công việc ra file CSV để báo cáo

## Quy trình sử dụng

### Cho Trưởng phòng:
1. **Tạo công việc**: Vào module Giao việc → Tạo công việc mới
2. **Giao việc**: Chọn người thực hiện và thiết lập các thông tin cần thiết
3. **Theo dõi**: Xem danh sách tất cả công việc để theo dõi tiến độ
4. **Quản lý**: Chỉnh sửa, xóa công việc khi cần thiết

### Cho Nhân viên:
1. **Xem công việc**: Vào "Công việc của tôi" để xem các công việc được giao
2. **Bắt đầu**: Cập nhật trạng thái từ "Chờ xử lý" sang "Đang xử lý"
3. **Hoàn thành**: Cập nhật trạng thái sang "Hoàn thành" khi xong việc
4. **Bàn giao**: Nếu cần, có thể bàn giao công việc cho đồng nghiệp

## Các trạng thái công việc

- **Chờ xử lý** (pending): Công việc mới được tạo, chưa bắt đầu
- **Đang xử lý** (in_progress): Công việc đang được thực hiện
- **Hoàn thành** (completed): Công việc đã hoàn thành
- **Đã hủy** (cancelled): Công việc bị hủy

## Độ ưu tiên

- **Cao** (high): Công việc khẩn cấp, cần xử lý ngay
- **Trung bình** (medium): Công việc bình thường
- **Thấp** (low): Công việc không khẩn cấp

## Quyền hạn

- **Xem**: Tất cả người dùng có quyền `task_assignment`
- **Tạo**: Tất cả người dùng có quyền `task_assignment`
- **Chỉnh sửa**: Tất cả người dùng có quyền `task_assignment`
- **Xóa**: Tất cả người dùng có quyền `task_assignment`
- **Cập nhật trạng thái**: Chỉ người được giao việc
- **Bàn giao**: Chỉ người được giao việc

## Lưu ý quan trọng

1. **Bàn giao công việc**: Sau khi bàn giao, bạn sẽ không còn quyền chỉnh sửa công việc đó trừ khi được bàn giao lại
2. **Lịch sử bàn giao**: Tất cả các lần bàn giao đều được ghi lại với thời gian và ghi chú
3. **Hạn hoàn thành**: Có thể đặt hạn hoàn thành để theo dõi tiến độ
4. **Tìm kiếm**: Hỗ trợ tìm kiếm theo tiêu đề, mô tả, danh mục và ghi chú

## Hỗ trợ

Nếu gặp vấn đề hoặc cần hỗ trợ, vui lòng liên hệ với quản trị viên hệ thống.
