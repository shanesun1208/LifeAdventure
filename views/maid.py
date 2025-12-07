import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_settings, load_all_finance_data, get_weather, chat_with_maid, save_chat_log

def render_maid_sidebar():
    """
    這個函式現在專門設計放在 st.sidebar 裡面呼叫
    """
    
    # --- 1. 讀取設定與資料 ---
    settings = get_settings()
    maid_img = settings.get('Maid_Image_URL', "https://cdn-icons-png.flaticon.com/512/4140/4140047.png")
    current_city = settings.get('Location', 'Taipei,TW')
    
    all_data = load_all_finance_data()
    now = datetime.now()
    weather_info = get_weather(current_city)
    
    # --- 2. 快速計算狀態 (給 AI 參考) ---
    df_fin = all_data.get("Finance", pd.DataFrame())
    df_income = all_data.get("Income", pd.DataFrame())
    df_qb = all_data.get("QuestBoard", pd.DataFrame())
    
    curr_m = now.strftime("%Y-%m")
    inc = df_income[df_income['Date'].astype(str).str.contains(curr_m)]['Amount'].sum() if not df_income.empty and 'Date' in df_income.columns else 0
    exp = df_fin[df_fin['Date'].astype(str).str.contains(curr_m)]['Price'].sum() if not df_fin.empty and 'Date' in df_fin.columns else 0
    tasks = len(df_qb[df_qb['Status'] == '進行中']) if not df_qb.empty and 'Status' in df_qb.columns else 0
    
    context_info = f"時間:{now.strftime('%H:%M')}, 天氣:{weather_info}, 本月收入:{inc}, 本月已花:{exp}, 進行中任務:{tasks}"

    # --- 3. 側邊欄顯示區 ---
    
    # 分隔線，把導航跟女僕分開
    st.markdown("---")
    
    # 顯示圖片與狀態
    col_img, col_stat = st.columns([1, 2])
    with col_img:
        st.image(maid_img, use_container_width=True)
    with col_stat:
        st.caption(f"📍 {weather_info}")
        if tasks > 3:
            st.warning(f"🔥 {tasks} 個任務燃燒中")
        else:
            st.success(f"✨ 狀態良好")

    # --- 4. 對話折疊區 ---
    with st.expander("💬 呼叫貼身秘書", expanded=False):
        
        # 讀取歷史
        df_chat = all_data.get("ChatHistory", pd.DataFrame())
        chat_history = []
        if not df_chat.empty:
            # 側邊欄空間小，只顯示最近 3 則
            for _, row in df_chat.tail(3).iterrows():
                chat_history.append({"Role": row['Role'], "Message": row['Message']})
                
                # 簡單的對話泡泡顯示
                if row['Role'] == 'user':
                    st.info(f"👤 {row['Message']}")
                else:
                    st.success(f"👧 {row['Message']}")

        # 輸入區 (使用 Form 避免輸入一個字就重整)
        with st.form("sidebar_chat_form", clear_on_submit=True):
            user_in = st.text_input("輸入指令...", placeholder="Ex: 還有多少錢?")
            if st.form_submit_button("送出"):
                if user_in:
                    save_chat_log("user", user_in)
                    reply = chat_with_maid(user_in, chat_history, context_info)
                    save_chat_log("assistant", reply)
                    st.rerun()