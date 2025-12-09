import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests
import google.generativeai as genai
import pandas as pd
import concurrent.futures
import random
import base64
import time
from datetime import datetime, timedelta

# --- 常數 ---
SHEET_NAME = "LifeAdventure"
CITY_OPTIONS = ["Taipei,TW", "New Taipei,TW", "Taichung,TW", "Kaohsiung,TW", "Tokyo,JP", "New York,US", "London,GB"]

# --- API 初始化 ---
def init_api():
    w_key = ""
    g_key = ""
    if "general" in st.secrets:
        w_key = st.secrets["general"]["weather_api_key"]
        g_key = st.secrets["general"]["gemini_api_key"]
    return w_key, g_key

WEATHER_API_KEY, GEMINI_API_KEY = init_api()

# --- API 設定 (包含 429 防護與模型選擇) ---
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 優先使用免費額度較高的 flash-latest
    try:
        model_name = 'gemini-flash-latest'
        model = genai.GenerativeModel(model_name)
        print(f"✅ 已設定模型: {model_name}")
    except Exception as e:
        print(f"❌ 模型設定失敗: {e}")
        model = None

# --- Google Sheet 連線 ---
@st.cache_resource
def get_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if os.path.exists("credentials.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    elif "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        st.error("找不到憑證！")
        st.stop()
    return gspread.authorize(creds)

@st.cache_resource
def get_spreadsheet():
    client = get_client()
    try:
        return client.open(SHEET_NAME)
    except Exception as e:
        st.error(f"無法開啟試算表 '{SHEET_NAME}'：{e}")
        return None

def get_worksheet(worksheet_name):
    sh = get_spreadsheet()
    if sh:
        try:
            return sh.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            return None
        except Exception as e:
            print(f"Error fetching {worksheet_name}: {e}")
            return None
    return None

# --- 資料讀取 ---
@st.cache_data(ttl=60)
def load_sheet_data(worksheet_name):
    sheet = get_worksheet(worksheet_name)
    if sheet:
        return pd.DataFrame(sheet.get_all_records())
    return pd.DataFrame()

@st.cache_data(ttl=60)
def load_all_finance_data():
    sheet_names = ["Finance", "FixedExpenses", "Income", "Budget", "ReserveFund", "QuestBoard", "ChatHistory"]
    data = {}
    
    def fetch_one(name):
        sheet = get_worksheet(name)
        if sheet:
            return name, pd.DataFrame(sheet.get_all_records())
        return name, pd.DataFrame()

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        results = executor.map(fetch_one, sheet_names)
    
    for name, df in results:
        data[name] = df
        
    return data

# --- 設定相關 ---
@st.cache_data(ttl=300)
def get_settings():
    try:
        sheet = get_worksheet("Setting")
        if not sheet: return {}
        records = sheet.get_all_records()
        settings = {row['Item']: row['Value'] for row in records}
        defaults = {
            'LifeGoal': "未設定",
            'Location': "Taipei,TW",
            'Type1_Options': "飲食,交通,娛樂,固定開銷,其他",
            'Type2_Options': "早餐,午餐,晚餐,捷運,計程車,房租",
            'Income_Types': "薪資,獎金,投資,兼職,其他",
            'Fixed_Types': "訂閱,房租,保險,分期付款,孝親費,網路費,其他",
            'Quest_Types': "工作,採購,禪行,其他",
            'Payment_Methods': "現金,信用卡",
            'Maid_Image_URL': "https://cdn-icons-png.flaticon.com/512/4140/4140047.png",
            'Loading_Messages': "前往商會路上...|整理帳本中...|點算庫存貨物...",
            'Loading_Update_Date': "2000-01-01",
            'Daily_Maid_Img': "", 
            'Daily_Maid_Date': "2000-01-01"
        }
        for k, v in defaults.items():
            if k not in settings: settings[k] = v
        return settings
    except: return {}

def update_setting_value(key, val):
    sheet = get_worksheet("Setting")
    if sheet:
        try:
            cell = sheet.find(key)
            sheet.update_cell(cell.row, 2, val)
        except:
            sheet.append_row([key, val])
        get_settings.clear()
        return True
    return False

# --- 功能函式 ---
@st.cache_data(ttl=1800)
def get_weather(city):
    if not WEATHER_API_KEY: return "📍 API未設定"
    try:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        query = f"?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=zh_tw"
        url = base_url + query
        res = requests.get(url).json()
        return f"📍 {city} | 🌡️ {res['main']['temp']:.1f}°C"
    except: return f"📍 {city}"

def generate_reward(task_name, content, rank):
    if not GEMINI_API_KEY: return "公會積分 +10"
    try:
        prompt = f"玩家建立任務：{task_name} (內容:{content}, 等級:{rank})。請想一個有趣的「小獎勵」(15字內)。"
        return model.generate_content(prompt).text.strip()
    except: return "神秘的小禮物"

def get_loading_message(current_weather_info=""):
    settings = get_settings()
    saved_msgs = settings.get('Loading_Messages', "")
    last_update = settings.get('Loading_Update_Date', "2000-01-01")
    need_update = False
    try:
        last_date = datetime.strptime(last_update, "%Y-%m-%d")
        if (datetime.now() - last_date).days >= 7: need_update = True
    except: need_update = True
    
    if need_update and GEMINI_API_KEY:
        try:
            weather_desc = current_weather_info.split("|")[-1] if "|" in current_weather_info else "晴天"
            prompt = (
                f"請生成 15 句 RPG 風格的「過場讀取文字」。情境：前往商人公會或處理財務。"
                f"要求：簡短有趣(15字內)、結合天氣({weather_desc})。"
                f"請用 '|||' 符號將這 15 句隔開，不要有其他多餘文字。"
            )
            response = model.generate_content(prompt)
            new_msgs_str = response.text.strip()
            if "|||" in new_msgs_str:
                update_setting_value("Loading_Messages", new_msgs_str)
                update_setting_value("Loading_Update_Date", datetime.now().strftime("%Y-%m-%d"))
                saved_msgs = new_msgs_str
        except Exception as e: print(f"AI error: {e}")

    if saved_msgs:
        msg_list = [m.strip() for m in saved_msgs.split("|||") if m.strip()]
        if msg_list: return random.choice(msg_list)
    return "正在前往商會..."

# --- [關鍵] 小秘書對話大腦 (升級版) ---
def chat_with_maid(user_input, chat_history, context_info):
    if not GEMINI_API_KEY: return "主人，API Key 未設定，我無法思考。"
    
    if 'model' not in globals() or model is None:
        return "語言模組未啟動，請檢查設定。"

    history_text = ""
    for msg in chat_history[-3:]: # 只看最近 3 句，避免 Token 過多
        role = "主人" if msg['Role'] == 'user' else "秘書"
        history_text += f"{role}: {msg['Message']}\n"
    
    # 升級版 Prompt：強制要求根據數據回答
    prompt = f"""
    你是 'Life Adventure OS' 的核心 AI 秘書。
    你的職責是協助主人管理人生、財務與任務。
    
    【當前真實數據】(請基於此回答，不要捏造)
    {context_info}
    
    【近期對話】
    {history_text}
    
    【主人指令】
    {user_input}
    
    【回答準則】
    1. **數據優先**：如果主人問「我還有多少錢」或「最近做了什麼」，一定要看【當前真實數據】回答。
    2. **簡潔有力**：回答控制在 80 字以內。
    3. **誠實原則**：如果數據裡沒有顯示，就誠實說「紀錄中沒有相關資料」。
    4. **語氣**：保持專業但溫柔的女僕口吻。
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return "我需要休息一下 (API限流)...請稍後再試。"
        return f"發生錯誤: {e}"

def save_chat_log(role, message):
    sheet = get_worksheet("ChatHistory")
    if sheet:
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([time_str, role, message])

# --- [關鍵] 每日女僕圖 ---
@st.cache_data(ttl=3600)
def get_daily_maid_image():
    # 預設圖
    default_url = "https://cdn-icons-png.flaticon.com/512/4140/4140047.png"
    
    try:
        # 1. 取得設定
        settings = get_settings()
        saved_img_record = settings.get('Daily_Maid_Img', "")
        last_date = settings.get('Daily_Maid_Date', "2000-01-01")
        
        # 2. 鎖定資料夾 (絕對路徑)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.join(current_dir, "assets", "maid")
        
        # 3. 檢查資料夾
        if not os.path.exists(folder_path):
            return default_url
            
        # 4. 抓取存在的圖片
        files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files: return default_url

        # 5. 決定圖片
        today_str = datetime.now().strftime("%Y-%m-%d")
        target_file = saved_img_record

        # 如果日期換了 或 紀錄的圖不在了 -> 隨機挑一張
        if last_date != today_str or saved_img_record not in files:
            target_file = random.choice(files)
            
        # 6. 回傳絕對路徑
        full_path = os.path.join(folder_path, target_file)
        return full_path
        
    except Exception as e:
        print(f"Image load error: {e}")
        return default_url