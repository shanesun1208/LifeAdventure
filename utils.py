import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests
import google.generativeai as genai
import pandas as pd
import concurrent.futures
import random # 用來隨機選取
from datetime import datetime, timedelta # 用來計算日期

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

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

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
            st.error(f"❌ 找不到分頁：'{worksheet_name}'")
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
    sheet_names = ["Finance", "FixedExpenses", "Income", "Budget", "ReserveFund"]
    data = {}
    
    def fetch_one(name):
        sheet = get_worksheet(name)
        if sheet:
            return name, pd.DataFrame(sheet.get_all_records())
        return name, pd.DataFrame()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
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
            'Loading_Messages': "前往商會路上...|整理帳本中...|點算庫存貨物...", # 預設值
            'Loading_Update_Date': "2000-01-01"
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
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=zh_tw"
        res = requests.get(url).json()
        return f"📍 {city} | 🌡️ {res['main']['temp']:.1f}°C"
    except: return f"📍 {city}"

@st.cache_data(ttl=3600)
def get_ai_greeting(hour, weather):
    if not GEMINI_API_KEY: return "歡迎回到冒險者公會！"
    period = "晚上"
    if 5<=hour<11: period="早晨"
    elif 11<=hour<14: period="中午"
    elif 14<=hour<18: period="下午"
    prompt = f"現在是{period}({hour}點)，天氣{weather}。請以RPG櫃台小姐語氣給予20字內溫暖問候。"
    try: return model.generate_content(prompt).text.strip()
    except: return "今天也要加油喔！"

def ask_gemini(text, status):
    if not GEMINI_API_KEY: return "AI 休息中"
    try:
        prompt = f"你是RPG櫃檯小姐。玩家完成冒險：{text} (狀態:{status})。請給20字內鼓勵或評語。"
        return model.generate_content(prompt).text.strip()
    except: return "紀錄已保存。"

def generate_reward(task_name, content, rank):
    if not GEMINI_API_KEY: return "公會積分 +10"
    try:
        prompt = f"玩家建立任務：{task_name} (內容:{content}, 等級:{rank})。請想一個有趣的「小獎勵」(15字內)。"
        return model.generate_content(prompt).text.strip()
    except: return "神秘的小禮物"

# --- [新] 隨機載入語錄 (每週更新) ---
def get_loading_message(current_weather_info=""):
    # 1. 讀取目前的設定
    settings = get_settings()
    saved_msgs = settings.get('Loading_Messages', "")
    last_update = settings.get('Loading_Update_Date', "2000-01-01")
    
    # 2. 檢查是否過期 (7天)
    need_update = False
    try:
        last_date = datetime.strptime(last_update, "%Y-%m-%d")
        if (datetime.now() - last_date).days >= 7:
            need_update = True
    except:
        need_update = True
    
    # 3. 如果需要更新，且有 AI Key，就呼叫 AI 生成
    if need_update and GEMINI_API_KEY:
        try:
            # 簡單提取天氣狀況 (ex: rainy)
            weather_desc = current_weather_info.split("|")[-1] if "|" in current_weather_info else "晴天"
            
            prompt = f"""
            請生成 15 句 RPG 風格的「過場讀取文字」(Loading Screen Text)，情境是玩家正在前往「商人公會」或處理財務。
            
            要求：
            1. 簡短有趣 (15字以內)。
            2. 結合現在天氣 ({weather_desc}) 或冒險氛圍。
            3. 例如：「馬車在雨中疾馳...」、「正在清點金庫...」、「與地精討價還價中...」。
            4. 請用 '|||' 符號將這 15 句隔開，不要有其他多餘文字，直接給字串。
            """
            response = model.generate_content(prompt)
            new_msgs_str = response.text.strip()
            
            # 檢查格式是否正確 (有 ||| )
            if "|||" in new_msgs_str:
                # 存回 Google Sheet
                update_setting_value("Loading_Messages", new_msgs_str)
                update_setting_value("Loading_Update_Date", datetime.now().strftime("%Y-%m-%d"))
                saved_msgs = new_msgs_str # 更新變數供當次使用
        except Exception as e:
            print(f"AI 生成語錄失敗: {e}")
            # 失敗就算了，用舊的

    # 4. 隨機回傳一句
    if saved_msgs:
        msg_list = saved_msgs.split("|||")
        # 過濾掉空白項目
        msg_list = [m.strip() for m in msg_list if m.strip()]
        if msg_list:
            return random.choice(msg_list)
            
    return "正在前往商會..."