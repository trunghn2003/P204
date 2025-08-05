# Telegram Bot để Theo Dõi Google Sheets

Bot này sẽ theo dõi Google Sheets và gửi thông báo qua Telegram khi có dòng mới được thêm vào.

## Yêu cầu cài đặt

1. **Tạo Telegram Bot:**
   - Mở Telegram và tìm `@BotFather`
   - Gửi `/newbot` và làm theo hướng dẫn
   - Lưu lại Bot Token

2. **Lấy Chat ID:**
   - Thêm bot vào nhóm hoặc chat cá nhân
   - Gửi tin nhắn cho bot
   - Truy cập: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
   - Tìm "chat":{"id": để lấy Chat ID

3. **Thiết lập Google Sheets API:**
   - Truy cập [Google Cloud Console](https://console.cloud.google.com/)
   - Tạo project mới hoặc chọn project hiện có
   - Bật Google Sheets API và Google Drive API
   - Tạo Service Account và tải file JSON credentials
   - Đổi tên file thành `credentials.json` và đặt trong thư mục dự án
   - Chia sẻ Google Sheets với email của Service Account

## Cài đặt

1. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Cấu hình file .env:**
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   GOOGLE_SHEETS_ID=your_sheets_id_here
   GOOGLE_SHEETS_RANGE=Sheet1!A:Z
   GOOGLE_CREDENTIALS_FILE=credentials.json
   CHECK_INTERVAL_SECONDS=30
   LAST_ROW_FILE=last_row.txt
   ```

3. **Lấy Google Sheets ID:**
   - Mở Google Sheets
   - Copy ID từ URL: `https://docs.google.com/spreadsheets/d/SHEETS_ID/edit`

## Cấu trúc Google Sheets đề xuất

| A (Ngày) | B (Mô tả) | C (Số tiền) | D (Danh mục) | E (Ghi chú) |
|----------|-----------|-------------|--------------|-------------|
| 01/01/2024 | Mua xăng | 200000 | Di chuyển | Xe máy |
| 02/01/2024 | Ăn trưa | 50000 | Ăn uống | Cơm văn phòng |

## Chạy bot

```bash
python telegram_bot.py
```

## Tính năng

- ✅ Theo dõi Google Sheets theo thời gian thực
- ✅ Gửi thông báo qua Telegram khi có dòng mới
- ✅ Định dạng tin nhắn đẹp với emoji
- ✅ Xử lý số tiền với định dạng VNĐ
- ✅ Lưu trạng thái để tránh gửi trùng lặp
- ✅ Logging để debug

## Troubleshooting

1. **Bot không gửi tin nhắn:**
   - Kiểm tra Bot Token và Chat ID
   - Đảm bảo bot đã được thêm vào chat/nhóm

2. **Không đọc được Google Sheets:**
   - Kiểm tra file credentials.json
   - Đảm bảo đã chia sẻ Sheets với Service Account email
   - Kiểm tra Google Sheets ID

3. **Bot dừng hoạt động:**
   - Xem log để tìm lỗi
   - Kiểm tra kết nối internet
   - Restart bot nếu cần thiết

## Tùy chỉnh

Bạn có thể tùy chỉnh:
- Thời gian kiểm tra trong file `.env`
- Format tin nhắn trong hàm `format_row_message()`
- Cấu trúc cột trong Google Sheets
# P204
# P204
