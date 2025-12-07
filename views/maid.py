import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import base64 # 新增：為了處理圖片轉碼給 CSS 用

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 引入 utils
from utils import get_settings, load_all_finance_data, get_weather, chat_with_maid, save_chat_log, get_daily_maid_image

def get_image_base64(file_path):
    """
    輔助函式：將本地圖片路徑轉為 CSS 可用的 Base64 字串
    如果路徑是網址(http開頭)，就直接回傳
    """
    if file_path.startswith("http"):
        return file_path
    
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode()
            # 判斷副檔名
            ext = "png"
            if file_path.lower().endswith(".jpg") or file_path.lower().endswith(".jpeg"):
                ext = "jpeg"
            return f"data:image/{ext};base64,{encoded}"
    except Exception as e:
        # 如果讀取失敗，回傳預設圖
        return "https://cdn-icons-png.flaticon.com/512/4140/4140047.png"

def render_maid_sidebar():
    # --- 1. 初始化狀態 ---
    if 'maid_chat_open' not in st.session_state:
        st.session_state['maid_chat_open'] = False

    # [關鍵] 初始化對話暫存區，解決「寫入Sheet後畫面沒更新」的問題
    if 'local_chat_history' not in st.session_state:
        st.session_state['local_chat_history'] = []

    settings = get_settings()
    current_city = settings.get('Location', 'Taipei,TW')
    
    # 取得圖片路徑 (來自 utils 的新功能)
    raw_img_path = get_daily_maid_image()
    # [關鍵] 轉碼為 CSS 能讀的格式
    maid_img_src = get_image_base64(raw_img_path)

    # --- 2. CSS ---
    st.markdown(f"""
    <style>
        div.stButton.maid-avatar-btn > button {{
            width: 150px;
            height: 150px;
            border-radius: 50%;
            border: 4px solid #00CC99;
            /* 這裡填入處理過的 Base64 字串 */
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
        
        # [邏輯修正] 優先顯示 session_state 裡的對話，如果空的才去抓 Sheet
        # 這樣可以讓剛講的話立刻顯示，不需要等 Sheet 更新
        
        # 1. 載入歷史資料 (如果 session 還是空的)
        if not st.session_state['local_chat_history']:
            all_data = load_all_finance_data()
            df_chat = all_data.get("ChatHistory", pd.DataFrame())
            if not df_chat.empty:
                # 只取最後 5 筆塞入暫存
                for _, row in df_chat.tail(5).iterrows():
                    st.session_state['local_chat_history'].append({
                        "Role": row['Role'], 
                        "Message": row['Message']
                    })

        # 2. 顯示對話泡泡 (從 session_state 讀取)
        # 我們只顯示最後 4-5 筆，避免太長
        display_msgs = st.session_state['local_chat_history'][-5:]
        for msg in display_msgs:
            css = "sidebar-chat-user" if msg['Role'] == 'user' else "sidebar-chat-ai"
            st.markdown(f'<div class="{css}">{msg["Message"]}</div>', unsafe_allow_html=True)
        
        # 3. 輸入框與處理
        with st.form("sidebar_maid_form", clear_on_submit=True):
            user_input = st.text_input("輸入...", label_visibility="collapsed", placeholder="請吩咐...")
            submitted = st.form_submit_button("送出")
            
            if submitted and user_input:
                # A. 先把主人的話顯示出來 (更新 Session)
                st.session_state['local_chat_history'].append({"Role": "user", "Message": user_input})
                
                # B. 準備 Context
                now = datetime.now()
                weather_info = get_weather(current_city)
                
                # 重新讀取數據以確保準確 (雖然有點耗效能，但在此處還好)
                # 為了加速，也可以用 st.session_state 緩存的資料，這裡先維持您的寫法
                all_data = load_all_finance_data() 
                df_fin = all_data.get("Finance", pd.DataFrame())
                df_income = all_data.get("Income", pd.DataFrame())
                df_qb = all_data.get("QuestBoard", pd.DataFrame())
                
                curr_m = now.strftime("%Y-%m")
                inc = df_income[df_income['Date'].astype(str).str.contains(curr_m)]['Amount'].sum() if not df_income.empty and 'Date' in df_income.columns else 0
                exp = df_fin[df_fin['Date'].astype(str).str.contains(curr_m)]['Price'].sum() if not df_fin.empty and 'Date' in df_fin.columns else 0
                tasks = len(df_qb[df_qb['Status'] == '進行中']) if not df_qb.empty and 'Status' in df_qb.columns else 0
                
                context = f"時間:{now.strftime('%H:%M')}, 天氣:{weather_info}, 本月收入:{inc}, 本月已花:{exp}, 進行中任務:{tasks}"
                
                # C. 呼叫 AI (帶入最近的對話記憶)
                reply = chat_with_maid(user_input, st.session_state['local_chat_history'], context)
                
                # D. 把女僕的話顯示出來 (更新 Session)
                st.session_state['local_chat_history'].append({"Role": "model", "Message": reply})
                
                # E. 背景存檔 (寫入 Sheet)
                save_chat_log("user", user_input)
                save_chat_log("model", reply) # 修正：統一用 model 或 assistant，這裡用 model 配合 utils
                
                # F. 重新整理頁面，讓對話框立刻更新
                st.rerun()