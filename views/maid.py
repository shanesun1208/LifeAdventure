import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import base64 

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 引入 utils
from utils import get_settings, load_all_finance_data, get_weather, chat_with_maid, save_chat_log, get_daily_maid_image

def get_image_base64(file_path):
    """
    將圖片轉為 CSS 用的 Base64 字串，並移除可能導致破圖的換行符號
    """
    # 如果是預設的網路圖，直接回傳
    if file_path.startswith("http"):
        return file_path
    
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            # [關鍵修正] .replace("\n", "") 非常重要！CSS 不接受 Base64 裡有換行
            encoded = base64.b64encode(data).decode().replace("\n", "")
            
            ext = "png"
            if file_path.lower().endswith(".jpg") or file_path.lower().endswith(".jpeg"):
                ext = "jpeg"
            
            return f"data:image/{ext};base64,{encoded}"
    except Exception as e:
        print(f"Base64 error: {e}")
        # 讀取失敗時的回退圖片
        return "https://cdn-icons-png.flaticon.com/512/4140/4140047.png"

def render_maid_sidebar():
    # --- 1. 初始化狀態 ---
    if 'maid_chat_open' not in st.session_state:
        st.session_state['maid_chat_open'] = False

    if 'local_chat_history' not in st.session_state:
        st.session_state['local_chat_history'] = []

    settings = get_settings()
    current_city = settings.get('Location', 'Taipei,TW')
    
    # 取得圖片路徑
    raw_img_path = get_daily_maid_image()
    
    # [除錯區塊] 如果圖片沒出來，請看側邊欄這行字寫什麼，確認路徑對不對
    # 測試成功後可以把下面這行 st.caption 註解掉
    # st.sidebar.caption(f"DEBUG: 圖片路徑 = {raw_img_path}")
    
    # 轉碼
    maid_img_src = get_image_base64(raw_img_path)

    # --- 2. CSS ---
    # 注意：這裡的 background-image 使用了處理過的 maid_img_src
    st.markdown(f"""
    <style>
        div.stButton.maid-avatar-btn > button {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 4px solid #00CC99;
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
        
        # 1. 載入歷史資料
        if not st.session_state['local_chat_history']:
            all_data = load_all_finance_data()
            df_chat = all_data.get("ChatHistory", pd.DataFrame())
            if not df_chat.empty:
                for _, row in df_chat.tail(5).iterrows():
                    st.session_state['local_chat_history'].append({
                        "Role": row['Role'], 
                        "Message": row['Message']
                    })

        # 2. 顯示對話
        display_msgs = st.session_state['local_chat_history'][-5:]
        for msg in display_msgs:
            css = "sidebar-chat-user" if msg['Role'] == 'user' else "sidebar-chat-ai"
            st.markdown(f'<div class="{css}">{msg["Message"]}</div>', unsafe_allow_html=True)
        
        # 3. 輸入框
        with st.form("sidebar_maid_form", clear_on_submit=True):
            user_input = st.text_input("輸入...", label_visibility="collapsed", placeholder="請吩咐...")
            submitted = st.form_submit_button("送出")
            
            if submitted and user_input:
                st.session_state['local_chat_history'].append({"Role": "user", "Message": user_input})
                
                # Context 準備
                now = datetime.now()
                weather_info = get_weather(current_city)
                
                # 簡單讀取一下資料作為背景知識
                all_data = load_all_finance_data() 
                context = f"時間:{now.strftime('%H:%M')}, 天氣:{weather_info}"
                
                # 呼叫 AI
                reply = chat_with_maid(user_input, st.session_state['local_chat_history'], context)
                
                st.session_state['local_chat_history'].append({"Role": "model", "Message": reply})
                
                save_chat_log("user", user_input)
                save_chat_log("model", reply)
                
                st.rerun()