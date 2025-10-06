# 📚 Tài Liệu Kỹ Thuật - P204 Telegram Bot

## 🎯 Tổng Quan Dự Án

**P204** là một hệ thống Telegram bot thông minh để quản lý chi tiêu và theo dõi Google Sheets. Bot hỗ trợ tự động theo dõi các thay đổi trong Google Sheets và gửi thông báo qua Telegram, đồng thời cung cấp nhiều tính năng quản lý chi tiêu nâng cao.

### 🌟 Tính Năng Chính

1. **Theo dõi Google Sheets tự động**
2. **Quản lý chi tiêu thông minh**
3. **Tính toán chia tiền theo nhóm**
4. **Phân tích thống kê chi tiết**
5. **Quản lý ngân sách**
6. **Xuất báo cáo CSV**

## 🏗️ Kiến Trúc Hệ Thống

### 📁 Cấu Trúc Project

```
P204/
├── 🤖 advanced_bot.py          # Bot chính với đầy đủ tính năng
├── 📞 telegram_bot.py          # Bot cơ bản theo dõi sheets
├── 🎮 interactive_bot.py       # Bot tương tác thêm chi phí
├── 🧪 test_bot.py             # Script kiểm tra kết nối
├── ⏰ timezone_utils.py        # Utilities xử lý timezone
├── 📊 add_expense.py          # Script thêm chi phí
├── 🔧 setup_sheets.py         # Setup Google Sheets
├── 📋 requirements.txt        # Python dependencies
├── ⚙️ .env                    # Cấu hình môi trường
├── 🔑 credentials.json        # Google API credentials
├── 🚀 setup.sh               # Script cài đặt
├── ▶️  start_bot.sh           # Script khởi động
├── 📖 README.md              # Hướng dẫn cơ bản
├── 📚 SETUP_GUIDE.md         # Hướng dẫn chi tiết
├── 📁 PROJECT_STRUCTURE.md   # Cấu trúc dự án
└── 💾 budget_settings.txt    # Cài đặt ngân sách
```

## 🤖 Các Bot Components

### 1. AdvancedTelegramBot (advanced_bot.py)

**Bot chính với đầy đủ tính năng nâng cao:**

#### 🎯 Core Features
- Quản lý sheets theo tháng tự động
- Tính toán chia tiền thông minh
- Quản lý ngân sách với cảnh báo
- Phân tích thống kê chi tiết
- Tìm kiếm và lọc dữ liệu

#### 🔧 Key Methods

```python
class AdvancedTelegramBot:
    def __init__(self):
        # Khởi tạo bot với đầy đủ cấu hình
        
    def ensure_current_month_sheet(self):
        # Tự động tạo sheet theo tháng
        
    def add_expense_to_sheet(self, description, amount, category, person, note):
        # Thêm chi phí vào sheet hiện tại
        
    async def split_command(self, update, context):
        # Tính toán chia tiền theo cột "Loại"
        
    def get_monthly_summary(self, sheet_name=None):
        # Tạo báo cáo tổng kết tháng
```

#### 💰 Tính Năng Chia Tiền Đặc Biệt

Bot hỗ trợ tính toán chia tiền dựa trên cột "Loại" trong Google Sheets:

- **Loại 1**: 3 người cùng dùng (Nhật, Trung, Tài) - chia đều cho 3
- **Loại 2**: Trung + Tài dùng - chia đôi
- **Loại 3**: Trung + Nhật dùng - chia đôi  
- **Loại 4**: Nhật + Tài dùng - chia đôi

```python
user_groups = {
    1: ["Nhật", "Trung", "Tài"],  # 3 người cùng dùng
    2: ["Trung", "Tài"],          # Trung + Tài dùng
    3: ["Trung", "Nhật"],         # Trung + Nhật dùng
    4: ["Nhật", "Tài"]            # Nhật + Tài dùng
}
```

### 2. GoogleSheetsMonitor (telegram_bot.py)

**Bot cơ bản theo dõi Google Sheets:**

```python
class GoogleSheetsMonitor:
    async def check_for_new_rows(self):
        # Theo dõi dòng mới trong sheets
        
    def format_row_message(self, row_data, row_number):
        # Format tin nhắn thông báo
        
    async def start_monitoring(self):
        # Bắt đầu vòng lặp theo dõi
```

### 3. InteractiveTelegramBot (interactive_bot.py)

**Bot tương tác thêm chi phí:**

- Conversation handler để thêm chi phí từng bước
- Quick add với format: `/quick Mô tả|Số tiền|Danh mục|Người chi|Ghi chú`
- Validation dữ liệu đầu vào

## 🌍 Timezone Utils (timezone_utils.py)

