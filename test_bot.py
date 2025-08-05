import asyncio
import os
from dotenv import load_dotenv
from telegram_bot import GoogleSheetsMonitor

# Load environment variables
load_dotenv()

async def test_telegram_connection():
    """Test Telegram bot connection"""
    print("🧪 Testing Telegram connection...")
    
    try:
        monitor = GoogleSheetsMonitor()
        await monitor.send_telegram_message(
            "🧪 **Test Message**\n\n"
            "Đây là tin nhắn test từ Telegram Bot.\n"
            "Nếu bạn nhận được tin nhắn này, bot đã hoạt động đúng! ✅"
        )
        print("✅ Telegram connection successful!")
    except Exception as e:
        print(f"❌ Telegram connection failed: {e}")

async def test_google_sheets_connection():
    """Test Google Sheets connection"""
    print("🧪 Testing Google Sheets connection...")
    
    try:
        monitor = GoogleSheetsMonitor()
        current_count = monitor.get_current_row_count()
        print(f"✅ Google Sheets connection successful! Current rows: {current_count}")
        
        # Get first few rows as sample
        if current_count > 0:
            sample_rows = monitor.get_new_rows(0)[:3]  # Get first 3 rows
            print("📋 Sample data:")
            for i, row in enumerate(sample_rows):
                print(f"   Row {i+1}: {row}")
                
    except Exception as e:
        print(f"❌ Google Sheets connection failed: {e}")

async def test_full_functionality():
    """Test the complete bot functionality"""
    print("🧪 Testing complete bot functionality...")
    
    try:
        monitor = GoogleSheetsMonitor()
        
        # Test both connections
        current_count = monitor.get_current_row_count()
        print(f"📊 Current sheet rows: {current_count}")
        
        # Send test notification
        test_message = (
            "🧪 **Full Functionality Test**\n\n"
            f"📊 Google Sheets đang có {current_count} dòng\n"
            f"⏱️ Kiểm tra mỗi {monitor.check_interval} giây\n"
            "🚀 Bot sẵn sàng hoạt động!"
        )
        
        await monitor.send_telegram_message(test_message)
        print("✅ Full functionality test successful!")
        
    except Exception as e:
        print(f"❌ Full functionality test failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting bot tests...\n")
    
    # Check if required environment variables are set
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID', 
        'GOOGLE_SHEETS_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and try again.")
        return
    
    # Run tests
    await test_telegram_connection()
    print()
    await test_google_sheets_connection()
    print()
    await test_full_functionality()
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
