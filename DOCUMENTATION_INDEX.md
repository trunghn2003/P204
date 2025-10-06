# 📚 Index Tài Liệu P204

## 📋 Danh Sách Tài Liệu

### 🚀 Hướng Dẫn Nhanh
- **[README.md](README.md)** - Hướng dẫn cơ bản và khởi động nhanh
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Hướng dẫn cài đặt chi tiết từng bước
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Tổng quan cấu trúc dự án

### 📖 Tài Liệu Kỹ Thuật
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** - Tài liệu kỹ thuật đầy đủ về codebase
- **[SPLIT_MONEY_GUIDE.md](SPLIT_MONEY_GUIDE.md)** - Hướng dẫn chi tiết tính năng chia tiền

## 🎯 Hướng Dẫn Đọc Theo Mục Đích

### 🔰 Người Dùng Mới
1. **Bắt đầu**: [README.md](README.md) - Hiểu tổng quan
2. **Cài đặt**: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Thiết lập từ A-Z
3. **Sử dụng**: [SPLIT_MONEY_GUIDE.md](SPLIT_MONEY_GUIDE.md) - Tính năng chính

### 👨‍💻 Developer
1. **Cấu trúc**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Hiểu tổ chức code
2. **Kỹ thuật**: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Dive deep vào code
3. **Tính năng**: [SPLIT_MONEY_GUIDE.md](SPLIT_MONEY_GUIDE.md) - Logic nghiệp vụ

### 🔧 System Admin
1. **Setup**: [SETUP_GUIDE.md](SETUP_GUIDE.md) - Deploy và configuration
2. **Operations**: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) - Monitoring và troubleshooting

## 📊 Tính Năng Chính

### 💰 Chia Tiền Thông Minh
- **File**: [SPLIT_MONEY_GUIDE.md](SPLIT_MONEY_GUIDE.md)
- **Code**: `advanced_bot.py` → `split_command()`
- **Lệnh**: `/split`

### 📈 Quản Lý Chi Tiêu
- **File**: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- **Code**: `advanced_bot.py` → `AdvancedTelegramBot`
- **Lệnh**: `/add`, `/summary`, `/budget`

### 🔍 Tìm Kiếm & Phân Tích  
- **File**: [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- **Code**: `advanced_bot.py` → `search_command()`, `insight_command()`
- **Lệnh**: `/search`, `/filter`, `/insight`

## 🏗️ Kiến Trúc Hệ Thống

```
P204 Bot System
├── 🤖 Core Bots
│   ├── advanced_bot.py (Main bot with full features)
│   ├── telegram_bot.py (Basic monitoring bot)  
│   └── interactive_bot.py (Expense adding bot)
├── 🔧 Utilities
│   ├── timezone_utils.py (Bangkok timezone handling)
│   ├── add_expense.py (CLI expense tool)
│   └── setup_sheets.py (Google Sheets setup)
├── 📊 Google Sheets Integration
│   ├── credentials.json (Service account auth)
│   └── Auto month sheet creation
├── 💾 Data Management
│   ├── budget_settings.txt (Monthly budget)
│   ├── last_row_*.txt (Position tracking)
│   └── CSV export functionality
└── 🎮 User Interface
    ├── Telegram bot commands
    ├── Interactive conversations
    └── Rich formatted reports
```

## 🎮 Command Reference

| Category | Command | Description | Document |
|----------|---------|-------------|----------|
| **💰 Money** | `/split` | Tính toán chia tiền | [SPLIT_MONEY_GUIDE.md](SPLIT_MONEY_GUIDE.md) |
| **💰 Money** | `/budget` | Quản lý ngân sách | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **📝 Expense** | `/add` | Thêm chi phí tương tác | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **📝 Expense** | `/quick` | Thêm chi phí nhanh | [README.md](README.md) |
| **📊 Report** | `/summary` | Tổng kết tháng | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **📊 Report** | `/today` | Chi tiêu hôm nay | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **📊 Report** | `/export` | Xuất CSV | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **🔍 Search** | `/search` | Tìm kiếm giao dịch | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **🔍 Search** | `/filter` | Lọc dữ liệu | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **🧠 Analysis** | `/insight` | Phân tích thông minh | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **⚙️ System** | `/status` | Trạng thái bot | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |
| **⚙️ System** | `/help` | Hướng dẫn đầy đủ | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |

## 🔧 Configuration Files

| File | Purpose | Document |
|------|---------|----------|
| `.env` | Environment variables | [SETUP_GUIDE.md](SETUP_GUIDE.md) |
| `credentials.json` | Google API auth | [SETUP_GUIDE.md](SETUP_GUIDE.md) |
| `requirements.txt` | Python dependencies | [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) |
| `budget_settings.txt` | Monthly budget | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |

## 🚨 Troubleshooting Quick Reference

| Issue | Solution | Document |
|-------|----------|----------|
| Bot không gửi tin nhắn | Check token & chat ID | [README.md](README.md) |
| Không đọc được Sheets | Check credentials & permissions | [SETUP_GUIDE.md](SETUP_GUIDE.md) |
| Chia tiền sai kết quả | Check cột "Loại" format | [SPLIT_MONEY_GUIDE.md](SPLIT_MONEY_GUIDE.md) |
| Bot dừng hoạt động | Check logs & restart | [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) |

## 📱 Quick Start Commands

```bash
# Development
git clone <repo>
cd P204
./setup.sh
python test_bot.py

# Production  
./start_bot.sh

# Monitoring
tail -f telegram-bot.log
```

## 🎯 Use Cases

### 👥 Shared Expense Management
- **Nhóm bạn**: Quản lý chi tiêu chung, chia tiền tự động
- **Gia đình**: Theo dõi ngân sách hàng tháng
- **Team**: Quản lý chi phí dự án

### 📊 Financial Tracking
- **Cá nhân**: Theo dõi chi tiêu cá nhân
- **Doanh nghiệp nhỏ**: Quản lý chi phí kinh doanh
- **Sự kiện**: Quản lý ngân sách tổ chức sự kiện

### 🤖 Automation
- **Thông báo real-time**: Ngay khi có chi tiêu mới
- **Báo cáo tự động**: Tổng kết định kỳ
- **Cảnh báo ngân sách**: Khi sắp vượt ngân sách

## 🔮 Roadmap

### v3.0 (Planned)
- [ ] Web dashboard
- [ ] Mobile app
- [ ] AI-powered insights
- [ ] Multi-currency support

### v2.1 (Current)
- [x] Smart money split
- [x] Budget management  
- [x] Advanced analytics
- [x] Auto month sheets

## 📞 Support

- **Technical Issues**: Check [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)
- **Setup Problems**: Follow [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **Feature Questions**: See [SPLIT_MONEY_GUIDE.md](SPLIT_MONEY_GUIDE.md)

---

*Tài liệu được tạo và duy trì bởi P204 Development Team - October 2025*