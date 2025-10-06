# 💰 Hướng Dẫn Tính Toán Chia Tiền

## 📋 Tổng Quan

Chức năng `/split` trong bot giúp tính toán số tiền mỗi người cần trả dựa trên cột **"Loại"** trong Google Sheets. Đây là tính năng đặc biệt được thiết kế cho nhóm 3 người: **Nhật**, **Trung**, và **Tài**.

## 🏷️ Hệ Thống Phân Loại

### Các Loại Chi Phí

| Loại | Mô Tả | Người Dùng | Cách Chia |
|------|-------|------------|-----------|
| **1** | 3 người cùng dùng | Nhật + Trung + Tài | Chia đều cho 3 người |
| **2** | Trung + Tài dùng | Trung + Tài | Chia đôi |  
| **3** | Trung + Nhật dùng | Trung + Nhật | Chia đôi |
| **4** | Nhật + Tài dùng | Nhật + Tài | Chia đôi |

### 📊 Ví Dụ Cụ Thể

#### Trường Hợp 1: Ăn Chung
```
Mô tả: Ăn trưa nhóm
Số tiền: 150,000 VNĐ  
Loại: 1 (3 người cùng dùng)
→ Mỗi người trả: 150,000 ÷ 3 = 50,000 VNĐ
```

#### Trường Hợp 2: Mua Đồ Riêng
```
Mô tả: Mua đồ ăn cho Trung và Tài
Số tiền: 80,000 VNĐ
Loại: 2 (Trung + Tài dùng)  
→ Mỗi người trả: 80,000 ÷ 2 = 40,000 VNĐ
```

## 🎯 Cách Sử Dụng

### Bước 1: Chuẩn Bị Dữ Liệu

Đảm bảo Google Sheets có đúng cấu trúc:

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| **Ngày** | **Mô tả** | **Số tiền** | **Danh mục** | **Người chi** | **Ghi chú** | **Loại** |
| 05/08/2025 | Ăn trưa | 150000 | Ăn uống | Trung | Quán cơm | 1 |
| 05/08/2025 | Cafe | 60000 | Giải trí | Tài | Với Trung | 2 |
| 05/08/2025 | Xăng xe | 100000 | Di chuyển | Nhật | Cho Nhật và Trung | 3 |

### Bước 2: Chạy Lệnh

Trong Telegram, gõ:
```
/split
```

### Bước 3: Đọc Kết Quả

Bot sẽ trả về báo cáo chi tiết bao gồm:

1. **Chi tiết theo loại**
2. **Tình hình thực tế** (ai đã trả bao nhiêu)
3. **Kết quả cuối cùng** (ai nợ/được nhận bao nhiêu)
4. **Gợi ý thanh toán** (cách chuyển tiền tối ưu)

## 📊 Ví Dụ Báo Cáo Đầy Đủ

```
💰 TÍNH TOÁN CHIA TIỀN THEO LOẠI - THÁNG 8 2025

📊 Tổng chi tiêu tháng: 850,000 VNĐ

📋 CHI TIẾT THEO LOẠI:

🔹 Loại 1 (Nhật + Trung + Tài):
   💰 Tổng: 450,000 VNĐ
   👤 Mỗi người: 150,000 VNĐ
   📊 Số giao dịch: 3

🔹 Loại 2 (Trung + Tài):
   💰 Tổng: 200,000 VNĐ
   👤 Mỗi người: 100,000 VNĐ
   📊 Số giao dịch: 2

🔹 Loại 3 (Trung + Nhật):
   💰 Tổng: 200,000 VNĐ
   👤 Mỗi người: 100,000 VNĐ
   📊 Số giao dịch: 1

👤 TÌNH HÌNH THỰC TẾ:
• Nhật: Đã trả 300,000 VNĐ (35.3%)
  └ Cần trả: 250,000 VNĐ
• Trung: Đã trả 400,000 VNĐ (47.1%)
  └ Cần trả: 350,000 VNĐ
• Tài: Đã trả 150,000 VNĐ (17.6%)
  └ Cần trả: 250,000 VNĐ

💸 KẾT QUẢ CUỐI CÙNG:
🟢 Nhật: Được nhận lại 50,000 VNĐ
🟢 Trung: Được nhận lại 50,000 VNĐ
🔴 Tài: Cần trả thêm 100,000 VNĐ

💡 GỢI Ý THANH TOÁN:
💳 Tài → Nhật: 50,000 VNĐ
💳 Tài → Trung: 50,000 VNĐ
```

## 🔧 Xử Lý Các Trường Hợp Đặc Biệt

### 1. Dữ Liệu Thiếu/Sai

**Vấn đề**: Cột "Loại" bị trống hoặc không phải số 1-4
**Giải pháp**: Bot sẽ bỏ qua dòng đó và hiển thị cảnh báo

**Vấn đề**: Số tiền không hợp lệ
**Giải pháp**: Bot sẽ bỏ qua dòng đó

