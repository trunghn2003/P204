import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class GoogleSheetsSetup:
    def __init__(self):
        self.sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.setup_google_sheets()
    
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
            print("✅ Kết nối Google Sheets thành công!")
            
        except Exception as e:
            print(f"❌ Lỗi kết nối Google Sheets: {e}")
            raise
    
    def setup_headers(self):
        """Thiết lập tiêu đề cột"""
        headers = ['Ngày', 'Mô tả', 'Số tiền', 'Danh mục', 'Người chi', 'Ghi chú']
        
        try:
            # Xóa tất cả dữ liệu hiện tại
            self.sheet.clear()
            
            # Thêm header vào dòng đầu tiên
            self.sheet.insert_row(headers, 1)
            
            # Format header
            self.sheet.format('A1:F1', {
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
            
            print("✅ Đã thiết lập tiêu đề cột:")
            for i, header in enumerate(headers, 1):
                print(f"   Cột {chr(64+i)}: {header}")
                
        except Exception as e:
            print(f"❌ Lỗi thiết lập header: {e}")
    
    def add_sample_data(self):
        """Thêm dữ liệu mẫu"""
        sample_data = [
            ['05/08/2025', 'Ăn trưa', '50000', 'Ăn uống', 'Hoàng Việt', 'Cơm văn phòng'],
            ['05/08/2025', 'Xăng xe', '200000', 'Di chuyển', 'Hoàng Việt', 'Đổ đầy bình'],
            ['05/08/2025', 'Cafe', '35000', 'Giải trí', 'Anh Tài', 'Với bạn bè'],
            ['05/08/2025', 'Mua sách', '150000', 'Học tập', 'Chị Hoa', 'Sách lập trình'],
            ['05/08/2025', 'Tiền điện', '300000', 'Hóa đơn', 'Gia đình', 'Tiền điện tháng 8']
        ]
        
        try:
            for row_data in sample_data:
                self.sheet.append_row(row_data)
                print(f"   ➕ Đã thêm: {row_data[1]} - {int(row_data[2]):,} VNĐ ({row_data[4]})")
            
            print("✅ Đã thêm dữ liệu mẫu thành công!")
            
        except Exception as e:
            print(f"❌ Lỗi thêm dữ liệu mẫu: {e}")
    
    def add_custom_row(self, date, description, amount, category, person, note=""):
        """Thêm dòng dữ liệu tùy chỉnh"""
        try:
            row_data = [date, description, str(amount), category, person, note]
            self.sheet.append_row(row_data)
            print(f"✅ Đã thêm: {description} - {amount:,} VNĐ ({person})")
            return True
        except Exception as e:
            print(f"❌ Lỗi thêm dữ liệu: {e}")
            return False
    
    def show_current_data(self):
        """Hiển thị dữ liệu hiện tại"""
        try:
            all_data = self.sheet.get_all_values()
            print("\n📊 Dữ liệu hiện tại trong Google Sheets:")
            print("-" * 80)
            
            if not all_data:
                print("   Sheet trống!")
                return
            
            # Hiển thị header
            if len(all_data) > 0:
                headers = all_data[0]
                print(f"{'STT':>3} | {headers[0]:<12} | {headers[1]:<20} | {headers[2]:>12} | {headers[3]:<15} | {headers[4]:<12} | {headers[5] if len(headers) > 5 else 'Ghi chú'}")
                print("-" * 95)
                
                # Hiển thị từng dòng
                for i, row in enumerate(all_data[1:], 1):
                    if len(row) >= 5:
                        try:
                            amount = int(row[2]) if row[2].isdigit() else row[2]
                            amount_str = f"{amount:,}" if isinstance(amount, int) else str(amount)
                        except:
                            amount_str = row[2]
                        
                        person = row[4] if len(row) > 4 else ""
                        note = row[5] if len(row) > 5 else ""
                        print(f"{i:>3} | {row[0]:<12} | {row[1]:<20} | {amount_str:>12} | {row[3]:<15} | {person:<12} | {note}")
            
            print(f"\n📈 Tổng cộng: {len(all_data)-1} dòng dữ liệu")
            
        except Exception as e:
            print(f"❌ Lỗi hiển thị dữ liệu: {e}")

def main():
    print("🚀 Google Sheets Setup Tool")
    print("=" * 50)
    
    try:
        setup = GoogleSheetsSetup()
        
        while True:
            print("\n📋 Chọn hành động:")
            print("1. Thiết lập cấu trúc cột (xóa dữ liệu cũ)")
            print("2. Thêm dữ liệu mẫu") 
            print("3. Thêm dòng mới")
            print("4. Xem dữ liệu hiện tại")
            print("5. Thoát")
            
            choice = input("\n👉 Nhập lựa chọn (1-5): ").strip()
            
            if choice == '1':
                print("\n🛠️  Thiết lập cấu trúc cột...")
                setup.setup_headers()
                
            elif choice == '2':
                print("\n📊 Thêm dữ liệu mẫu...")
                setup.add_sample_data()
                
            elif choice == '3':
                print("\n➕ Thêm dòng mới:")
                date = input("   Ngày (dd/mm/yyyy): ") or datetime.now().strftime('%d/%m/%Y')
                description = input("   Mô tả: ")
                
                while True:
                    try:
                        amount = int(input("   Số tiền (VNĐ): "))
                        break
                    except ValueError:
                        print("   ❌ Vui lòng nhập số!")
                
                category = input("   Danh mục: ")
                person = input("   Người chi: ")
                note = input("   Ghi chú (tùy chọn): ")
                
                setup.add_custom_row(date, description, amount, category, person, note)
                
            elif choice == '4':
                setup.show_current_data()
                
            elif choice == '5':
                print("\n👋 Tạm biệt!")
                break
                
            else:
                print("❌ Lựa chọn không hợp lệ!")
    
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()
