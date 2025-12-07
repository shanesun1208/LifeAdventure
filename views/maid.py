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
    # --- 1. 初始化與讀取 ---
    if 'maid_chat_open' not in st.session_state:
        st.session_state['maid_chat_open'] = False

    settings = get_settings()
    maid_img = settings.get('Maid_Image_URL', "https://cdn-icons-png.flaticon.com/512/4140/4140047.png")
    current_city = settings.get('Location', 'Taipei,TW')
    
    # 準備數據 (只在需要時計算，或簡單計算)
    # 這裡我們只在對話時需要詳細數據，平時只要圖片
    
    # --- 2. CSS: 把按鈕變成圖片 & 對話框樣式 ---
    st.markdown(f"""
    <style>
        /* 偽裝成圖片的按鈕 */
        div.stButton.maid-avatar-btn > button {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 4px solid #00CC99;
            background-image: url('{maid_img}');
            background-size: cover;
            background-position: center;
            background-color: #2b2b2b;
            color: transparent;
            margin: 0 auto; /* 置中 */
            display: block;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        div.stButton.maid-avatar-btn > button:hover {{
            transform: scale(1.05);
            border-color: #FFD700;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
        }}
        div.stButton.maid-avatar-btn > button:active {{
            color: transparent; /* 確保點擊時文字不跑出來 */
        }}

        /* 對話氣泡樣式 */
        .sidebar-chat-user {{
            background-color: #00CC99; color: #000;
            padding: 8px; border-radius: 10px; margin: 5px 0; font-size: 13px; text-align: right;
        }}
        .sidebar-chat-ai {{
            background-color: #444; color: #fff; border: 1px solid #666;
            padding: 8px; border-radius: 10px; margin: 5px 0; font-size: 13px; text-align: left;
        }}
    </style>
    """, unsafe_allow_html=True)

    # --- 3. 顯示邏輯 ---
    
    st.markdown("---") # 上分隔線
    
    # A. 頭像區 (點擊切換開關)
    # 使用 columns 來置中
    c1, c2, c3 = st.columns([0.1, 1, 0.1])
    with c2:
        # 使用空的 container 包裹並加上 class
        c_btn = st.container()
        c_btn.markdown('<div class="stButton maid-avatar-btn">', unsafe_allow_html=True)
        # 按鈕本身 (文字設為透明)
        if c_btn.button("Maid", key="maid_toggle"):
            # 切換開關
            st.session_state['maid_chat_open'] = not st.session_state['maid_chat_open']
            st.rerun()
        c_btn.markdown('</div>', unsafe_allow_html=True)
        
        st.caption("👆 點擊頭像對話")

    # B. 對話區 (只有打開時顯示)
    if st.session_state['maid_chat_open']:
        st.markdown("##### 💬 貼身秘書")
        
        # 準備資料
        all_data = load_all_finance_data()
        df_chat = all_data.get("ChatHistory", pd.DataFrame())
        
        # 顯示歷史 (最近 3 則)
        if not df_chat.empty:
            for _, row in df_chat.tail(3).iterrows():
                css = "sidebar-chat-user" if row['Role'] == 'user' else "sidebar-chat-ai"
                st.markdown(f'<div class="{css}">{row["Message"]}</div>', unsafe_allow_html=True)
        
        # 輸入區
        with st.form("sidebar_maid_form", clear_on_submit=True):
            user_input = st.text_input("輸入...", label_visibility="collapsed", placeholder="請吩咐...")
            if st.form_submit_button("送出"):
                if user_input:
                    # 讀取上下文
                    now = datetime.now()
                    weather_info = get_weather(current_city)
                    
                    df_fin = all_data.get("Finance", pd.DataFrame())
                    df_income = all_data.get("Income", pd.DataFrame())
                    df_qb = all_data.get("QuestBoard", pd.DataFrame())
                    
                    curr_m = now.strftime("%Y-%m")
                    inc = df_income[df_income['Date'].astype(str).str.contains(curr_m)]['Amount'].sum() if not df_income.empty and 'Date' in df_income.columns else 0
                    exp = df_fin[df_fin['Date'].astype(str).str.contains(curr_m)]['Price'].sum() if not df_fin.empty and 'Date' in df_fin.columns else 0
                    tasks = len(df_qb[df_qb['Status'] == '進行中']) if not df_qb.empty and 'Status' in df_qb.columns else 0
                    
                    context = f"時間:{now.strftime('%H:%M')}, 天氣:{weather_info}, 本月收入:{inc}, 本月已花:{exp}, 進行中任務:{tasks}"
                    
                    # 紀錄與回應
                    save_chat_log("user", user_input)
                    reply = chat_with_maid(user_input, [{"Role":r['Role'],"Message":r['Message']} for i,r in df_chat.tail(5).iterrows()], context)
                    save_chat_log("assistant", reply)
                    st.rerun()