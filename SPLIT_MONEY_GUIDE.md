# 💰 Hướng Dẫn Tính Toán Chia Tiền

## 📋 Tổng Quan

Chức năng `/split` giúp tự động tính toán chi phí giữa **Trung** và **Chung** dựa trên cột **"Loại"** trong Google Sheets. Hệ thống này thay thế các con số (1, 2, 3) bằng các tên gọi trực quan để tránh nhầm lẫn.

## 🏷️ Hệ Thống Phân Loại

### Các Loại Chi Phí

| Loại | Người Dùng | Cách Chia |
|------|------------|-----------|
| **Cả hai** | Trung + Chung | Chia đều 50/50 |
| **Trung** | Chỉ Trung | Trung chịu 100% |
| **Chung** | Chỉ Chung | Chung chịu 100% |

> [!NOTE]
> Bot vẫn hỗ trợ nhập nhanh bằng số cho các giao dịch cũ:
> - **1** tương đương **Cả hai**
> - **2** tương đương **Trung**
> - **3** tương đương **Chung**

## 🎯 Cách Sử Dụng

### Bước 1: Nhập Dữ Liệu
Trên Google Sheets, hãy chọn từ menu thả xuống (Dropdown) ở cột **G (Loại)**:

| Ngày | Mô tả | Số tiền | ... | Loại |
|------|-------|---------|-----|------|
| 05/05 | Ăn sáng | 100000 | ... | **Cả hai** |
| 05/05 | Mua game | 250000 | ... | **Trung** |

### Bước 2: Chạy Lệnh
Trong Telegram, sử dụng các lệnh:
- `/split`: Tính toán cho tháng hiện tại.
- `/split_month`: Xem danh sách và tính toán cho các tháng trước.

### Bước 3: Đọc Kết Quả
Bot sẽ gửi báo cáo chi tiết:
1. **Tổng chi tiêu**: Tổng số tiền đã ghi nhận trong tháng.
2. **Chi tiết theo loại**: Gom nhóm các khoản chi chung và chi riêng.
3. **Tình hình thực tế**: Ai đã bỏ ra bao nhiêu tiền túi.
4. **Kết quả & Gợi ý**: Ai cần chuyển tiền cho ai để cân bằng.

## 📊 Ví Dụ Báo Cáo

```
💰 TÍNH TOÁN CHIA TIỀN - THÁNG 5 2026

📊 Tổng chi tiêu tháng: 1,710,000 VNĐ

📋 CHI TIẾT THEO LOẠI:
🔹 Cả hai (Trung + Chung): 1,400,000 VNĐ
🔹 Trung: 250,000 VNĐ
🔹 Chung: 60,000 VNĐ

👤 TÌNH HÌNH THỰC TẾ:
• Trung: Đã trả 1,150,000 VNĐ
• Chung: Đã trả 560,000 VNĐ

💸 KẾT QUẢ CUỐI CÙNG:
🟢 Trung: Được nhận lại 200,000 VNĐ
🔴 Chung: Cần trả thêm 200,000 VNĐ

💳 GỢI Ý THANH TOÁN:
👉 Chung chuyển cho Trung: 200,000 VNĐ
```

## 🔍 Lưu Ý Quan Trọng

1. **Tên Người Chi**: Bot nhận diện tên **Trung** và **Chung** (không phân biệt hoa thường).
2. **Loại Chi Phí**: Khuyến khích sử dụng Dropdown để đảm bảo bot nhận diện chính xác.
3. **Lọc Dòng Trống**: Bot tự động bỏ qua các dòng không có mô tả hoặc số tiền.
4. **Chọn Ngày**: Double-click vào cột Ngày để chọn từ lịch.

---
*Cập nhật lần cuối: 03/05/2026*