### 2. Tên Người Không Đúng

Bot chỉ nhận diện 3 tên: **Nhật**, **Trung**, **Tài** (không phân biệt hoa thường)

Các tên khác sẽ được bỏ qua trong tính toán.

### 3. Số Tiền Nhỏ

Bot có ngưỡng 1,000 VNĐ để tránh tính toán những số tiền quá nhỏ:
- Nếu số dư < 1,000 VNĐ → Coi như đã cân bằng
- Nếu số dư ≥ 1,000 VNĐ → Hiển thị cần trả/nhận

## 🎨 Các Tính Năng Nâng Cao

### 1. Thuật Toán Tối Ưu Thanh Toán

Bot sử dụng thuật toán "debt settlement" để giảm thiểu số lần chuyển tiền:

```python
# Thay vì:
# Tài → Nhật: 30,000
# Tài → Trung: 20,000  
# Nhật → Trung: 10,000

# Bot gợi ý:
# Tài → Nhật: 20,000
# Tài → Trung: 30,000
```

### 2. Phân Tích Xu Hướng

Bot có thể mở rộng để phân tích:
- Ai thường chi nhiều nhất?
- Loại chi phí nào phổ biến?
- Xu hướng chi tiêu theo thời gian

### 3. Cảnh Báo Thông Minh

Bot có thể cảnh báo khi:
- Một người chi quá nhiều so với mức trung bình
- Có sự mất cân bằng lớn trong chi tiêu
- Phát hiện pattern bất thường

## 🔍 Troubleshooting

### Lỗi Thường Gặp

**1. "❌ Chưa có dữ liệu chi tiêu tháng này để chia!"**
- **Nguyên nhân**: Sheet tháng hiện tại chưa có dữ liệu
- **Giải pháp**: Thêm ít nhất một dòng chi tiêu

**2. "❌ Có lỗi xảy ra khi tính toán chia tiền"**
- **Nguyên nhân**: Lỗi format dữ liệu hoặc kết nối
- **Giải pháp**: Kiểm tra cấu trúc sheet và kết nối

**3. Kết quả không chính xác**
- **Nguyên nhân**: Cột "Loại" không đúng format (1,2,3,4)
- **Giải pháp**: Đảm bảo cột G chỉ chứa số 1, 2, 3, hoặc 4

**4. Không thấy một số giao dịch**
- **Nguyên nhân**: Cột "Số tiền" không phải số hợp lệ
- **Giải pháp**: Đảm bảo cột C chỉ chứa số (không có chữ)

### Debug

Để kiểm tra dữ liệu:
```
/status  # Xem trạng thái sheet hiện tại
/summary # Xem tổng kết để đối chiếu
```

## 💡 Tips & Best Practices

### 1. Quy Ước Đặt Tên

- Luôn dùng tên đầy đủ: "Nhật", "Trung", "Tài"
- Không viết tắt: "N", "T", "Tr"
- Không thêm ký tự đặc biệt

### 2. Phân Loại Hợp Lý

- **Loại 1**: Ăn uống chung, đi chơi chung, mua sắm chung
- **Loại 2**: Đồ ăn riêng cho Trung+Tài, transport riêng
- **Loại 3**: Đồ ăn riêng cho Trung+Nhật  
- **Loại 4**: Đồ ăn riêng cho Nhật+Tài

### 3. Kiểm Tra Định Kỳ

- Chạy `/split` cuối mỗi tuần để theo dõi
- So sánh với `/summary` để đảm bảo nhất quán
- Backup dữ liệu với `/backup` trước khi settle

### 4. Quy Trình Settle

1. Cuối tháng: Chạy `/split` để có báo cáo cuối cùng
2. Screenshot báo cáo để lưu trữ
3. Thực hiện chuyển tiền theo gợi ý
4. Xác nhận với nhóm đã hoàn thành

## 🔮 Tính Năng Sắp Tới

### 1. Split by Date Range
```
/split 01/08 31/08  # Tính toán cho khoảng thời gian cụ thể
```

### 2. Split History
```
/split_history  # Xem lịch sử settle các tháng trước
```

### 3. Auto Settlement Reminder
```
Bot tự động nhắc nhở cuối tháng: "⏰ Đến lúc settle tiền tháng 8!"
```

### 4. Integration với Banking
```
Tích hợp với API ngân hàng để track chuyển tiền tự động
```

---

## 📞 Hỗ Trợ

Nếu có vấn đề với tính năng chia tiền:

1. Kiểm tra format dữ liệu trong sheet
2. Chạy `/status` để xem trạng thái bot
3. Thử `/reset` nếu bot có vấn đề
4. Liên hệ admin để được hỗ trợ

**Lưu ý**: Tính năng này được thiết kế đặc biệt cho nhóm 3 người với tên cố định. Nếu cần customize cho nhóm khác, cần chỉnh sửa code.