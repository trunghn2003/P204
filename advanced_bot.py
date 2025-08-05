import os
import logging
from datetime import datetime, date
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

class AdvancedTelegramBot:
    def __init__(self):
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.check_interval = int(os.getenv('CHECK_INTERVAL_SECONDS', 30))
        self.last_row_file = os.getenv('LAST_ROW_FILE', 'last_row.txt')
        
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
        
        # Add handlers
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('quick', self.quick_add))
        self.application.add_handler(CommandHandler('summary', self.summary_command))
        self.application.add_handler(CommandHandler('month', self.month_summary_command))
        self.application.add_handler(CommandHandler('status', self.status_command))
        self.application.add_handler(CommandHandler('reset', self.reset_position_command))
        self.application.add_handler(conv_handler)
    
    async def start_command(self, update: Update, context):
        """Handle /start command"""
        welcome_message = (
            "🤖 **Chào mừng đến với Bot Quản Lý Chi Phí Nâng Cao!**\n\n"
            "📝 **Các lệnh có thể sử dụng:**\n"
            "• `/add` - Thêm chi phí mới (tương tác)\n"
            "• `/quick` - Thêm nhanh (một dòng)\n"
            "• `/summary` - Xem tổng kết tháng hiện tại\n"
            "• `/month` - Xem tổng kết tháng cụ thể\n"
            "• `/status` - Xem trạng thái bot\n"
            "• `/reset` - Reset vị trí theo dõi dòng\n"
            "• `/help` - Hiển thị hướng dẫn\n"
            "• `/cancel` - Hủy thao tác hiện tại\n\n"
            "✨ **Tính năng mới:**\n"
            "🗓️ Tự động tạo sheet cho mỗi tháng\n"
            "📊 Tính tổng chi tiêu theo tháng/danh mục/người\n"
            "📈 Báo cáo tự động đầu tháng\n\n"
            "💡 **Ví dụ thêm nhanh:**\n"
            "`/quick Ăn trưa|50000|Ăn uống|Hoàng Việt|Cơm văn phòng`"
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
            "🔹 **Thêm chi phí tương tác:**\n"
            "   Gõ `/add` và làm theo hướng dẫn\n\n"
            "🔹 **Thêm nhanh:**\n"
            "   `/quick Mô tả|Số tiền|Danh mục|Người chi|Ghi chú`\n"
            "   Ví dụ: `/quick Cafe|35000|Giải trí|Anh Tài|Với bạn`\n\n"
            "🔹 **Xem báo cáo:**\n"
            "   `/summary` - Tổng kết tháng hiện tại\n"
            "   `/month` - Danh sách tất cả các tháng\n\n"
            "🔹 **Tính năng tự động:**\n"
            "   • Bot tự tạo sheet mới cho mỗi tháng\n"
            "   • Tính tổng chi tiêu theo danh mục/người\n"
            "   • Gửi báo cáo định kỳ\n\n"
            "🔹 **Khác:**\n"
            "   `/status` - Xem trạng thái bot\n"
            "   `/reset` - Reset vị trí theo dõi dòng\n"
            "   `/cancel` - Hủy thao tác hiện tại\n\n"
            "📊 **Cấu trúc dữ liệu:**\n"
            "   Ngày | Mô tả | Số tiền | Danh mục | Người chi | Ghi chú"
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