Xử lý múi giờ Bangkok (UTC+7):

```python
def get_current_bangkok_time():
    # Lấy thời gian hiện tại Bangkok
    
def get_bangkok_date_str():
    # Format ngày theo định dạng dd/mm/yyyy
    
def format_bangkok_datetime(dt=None, format_str='%d/%m/%Y %H:%M:%S'):
    # Format datetime tùy chỉnh
```

## 📊 Google Sheets Integration

### Cấu Trúc Sheet

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| Ngày | Mô tả | Số tiền | Danh mục | Người chi | Ghi chú | Loại |
| 05/08/2025 | Ăn trưa | 50000 | Ăn uống | Trung | Cơm văn phòng | 2 |

### Google Sheets API Setup

```python
def setup_google_sheets(self):
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = Credentials.from_service_account_file(
        self.credentials_file, 
        scopes=scope
    )
    
    self.gc = gspread.Client(auth=creds)
    self.workbook = self.gc.open_by_key(self.sheets_id)
```

## 🎮 Bot Commands

### 📝 Thêm Chi Phí
- `/add` - Thêm chi phí tương tác từng bước
- `/quick Mô tả|Số tiền|Danh mục|Người chi|Ghi chú` - Thêm nhanh

### 📊 Báo Cáo & Thống Kê
- `/summary` - Tổng kết tháng hiện tại
- `/today` - Chi tiêu hôm nay
- `/week` - Chi tiêu tuần này
- `/daily` - Chi tiêu theo từng ngày
- `/month` - Danh sách tất cả các tháng
- `/topspenders` - Top người chi nhiều nhất
- `/topcategories` - Top danh mục chi tiêu

### 💰 Quản Lý Ngân Sách
- `/budget` - Xem trạng thái ngân sách
- `/budget [số tiền]` - Đặt ngân sách mới

### 🔍 Tìm Kiếm & Lọc
- `/search [từ khóa]` - Tìm kiếm giao dịch
- `/filter >100000` - Lọc chi tiêu trên 100k
- `/filter person:Trung` - Lọc theo người
- `/filter category:Ăn uống` - Lọc theo danh mục

### 🧠 Phân Tích Thông Minh
- `/insight` - Phân tích thông minh
- `/compare` - So sánh các tháng
- `/split` - **Tính toán chia tiền theo loại**

### ⚙️ Quản Lý Hệ Thống
- `/edit` - Chỉnh sửa giao dịch gần nhất
- `/delete` - Xóa giao dịch gần nhất
- `/export` - Xuất dữ liệu CSV
- `/backup` - Sao lưu dữ liệu
- `/status` - Trạng thái bot
- `/reset` - Reset vị trí theo dõi

## 🔧 Configuration

### Environment Variables (.env)

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
GOOGLE_SHEETS_ID=your_sheets_id_here
GOOGLE_SHEETS_RANGE=Sheet1!A:Z
GOOGLE_CREDENTIALS_FILE=credentials.json
CHECK_INTERVAL_SECONDS=30
LAST_ROW_FILE=last_row.txt
```

### Dependencies (requirements.txt)

```
python-telegram-bot==20.7
google-api-python-client==2.108.0
google-auth-httplib2==0.1.1
google-auth-oauthlib==1.1.0
gspread==5.12.0
python-dotenv==1.0.0
schedule==1.2.0
pytz==2024.1
```

## 🚀 Deployment & Operations

### Cài Đặt

```bash
# 1. Clone repository
git clone <repo-url>
cd P204

# 2. Chạy setup
./setup.sh

# 3. Cấu hình .env và credentials.json
cp .env.example .env
cp credentials.json.example credentials.json
# Edit files with your configuration

# 4. Test setup
python test_bot.py

# 5. Start bot
./start_bot.sh
```

### Production Deployment

```bash
# Sử dụng screen cho background process
screen -S telegram-bot
./start_bot.sh
# Ctrl+A, D để detach

# Hoặc tạo systemd service
sudo nano /etc/systemd/system/telegram-bot.service
```

## 🧪 Testing

### test_bot.py

Script kiểm tra kết nối:

```python
def test_telegram_connection():
    # Test Telegram bot connection
    
def test_google_sheets_connection():
    # Test Google Sheets API connection
    
def test_environment_variables():
    # Validate environment configuration
```

## 🛡️ Error Handling & Logging

### Logging Configuration

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Common Error Scenarios

1. **Google Sheets API Errors**
   - Invalid credentials
   - Sheet not found
   - Permission denied

2. **Telegram API Errors**
   - Invalid bot token
   - Chat not found
   - Message too long

3. **Data Validation Errors**
   - Invalid amount format
   - Missing required fields
   - Invalid date format

## 🔄 Advanced Features

### 1. Automatic Month Sheet Creation

Bot tự động tạo sheet mới cho mỗi tháng:

```python
def get_sheet_name_for_month(self, year=None, month=None):
    month_names = [
        "", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
        "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"
    ]
    return f"{month_names[month]} {year}"
