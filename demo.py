import asyncio
import json
from datetime import datetime
from telegram_bot import GoogleSheetsMonitor

async def demo_message_format():
    """Demo how messages will look"""
    print("🎭 Demo: Message Format")
    print("=" * 50)
    
    # Sample row data
    sample_rows = [
        ["05/08/2025", "Ăn trưa", "50000", "Ăn uống", "Hoàng Việt", "Cơm văn phòng"],
        ["05/08/2025", "Xăng xe", "200000", "Di chuyển", "Hoàng Việt", "Đổ đầy bình"],
        ["05/08/2025", "Cafe", "35000", "Giải trí", "Anh Tài", "Với bạn bè"],
    ]
    
    monitor = GoogleSheetsMonitor()
    
    for i, row in enumerate(sample_rows, 1):
        message = monitor.format_row_message(row, i)
        print(f"📱 Message {i}:")
        print(message)
        print("-" * 30)

def demo_config():
    """Show configuration example"""
    print("⚙️  Demo: Configuration")
    print("=" * 50)
    
    print("📝 File .env example:")
    print("""
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
GOOGLE_SHEETS_ID=1a2b3c4d5e6f7g8h9i0j_example_sheet_id
GOOGLE_SHEETS_RANGE=Sheet1!A:Z
CHECK_INTERVAL_SECONDS=30
""")
    
    print("🔐 credentials.json structure:")
    print("""
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
  "client_email": "telegram-bot@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
""")

def demo_sheets_structure():
    """Show Google Sheets structure"""
    print("📊 Demo: Google Sheets Structure")
    print("=" * 50)
    
    print("Cấu trúc đề xuất:")
    print("""
| A (Ngày)    | B (Mô tả)     | C (Số tiền) | D (Danh mục) | E (Người chi) | F (Ghi chú)      |
|-------------|---------------|-------------|--------------|---------------|------------------|
| 05/08/2025  | Ăn trưa       | 50000       | Ăn uống      | Hoàng Việt    | Cơm văn phòng    |
| 05/08/2025  | Xăng xe       | 200000      | Di chuyển    | Hoàng Việt    | Đổ đầy bình      |
| 05/08/2025  | Mua sách      | 150000      | Học tập      | Chị Hoa       | Sách lập trình   |
""")

async def main():
    """Main demo function"""
    print("🚀 Demo: Telegram Bot for Google Sheets")
    print("=" * 60)
    print()
    
    demo_config()
    print()
    
    demo_sheets_structure()
    print()
    
    await demo_message_format()
    print()
    
    print("✨ End of Demo")
    print("📋 Để bắt đầu:")
    print("1. Cấu hình .env và credentials.json")
    print("2. Chạy: python test_bot.py")
    print("3. Chạy: ./start_bot.sh")

if __name__ == "__main__":
    asyncio.run(main())
