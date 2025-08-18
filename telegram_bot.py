import os
import time
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
from telegram import Bot
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

class GoogleSheetsMonitor:
    def __init__(self):
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        self.sheets_range = os.getenv('GOOGLE_SHEETS_RANGE', 'Sheet1!A:Z')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.check_interval = int(os.getenv('CHECK_INTERVAL_SECONDS', 30))
        self.last_row_file = os.getenv('LAST_ROW_FILE', 'last_row.txt')
        
        # Initialize Telegram bot
        self.bot = Bot(token=self.telegram_bot_token)
        
        # Initialize Google Sheets client
        self.setup_google_sheets()
        
        # Get initial row count
        self.last_row_count = self.get_last_row_count()
    
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
                # If file doesn't exist, get current row count and save it
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
    
    def get_new_rows(self, start_row):
        """Get new rows starting from specified row number"""
        try:
            all_values = self.sheet.get_all_values()
            if len(all_values) > start_row:
                return all_values[start_row:]
            return []
        except Exception as e:
            logger.error(f"Error getting new rows: {e}")
            return []
    
    def format_row_message(self, row_data, row_number):
        """Format row data into a readable message"""
        message = f"🆕 **Dòng mới được thêm vào Google Sheets** (Dòng #{row_number})\n\n"
        
        # Updated sheet structure with 'Người chi' column
        # Adjust this based on your actual sheet structure
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
    
    async def send_telegram_message(self, message):
        """Send message to Telegram"""
        try:
            await self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("Message sent to Telegram successfully")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
    
    async def check_for_new_rows(self):
        """Check for new rows and send notifications"""
        try:
            current_count = self.get_current_row_count()
            
            if current_count > self.last_row_count:
                logger.info(f"New rows detected: {current_count - self.last_row_count}")
                
                # Get new rows
                new_rows = self.get_new_rows(self.last_row_count)
                
                # Send notification for each new row
                for i, row in enumerate(new_rows):
                    if any(cell.strip() for cell in row):  # Only process non-empty rows
                        row_number = self.last_row_count + i + 1
                        message = self.format_row_message(row, row_number)
                        await self.send_telegram_message(message)
                        
                        # Add small delay between messages if multiple rows
                        if len(new_rows) > 1:
                            await asyncio.sleep(1)
                
                # Update last row count
                self.last_row_count = current_count
                self.save_last_row_count(current_count)
                
        except Exception as e:
            logger.error(f"Error checking for new rows: {e}")
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        logger.info("Starting Google Sheets monitoring...")
        
        # Send startup message
        startup_message = (
            f"🤖 **Telegram Bot đã khởi động**\n\n"
            f"📊 Đang theo dõi Google Sheets\n"
            f"⏱️ Kiểm tra mỗi {self.check_interval} giây\n"
            f"📝 Dòng hiện tại: {self.last_row_count}\n"
            f"🕐 Thời gian khởi động: {get_bangkok_datetime_str()}"
        )
        await self.send_telegram_message(startup_message)
        
        while True:
            try:
                await self.check_for_new_rows()
                await asyncio.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)

async def main():
    """Main function"""
    try:
        monitor = GoogleSheetsMonitor()
        await monitor.start_monitoring()
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())
