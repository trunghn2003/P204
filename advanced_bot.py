import os
import logging
from datetime import datetime, date, timedelta
from calendar import monthrange
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Conversation states
DESCRIPTION, AMOUNT, CATEGORY, PERSON, NOTE = range(5)
BUDGET_AMOUNT, SEARCH_QUERY, EDIT_SELECT, EDIT_FIELD, EDIT_VALUE = range(5, 10)

class AdvancedTelegramBot:
    def __init__(self):
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.check_interval = int(os.getenv('CHECK_INTERVAL_SECONDS', 30))
        self.last_row_file = os.getenv('LAST_ROW_FILE', 'last_row.txt')
        
        # Budget settings
        self.budget_file = 'budget_settings.txt'
        self.monthly_budget = self.load_monthly_budget()
        
        # Setup Google Sheets
        self.setup_google_sheets()
        
        # Ensure current month sheet exists
        self.current_sheet = self.ensure_current_month_sheet()
        
        # Get initial row count
        self.last_row_count = self.get_last_row_count()
        
        # Create application
        self.application = Application.builder().token(self.telegram_bot_token).build()
        self.setup_handlers()
    
    def setup_google_sheets(self):
        """Setup Google Sheets API connection"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=scope
            )
            
            self.gc = gspread.authorize(creds)
            self.workbook = self.gc.open_by_key(self.sheets_id)
            logger.info("Google Sheets connection established successfully")
            
        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}")
            raise
    
    def get_sheet_name_for_month(self, year=None, month=None):
        """Get sheet name for a specific month"""
        if year is None or month is None:
            now = datetime.now()
            year, month = now.year, now.month
        
        month_names = [
            "", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
            "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"
        ]
        return f"{month_names[month]} {year}"
    
    def ensure_current_month_sheet(self):
        """Ensure current month sheet exists and return it"""
        sheet_name = self.get_sheet_name_for_month()
        
        try:
            # Try to get existing sheet
            sheet = self.workbook.worksheet(sheet_name)
            logger.info(f"Found existing sheet: {sheet_name}")
            return sheet
        except gspread.WorksheetNotFound:
            # Create new sheet for current month
            logger.info(f"Creating new sheet: {sheet_name}")
            sheet = self.workbook.add_worksheet(title=sheet_name, rows=1000, cols=10)
            
            # Setup headers
            headers = ['Ngày', 'Mô tả', 'Số tiền', 'Danh mục', 'Người chi', 'Ghi chú']
            sheet.insert_row(headers, 1)
            
            # Format header
            sheet.format('A1:F1', {
                "backgroundColor": {
                    "red": 0.2,
                    "green": 0.4,
                    "blue": 0.8
                },
                "textFormat": {
                    "foregroundColor": {
                        "red": 1.0,
                        "green": 1.0,
                        "blue": 1.0
                    },
                    "fontSize": 12,
                    "bold": True
                }
            })
            
            # Add summary section at the bottom
            self.setup_summary_section(sheet)
            
            logger.info(f"Successfully created and formatted sheet: {sheet_name}")
            return sheet
    
    def setup_summary_section(self, sheet):
        """Setup summary section at the bottom of the sheet"""
        try:
            # Add summary headers at row 50 (leaving space for data)
            summary_row = 50
            
            # Summary headers
            sheet.update(f'A{summary_row}', 'TỔNG KẾT THÁNG')
            sheet.update(f'A{summary_row + 2}', 'Tổng chi tiêu:')
            sheet.update(f'A{summary_row + 3}', 'Số giao dịch:')
            sheet.update(f'A{summary_row + 4}', 'Chi tiêu trung bình:')
            sheet.update(f'A{summary_row + 6}', 'CHI TIẾT THEO DANH MỤC')
            
            # Format summary section
            sheet.format(f'A{summary_row}:F{summary_row}', {
                "backgroundColor": {"red": 0.8, "green": 0.9, "blue": 0.8},
                "textFormat": {"bold": True, "fontSize": 14}
            })
            
            # Formulas for automatic calculation
            sheet.update(f'B{summary_row + 2}', f'=SUM(C2:C49)')  # Total amount
            sheet.update(f'B{summary_row + 3}', f'=COUNTA(C2:C49)')  # Count transactions
            sheet.update(f'B{summary_row + 4}', f'=B{summary_row + 2}/B{summary_row + 3}')  # Average
            
            logger.info("Summary section setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up summary section: {e}")
    
    def load_monthly_budget(self):
        """Load monthly budget from file"""
        try:
            if os.path.exists(self.budget_file):
                with open(self.budget_file, 'r') as f:
                    return int(f.read().strip())
            return 0
        except Exception as e:
            logger.error(f"Error loading budget: {e}")
            return 0
    
    def save_monthly_budget(self, amount):
        """Save monthly budget to file"""
        try:
            with open(self.budget_file, 'w') as f:
                f.write(str(amount))
            self.monthly_budget = amount
        except Exception as e:
            logger.error(f"Error saving budget: {e}")
    
    def get_budget_status(self):
        """Get current budget status"""
        if self.monthly_budget <= 0:
            return None
        
        summary = self.get_monthly_summary()
        if not summary:
            return None
        
        spent = summary['total']
        remaining = self.monthly_budget - spent
        percentage = (spent / self.monthly_budget) * 100 if self.monthly_budget > 0 else 0
        
        return {
            'budget': self.monthly_budget,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage,
            'over_budget': spent > self.monthly_budget
        }
    
    async def check_budget_warning(self):
        """Check if budget warning should be shown"""
        try:
            budget_status = self.get_budget_status()
            if not budget_status:
                return None
            
            percentage = budget_status['percentage']
            
            if percentage >= 100:
                return (
                    "🚨 **CẢNH BÁO NGÂN SÁCH!**\n"
                    f"⚠️ Đã vượt ngân sách {percentage-100:.1f}%\n"
                    f"💸 Vượt: {abs(budget_status['remaining']):,} VNĐ"
                )
            elif percentage >= 90:
                return (
                    "⚠️ **CẢNH BÁO!**\n"
                    f"🔴 Đã dùng {percentage:.1f}% ngân sách\n"
                    f"💰 Còn lại: {budget_status['remaining']:,} VNĐ"
                )
            elif percentage >= 80:
                return (
                    "⚡ **CHÚ Ý!**\n"
                    f"🟡 Đã dùng {percentage:.1f}% ngân sách\n"
                    f"💰 Còn lại: {budget_status['remaining']:,} VNĐ"
                )
            
            return None
        except Exception as e:
            logger.error(f"Error checking budget warning: {e}")
            return None
    
    def get_last_row_count(self):
        """Get the last stored row count from file for current sheet"""
        sheet_name = self.current_sheet.title
        file_name = f"last_row_{sheet_name.replace(' ', '_')}.txt"
        
        try:
            if os.path.exists(file_name):
                with open(file_name, 'r') as f:
                    return int(f.read().strip())
            else:
                current_count = len(self.current_sheet.get_all_values())
                self.save_last_row_count(current_count)
                return current_count
        except Exception as e:
            logger.error(f"Error reading last row count: {e}")
            return 0
    
    def save_last_row_count(self, count):
        """Save the current row count to file for current sheet"""
        sheet_name = self.current_sheet.title
        file_name = f"last_row_{sheet_name.replace(' ', '_')}.txt"
        
        try:
            with open(file_name, 'w') as f:
                f.write(str(count))
        except Exception as e:
            logger.error(f"Error saving last row count: {e}")
    
    def get_current_row_count(self):
        """Get current number of rows in the current sheet"""
        try:
            return len(self.current_sheet.get_all_values())
        except Exception as e:
            logger.error(f"Error getting current row count: {e}")
            return 0
    
    def add_expense_to_sheet(self, description, amount, category, person, note=""):
        """Add expense to current month's sheet"""
        try:
            date_str = datetime.now().strftime('%d/%m/%Y')
            row_data = [date_str, description, str(amount), category, person, note]
            
            # Check if we need a new month sheet
            current_month_sheet_name = self.get_sheet_name_for_month()
            if self.current_sheet.title != current_month_sheet_name:
                self.current_sheet = self.ensure_current_month_sheet()
                self.last_row_count = self.get_last_row_count()
            
            # Log which sheet we're adding to
            logger.info(f"Adding expense to sheet: {self.current_sheet.title}")
            
            # Get current row count to insert at the correct position
            current_rows = len(self.current_sheet.get_all_values())
            next_row = current_rows + 1
            
            # Insert the row at the specific position
            self.current_sheet.insert_row(row_data, next_row)
            
            logger.info(f"Successfully added expense to row {next_row} in {self.current_sheet.title}")
            return True
        except Exception as e:
            logger.error(f"Error adding expense to sheet: {e}")
            return False
    
    def get_monthly_summary(self, sheet_name=None):
        """Get summary for a specific month"""
        try:
            if sheet_name is None:
                sheet = self.current_sheet
                sheet_name = sheet.title
            else:
                sheet = self.workbook.worksheet(sheet_name)
            
            # Get all data (excluding header)
            all_data = sheet.get_all_values()[1:]
            
            # Filter out empty rows and summary rows
            data_rows = []
            for row in all_data:
                if len(row) >= 3 and row[2].strip() and row[2].replace(',', '').isdigit():
                    data_rows.append(row)
            
            if not data_rows:
                return {
                    'total': 0,
                    'count': 0,
                    'average': 0,
                    'by_category': {},
                    'by_person': {},
                    'sheet_name': sheet_name
                }
            
            # Calculate summary
            total = sum(int(row[2].replace(',', '')) for row in data_rows)
            count = len(data_rows)
            average = total / count if count > 0 else 0
            
            # Group by category
            by_category = {}
            for row in data_rows:
                category = row[3] if len(row) > 3 else 'Khác'
                amount = int(row[2].replace(',', ''))
                by_category[category] = by_category.get(category, 0) + amount
            
            # Group by person
            by_person = {}
            for row in data_rows:
                person = row[4] if len(row) > 4 else 'Không rõ'
                amount = int(row[2].replace(',', ''))
                by_person[person] = by_person.get(person, 0) + amount
            
            return {
                'total': total,
                'count': count,
                'average': average,
                'by_category': by_category,
                'by_person': by_person,
                'sheet_name': sheet_name
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly summary: {e}")
            return None
    
    def setup_handlers(self):
        """Setup command and message handlers"""
        # Conversation handler for adding expenses
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('add', self.start_add_expense)],
            states={
                DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_description)],
                AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_amount)],
                CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_category)],
                PERSON: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_person)],
                NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_note)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Budget conversation handler
        budget_handler = ConversationHandler(
            entry_points=[CommandHandler('budget', self.budget_command)],
            states={
                BUDGET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.set_budget_amount)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Search conversation handler
        search_handler = ConversationHandler(
            entry_points=[CommandHandler('search', self.search_command)],
            states={
                SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_search)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Add handlers
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('quick', self.quick_add))
        self.application.add_handler(CommandHandler('summary', self.summary_command))
        self.application.add_handler(CommandHandler('month', self.month_summary_command))
        self.application.add_handler(CommandHandler('status', self.status_command))
        self.application.add_handler(CommandHandler('reset', self.reset_position_command))
        self.application.add_handler(CommandHandler('today', self.today_command))
        self.application.add_handler(CommandHandler('week', self.week_command))
        self.application.add_handler(CommandHandler('daily', self.daily_command))
        self.application.add_handler(CommandHandler('compare', self.compare_command))
        self.application.add_handler(CommandHandler('filter', self.filter_command))
        self.application.add_handler(CommandHandler('insight', self.insight_command))
        self.application.add_handler(CommandHandler('edit', self.edit_command))
        self.application.add_handler(CommandHandler('delete', self.delete_command))
        self.application.add_handler(CommandHandler('backup', self.backup_command))
        self.application.add_handler(conv_handler)
        self.application.add_handler(budget_handler)
        self.application.add_handler(search_handler)
        
        # Add handler for edit/delete responses (catch-all for text messages)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_edit_delete_response))
    
    async def start_command(self, update: Update, context):
        """Handle /start command"""
        welcome_message = (
            "🤖 **Chào mừng đến với Bot Quản Lý Chi Phí Siêu Nâng Cao!**\n\n"
            "🎯 **Tính năng chính:**\n"
            "💰 Quản lý ngân sách thông minh\n"
            "📊 Phân tích chi tiêu chi tiết\n"
            "🔍 Tìm kiếm & lọc mạnh mẽ\n"
            "✏️ Chỉnh sửa & xóa giao dịch\n"
            "📈 So sánh xu hướng theo tháng\n\n"
            "⚡ **Lệnh cơ bản:**\n"
            "• `/add` - Thêm chi phí (tương tác)\n"
            "• `/quick` - Thêm nhanh (một dòng)\n"
            "• `/budget` - Quản lý ngân sách\n"
            "• `/summary` - Tổng kết tháng hiện tại\n\n"
            "🔍 **Tìm kiếm & Phân tích:**\n"
            "• `/search` - Tìm kiếm giao dịch\n"
            "• `/filter` - Lọc theo điều kiện\n"
            "• `/compare` - So sánh các tháng\n"
            "• `/insight` - Phân tích thông minh\n\n"
            "📅 **Báo cáo theo thời gian:**\n"
            "• `/today` - Chi tiêu hôm nay\n"
            "• `/week` - Chi tiêu tuần này\n"
            "• `/daily` - Chi tiêu theo ngày\n\n"
            "⚙️ **Quản lý:**\n"
            "• `/edit` - Sửa giao dịch gần nhất\n"
            "• `/delete` - Xóa giao dịch gần nhất\n"
            "• `/backup` - Sao lưu dữ liệu\n"
            "• `/help` - Hướng dẫn chi tiết\n\n"
            "💡 **Ví dụ nhanh:**\n"
            "`/quick Cafe|35000|Giải trí|Hoàng Việt|Với bạn`\n"
            "`/budget 5000000` (đặt ngân sách 5 triệu)\n"
            "`/search >100000` (tìm giao dịch trên 100k)\n\n"
            "✨ **Bot sẽ tự động cảnh báo khi gần hết ngân sách!**"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def summary_command(self, update: Update, context):
        """Handle /summary command"""
        try:
            summary = self.get_monthly_summary()
            if not summary:
                await update.message.reply_text("❌ Không thể lấy thông tin tổng kết!")
                return
            
            message = (
                f"📊 **TỔNG KẾT {summary['sheet_name'].upper()}**\n\n"
                f"💰 **Tổng chi tiêu:** {summary['total']:,} VNĐ\n"
                f"📝 **Số giao dịch:** {summary['count']} lần\n"
                f"📈 **Chi tiêu trung bình:** {summary['average']:,.0f} VNĐ/lần\n\n"
                f"📂 **CHI TIẾT THEO DANH MỤC:**\n"
            )
            
            for category, amount in sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / summary['total'] * 100) if summary['total'] > 0 else 0
                message += f"• {category}: {amount:,} VNĐ ({percentage:.1f}%)\n"
            
            message += f"\n👥 **CHI TIẾT THEO NGƯỜI:**\n"
            for person, amount in sorted(summary['by_person'].items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / summary['total'] * 100) if summary['total'] > 0 else 0
                message += f"• {person}: {amount:,} VNĐ ({percentage:.1f}%)\n"
            
            message += f"\n📅 Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in summary command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi tạo báo cáo!")
    
    async def month_summary_command(self, update: Update, context):
        """Handle /month command to show specific month summary"""
        try:
            # Get list of all sheets (months)
            worksheets = self.workbook.worksheets()
            month_sheets = [ws for ws in worksheets if 'Tháng' in ws.title]
            
            if not month_sheets:
                await update.message.reply_text("❌ Chưa có dữ liệu tháng nào!")
                return
            
            message = "📅 **DANH SÁCH CÁC THÁNG:**\n\n"
            for i, sheet in enumerate(month_sheets, 1):
                summary = self.get_monthly_summary(sheet.title)
                if summary and summary['total'] > 0:
                    message += f"{i}. {sheet.title}: {summary['total']:,} VNĐ ({summary['count']} giao dịch)\n"
                else:
                    message += f"{i}. {sheet.title}: Chưa có dữ liệu\n"
            
            message += f"\n💡 Gõ `/summary` để xem chi tiết tháng hiện tại"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in month command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi lấy danh sách tháng!")
    
    async def help_command(self, update: Update, context):
        """Handle /help command"""
        help_message = (
            "📖 **HƯỚNG DẪN SỬ DỤNG BOT NÂNG CAO:**\n\n"
            "🔹 **Thêm chi phí:**\n"
            "   `/add` - Thêm tương tác từng bước\n"
            "   `/quick Mô tả|Số tiền|Danh mục|Người chi|Ghi chú`\n\n"
            "🔹 **Xem báo cáo:**\n"
            "   `/summary` - Tổng kết tháng hiện tại\n"
            "   `/today` - Chi tiêu hôm nay\n"
            "   `/week` - Chi tiêu tuần này\n"
            "   `/daily` - Chi tiêu theo từng ngày\n"
            "   `/month` - Danh sách tất cả các tháng\n\n"
            "🔹 **Quản lý ngân sách:**\n"
            "   `/budget` - Xem trạng thái ngân sách\n"
            "   `/budget 5000000` - Đặt ngân sách 5 triệu\n\n"
            "🔹 **Tìm kiếm & Lọc:**\n"
            "   `/search cafe` - Tìm giao dịch có 'cafe'\n"
            "   `/filter >100000` - Lọc chi tiêu trên 100k\n"
            "   `/filter person:Hoàng` - Lọc theo người\n"
            "   `/filter category:Ăn uống` - Lọc theo danh mục\n\n"
            "🔹 **Phân tích nâng cao:**\n"
            "   `/compare` - So sánh các tháng\n"
            "   `/insight` - Phân tích thông minh\n\n"
            "🔹 **Chỉnh sửa dữ liệu:**\n"
            "   `/edit` - Chỉnh sửa giao dịch gần nhất\n"
            "   `/delete` - Xóa giao dịch gần nhất\n\n"
            "🔹 **Quản lý hệ thống:**\n"
            "   `/backup` - Sao lưu dữ liệu\n"
            "   `/status` - Trạng thái bot\n"
            "   `/reset` - Reset vị trí theo dõi\n"
            "   `/cancel` - Hủy thao tác hiện tại\n\n"
            "✨ **Tính năng nổi bật:**\n"
            "🎯 Cảnh báo ngân sách thông minh\n"
            "📊 So sánh xu hướng chi tiêu\n"
            "🔍 Tìm kiếm & lọc dữ liệu mạnh mẽ\n"
            "🧠 Phân tích insight tự động\n"
            "📈 Dự đoán chi tiêu cuối tháng\n\n"
            "💡 **Ví dụ nhanh:**\n"
            "`/quick Cafe|35000|Giải trí|Hoàng Việt|Với bạn`"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def quick_add(self, update: Update, context):
        """Handle /quick command for fast expense adding"""
        try:
            # Get text after /quick command
            text = update.message.text[7:].strip()  # Remove '/quick ' prefix
            
            if not text:
                await update.message.reply_text(
                    "❌ **Cú pháp sai!**\n\n"
                    "✅ **Cú pháp đúng:**\n"
                    "`/quick Mô tả|Số tiền|Danh mục|Người chi|Ghi chú`\n\n"
                    "💡 **Ví dụ:**\n"
                    "`/quick Ăn trưa|50000|Ăn uống|Hoàng Việt|Cơm văn phòng`",
                    parse_mode='Markdown'
                )
                return
            
            # Parse the input
            parts = text.split('|')
            
            if len(parts) < 4:
                await update.message.reply_text(
                    "❌ **Thiếu thông tin!**\n\n"
                    "Cần ít nhất: `Mô tả|Số tiền|Danh mục|Người chi`\n"
                    "Ghi chú là tùy chọn.",
                    parse_mode='Markdown'
                )
                return
            
            description = parts[0].strip()
            try:
                amount = int(parts[1].strip())
            except ValueError:
                await update.message.reply_text("❌ Số tiền phải là số nguyên!")
                return
            
            category = parts[2].strip()
            person = parts[3].strip()
            note = parts[4].strip() if len(parts) > 4 else ""
            
            # Add to sheet
            if self.add_expense_to_sheet(description, amount, category, person, note):
                success_message = (
                    f"✅ **Đã thêm chi phí thành công!**\n\n"
                    f"📝 **Mô tả:** {description}\n"
                    f"💰 **Số tiền:** {amount:,} VNĐ\n"
                    f"📂 **Danh mục:** {category}\n"
                    f"👤 **Người chi:** {person}\n"
                    f"📝 **Ghi chú:** {note if note else 'Không có'}\n"
                    f"📅 **Ngày:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                    f"📊 **Sheet:** {self.current_sheet.title}"
                )
                
                # Check budget and add warning if needed
                budget_warning = await self.check_budget_warning()
                if budget_warning:
                    success_message += f"\n\n{budget_warning}"
                
                await update.message.reply_text(success_message, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Có lỗi xảy ra khi thêm dữ liệu!")
                
        except Exception as e:
            logger.error(f"Error in quick_add: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra! Vui lòng thử lại.")
    
    async def start_add_expense(self, update: Update, context):
        """Start the add expense conversation"""
        await update.message.reply_text(
            f"💰 **Thêm chi phí mới vào {self.current_sheet.title}**\n\n"
            "📝 Nhập mô tả chi phí:\n"
            "(Ví dụ: Ăn trưa, Xăng xe, Mua sách...)"
        )
        return DESCRIPTION
    
    async def get_description(self, update: Update, context):
        """Get expense description"""
        context.user_data['description'] = update.message.text
        await update.message.reply_text(
            f"✅ Mô tả: {update.message.text}\n\n"
            "💰 Nhập số tiền (VNĐ):\n"
            "(Chỉ nhập số, ví dụ: 50000)"
        )
        return AMOUNT
    
    async def get_amount(self, update: Update, context):
        """Get expense amount"""
        try:
            amount = int(update.message.text.replace(',', '').replace('.', ''))
            context.user_data['amount'] = amount
            await update.message.reply_text(
                f"✅ Số tiền: {amount:,} VNĐ\n\n"
                "📂 Nhập danh mục:\n"
                "(Ví dụ: Ăn uống, Di chuyển, Giải trí, Học tập, Hóa đơn...)"
            )
            return CATEGORY
        except ValueError:
            await update.message.reply_text(
                "❌ Vui lòng nhập số hợp lệ!\n"
                "Ví dụ: 50000 hoặc 50,000"
            )
            return AMOUNT
    
    async def get_category(self, update: Update, context):
        """Get expense category"""
        context.user_data['category'] = update.message.text
        await update.message.reply_text(
            f"✅ Danh mục: {update.message.text}\n\n"
            "👤 Nhập tên người chi:\n"
            "(Ví dụ: Hoàng Việt, Anh Tài, Chị Hoa...)"
        )
        return PERSON
    
    async def get_person(self, update: Update, context):
        """Get person who made the expense"""
        context.user_data['person'] = update.message.text
        await update.message.reply_text(
            f"✅ Người chi: {update.message.text}\n\n"
            "📝 Nhập ghi chú (tùy chọn):\n"
            "Gõ 'skip' để bỏ qua hoặc nhập ghi chú của bạn"
        )
        return NOTE
    
    async def get_note(self, update: Update, context):
        """Get expense note and finalize"""
        note = "" if update.message.text.lower() == 'skip' else update.message.text
        context.user_data['note'] = note
        
        # Get all data
        description = context.user_data['description']
        amount = context.user_data['amount']
        category = context.user_data['category']
        person = context.user_data['person']
        
        # Add to sheet
        if self.add_expense_to_sheet(description, amount, category, person, note):
            success_message = (
                f"🎉 **Chi phí đã được thêm thành công!**\n\n"
                f"📝 **Mô tả:** {description}\n"
                f"💰 **Số tiền:** {amount:,} VNĐ\n"
                f"📂 **Danh mục:** {category}\n"
                f"👤 **Người chi:** {person}\n"
                f"📝 **Ghi chú:** {note if note else 'Không có'}\n"
                f"📅 **Ngày:** {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                f"📊 **Sheet:** {self.current_sheet.title}\n\n"
                f"💡 Gõ `/add` để thêm chi phí khác hoặc `/summary` để xem tổng kết!"
            )
            
            # Check budget and add warning if needed
            budget_warning = await self.check_budget_warning()
            if budget_warning:
                success_message += f"\n\n{budget_warning}"
            
            await update.message.reply_text(success_message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Có lỗi xảy ra khi lưu dữ liệu! Vui lòng thử lại.")
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def cancel(self, update: Update, context):
        """Cancel the conversation"""
        context.user_data.clear()
        await update.message.reply_text(
            "🚫 **Đã hủy thêm chi phí.**\n\n"
            "💡 Gõ `/add` để bắt đầu lại!"
        )
        return ConversationHandler.END
    
    async def status_command(self, update: Update, context):
        """Handle /status command"""
        try:
            current_count = self.get_current_row_count()
            summary = self.get_monthly_summary()
            
            status_message = (
                f"📊 **TRẠNG THÁI BOT:**\n\n"
                f"📈 **Sheet hiện tại:** {self.current_sheet.title}\n"
                f"📊 **Tổng số dòng:** {current_count}\n"
                f"📝 **Dòng dữ liệu:** {current_count - 1} (trừ header)\n"
                f"💰 **Tổng chi tháng này:** {summary['total']:,} VNĐ\n"
                f"📝 **Số giao dịch:** {summary['count']} lần\n"
                f"⏱️ **Kiểm tra mỗi:** {self.check_interval} giây\n"
                f"🕐 **Thời gian:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                f"🤖 **Bot đang hoạt động bình thường!**"
            )
            await update.message.reply_text(status_message, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi khi kiểm tra trạng thái: {e}")
    
    async def reset_position_command(self, update: Update, context):
        """Handle /reset command to reset row position tracking"""
        try:
            # Get current actual row count
            current_count = self.get_current_row_count()
            old_position = self.last_row_count
            
            # Update the tracking
            self.last_row_count = current_count
            self.save_last_row_count(current_count)
            
            reset_message = (
                f"🔄 **RESET VỊ TRÍ THÀNH CÔNG!**\n\n"
                f"📊 **Sheet:** {self.current_sheet.title}\n"
                f"📍 **Vị trí cũ:** {old_position}\n"
                f"📍 **Vị trí mới:** {current_count}\n"
                f"📝 **Dữ liệu thực tế:** {current_count - 1} dòng (trừ header)\n\n"
                f"✅ Bot sẽ theo dõi từ vị trí {current_count} trở đi"
            )
            await update.message.reply_text(reset_message, parse_mode='Markdown')
            
            logger.info(f"Position reset from {old_position} to {current_count} for sheet {self.current_sheet.title}")
            
        except Exception as e:
            logger.error(f"Error in reset command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi reset vị trí!")
    
    def get_expenses_by_date_range(self, start_date, end_date, sheet_name=None):
        """Get expenses within a date range"""
        try:
            if sheet_name is None:
                sheet = self.current_sheet
                sheet_name = sheet.title
            else:
                sheet = self.workbook.worksheet(sheet_name)
            
            # Get all data (excluding header)
            all_data = sheet.get_all_values()[1:]
            
            # Filter rows by date range
            filtered_rows = []
            for row in all_data:
                if len(row) >= 3 and row[0].strip() and row[2].strip():
                    try:
                        # Parse date (format: dd/mm/yyyy)
                        row_date = datetime.strptime(row[0], '%d/%m/%Y').date()
                        if start_date <= row_date <= end_date:
                            # Check if amount is valid
                            if row[2].replace(',', '').isdigit():
                                filtered_rows.append(row)
                    except ValueError:
                        continue  # Skip invalid date formats
            
            return filtered_rows
        except Exception as e:
            logger.error(f"Error getting expenses by date range: {e}")
            return []
    
    def calculate_summary_from_rows(self, rows):
        """Calculate summary statistics from expense rows"""
        if not rows:
            return {
                'total': 0,
                'count': 0,
                'average': 0,
                'by_category': {},
                'by_person': {}
            }
        
        total = sum(int(row[2].replace(',', '')) for row in rows)
        count = len(rows)
        average = total / count if count > 0 else 0
        
        # Group by category
        by_category = {}
        for row in rows:
            category = row[3] if len(row) > 3 and row[3].strip() else 'Khác'
            amount = int(row[2].replace(',', ''))
            by_category[category] = by_category.get(category, 0) + amount
        
        # Group by person
        by_person = {}
        for row in rows:
            person = row[4] if len(row) > 4 and row[4].strip() else 'Không rõ'
            amount = int(row[2].replace(',', ''))
            by_person[person] = by_person.get(person, 0) + amount
        
        return {
            'total': total,
            'count': count,
            'average': average,
            'by_category': by_category,
            'by_person': by_person
        }
    
    async def today_command(self, update: Update, context):
        """Handle /today command - show today's expenses"""
        try:
            today = date.today()
            rows = self.get_expenses_by_date_range(today, today)
            summary = self.calculate_summary_from_rows(rows)
            
            message = (
                f"📅 **CHI TIÊU HÔM NAY ({today.strftime('%d/%m/%Y')})**\n\n"
                f"💰 **Tổng chi tiêu:** {summary['total']:,} VNĐ\n"
                f"📝 **Số giao dịch:** {summary['count']} lần\n"
            )
            
            if summary['count'] > 0:
                message += f"📈 **Trung bình/giao dịch:** {summary['average']:,.0f} VNĐ\n\n"
                
                # Show detailed transactions
                message += "📋 **CHI TIẾT:\n"
                for i, row in enumerate(rows, 1):
                    amount = int(row[2].replace(',', ''))
                    description = row[1] if len(row) > 1 else 'Không có mô tả'
                    category = row[3] if len(row) > 3 else 'Khác'
                    person = row[4] if len(row) > 4 else 'Không rõ'
                    message += f"{i}. {description} - {amount:,} VNĐ ({category}) - {person}\n"
                
                if summary['by_category']:
                    message += f"\n📂 **Theo danh mục:**\n"
                    for category, amount in sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True):
                        message += f"• {category}: {amount:,} VNĐ\n"
            else:
                message += "\n🎉 **Chưa có chi tiêu nào hôm nay!**"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in today command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi lấy dữ liệu hôm nay!")
    
    async def week_command(self, update: Update, context):
        """Handle /week command - show this week's expenses"""
        try:
            today = date.today()
            # Get start of week (Monday)
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            rows = self.get_expenses_by_date_range(start_of_week, end_of_week)
            summary = self.calculate_summary_from_rows(rows)
            
            message = (
                f"📊 **CHI TIÊU TUẦN NÀY**\n"
                f"📅 ({start_of_week.strftime('%d/%m')} - {end_of_week.strftime('%d/%m/%Y')})\n\n"
                f"💰 **Tổng chi tiêu:** {summary['total']:,} VNĐ\n"
                f"📝 **Số giao dịch:** {summary['count']} lần\n"
            )
            
            if summary['count'] > 0:
                daily_avg = summary['total'] / 7
                message += f"📈 **Trung bình/ngày:** {daily_avg:,.0f} VNĐ\n"
                message += f"📈 **Trung bình/giao dịch:** {summary['average']:,.0f} VNĐ\n\n"
                
                # Group by day
                daily_expenses = {}
                for row in rows:
                    row_date = datetime.strptime(row[0], '%d/%m/%Y').date()
                    date_str = row_date.strftime('%d/%m (%A)')
                    if date_str not in daily_expenses:
                        daily_expenses[date_str] = []
                    daily_expenses[date_str].append(row)
                
                message += "📅 **Chi tiết theo ngày:**\n"
                for day_str in sorted(daily_expenses.keys()):
                    day_rows = daily_expenses[day_str]
                    day_total = sum(int(row[2].replace(',', '')) for row in day_rows)
                    message += f"• {day_str}: {day_total:,} VNĐ ({len(day_rows)} giao dịch)\n"
                
                if summary['by_category']:
                    message += f"\n📂 **Top danh mục:**\n"
                    top_categories = sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True)[:5]
                    for category, amount in top_categories:
                        percentage = (amount / summary['total'] * 100)
                        message += f"• {category}: {amount:,} VNĐ ({percentage:.1f}%)\n"
            else:
                message += "\n🎉 **Chưa có chi tiêu nào tuần này!**"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in week command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi lấy dữ liệu tuần!")
    
    async def daily_command(self, update: Update, context):
        """Handle /daily command - show daily breakdown for current month"""
        try:
            # Get current month data
            all_rows = self.get_expenses_by_date_range(
                date.today().replace(day=1),  # First day of month
                date.today()  # Today
            )
            
            if not all_rows:
                await update.message.reply_text("❌ Chưa có dữ liệu chi tiêu tháng này!")
                return
            
            # Group by date
            daily_summary = {}
            for row in all_rows:
                row_date = datetime.strptime(row[0], '%d/%m/%Y').date()
                date_str = row_date.strftime('%d/%m')
                
                if date_str not in daily_summary:
                    daily_summary[date_str] = {
                        'total': 0,
                        'count': 0,
                        'transactions': []
                    }
                
                amount = int(row[2].replace(',', ''))
                daily_summary[date_str]['total'] += amount
                daily_summary[date_str]['count'] += 1
                daily_summary[date_str]['transactions'].append({
                    'description': row[1] if len(row) > 1 else 'Không có mô tả',
                    'amount': amount,
                    'category': row[3] if len(row) > 3 else 'Khác',
                    'person': row[4] if len(row) > 4 else 'Không rõ'
                })
            
            # Sort by date
            sorted_days = sorted(daily_summary.keys(), key=lambda x: datetime.strptime(x + '/2025', '%d/%m/%Y'))
            
            message = f"📊 **CHI TIÊU THEO NGÀY - {self.current_sheet.title.upper()}**\n\n"
            
            total_month = sum(day['total'] for day in daily_summary.values())
            total_transactions = sum(day['count'] for day in daily_summary.values())
            
            message += f"💰 **Tổng tháng:** {total_month:,} VNĐ ({total_transactions} giao dịch)\n"
            message += f"📈 **Trung bình/ngày:** {total_month/len(sorted_days):,.0f} VNĐ\n\n"
            
            # Show daily breakdown
            for date_str in sorted_days[-10:]:  # Show last 10 days to avoid too long message
                day_data = daily_summary[date_str]
                message += f"📅 **{date_str}**: {day_data['total']:,} VNĐ ({day_data['count']} giao dịch)\n"
                
                # Show top 3 transactions for the day
                top_transactions = sorted(day_data['transactions'], key=lambda x: x['amount'], reverse=True)
                for i, trans in enumerate(top_transactions, 1):
                    message += f"   {i}. {trans['description']} - {trans['amount']:,} VNĐ ({trans['category']})\n"
                message += "\n"
            
            if len(sorted_days) > 10:
                message += f"📝 *Hiển thị 10 ngày gần nhất. Tổng có {len(sorted_days)} ngày có chi tiêu.*"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in daily command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi lấy dữ liệu hàng ngày!")
    
    async def budget_command(self, update: Update, context):
        """Handle /budget command"""
        try:
            # Check if user wants to see current budget or set new one
            text = update.message.text[8:].strip()  # Remove '/budget ' prefix
            
            if text:
                # Try to set budget directly
                try:
                    amount = int(text.replace(',', '').replace('.', ''))
                    self.save_monthly_budget(amount)
                    
                    await update.message.reply_text(
                        f"✅ **Đã đặt ngân sách tháng:** {amount:,} VNĐ\n\n"
                        f"💡 Gõ `/budget` để xem trạng thái ngân sách",
                        parse_mode='Markdown'
                    )
                    return ConversationHandler.END
                except ValueError:
                    await update.message.reply_text("❌ Số tiền không hợp lệ!")
                    return ConversationHandler.END
            
            # Show current budget status
            budget_status = self.get_budget_status()
            
            if budget_status is None:
                await update.message.reply_text(
                    "💰 **QUẢN LÝ NGÂN SÁCH**\n\n"
                    "❌ Chưa đặt ngân sách cho tháng này\n\n"
                    "💡 Nhập số tiền ngân sách (VNĐ):\n"
                    "Ví dụ: 5000000 (5 triệu)"
                )
                return BUDGET_AMOUNT
            
            # Show budget status
            message = f"💰 **NGÂN SÁCH {self.current_sheet.title.upper()}**\n\n"
            message += f"🎯 **Ngân sách:** {budget_status['budget']:,} VNĐ\n"
            message += f"💸 **Đã chi:** {budget_status['spent']:,} VNĐ\n"
            
            if budget_status['over_budget']:
                message += f"🚨 **Vượt ngân sách:** {abs(budget_status['remaining']):,} VNĐ\n"
                message += f"📊 **Tỷ lệ:** {budget_status['percentage']:.1f}% ⚠️\n\n"
                message += "⚠️ **CẢNH BÁO: Bạn đã vượt ngân sách!**"
            else:
                message += f"💰 **Còn lại:** {budget_status['remaining']:,} VNĐ\n"
                message += f"📊 **Đã dùng:** {budget_status['percentage']:.1f}%\n\n"
                
                if budget_status['percentage'] >= 80:
                    message += "⚠️ **CẢNH BÁO: Sắp hết ngân sách!**"
                elif budget_status['percentage'] >= 60:
                    message += "⚡ **CHÚ Ý: Đã dùng hơn 60% ngân sách**"
                else:
                    message += "✅ **Ngân sách đang an toàn**"
            
            # Add progress bar
            filled = int(budget_status['percentage'] / 10)
            empty = 10 - filled
            progress_bar = "█" * filled + "░" * empty
            message += f"\n\n📊 {progress_bar} {budget_status['percentage']:.1f}%"
            
            message += f"\n\n💡 Gõ `/budget [số tiền]` để đặt lại ngân sách"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in budget command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra!")
            return ConversationHandler.END
    
    async def set_budget_amount(self, update: Update, context):
        """Set budget amount"""
        try:
            amount = int(update.message.text.replace(',', '').replace('.', ''))
            self.save_monthly_budget(amount)
            
            message = (
                f"✅ **Đã đặt ngân sách thành công!**\n\n"
                f"💰 **Ngân sách tháng:** {amount:,} VNĐ\n"
                f"📊 **Sheet:** {self.current_sheet.title}\n\n"
                f"💡 Bot sẽ cảnh báo khi bạn chi gần hết ngân sách"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ Vui lòng nhập số hợp lệ!\n"
                "Ví dụ: 5000000 hoặc 5,000,000"
            )
            return BUDGET_AMOUNT
    
    async def compare_command(self, update: Update, context):
        """Handle /compare command"""
        try:
            # Get all month sheets
            worksheets = self.workbook.worksheets()
            month_sheets = [ws for ws in worksheets if 'Tháng' in ws.title]
            
            if len(month_sheets) < 2:
                await update.message.reply_text("❌ Cần ít nhất 2 tháng để so sánh!")
                return
            
            # Get summaries for all months
            month_data = []
            for sheet in month_sheets:
                summary = self.get_monthly_summary(sheet.title)
                if summary and summary['total'] > 0:
                    month_data.append({
                        'name': sheet.title,
                        'total': summary['total'],
                        'count': summary['count'],
                        'average': summary['average'],
                        'by_category': summary['by_category']
                    })
            
            if len(month_data) < 2:
                await update.message.reply_text("❌ Cần ít nhất 2 tháng có dữ liệu để so sánh!")
                return
            
            # Sort by month (latest first)
            month_data.sort(key=lambda x: x['name'], reverse=True)
            
            message = "📊 **SO SÁNH CÁC THÁNG**\n\n"
            
            # Show overall comparison
            for i, month in enumerate(month_data[:3]):  # Show top 3 months
                rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
                message += f"{rank_emoji} **{month['name']}**\n"
                message += f"   💰 {month['total']:,} VNĐ ({month['count']} giao dịch)\n"
                message += f"   📈 {month['average']:,.0f} VNĐ/giao dịch\n\n"
            
            # Compare latest 2 months
            if len(month_data) >= 2:
                current = month_data[0]
                previous = month_data[1]
                
                diff = current['total'] - previous['total']
                diff_percent = (diff / previous['total']) * 100 if previous['total'] > 0 else 0
                
                message += "📈 **SO SÁNH GẦN NHẤT:**\n"
                message += f"🆚 {current['name']} vs {previous['name']}\n"
                
                if diff > 0:
                    message += f"📈 Tăng {diff:,} VNĐ (+{diff_percent:.1f}%)\n"
                elif diff < 0:
                    message += f"📉 Giảm {abs(diff):,} VNĐ ({diff_percent:.1f}%)\n"
                else:
                    message += f"➡️ Không thay đổi\n"
                
                # Category comparison
                message += f"\n📂 **Thay đổi theo danh mục:**\n"
                current_categories = current['by_category']
                previous_categories = previous['by_category']
                
                all_categories = set(current_categories.keys()) | set(previous_categories.keys())
                category_changes = []
                
                for category in all_categories:
                    current_amount = current_categories.get(category, 0)
                    previous_amount = previous_categories.get(category, 0)
                    change = current_amount - previous_amount
                    
                    if abs(change) > 10000:  # Only show significant changes
                        category_changes.append((category, change, current_amount, previous_amount))
                
                # Sort by absolute change
                category_changes.sort(key=lambda x: abs(x[1]), reverse=True)
                
                for category, change, current_amt, previous_amt in category_changes[:5]:
                    if change > 0:
                        message += f"📈 {category}: +{change:,} VNĐ\n"
                    else:
                        message += f"📉 {category}: {change:,} VNĐ\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in compare command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi so sánh!")
    
    async def search_command(self, update: Update, context):
        """Handle /search command"""
        try:
            # Check if search query provided directly
            text = update.message.text[8:].strip()  # Remove '/search ' prefix
            
            if text:
                # Process search directly
                await self.process_search_query(update, text)
                return ConversationHandler.END
            
            await update.message.reply_text(
                "🔍 **TÌM KIẾM GIAO DỊCH**\n\n"
                "💡 Nhập từ khóa để tìm kiếm:\n"
                "• Mô tả: cafe, ăn trưa, xăng\n"
                "• Danh mục: ăn uống, di chuyển\n"
                "• Người chi: Hoàng, Tài\n"
                "• Số tiền: >100000, <50000\n\n"
                "📝 Ví dụ: cafe, >50000, Hoàng Việt"
            )
            return SEARCH_QUERY
            
        except Exception as e:
            logger.error(f"Error in search command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra!")
            return ConversationHandler.END
    
    async def process_search(self, update: Update, context):
        """Process search query"""
        query = update.message.text
        await self.process_search_query(update, query)
        return ConversationHandler.END
    
    async def process_search_query(self, update, query):
        """Process search query and return results"""
        try:
            # Get all data from current month
            all_data = self.current_sheet.get_all_values()[1:]  # Skip header
            results = []
            
            # Filter data based on query
            for i, row in enumerate(all_data, 2):  # Start from row 2 (after header)
                if len(row) >= 3 and row[2].strip():
                    # Check if query matches any field
                    match = False
                    
                    # Handle amount filters
                    if query.startswith('>') or query.startswith('<'):
                        try:
                            operator = query[0]
                            amount_threshold = int(query[1:].replace(',', ''))
                            row_amount = int(row[2].replace(',', ''))
                            
                            if operator == '>' and row_amount > amount_threshold:
                                match = True
                            elif operator == '<' and row_amount < amount_threshold:
                                match = True
                        except ValueError:
                            pass
                    else:
                        # Text search in all fields
                        search_text = query.lower()
                        for field in row[:6]:  # Search in all main fields
                            if search_text in field.lower():
                                match = True
                                break
                    
                    if match:
                        results.append((i, row))
            
            if not results:
                await update.message.reply_text(
                    f"❌ **Không tìm thấy kết quả cho:** `{query}`\n\n"
                    f"💡 Thử tìm kiếm khác hoặc `/search` để tìm kiếm mới",
                    parse_mode='Markdown'
                )
                return
            
            # Format results
            message = f"🔍 **KẾT QUẢ TÌM KIẾM: '{query}'**\n"
            message += f"📊 Tìm thấy {len(results)} giao dịch\n\n"
            
            total_found = 0
            for i, (row_num, row) in enumerate(results[:10], 1):  # Show max 10 results
                try:
                    amount = int(row[2].replace(',', ''))
                    total_found += amount
                    
                    message += f"**{i}. Dòng #{row_num}**\n"
                    message += f"📅 {row[0]} | 💰 {amount:,} VNĐ\n"
                    message += f"📝 {row[1][:30]}{'...' if len(row[1]) > 30 else ''}\n"
                    message += f"📂 {row[3] if len(row) > 3 else 'N/A'} | "
                    message += f"👤 {row[4] if len(row) > 4 else 'N/A'}\n\n"
                except:
                    continue
            
            if len(results) > 10:
                message += f"📝 *Hiển thị 10/{len(results)} kết quả đầu tiên*\n"
            
            message += f"💰 **Tổng cộng:** {total_found:,} VNĐ"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error processing search: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi tìm kiếm!")
    
    async def filter_command(self, update: Update, context):
        """Handle /filter command"""
        try:
            # Parse filter parameters
            text = update.message.text[8:].strip()  # Remove '/filter ' prefix
            
            if not text:
                await update.message.reply_text(
                    "🔽 **LỌC DỮ LIỆU**\n\n"
                    "💡 **Cú pháp:**\n"
                    "• `/filter >100000` - Chi tiêu trên 100k\n"
                    "• `/filter <50000` - Chi tiêu dưới 50k\n"
                    "• `/filter person:Hoàng` - Theo người chi\n"
                    "• `/filter category:Ăn uống` - Theo danh mục\n"
                    "• `/filter date:06/08` - Theo ngày\n\n"
                    "📝 **Ví dụ:** `/filter >200000 category:Giải trí`"
                )
                return
            
            # Parse filters
            filters = text.split()
            all_data = self.current_sheet.get_all_values()[1:]  # Skip header
            filtered_results = []
            
            for i, row in enumerate(all_data, 2):
                if len(row) >= 3 and row[2].strip():
                    match = True
                    
                    for filter_param in filters:
                        if not self.apply_filter(row, filter_param):
                            match = False
                            break
                    
                    if match:
                        filtered_results.append((i, row))
            
            if not filtered_results:
                await update.message.reply_text(f"❌ Không tìm thấy dữ liệu phù hợp với bộ lọc: `{text}`")
                return
            
            # Calculate summary
            total_amount = 0
            categories = {}
            persons = {}
            
            for _, row in filtered_results:
                try:
                    amount = int(row[2].replace(',', ''))
                    total_amount += amount
                    
                    category = row[3] if len(row) > 3 else 'Khác'
                    person = row[4] if len(row) > 4 else 'Không rõ'
                    
                    categories[category] = categories.get(category, 0) + amount
                    persons[person] = persons.get(person, 0) + amount
                except:
                    continue
            
            # Format results
            message = f"🔽 **KẾT QUẢ LỌC: {text}**\n\n"
            message += f"📊 **Tổng quan:**\n"
            message += f"💰 Tổng tiền: {total_amount:,} VNĐ\n"
            message += f"📝 Số giao dịch: {len(filtered_results)}\n"
            message += f"📈 Trung bình: {total_amount//len(filtered_results):,} VNĐ\n\n"
            
            # Show top categories
            if categories:
                message += "📂 **Top danh mục:**\n"
                sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
                for category, amount in sorted_categories[:3]:
                    percentage = (amount / total_amount) * 100
                    message += f"• {category}: {amount:,} VNĐ ({percentage:.1f}%)\n"
                message += "\n"
            
            # Show recent transactions
            message += "📋 **Giao dịch gần đây:**\n"
            for i, (row_num, row) in enumerate(filtered_results[-5:], 1):  # Show last 5
                try:
                    amount = int(row[2].replace(',', ''))
                    message += f"{i}. {row[1][:25]}{'...' if len(row[1]) > 25 else ''} - {amount:,} VNĐ\n"
                except:
                    continue
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in filter command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi lọc dữ liệu!")
    
    def apply_filter(self, row, filter_param):
        """Apply a single filter to a row"""
        try:
            if filter_param.startswith('>'):
                amount_threshold = int(filter_param[1:].replace(',', ''))
                row_amount = int(row[2].replace(',', ''))
                return row_amount > amount_threshold
            
            elif filter_param.startswith('<'):
                amount_threshold = int(filter_param[1:].replace(',', ''))
                row_amount = int(row[2].replace(',', ''))
                return row_amount < amount_threshold
            
            elif filter_param.startswith('person:'):
                person_filter = filter_param[7:].lower()
                row_person = row[4].lower() if len(row) > 4 else ''
                return person_filter in row_person
            
            elif filter_param.startswith('category:'):
                category_filter = filter_param[9:].lower()
                row_category = row[3].lower() if len(row) > 3 else ''
                return category_filter in row_category
            
            elif filter_param.startswith('date:'):
                date_filter = filter_param[5:]
                row_date = row[0] if len(row) > 0 else ''
                return date_filter in row_date
            
            else:
                # Generic text search
                search_text = filter_param.lower()
                for field in row[:6]:
                    if search_text in field.lower():
                        return True
                return False
                
        except:
            return False
    
    async def insight_command(self, update: Update, context):
        """Handle /insight command - provide smart analysis"""
        try:
            summary = self.get_monthly_summary()
            if not summary or summary['total'] == 0:
                await update.message.reply_text("❌ Chưa có dữ liệu để phân tích!")
                return
            
            # Get data from previous month for comparison
            current_month = datetime.now()
            if current_month.month == 1:
                prev_month = current_month.replace(year=current_month.year-1, month=12)
            else:
                prev_month = current_month.replace(month=current_month.month-1)
            
            prev_sheet_name = self.get_sheet_name_for_month(prev_month.year, prev_month.month)
            prev_summary = None
            
            try:
                prev_summary = self.get_monthly_summary(prev_sheet_name)
            except:
                pass
            
            message = f"🧠 **PHÂN TÍCH THÔNG MINH - {summary['sheet_name'].upper()}**\n\n"
            
            # Basic insights
            avg_per_day = summary['total'] / datetime.now().day
            message += f"📊 **Thống kê cơ bản:**\n"
            message += f"• Trung bình/ngày: {avg_per_day:,.0f} VNĐ\n"
            message += f"• Dự đoán cuối tháng: {avg_per_day * 30:,.0f} VNĐ\n\n"
            
            # Category analysis
            if summary['by_category']:
                message += "🎯 **Phân tích danh mục:**\n"
                sorted_categories = sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True)
                
                top_category = sorted_categories[0]
                message += f"• Danh mục chi nhiều nhất: {top_category[0]} ({top_category[1]:,} VNĐ)\n"
                
                if len(sorted_categories) > 1:
                    second_category = sorted_categories[1]
                    diff = top_category[1] - second_category[1]
                    message += f"• Chênh lệch với hạng 2: {diff:,} VNĐ\n"
                
                # Spending pattern
                if summary['count'] > 0:
                    avg_transaction = summary['total'] / summary['count']
                    message += f"• Giao dịch trung bình: {avg_transaction:,.0f} VNĐ\n"
                    
                    # Find large transactions
                    all_data = self.current_sheet.get_all_values()[1:]
                    large_transactions = 0
                    for row in all_data:
                        if len(row) >= 3 and row[2].strip():
                            try:
                                amount = int(row[2].replace(',', ''))
                                if amount > avg_transaction * 2:
                                    large_transactions += 1
                            except:
                                continue
                    
                    if large_transactions > 0:
                        message += f"• Giao dịch lớn (>2x TB): {large_transactions} lần\n"
                
                message += "\n"
            
            # Comparison with previous month
            if prev_summary and prev_summary['total'] > 0:
                diff = summary['total'] - prev_summary['total']
                diff_percent = (diff / prev_summary['total']) * 100
                
                message += "📈 **So sánh tháng trước:**\n"
                if diff > 0:
                    message += f"• Chi tiêu tăng {diff:,} VNĐ (+{diff_percent:.1f}%)\n"
                elif diff < 0:
                    message += f"• Chi tiêu giảm {abs(diff):,} VNĐ ({diff_percent:.1f}%)\n"
                else:
                    message += f"• Chi tiêu không đổi\n"
                
                # Category changes
                current_categories = summary['by_category']
                prev_categories = prev_summary['by_category']
                
                biggest_increase = None
                biggest_increase_amount = 0
                
                for category, amount in current_categories.items():
                    prev_amount = prev_categories.get(category, 0)
                    increase = amount - prev_amount
                    if increase > biggest_increase_amount:
                        biggest_increase = category
                        biggest_increase_amount = increase
                
                if biggest_increase and biggest_increase_amount > 10000:
                    message += f"• Tăng mạnh nhất: {biggest_increase} (+{biggest_increase_amount:,} VNĐ)\n"
                
                message += "\n"
            
            # Budget insights
            budget_status = self.get_budget_status()
            if budget_status:
                message += "💰 **Phân tích ngân sách:**\n"
                
                days_left = 30 - datetime.now().day
                if days_left > 0 and budget_status['remaining'] > 0:
                    daily_budget_left = budget_status['remaining'] / days_left
                    message += f"• Có thể chi: {daily_budget_left:,.0f} VNĐ/ngày ({days_left} ngày còn lại)\n"
                
                if budget_status['percentage'] > 100:
                    message += f"• ⚠️ Đã vượt ngân sách {budget_status['percentage']-100:.1f}%\n"
                elif budget_status['percentage'] > 80:
                    message += f"• ⚡ Sắp hết ngân sách (đã dùng {budget_status['percentage']:.1f}%)\n"
                else:
                    message += f"• ✅ Ngân sách an toàn ({budget_status['percentage']:.1f}%)\n"
                
                message += "\n"
            
            # Smart recommendations
            message += "💡 **Gợi ý thông minh:**\n"
            
            if summary['by_category']:
                # Find dominant category
                top_category_name, top_category_amount = max(summary['by_category'].items(), key=lambda x: x[1])
                top_percentage = (top_category_amount / summary['total']) * 100
                
                if top_percentage > 40:
                    message += f"• Danh mục '{top_category_name}' chiếm {top_percentage:.1f}% - cân nhắc giảm bớt\n"
                
                # Check for unusual patterns
                if summary['count'] > 50:
                    message += f"• Có {summary['count']} giao dịch trong tháng - nhiều giao dịch nhỏ\n"
                elif summary['count'] < 10:
                    message += f"• Chỉ {summary['count']} giao dịch - ít giao dịch lớn\n"
            
            # Weekly pattern analysis
            today = date.today()
            start_of_month = today.replace(day=1)
            week_data = self.get_expenses_by_date_range(start_of_month, today)
            
            if len(week_data) > 7:
                # Analyze by day of week
                weekday_spending = {i: 0 for i in range(7)}  # 0=Monday, 6=Sunday
                
                for row in week_data:
                    try:
                        row_date = datetime.strptime(row[0], '%d/%m/%Y')
                        amount = int(row[2].replace(',', ''))
                        weekday_spending[row_date.weekday()] += amount
                    except:
                        continue
                
                max_day = max(weekday_spending.items(), key=lambda x: x[1])
                weekdays = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
                
                if max_day[1] > 0:
                    message += f"• Ngày chi nhiều nhất: {weekdays[max_day[0]]} ({max_day[1]:,} VNĐ)\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in insight command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi phân tích!")
    
    async def edit_command(self, update: Update, context):
        """Handle /edit command - edit last transaction"""
        try:
            # Get all data to find the last transaction
            all_data = self.current_sheet.get_all_values()
            
            # Find the last non-empty data row
            last_row = None
            last_row_index = 0
            
            for i in range(len(all_data) - 1, 0, -1):  # Start from bottom, skip header
                if len(all_data[i]) >= 3 and all_data[i][2].strip():
                    last_row = all_data[i]
                    last_row_index = i + 1  # Convert to 1-based index
                    break
            
            if not last_row:
                await update.message.reply_text("❌ Không tìm thấy giao dịch nào để chỉnh sửa!")
                return
            
            # Show current transaction
            try:
                amount = int(last_row[2].replace(',', ''))
                message = f"✏️ **CHỈNH SỬA GIAO DỊCH (Dòng #{last_row_index})**\n\n"
                message += f"📅 **Ngày:** {last_row[0]}\n"
                message += f"📝 **Mô tả:** {last_row[1]}\n"
                message += f"💰 **Số tiền:** {amount:,} VNĐ\n"
                message += f"📂 **Danh mục:** {last_row[3] if len(last_row) > 3 else 'N/A'}\n"
                message += f"👤 **Người chi:** {last_row[4] if len(last_row) > 4 else 'N/A'}\n"
                message += f"📝 **Ghi chú:** {last_row[5] if len(last_row) > 5 else 'Không có'}\n\n"
                message += "🔧 **Chọn trường cần sửa:**\n"
                message += "1️⃣ Mô tả\n"
                message += "2️⃣ Số tiền\n"
                message += "3️⃣ Danh mục\n"
                message += "4️⃣ Người chi\n"
                message += "5️⃣ Ghi chú\n\n"
                message += "💡 Gõ số (1-5) để chọn trường cần sửa"
                
                # Store edit context
                context.user_data['edit_row'] = last_row_index
                context.user_data['edit_data'] = last_row
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                await update.message.reply_text(f"❌ Lỗi hiển thị giao dịch: {e}")
                
        except Exception as e:
            logger.error(f"Error in edit command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi chỉnh sửa!")
    
    async def delete_command(self, update: Update, context):
        """Handle /delete command - delete last transaction"""
        try:
            # Get all data to find the last transaction
            all_data = self.current_sheet.get_all_values()
            
            # Find the last non-empty data row
            last_row = None
            last_row_index = 0
            
            for i in range(len(all_data) - 1, 0, -1):  # Start from bottom, skip header
                if len(all_data[i]) >= 3 and all_data[i][2].strip():
                    last_row = all_data[i]
                    last_row_index = i + 1  # Convert to 1-based index
                    break
            
            if not last_row:
                await update.message.reply_text("❌ Không tìm thấy giao dịch nào để xóa!")
                return
            
            # Show transaction to be deleted
            try:
                amount = int(last_row[2].replace(',', ''))
                message = f"🗑️ **XÓA GIAO DỊCH (Dòng #{last_row_index})**\n\n"
                message += f"📅 **Ngày:** {last_row[0]}\n"
                message += f"📝 **Mô tả:** {last_row[1]}\n"
                message += f"💰 **Số tiền:** {amount:,} VNĐ\n"
                message += f"📂 **Danh mục:** {last_row[3] if len(last_row) > 3 else 'N/A'}\n"
                message += f"👤 **Người chi:** {last_row[4] if len(last_row) > 4 else 'N/A'}\n\n"
                message += "⚠️ **CẢNH BÁO: Thao tác này không thể hoàn tác!**\n\n"
                message += "💡 Gõ `XAC NHAN` để xóa hoặc bất kỳ gì khác để hủy"
                
                # Store delete context
                context.user_data['delete_row'] = last_row_index
                context.user_data['delete_data'] = last_row
                context.user_data['awaiting_delete_confirm'] = True
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                await update.message.reply_text(f"❌ Lỗi hiển thị giao dịch: {e}")
                
        except Exception as e:
            logger.error(f"Error in delete command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi xóa!")
    
    async def backup_command(self, update: Update, context):
        """Handle /backup command - create backup"""
        try:
            import json
            from datetime import datetime
            
            # Get current month summary
            summary = self.get_monthly_summary()
            
            # Get all data from current sheet
            all_data = self.current_sheet.get_all_values()
            
            # Create backup data structure
            backup_data = {
                'sheet_name': self.current_sheet.title,
                'backup_date': datetime.now().isoformat(),
                'summary': summary,
                'raw_data': all_data,
                'total_rows': len(all_data),
                'budget': self.monthly_budget
            }
            
            # Save to file
            backup_filename = f"backup_{self.current_sheet.title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            message = (
                f"💾 **SAO LƯU THÀNH CÔNG!**\n\n"
                f"📊 **Sheet:** {self.current_sheet.title}\n"
                f"📁 **File:** `{backup_filename}`\n"
                f"📝 **Dữ liệu:** {len(all_data)-1} giao dịch\n"
                f"💰 **Tổng tiền:** {summary['total']:,} VNĐ\n"
                f"🕐 **Thời gian:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
                f"✅ **Backup đã được lưu trong thư mục bot**"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in backup command: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra khi sao lưu!")
    
    async def handle_edit_delete_response(self, update: Update, context):
        """Handle responses for edit/delete operations"""
        try:
            text = update.message.text.strip()
            
            # Handle delete confirmation
            if context.user_data.get('awaiting_delete_confirm'):
                if text.upper() == 'XAC NHAN':
                    # Delete the row
                    row_index = context.user_data['delete_row']
                    self.current_sheet.delete_rows(row_index)
                    
                    # Update row count
                    self.last_row_count = self.get_current_row_count()
                    self.save_last_row_count(self.last_row_count)
                    
                    await update.message.reply_text(
                        f"✅ **Đã xóa giao dịch thành công!**\n\n"
                        f"🗑️ Dòng #{row_index} đã được xóa\n"
                        f"📊 Cập nhật vị trí theo dõi: {self.last_row_count}",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text("❌ **Đã hủy xóa giao dịch**")
                
                # Clear delete context
                context.user_data.pop('awaiting_delete_confirm', None)
                context.user_data.pop('delete_row', None)
                context.user_data.pop('delete_data', None)
                return
            
            # Handle edit field selection
            if 'edit_row' in context.user_data:
                if text in ['1', '2', '3', '4', '5']:
                    fields = ['description', 'amount', 'category', 'person', 'note']
                    field_names = ['Mô tả', 'Số tiền', 'Danh mục', 'Người chi', 'Ghi chú']
                    
                    selected_field = fields[int(text) - 1]
                    selected_name = field_names[int(text) - 1]
                    
                    context.user_data['edit_field'] = selected_field
                    context.user_data['edit_field_name'] = selected_name
                    
                    current_value = ""
                    data = context.user_data['edit_data']
                    
                    if selected_field == 'description' and len(data) > 1:
                        current_value = data[1]
                    elif selected_field == 'amount' and len(data) > 2:
                        current_value = data[2]
                    elif selected_field == 'category' and len(data) > 3:
                        current_value = data[3]
                    elif selected_field == 'person' and len(data) > 4:
                        current_value = data[4]
                    elif selected_field == 'note' and len(data) > 5:
                        current_value = data[5]
                    
                    await update.message.reply_text(
                        f"✏️ **Chỉnh sửa {selected_name}**\n\n"
                        f"📝 **Giá trị hiện tại:** {current_value}\n\n"
                        f"💡 Nhập giá trị mới:"
                    )
                    return
                    
                # Handle edit value input
                elif 'edit_field' in context.user_data:
                    field = context.user_data['edit_field']
                    field_name = context.user_data['edit_field_name']
                    row_index = context.user_data['edit_row']
                    
                    # Validate input based on field type
                    new_value = text
                    if field == 'amount':
                        try:
                            new_value = str(int(text.replace(',', '').replace('.', '')))
                        except ValueError:
                            await update.message.reply_text("❌ Số tiền phải là số hợp lệ!")
                            return
                    
                    # Update the cell
                    column_map = {
                        'description': 'B',
                        'amount': 'C',
                        'category': 'D',
                        'person': 'E',
                        'note': 'F'
                    }
                    
                    cell = f"{column_map[field]}{row_index}"
                    self.current_sheet.update(cell, new_value)
                    
                    formatted_value = f"{int(new_value):,} VNĐ" if field == 'amount' else new_value
                    
                    await update.message.reply_text(
                        f"✅ **Đã cập nhật thành công!**\n\n"
                        f"📝 **Trường:** {field_name}\n"
                        f"🆕 **Giá trị mới:** {formatted_value}\n"
                        f"📊 **Dòng:** #{row_index}",
                        parse_mode='Markdown'
                    )
                    
                    # Clear edit context
                    context.user_data.pop('edit_row', None)
                    context.user_data.pop('edit_data', None)
                    context.user_data.pop('edit_field', None)
                    context.user_data.pop('edit_field_name', None)
                    
        except Exception as e:
            logger.error(f"Error handling edit/delete response: {e}")
            await update.message.reply_text("❌ Có lỗi xảy ra!")
    
    async def check_for_new_rows(self):
        """Check for new rows and send notifications"""
        try:
            # Check if we need to switch to new month
            current_month_sheet_name = self.get_sheet_name_for_month()
            if self.current_sheet.title != current_month_sheet_name:
                # Send end of month summary before switching
                await self.send_month_end_summary()
                
                # Switch to new month
                self.current_sheet = self.ensure_current_month_sheet()
                self.last_row_count = self.get_last_row_count()
                
                # Send new month notification
                await self.send_new_month_notification()
            
            current_count = self.get_current_row_count()
            
            if current_count > self.last_row_count:
                logger.info(f"New rows detected: {current_count - self.last_row_count}")
                
                # Get new rows
                all_values = self.current_sheet.get_all_values()
                new_rows = all_values[self.last_row_count:]
                
                # Send notification for each new row
                for i, row in enumerate(new_rows):
                    if any(cell.strip() for cell in row):  # Only process non-empty rows
                        row_number = self.last_row_count + i + 1
                        message = self.format_row_message(row, row_number)
                        
                        # Send to chat
                        bot = Bot(token=self.telegram_bot_token)
                        await bot.send_message(
                            chat_id=self.telegram_chat_id,
                            text=message,
                            parse_mode='Markdown'
                        )
                        
                        # Add small delay between messages
                        if len(new_rows) > 1:
                            await asyncio.sleep(1)
                
                # Update last row count
                self.last_row_count = current_count
                self.save_last_row_count(current_count)
                
        except Exception as e:
            logger.error(f"Error checking for new rows: {e}")
    
    async def send_month_end_summary(self):
        """Send month end summary"""
        try:
            summary = self.get_monthly_summary()
            if summary and summary['total'] > 0:
                message = (
                    f"📊 **KẾT THÚC {summary['sheet_name'].upper()}**\n\n"
                    f"💰 **Tổng chi tiêu:** {summary['total']:,} VNĐ\n"
                    f"📝 **Số giao dịch:** {summary['count']} lần\n"
                    f"📈 **Trung bình/ngày:** {summary['total']/30:,.0f} VNĐ\n\n"
                    f"🏆 **Top danh mục:**\n"
                )
                
                # Top 3 categories
                top_categories = sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True)[:3]
                for i, (category, amount) in enumerate(top_categories, 1):
                    percentage = (amount / summary['total'] * 100)
                    message += f"{i}. {category}: {amount:,} VNĐ ({percentage:.1f}%)\n"
                
                bot = Bot(token=self.telegram_bot_token)
                await bot.send_message(
                    chat_id=self.telegram_chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending month end summary: {e}")
    
    async def send_new_month_notification(self):
        """Send new month notification"""
        try:
            message = (
                f"🎉 **CHÀO MỪNG {self.current_sheet.title.upper()}!**\n\n"
                f"📊 Đã tạo sheet mới cho tháng này\n"
                f"🎯 Hãy bắt đầu ghi chép chi tiêu!\n\n"
                f"💡 Gõ `/add` để thêm chi phí đầu tiên"
            )
            
            bot = Bot(token=self.telegram_bot_token)
            await bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error sending new month notification: {e}")
    
    def format_row_message(self, row_data, row_number):
        """Format row data into a readable message"""
        message = f"🆕 **Dòng mới được thêm vào {self.current_sheet.title}** (Dòng #{row_number})\n\n"
        
        # Updated sheet structure with 'Người chi' column
        headers = ['Ngày', 'Mô tả', 'Số tiền', 'Danh mục', 'Người chi', 'Ghi chú']
        
        for i, value in enumerate(row_data):
            if i < len(headers) and value.strip():
                if i == 2 and value.strip():  # Amount column
                    try:
                        amount = float(value.replace(',', ''))
                        message += f"💰 **{headers[i]}**: {amount:,.0f} VNĐ\n"
                    except:
                        message += f"💰 **{headers[i]}**: {value}\n"
                elif i == 4 and value.strip():  # Người chi column
                    message += f"👤 **{headers[i]}**: {value}\n"
                else:
                    message += f"📝 **{headers[i]}**: {value}\n"
        
        message += f"\n⏰ Thời gian phát hiện: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        return message
    
    async def run_bot(self):
        """Run the advanced bot"""
        logger.info("Starting Advanced Telegram Bot...")
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        
        # Send startup message
        bot = Bot(token=self.telegram_bot_token)
        startup_message = (
            f"🤖 **Advanced Telegram Bot đã khởi động!**\n\n"
            f"💡 **Gõ `/start` để xem hướng dẫn**\n"
            f"📊 **Sheet hiện tại:** {self.current_sheet.title}\n"
            f"⏱️ Kiểm tra mỗi {self.check_interval} giây\n"
            f"📝 Dòng hiện tại: {self.last_row_count}\n"
            f"🕐 Thời gian khởi động: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"✨ **Tính năng mới:** Tự động tạo sheet theo tháng & tính tổng!"
        )
        await bot.send_message(
            chat_id=self.telegram_chat_id,
            text=startup_message,
            parse_mode='Markdown'
        )
        
        # Start polling for updates
        await self.application.updater.start_polling()
        
        # Background task to check for new rows
        while True:
            try:
                await self.check_for_new_rows()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

async def main():
    """Main function"""
    try:
        bot = AdvancedTelegramBot()
        await bot.run_bot()
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
