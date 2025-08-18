import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import asyncio
from timezone_utils import (
    get_current_bangkok_time, get_current_bangkok_date, 
    format_bangkok_datetime, format_bangkok_date,
    get_bangkok_datetime_str, get_bangkok_date_str
)

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

class InteractiveTelegramBot:
    def __init__(self):
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.check_interval = int(os.getenv('CHECK_INTERVAL_SECONDS', 30))
        self.last_row_file = os.getenv('LAST_ROW_FILE', 'last_row.txt')
        
        # Setup Google Sheets
        self.setup_google_sheets()
        
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
            self.sheet = self.gc.open_by_key(self.sheets_id).sheet1
            logger.info("Google Sheets connection established successfully")
            
        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}")
            raise
    
    def get_last_row_count(self):
        """Get the last stored row count from file"""
        try:
            if os.path.exists(self.last_row_file):
                with open(self.last_row_file, 'r') as f:
                    return int(f.read().strip())
            else:
                current_count = len(self.sheet.get_all_values())
                self.save_last_row_count(current_count)
                return current_count
        except Exception as e:
            logger.error(f"Error reading last row count: {e}")
            return 0
    
    def save_last_row_count(self, count):
        """Save the current row count to file"""
        try:
            with open(self.last_row_file, 'w') as f:
                f.write(str(count))
        except Exception as e:
            logger.error(f"Error saving last row count: {e}")
    
    def get_current_row_count(self):
        """Get current number of rows in the sheet"""
        try:
            return len(self.sheet.get_all_values())
        except Exception as e:
            logger.error(f"Error getting current row count: {e}")
            return 0
    
    def add_expense_to_sheet(self, description, amount, category, person, note=""):
        """Add expense to Google Sheets"""
        try:
            date = get_bangkok_date_str()
            row_data = [date, description, str(amount), category, person, note]
            self.sheet.append_row(row_data)
            return True
        except Exception as e:
            logger.error(f"Error adding expense to sheet: {e}")
            return False
    
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
        self.application.add_handler(CommandHandler('status', self.status_command))
        self.application.add_handler(conv_handler)
    
    async def start_command(self, update: Update, context):
        """Handle /start command"""
        welcome_message = (
            "🤖 **Chào mừng đến với Bot Quản Lý Chi Phí!**\n\n"
            "📝 **Các lệnh có thể sử dụng:**\n"
            "• `/add` - Thêm chi phí mới (tương tác)\n"
            "• `/quick` - Thêm nhanh (một dòng)\n"
            "• `/status` - Xem trạng thái bot\n"
            "• `/help` - Hiển thị hướng dẫn\n"
            "• `/cancel` - Hủy thao tác hiện tại\n\n"
            "💡 **Ví dụ thêm nhanh:**\n"
            "`/quick Ăn trưa|50000|Ăn uống|Hoàng Việt|Cơm văn phòng`"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context):
        """Handle /help command"""
        help_message = (
            "📖 **Hướng dẫn sử dụng Bot:**\n\n"
            "🔹 **Thêm chi phí tương tác:**\n"
            "   Gõ `/add` và làm theo hướng dẫn\n\n"
            "🔹 **Thêm nhanh:**\n"
            "   `/quick Mô tả|Số tiền|Danh mục|Người chi|Ghi chú`\n"
            "   Ví dụ: `/quick Cafe|35000|Giải trí|Anh Tài|Với bạn`\n\n"
            "🔹 **Xem trạng thái:**\n"
            "   `/status` - Xem số dòng hiện tại\n\n"
            "🔹 **Hủy thao tác:**\n"
            "   `/cancel` - Hủy khi đang thêm chi phí\n\n"
            "📊 **Cấu trúc Google Sheets:**\n"
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
                    f"📅 **Ngày:** {get_bangkok_datetime_str()}"
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
            "💰 **Thêm chi phí mới**\n\n"
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
                f"📅 **Ngày:** {get_bangkok_datetime_str()}\n\n"
                f"💡 Gõ `/add` để thêm chi phí khác!"
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
            status_message = (
                f"📊 **Trạng thái Bot:**\n\n"
                f"📈 **Tổng số dòng:** {current_count}\n"
                f"📝 **Dòng dữ liệu:** {current_count - 1} (trừ header)\n"
                f"⏱️ **Kiểm tra mỗi:** {self.check_interval} giây\n"
                f"🕐 **Thời gian:** {get_bangkok_datetime_str()}\n\n"
                f"🤖 **Bot đang hoạt động bình thường!**"
            )
            await update.message.reply_text(status_message, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi khi kiểm tra trạng thái: {e}")
    
    async def check_for_new_rows(self):
        """Check for new rows and send notifications"""
        try:
            current_count = self.get_current_row_count()
            
            if current_count > self.last_row_count:
                logger.info(f"New rows detected: {current_count - self.last_row_count}")
                
                # Get new rows
                all_values = self.sheet.get_all_values()
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
    
    def format_row_message(self, row_data, row_number):
        """Format row data into a readable message"""
        message = f"🆕 **Dòng mới được thêm vào Google Sheets** (Dòng #{row_number})\n\n"
        
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
        
        message += f"\n⏰ Thời gian phát hiện: {get_bangkok_datetime_str()}"
        return message
    
    async def run_bot(self):
        """Run the interactive bot"""
        logger.info("Starting Interactive Telegram Bot...")
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        
        # Send startup message
        bot = Bot(token=self.telegram_bot_token)
        startup_message = (
            f"🤖 **Interactive Telegram Bot đã khởi động!**\n\n"
            f"💡 **Gõ `/start` để xem hướng dẫn**\n"
            f"📊 Đang theo dõi Google Sheets\n"
            f"⏱️ Kiểm tra mỗi {self.check_interval} giây\n"
            f"📝 Dòng hiện tại: {self.last_row_count}\n"
            f"🕐 Thời gian khởi động: {get_bangkok_datetime_str()}"
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
        bot = InteractiveTelegramBot()
        await bot.run_bot()
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
