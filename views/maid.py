import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_settings, load_all_finance_data, get_weather, chat_with_maid, save_chat_log

def render_maid_widget():
    # --- 1. 初始化狀態 ---
    if 'maid_open' not in st.session_state:
        st.session_state['maid_open'] = False

    # 讀取設定
    settings = get_settings()
    maid_img = settings.get('Maid_Image_URL', "https://cdn-icons-png.flaticon.com/512/4140/4140047.png")
    current_city = settings.get('Location', 'Taipei,TW')

    # --- 2. 準備上下文數據 (給 AI 用) ---
    context_info = ""
    chat_history = []
    
    # 只有打開時才讀取資料，節省效能
    if st.session_state['maid_open']:
        all_data = load_all_finance_data()
        now = datetime.now()
        weather_info = get_weather(current_city)
        
        df_fin = all_data.get("Finance", pd.DataFrame())
        df_income = all_data.get("Income", pd.DataFrame())
        df_qb = all_data.get("QuestBoard", pd.DataFrame())
        
        curr_m = now.strftime("%Y-%m")
        inc = df_income[df_income['Date'].astype(str).str.contains(curr_m)]['Amount'].sum() if not df_income.empty and 'Date' in df_income.columns else 0
        exp = df_fin[df_fin['Date'].astype(str).str.contains(curr_m)]['Price'].sum() if not df_fin.empty and 'Date' in df_fin.columns else 0
        tasks = len(df_qb[df_qb['Status'] == '進行中']) if not df_qb.empty and 'Status' in df_qb.columns else 0
        
        context_info = f"時間:{now.strftime('%H:%M')}, 天氣:{weather_info}, 本月收入:{inc}, 本月已花:{exp}, 進行中任務:{tasks}"
        
        df_chat = all_data.get("ChatHistory", pd.DataFrame())
        if not df_chat.empty:
            for _, row in df_chat.tail(8).iterrows(): # 取最近 8 則
                chat_history.append({"Role": row['Role'], "Message": row['Message']})

    # --- 3. CSS 魔法 (核心修正) ---
    st.markdown(f"""
    <style>
        /* 1. 鎖定包含 'maid-marker' 的父容器，將其固定在右下角 */
        div[data-testid="stVerticalBlock"]:has(div.maid-marker) {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: auto;
            z-index: 100000; /* 最上層 */
            background: transparent;
            pointer-events: none; /* 讓容器本身不擋滑鼠，只有內部元素可點 */
        }}
        
        /* 2. 恢復內部元素的點擊事件 */
        div[data-testid="stVerticalBlock"]:has(div.maid-marker) * {{
            pointer-events: auto;
        }}

        /* 3. 圓形頭像按鈕樣式 (偽裝 st.button) */
        button[key="maid_toggle_btn"] {{
            width: 70px;
            height: 70px;
            border-radius: 50%;
            border: 3px solid #00CC99;
            background-image: url('{maid_img}');
            background-size: cover;
            background-position: center;
            background-color: #2b2b2b;
            color: transparent; /* 隱藏文字 */
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        button[key="maid_toggle_btn"]:hover {{
            transform: scale(1.1);
            box-shadow: 0 0 20px #00CC99;
            border-color: #FFD700;
        }}
        /* 隱藏按鈕內的預設文字容器 */
        button[key="maid_toggle_btn"] div {{
            display: none;
        }}

        /* 4. 聊天視窗樣式 */
        .maid-window-frame {{
            width: 320px;
            height: 480px;
            background-color: #1E1E1E;
            border: 1px solid #444;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            margin-bottom: 10px; /* 與按鈕的距離 */
        }}
        
        .chat-area {{
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            background: #252525;
            display: flex;
            flex-direction: column-reverse; /* 新訊息在下 */
        }}
        
        .msg-bubble {{
            padding: 8px 12px;
            border-radius: 12px;
            margin: 5px 0;
            font-size: 14px;
            max-width: 85%;
            line-height: 1.4;
        }}
        .msg-user {{ background: #00CC99; color: #000; align-self: flex-end; border-bottom-right-radius: 2px; }}
        .msg-ai {{ background: #444; color: #fff; align-self: flex-start; border-bottom-left-radius: 2px; border: 1px solid #555; }}

    </style>
    """, unsafe_allow_html=True)

    # --- 4. 介面渲染 (懸浮區塊) ---
    
    # 建立一個容器，這就是我們要讓 CSS 鎖定並浮動的對象
    container = st.container()
    
    with container:
        # [關鍵] 插入一個隱藏的標記 DIV，讓 CSS 的 :has() 選擇器可以找到這個容器
        st.markdown('<div class="maid-marker"></div>', unsafe_allow_html=True)

        if st.session_state['maid_open']:
            # === A. 展開狀態：顯示聊天視窗 ===
            
            # 使用自訂 HTML 結構來畫視窗外框 (標題 + 內容區)
            # 注意：輸入框必須用 Streamlit 原生元件，所以我們只畫上半部
            
            # 1. 視窗上半部 (標題 + 關閉鈕)
            # 這裡用 columns 來排版關閉按鈕
            top_c1, top_c2 = st.columns([5, 1])
            with top_c1:
                st.markdown(f"**💬 貼身秘書** <span style='font-size:12px;color:#aaa;'>({weather_info})</span>", unsafe_allow_html=True)
            with top_c2:
                if st.button("✖️", key="close_maid"):
                    st.session_state['maid_open'] = False
                    st.rerun()
            
            # 2. 聊天歷史顯示區
            with st.container(height=350): # 使用固定高度容器產生捲軸
                for chat in chat_history:
                    role_cls = "msg-user" if chat["Role"] == "user" else "msg-ai"
                    # 使用 flex 排版讓氣泡靠左/靠右
                    align = "flex-end" if chat["Role"] == "user" else "flex-start"
                    st.markdown(f"""
                    <div style="display:flex; justify-content:{align};">
                        <div class="msg-bubble {role_cls}">{chat["Message"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # 3. 輸入區
            with st.form("maid_chat_form", clear_on_submit=True):
                user_in = st.text_input("輸入...", label_visibility="collapsed", placeholder="請吩咐...")
                if st.form_submit_button("送出 ➤", use_container_width=True):
                    if user_in:
                        save_chat_log("user", user_in)
                        reply = chat_with_maid(user_in, chat_history, context_info)
                        save_chat_log("assistant", reply)
                        st.rerun()

        else:
            # === B. 縮小狀態：顯示圓形按鈕 ===
            # 我們利用 CSS 把這個按鈕變形成圖片
            # key="maid_toggle_btn" 對應上面的 CSS選擇器
            if st.button("Open", key="maid_toggle_btn"):
                st.session_state['maid_open'] = True
                st.rerun()