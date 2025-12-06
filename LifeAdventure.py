import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. 設定通行證與權限範圍
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)
client = gspread.authorize(creds)

# 2. 開啟您的試算表 (請確認這裡的名字跟您的試算表檔名一模一樣)
sheet_name = "LifeAdventure"
try:
    # 開啟試算表的第一個工作表 (Sheet1)
    sheet = client.open(sheet_name).sheet1
    print(f"成功連線到冒險日誌：{sheet_name}")

    # 3. 測試寫入一筆資料
    # 格式：[日期, 類別, 內容, 狀態]
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_data = [
        current_time,
        "系統測試",
        "成功連結 Python 與 Google Sheets",
        "Completed",
    ]

    sheet.append_row(test_data)
    print("成功寫入測試資料！請去 Google Sheet 查看。")

except Exception as e:
    print("發生錯誤，請檢查檔名或憑證：", e)