```

### 2. Budget Management & Warnings

Hệ thống cảnh báo ngân sách thông minh:

```python
async def check_budget_warning(self):
    if percentage >= 100:
        return "🚨 CẢNH BÁO NGÂN SÁCH! Đã vượt ngân sách"
    elif percentage >= 90:
        return "⚠️ CẢNH BÁO! Đã dùng 90% ngân sách"
    elif percentage >= 80:
        return "⚡ CHÚ Ý! Đã dùng 80% ngân sách"
```

### 3. Smart Money Split Algorithm

Thuật toán tính toán chia tiền thông minh:

```python
# Simple debt settlement algorithm
while debtors_copy and creditors_copy:
    debtor_name, debt_amount = debtors_copy[0]
    creditor_name, credit_amount = creditors_copy[0]
    
    transfer_amount = min(debt_amount, credit_amount)
    # Generate payment suggestion
```

### 4. Data Analysis & Insights

Phân tích thông minh với Machine Learning cơ bản:

- Dự đoán chi tiêu cuối tháng
- Phát hiện pattern chi tiêu bất thường
- Gợi ý tối ưu hóa ngân sách
- So sánh xu hướng theo tháng

## 🎯 Best Practices

### 1. Code Organization

- Separation of concerns (bot logic, sheets logic, utils)
- Error handling at every level
- Comprehensive logging
- Configuration management

### 2. Data Handling

- Case-insensitive text comparison với `normalize_text()`
- Proper number formatting for Vietnamese currency
- Timezone-aware datetime handling
- Data validation và sanitization

### 3. User Experience

- Markdown formatting cho tin nhắn đẹp
- Emoji để tăng tính trực quan
- Progressive disclosure (không hiển thị quá nhiều thông tin cùng lúc)
- Error messages thân thiện với người dùng

## 🔮 Future Enhancements

### Planned Features

1. **Web Dashboard** - Interface web để quản lý
2. **Mobile App** - Ứng dụng di động companion
3. **AI-Powered Insights** - Phân tích thông minh với AI
4. **Multi-currency Support** - Hỗ trợ nhiều loại tiền tệ
5. **Recurring Expenses** - Chi phí định kỳ tự động
6. **Receipt OCR** - Quét hóa đơn tự động

### Technical Improvements

1. **Database Integration** - Chuyển từ Google Sheets sang database
2. **Microservices Architecture** - Tách thành các service nhỏ
3. **Real-time Sync** - Đồng bộ thời gian thực
4. **Advanced Analytics** - Dashboard phân tích nâng cao
5. **Multi-tenant Support** - Hỗ trợ nhiều team/organization

## 📞 Support & Troubleshooting

### Common Issues

1. **Bot không gửi tin nhắn**
   - Kiểm tra Bot Token và Chat ID
   - Đảm bảo bot đã được thêm vào chat/nhóm

2. **Không đọc được Google Sheets**
   - Kiểm tra file credentials.json
   - Đảm bảo đã share Sheets với Service Account email
   - Kiểm tra Google Sheets ID

3. **Lỗi tính toán chia tiền**
   - Kiểm tra cột "Loại" có đúng format (1, 2, 3, 4)
   - Đảm bảo cột "Số tiền" là số hợp lệ
   - Kiểm tra tên người trong cột "Người chi"

### Debug Commands

```bash
# Xem logs
tail -f telegram-bot.log

# Test connections
python test_bot.py

# Reset bot state
rm last_row_*.txt
```

## 👥 Contributing

### Development Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
python -m pytest

# Format code
black *.py

# Lint code
flake8 *.py
```

### Code Style Guidelines

- Sử dụng Black formatter
- Follow PEP 8
- Comprehensive docstrings
- Type hints where applicable
- Meaningful variable names

---

## 📝 Changelog

### v2.0.0 - Advanced Features
- ✅ Automatic month sheet creation
- ✅ Smart money split calculation
- ✅ Budget management with warnings
- ✅ Advanced search and filtering
- ✅ Data export capabilities
- ✅ Comprehensive analytics

### v1.0.0 - Basic Features  
- ✅ Google Sheets monitoring
- ✅ Telegram notifications
- ✅ Basic expense tracking
- ✅ Simple reporting

---

*Tài liệu này được cập nhật thường xuyên. Lần cập nhật cuối: October 2025*