import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests
import google.generativeai as genai
import pandas as pd
import concurrent.futures
import random

# --- 常數 ---
SHEET_NAME = "LifeAdventure"
CITY_OPTIONS = [
    "Taipei,TW",
    "New Taipei,TW",
    "Taichung,TW",
    "Kaohsiung,TW",
    "Tokyo,JP",
    "New York,US",
    "London,GB",
]


# --- API 初始化 ---
def init_api():
    w_key = ""
    g_key = ""
    if "general" in st.secrets:
        w_key = st.secrets["general"]["weather_api_key"]
        g_key = st.secrets["general"]["gemini_api_key"]
    return w_key, g_key


WEATHER_API_KEY, GEMINI_API_KEY = init_api()


# --- Google Sheet 連線 ---
@st.cache_resource
def get_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    if os.path.exists("credentials.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "credentials.json", scope
        )
    elif "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            creds_dict, scope
        )
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
    # [修改] 移除 ChatHistory
    sheet_names = [
        "Finance",
        "FixedExpenses",
        "Income",
        "Budget",
        "ReserveFund",
        "QuestBoard",
    ]
    data = {}

    def fetch_one(name):
        sheet = get_worksheet(name)
        if sheet:
            return name, pd.DataFrame(sheet.get_all_records())
        return name, pd.DataFrame()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        results = executor.map(fetch_one, sheet_names)

    for name, df in results:
        data[name] = df

    return data


# --- 設定相關 ---
@st.cache_data(ttl=300)
def get_settings():
    try:
        sheet = get_worksheet("Setting")
        if not sheet:
            return {}
        records = sheet.get_all_records()
        settings = {row["Item"]: row["Value"] for row in records}

        # [修改] 移除女僕與 Loading 相關設定
        defaults = {
            "LifeGoal": "未設定",
            "Location": "Taipei,TW",
            "Type1_Options": "飲食,交通,娛樂,固定開銷,其他",
            "Type2_Options": "早餐,午餐,晚餐,捷運,計程車,房租",
            "Income_Types": "薪資,獎金,投資,兼職,其他",
            "Fixed_Types": "訂閱,房租,保險,分期付款,孝親費,網路費,其他",
            "Quest_Types": "工作,採購,禪行,其他",
            "Payment_Methods": "現金,信用卡",
        }
        for k, v in defaults.items():
            if k not in settings:
                settings[k] = v
        return settings
    except:
        return {}


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
    if not WEATHER_API_KEY:
        return "📍 API未設定"
    try:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        query = f"?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=zh_tw"
        url = base_url + query
        res = requests.get(url).json()
        return f"📍 {city} | 🌡️ {res['main']['temp']:.1f}°C"
    except:
        return f"📍 {city}"
