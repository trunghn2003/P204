#!/usr/bin/env python3
"""
Script để lấy Chat ID từ Telegram Bot
Chạy script này, sau đó gửi tin nhắn cho bot để lấy Chat ID
"""

import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def get_chat_id():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ Không tìm thấy TELEGRAM_BOT_TOKEN trong file .env")
        return
    
    bot = Bot(token=bot_token)
    
    print("🤖 Bot đã sẵn sàng!")
    print("📱 Hãy gửi tin nhắn cho bot trong Telegram")
    print("⏱️  Đang chờ tin nhắn...")
    
    last_update_id = 0
    
    while True:
        try:
            updates = await bot.get_updates(offset=last_update_id + 1)
            
            for update in updates:
                if update.message:
                    chat_id = update.message.chat.id
                    chat_type = update.message.chat.type
                    username = update.message.from_user.username or "N/A"
                    first_name = update.message.from_user.first_name or "N/A"
                    
                    print(f"\n✅ Nhận được tin nhắn!")
                    print(f"📋 Chat ID: {chat_id}")
                    print(f"👤 Người gửi: {first_name} (@{username})")
                    print(f"💬 Loại chat: {chat_type}")
                    print(f"📝 Nội dung: {update.message.text}")
                    
                    print(f"\n📝 Cập nhật file .env với Chat ID này:")
                    print(f"TELEGRAM_CHAT_ID={chat_id}")
                    
                    # Tự động cập nhật file .env
                    await update_env_file(chat_id)
                    
                    # Gửi tin nhắn xác nhận
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ **Đã lấy Chat ID thành công!**\n\n"
                             f"📋 Chat ID của bạn: `{chat_id}`\n"
                             f"🤖 Bot đã sẵn sàng hoạt động!\n\n"
                             f"💡 File .env đã được tự động cập nhật.",
                        parse_mode='Markdown'
                    )
                    
                    return chat_id
                    
                last_update_id = update.update_id
                
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            
        await asyncio.sleep(2)

async def update_env_file(chat_id):
    """Cập nhật Chat ID trong file .env"""
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        # Thay thế hoặc thêm TELEGRAM_CHAT_ID
        lines = content.split('\n')
        updated = False
        
        for i, line in enumerate(lines):
            if line.startswith('TELEGRAM_CHAT_ID='):
                lines[i] = f'TELEGRAM_CHAT_ID={chat_id}'
                updated = True
                break
        
        if not updated:
            lines.append(f'TELEGRAM_CHAT_ID={chat_id}')
        
        with open('.env', 'w') as f:
            f.write('\n'.join(lines))
            
        print(f"✅ Đã cập nhật file .env với Chat ID: {chat_id}")
        
    except Exception as e:
        print(f"❌ Lỗi cập nhật file .env: {e}")

if __name__ == "__main__":
    asyncio.run(get_chat_id())
