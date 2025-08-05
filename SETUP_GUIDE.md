# Hướng Dẫn Chi Tiết Thiết Lập Telegram Bot

## Bước 1: Tạo Telegram Bot

1. **Mở Telegram và tìm BotFather:**
   - Mở ứng dụng Telegram
   - Tìm kiếm `@BotFather`
   - Bắt đầu chat với BotFather

2. **Tạo bot mới:**
   ```
   /newbot
   ```
   - Nhập tên bot (ví dụ: "Chi Phí Tracker")
   - Nhập username bot (phải kết thúc bằng "bot", ví dụ: "ChiPhiTrackerBot")

3. **Lưu Bot Token:**
   - BotFather sẽ cung cấp token có dạng: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - Lưu token này để cấu hình sau

## Bước 2: Lấy Chat ID

1. **Thêm bot vào chat:**
   - Thêm bot vào nhóm chat hoặc bắt đầu chat cá nhân
   - Gửi một tin nhắn bất kỳ cho bot

2. **Lấy Chat ID:**
   - Truy cập URL: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
   - Thay `<BOT_TOKEN>` bằng token của bạn
   - Tìm trong response JSON phần `"chat":{"id":123456789}`
   - Số `123456789` chính là Chat ID của bạn

## Bước 3: Thiết Lập Google Sheets API

1. **Truy cập Google Cloud Console:**
   - Đi tới https://console.cloud.google.com/
   - Đăng nhập với tài khoản Google

2. **Tạo Project:**
   - Click "Select a project" → "New Project"
   - Nhập tên project (ví dụ: "telegram-bot-sheets")
   - Click "Create"

3. **Bật APIs:**
   - Tìm "Google Sheets API" và bật nó
   - Tìm "Google Drive API" và bật nó

4. **Tạo Service Account:**
   - Đi tới "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Nhập tên (ví dụ: "telegram-bot")
   - Click "Create and Continue"
   - Skip các bước optional, click "Done"

5. **Tạo Key:**
   - Click vào Service Account vừa tạo
   - Đi tới tab "Keys"
   - Click "Add Key" → "Create new key"
   - Chọn "JSON" và click "Create"
   - File JSON sẽ được tải về

6. **Cấu hình Google Sheets:**
   - Mở Google Sheets cần theo dõi
   - Click "Share" (Chia sẻ)
   - Thêm email của Service Account (có trong file JSON, trường "client_email")
   - Cấp quyền "Editor"

## Bước 4: Cài Đặt Bot

1. **Chuẩn bị file:**
   ```bash
   # Copy file credentials
   cp credentials.json.example credentials.json
   
   # Mở file và điền thông tin từ file JSON đã tải
   nano credentials.json
   ```

2. **Cấu hình .env:**
   ```bash
   # Chỉnh sửa file .env
   nano .env
   ```
   
   Điền các thông tin:
   ```
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   GOOGLE_SHEETS_ID=1a2b3c4d5e6f7g8h9i0j_example_sheet_id
   ```

3. **Lấy Google Sheets ID:**
   - Mở Google Sheets
   - Xem URL: `https://docs.google.com/spreadsheets/d/SHEETS_ID/edit`
   - Copy phần `SHEETS_ID`

4. **Chạy setup:**
   ```bash
   ./setup.sh
   ```

5. **Test bot:**
   ```bash
   python test_bot.py
   ```

6. **Chạy bot:**
   ```bash
   ./start_bot.sh
   ```

## Cấu Trúc Google Sheets Đề Xuất

Tạo sheet với các cột sau:

| A | B | C | D | E |
|---|---|---|---|---|
| Ngày | Mô tả | Số tiền | Danh mục | Ghi chú |
| 05/08/2025 | Ăn trưa | 50000 | Ăn uống | Cơm văn phòng |
| 05/08/2025 | Xăng xe | 200000 | Di chuyển | Đổ đầy bình |

## Troubleshooting

### Bot không gửi tin nhắn
- Kiểm tra Bot Token có đúng không
- Kiểm tra Chat ID có đúng không
- Đảm bảo bot đã được thêm vào chat/nhóm

### Không đọc được Google Sheets
- Kiểm tra file credentials.json có đúng format không
- Đảm bảo đã share Sheets với email trong credentials
- Kiểm tra Google Sheets ID có đúng không

### Bot bị dừng
- Xem log để tìm lỗi cụ thể
- Kiểm tra kết nối internet
- Restart bot: `./start_bot.sh`

## Tính Năng Nâng Cao

### Chạy Bot 24/7
Để bot chạy liên tục, bạn có thể:

1. **Sử dụng screen:**
   ```bash
   screen -S telegram-bot
   ./start_bot.sh
   # Nhấn Ctrl+A rồi D để detach
   ```

2. **Tạo systemd service (Linux):**
   ```bash
   # Tạo file service
   sudo nano /etc/systemd/system/telegram-bot.service
   ```

### Tùy Chỉnh Tin Nhắn
Chỉnh sửa hàm `format_row_message()` trong `telegram_bot.py` để thay đổi format tin nhắn.

### Thêm Bộ Lọc
Bạn có thể thêm logic để chỉ gửi thông báo cho những dòng thỏa mãn điều kiện nhất định.
