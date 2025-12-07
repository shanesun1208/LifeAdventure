import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_settings, load_all_finance_data, get_weather, chat_with_maid, save_chat_log

def render_maid_widget():
    # 讀取設定與資料 (為了給 AI 上下文)
    settings = get_settings()
    maid_img = settings.get('Maid_Image_URL', "https://cdn-icons-png.flaticon.com/512/4140/4140047.png")
    current_city = settings.get('Location', 'Taipei,TW')
    
    # 準備上下文數據 (快速計算版)
    all_data = load_all_finance_data()
    now = datetime.now()
    weather_info = get_weather(current_city)
    
    # 簡單計算餘額與任務數
    df_fin = all_data.get("Finance", pd.DataFrame())
    df_income = all_data.get("Income", pd.DataFrame())
    df_qb = all_data.get("QuestBoard", pd.DataFrame())
    
    curr_m = now.strftime("%Y-%m")
    inc = 0
    if not df_income.empty and 'Date' in df_income.columns:
        df_income['Date'] = df_income['Date'].astype(str)
        inc = df_income[df_income['Date'].str.contains(curr_m)]['Amount'].sum()
    
    exp = 0
    if not df_fin.empty and 'Date' in df_fin.columns:
        df_fin['Date'] = df_fin['Date'].astype(str)
        exp = df_fin[df_fin['Date'].str.contains(curr_m)]['Price'].sum()
        
    tasks = 0
    if not df_qb.empty and 'Status' in df_qb.columns:
        tasks = len(df_qb[df_qb['Status'] == '進行中'])

    context_info = f"時間:{now.strftime('%H:%M')}, 天氣:{weather_info}, 本月收入:{inc}, 本月已花:{exp}, 進行中任務:{tasks}"

    # --- CSS 魔法：固定在右下角的懸浮視窗 ---
    st.markdown("""
    <style>
    /* 定義懸浮容器 */
    .maid-floating-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 99999; /* 確保在最上層 */
        width: 350px;
        max-width: 90%;
    }
    
    /* 美化 Expander */
    .maid-floating-container .streamlit-expanderHeader {
        background-color: #2b2b2b;
        border: 1px solid #00CC99;
        color: white;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    /* 內容區域背景 */
    .maid-floating-container .streamlit-expanderContent {
        background-color: #1e1e1e;
        border: 1px solid #444;
        border-radius: 0 0 10px 10px;
        max-height: 400px;
        overflow-y: auto;
    }
    
    /* 頭像樣式 */
    .maid-avatar-small {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 10px;
        vertical-align: middle;
    }
    
    /* 對話氣泡 */
    .chat-bubble-ai {
        background-color: #262730;
        border-left: 3px solid #00CC99;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        font-size: 14px;
    }
    .chat-bubble-user {
        background-color: #2c3e50;
        text-align: right;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- 懸浮結構 ---
    # 使用 container 包住，稍後用 CSS 把它搬到右下角 (這一招比較 tricky，需配合 hacky css)
    # Streamlit 原生不支援 fixed position，我們必須把這段 HTML 塞進去
    
    # 由於 st.expander 不能直接套用 style position: fixed
    # 我們改用一個 trick：把整個區塊放在頁面底部，然後用 CSS 把它移到右下角
    
    with st.container():
        st.markdown('<div class="maid-floating-container">', unsafe_allow_html=True)
        
        # 標題列：包含頭像
        with st.expander("💬 貼身秘書", expanded=False):
            # 顯示頭像
            st.image(maid_img, width=100)
            
            # 讀取歷史紀錄 (只顯示最近 3 則以免太長)
            df_chat = all_data.get("ChatHistory", pd.DataFrame())
            chat_history = []
            if not df_chat.empty:
                for _, row in df_chat.tail(5).iterrows():
                    chat_history.append({"Role": row['Role'], "Message": row['Message']})
                    # 顯示對話
                    css_class = "chat-bubble-user" if row['Role'] == 'user' else "chat-bubble-ai"
                    st.markdown(f'<div class="{css_class}">{row["Message"]}</div>', unsafe_allow_html=True)
            
            # 輸入區 (使用 Form 防止一直刷新)
            with st.form("maid_chat_form", clear_on_submit=True):
                user_input = st.text_input("說點什麼...", placeholder="Ex: 還有多少預算？")
                if st.form_submit_button("送出"):
                    if user_input:
                        # 存入 User 訊息
                        save_chat_log("user", user_input)
                        
                        # 呼叫 AI
                        reply = chat_with_maid(user_input, chat_history, context_info)
                        
                        # 存入 AI 回應
                        save_chat_log("assistant", reply)
                        
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)