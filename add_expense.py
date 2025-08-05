#!/usr/bin/env python3
"""
Script thêm nhanh chi phí vào Google Sheets
"""

import os
import sys
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def add_expense(description, amount, category, person, note=""):
    """Thêm nhanh một khoản chi tiêu"""
    try:
        # Setup Google Sheets
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = Credentials.from_service_account_file(
            'credentials.json', 
            scopes=scope
        )
        
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(os.getenv('GOOGLE_SHEETS_ID')).sheet1
        
        # Thêm dòng mới
        date = datetime.now().strftime('%d/%m/%Y')
        row_data = [date, description, str(amount), category, person, note]
        
        sheet.append_row(row_data)
        
        print(f"✅ Đã thêm: {description} - {amount:,} VNĐ ({category}) - Người chi: {person}")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        # Sử dụng arguments từ command line
        description = sys.argv[1]
        amount = int(sys.argv[2])
        category = sys.argv[3]
        person = sys.argv[4]
        note = sys.argv[5] if len(sys.argv) > 5 else ""
        
        add_expense(description, amount, category, person, note)
    else:
        # Interactive mode
        print("💰 Thêm nhanh chi phí")
        print("=" * 30)
        
        description = input("Mô tả: ")
        amount = int(input("Số tiền (VNĐ): "))
        category = input("Danh mục: ")
        person = input("Người chi: ")
        note = input("Ghi chú (tùy chọn): ")
        
        add_expense(description, amount, category, person, note)
        
        print("\n💡 Sử dụng nhanh:")
        print(f"python add_expense.py '{description}' {amount} '{category}' '{person}' '{note}'")
