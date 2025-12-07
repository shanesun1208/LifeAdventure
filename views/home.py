import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 路徑修正
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_worksheet, get_weather, chat_with_maid, save_chat_log, load_all_finance_data, get_settings

def show_home_page(current_city, current_goal):
    now = datetime.utcnow() + timedelta(hours=8)
    weather_info = get_weather(current_city)
    
    # 讀取設定 (為了拿圖片 URL)
    settings = get_settings()
    maid_image_url = settings.get('Maid_Image_URL', "https://cdn-icons-png.flaticon.com/512/4140/4140047.png")

    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color:#00CC99; font-family:'微軟正黑體';">🏠 我的小屋 (My Home)</h1>
        <p style="color:#aaa;">{now.strftime("%Y年%m月%d日 %H:%M")} | {weather_info}</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 1. 準備情報 (給 AI 看的) ---
    all_data = load_all_finance_data()
    
    # 計算財務
    df_fin = all_data.get("Finance", pd.DataFrame())
    df_income = all_data.get("Income", pd.DataFrame())
    df_fixed = all_data.get("FixedExpenses", pd.DataFrame())
    df_budget = all_data.get("Budget", pd.DataFrame())
    
    current_month_str = now.strftime("%Y-%m")
    total_income = 0
    if not df_income.empty and 'Date' in df_income.columns:
        df_income['Date'] = df_income['Date'].astype(str)
        inc = df_income[df_income['Date'].str.contains(current_month_str)]
        inc['Amount'] = pd.to_numeric(inc['Amount'], errors='coerce').fillna(0)
        total_income = int(inc['Amount'].sum())
        
    total_fixed = 0
    if not df_fixed.empty:
        df_fixed['Amount'] = pd.to_numeric(df_fixed['Amount'], errors='coerce').fillna(0)
        total_fixed = int(df_fixed['Amount'].sum())
        
    total_spent = 0
    if not df_fin.empty and 'Date' in df_fin.columns:
        df_fin['Date'] = df_fin['Date'].astype(str)
        fin = df_fin[df_fin['Date'].str.contains(current_month_str)]
        fin['Price'] = pd.to_numeric(fin['Price'], errors='coerce').fillna(0)
        total_spent = int(fin['Price'].sum())
        
    reserve_goal = 0
    if not df_budget.empty:
        df_budget['Budget'] = pd.to_numeric(df_budget['Budget'], errors='coerce').fillna(0)
        for _, row in df_budget.iterrows():
            if "預備金" in str(row['Item']): reserve_goal = int(row['Budget'])

    free_cash = total_income - total_fixed - total_spent - reserve_goal

    # 計算任務
    df_qb = all_data.get("QuestBoard", pd.DataFrame())
    urgent_count = 0
    active_count = 0
    if not df_qb.empty and 'Status' in df_qb.columns:
        urgent_count = len(df_qb[df_qb['Status'] == '待接取'])
        active_count = len(df_qb[df_qb['Status'] == '進行中'])

    # 整理情報字串
    context_info = f"""
    [時間]: {now.strftime("%H:%M")}, 天氣: {weather_info}
    [本月財務]: 收入 ${total_income}, 已花 ${total_spent}, 剩餘可支配 ${free_cash}
    [任務狀態]: {active_count} 個任務進行中, {urgent_count} 個任務待接取
    [人生目標]: {current_goal}
    """

    # --- 2. 介面佈局 ---
    col_img, col_chat = st.columns([1, 2])

    with col_img:
        # 顯示女僕圖片
        st.image(maid_image_url, caption="專屬女僕", use_container_width=True)
        
        # 簡易數據卡片
        st.info(f"💰 剩餘預算: **${free_cash:,}**")
        st.success(f"⚔️ 進行中任務: **{active_count}**")

    with col_chat:
        st.subheader("💬 與女僕對話")
        
        # 讀取歷史訊息 (從 session_state 或 DataFrame)
        df_chat = all_data.get("ChatHistory", pd.DataFrame())
        
        # 轉換成 list of dict 方便處理
        chat_history = []
        if not df_chat.empty:
            # 取最近 10 筆顯示就好，不然太長
            recent_chats = df_chat.tail(10)
            for _, row in recent_chats.iterrows():
                chat_history.append({"Role": row['Role'], "Message": row['Message']})
        
        # 顯示歷史訊息
        for chat in chat_history:
            with st.chat_message(chat["Role"]):
                st.write(chat["Message"])

        # 輸入框
        if user_input := st.chat_input("跟女僕說點什麼..."):
            # 1. 顯示使用者輸入
            with st.chat_message("user"):
                st.write(user_input)
            
            # 2. 呼叫 AI
            with st.spinner("女僕思考中..."):
                reply = chat_with_maid(user_input, chat_history, context_info)
            
            # 3. 顯示 AI 回應
            with st.chat_message("assistant"):
                st.write(reply)
            
            # 4. 存入資料庫 (背景執行)
            save_chat_log("user", user_input)
            save_chat_log("assistant", reply)
            
            # 5. 強制重整以更新顯示 (雖然有點卡，但為了確保歷史紀錄同步)
            # 為了體驗好一點，我們其實可以不重整，只要 session state 更新就好
            # 但為了簡單起見，且讓您確認有存進去，我們先不強制重整，下次進來就會看到