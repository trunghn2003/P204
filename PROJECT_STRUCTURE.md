# 📁 Cấu Trúc Dự Án

```
bot204/
├── 📄 .env                      # Cấu hình biến môi trường
├── 📄 .gitignore               # Loại trừ file khỏi git
├── 📄 README.md                # Hướng dẫn tổng quan
├── 📄 SETUP_GUIDE.md           # Hướng dẫn chi tiết
├── 📄 requirements.txt         # Python dependencies
├── 📄 credentials.json.example # Template cho Google credentials
├── 🐍 telegram_bot.py          # Code chính của bot
├── 🧪 test_bot.py             # Script test bot
├── 🚀 setup.sh                # Script cài đặt
├── ▶️  start_bot.sh            # Script chạy bot
└── 📁 .venv/                  # Virtual environment
```

## 📋 Mô Tả File

### 🔧 File Cấu Hình
- **`.env`**: Chứa token, chat ID, và các cài đặt
- **`credentials.json`**: File xác thực Google API (tự tạo từ template)
- **`requirements.txt`**: Danh sách Python packages cần thiết

### 🐍 File Python
- **`telegram_bot.py`**: Bot chính, theo dõi Sheets và gửi tin nhắn
- **`test_bot.py`**: Kiểm tra kết nối Telegram và Google Sheets

### 🛠️ File Script
- **`setup.sh`**: Tự động cài đặt môi trường
- **`start_bot.sh`**: Khởi động bot với kiểm tra điều kiện

### 📚 File Tài Liệu
- **`README.md`**: Hướng dẫn nhanh
- **`SETUP_GUIDE.md`**: Hướng dẫn từng bước chi tiết

## 🚀 Quy Trình Sử Dụng

1. **Cài đặt**: `./setup.sh`
2. **Cấu hình**: Điền thông tin vào `.env` và `credentials.json`
3. **Test**: `python test_bot.py`
4. **Chạy**: `./start_bot.sh`

## 📊 Luồng Hoạt Động

```
Google Sheets → Bot Check → New Row? → Format Message → Send Telegram
     ↑              ↓                         ↓              ↓
     └─── Every 30s ────────────────────── Save State ── Wait 30s
```
