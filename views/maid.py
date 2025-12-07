import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 引入 get_daily_maid_image
from utils import get_settings, load_all_finance_data, get_weather, chat_with_maid, save_chat_log, get_daily_maid_image

def render_maid_sidebar():
    # --- 1. 初始化狀態 ---
    if 'maid_chat_open' not in st.session_state:
        st.session_state['maid_chat_open'] = False

    settings = get_settings()
    current_city = settings.get('Location', 'Taipei,TW')
    
    # 取得圖片 (Base64)
    maid_img_src = get_daily_maid_image()

    # --- 2. CSS ---
    st.markdown(f"""
    <style>
        div.stButton.maid-avatar-btn > button {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 4px solid #00CC99;
            /* 這裡直接填入 Base64 字串 */
            background-image: url('{maid_img_src}');
            background-size: cover;
            background-position: center;
            background-color: #2b2b2b;
            color: transparent;
            margin: 0 auto;
            display: block;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        div.stButton.maid-avatar-btn > button:hover {{
            transform: scale(1.05);
            border-color: #FFD700;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
        }}
        div.stButton.maid-avatar-btn > button:active {{
            color: transparent;
        }}
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
    
    st.markdown("---")
    
    c1, c2, c3 = st.columns([0.1, 1, 0.1])
    with c2:
        c_btn = st.container()
        c_btn.markdown('<div class="stButton maid-avatar-btn">', unsafe_allow_html=True)
        if c_btn.button("Maid", key="maid_toggle"):
            st.session_state['maid_chat_open'] = not st.session_state['maid_chat_open']
            st.rerun()
        c_btn.markdown('</div>', unsafe_allow_html=True)
        st.caption("👆 點擊頭像對話")

    if st.session_state['maid_chat_open']:
        st.markdown("##### 💬 貼身秘書")
        
        all_data = load_all_finance_data()
        df_chat = all_data.get("ChatHistory", pd.DataFrame())
        
        if not df_chat.empty:
            for _, row in df_chat.tail(3).iterrows():
                css = "sidebar-chat-user" if row['Role'] == 'user' else "sidebar-chat-ai"
                st.markdown(f'<div class="{css}">{row["Message"]}</div>', unsafe_allow_html=True)
        
        with st.form("sidebar_maid_form", clear_on_submit=True):
            user_input = st.text_input("輸入...", label_visibility="collapsed", placeholder="請吩咐...")
            if st.form_submit_button("送出"):
                if user_input:
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
                    
                    save_chat_log("user", user_input)
                    reply = chat_with_maid(user_input, [{"Role":r['Role'],"Message":r['Message']} for i,r in df_chat.tail(5).iterrows()], context)
                    save_chat_log("assistant", reply)
                    st.rerun()