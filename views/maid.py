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
    if 'show_maid_window' not in st.session_state:
        st.session_state['show_maid_window'] = False # 預設縮小

    # 讀取設定
    settings = get_settings()
    maid_img = settings.get('Maid_Image_URL', "https://cdn-icons-png.flaticon.com/512/4140/4140047.png")
    current_city = settings.get('Location', 'Taipei,TW')

    # --- 2. CSS 魔法 (介面靈魂) ---
    st.markdown("""
    <style>
        /* 懸浮容器定位 */
        .maid-float-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: flex-end; /* 靠右對齊 */
        }

        /* A. 圓形頭像按鈕 (縮小態) */
        .maid-bubble-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background-color: #2b2b2b;
            border: 2px solid #00CC99;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            cursor: pointer;
            overflow: hidden;
            transition: transform 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .maid-bubble-btn:hover {
            transform: scale(1.1);
            border-color: #FFD700;
        }
        .maid-bubble-btn img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        /* B. 聊天視窗 (展開態) */
        .maid-chat-window {
            width: 350px;
            height: 500px;
            background-color: #1E1E1E;
            border: 1px solid #444;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            margin-bottom: 15px; /* 與按鈕的距離 */
            overflow: hidden;
        }
        
        /* 視窗標題列 */
        .maid-header {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            padding: 10px 15px;
            color: white;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        /* 對話內容區 */
        .maid-body {
            flex-grow: 1;
            padding: 10px;
            overflow-y: auto;
            background-color: #252525;
            display: flex;
            flex-direction: column-reverse; /* 讓最新訊息在最下面 (配合 st.container 邏輯) */
        }

        /* 訊息氣泡 */
        .msg-row { margin: 5px 0; display: flex; }
        .msg-row.user { justify-content: flex-end; }
        .msg-row.ai { justify-content: flex-start; }
        
        .msg-bubble {
            max-width: 80%;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.4;
        }
        .msg-bubble.user { background-color: #00CC99; color: #000; border-bottom-right-radius: 2px; }
        .msg-bubble.ai { background-color: #444; color: #fff; border-bottom-left-radius: 2px; border: 1px solid #666; }

    </style>
    """, unsafe_allow_html=True)

    # --- 3. 準備上下文數據 (給 AI) ---
    # 只有當視窗打開時才去計算，節省資源
    context_info = ""
    chat_history = []
    
    if st.session_state['show_maid_window']:
        all_data = load_all_finance_data()
        now = datetime.now()
        weather_info = get_weather(current_city)
        
        # 簡單計算 (為了速度，只取關鍵指標)
        df_fin = all_data.get("Finance", pd.DataFrame())
        df_income = all_data.get("Income", pd.DataFrame())
        df_qb = all_data.get("QuestBoard", pd.DataFrame())
        
        curr_m = now.strftime("%Y-%m")
        inc = df_income[df_income['Date'].astype(str).str.contains(curr_m)]['Amount'].sum() if not df_income.empty and 'Date' in df_income.columns else 0
        exp = df_fin[df_fin['Date'].astype(str).str.contains(curr_m)]['Price'].sum() if not df_fin.empty and 'Date' in df_fin.columns else 0
        tasks = len(df_qb[df_qb['Status'] == '進行中']) if not df_qb.empty and 'Status' in df_qb.columns else 0
        
        context_info = f"時間:{now.strftime('%H:%M')}, 天氣:{weather_info}, 本月收入:{inc}, 本月已花:{exp}, 進行中任務:{tasks}"
        
        # 讀取對話紀錄
        df_chat = all_data.get("ChatHistory", pd.DataFrame())
        if not df_chat.empty:
            for _, row in df_chat.tail(10).iterrows():
                chat_history.append({"Role": row['Role'], "Message": row['Message']})

    # --- 4. 介面渲染區 (Floating Layout) ---
    
    # 我們使用一個固定的 container 來包裝
    # 這裡利用 columns 來切版：
    # 如果是縮小態：只顯示一個圓形按鈕
    # 如果是展開態：顯示視窗 (不顯示圓形按鈕，改為視窗內的關閉鈕，或是保留按鈕作為 toggle)
    
    # 為了讓按鈕能點擊，我們必須使用 Streamlit 的 native button，
    # 但要用 CSS 把它偽裝成懸浮球。
    
    # 容器開始
    with st.container():
        # A. 展開的聊天視窗
        if st.session_state['show_maid_window']:
            # 為了要把視窗固定在右下角，我們用 sidebar 或是空的 container 撐住位置
            # 但最好的方法是直接畫出 UI
            
            # 使用 CSS 容器包裹
            st.markdown('<div class="maid-float-container">', unsafe_allow_html=True)
            
            # 視窗本體
            with st.container():
                st.markdown('<div class="maid-chat-window">', unsafe_allow_html=True)
                
                # 標題列 (含關閉按鈕)
                c_head_1, c_head_2 = st.columns([4, 1])
                with c_head_1:
                    st.markdown(f'<div style="padding:10px; color:white; font-weight:bold;">💬 貼身秘書 ({weather_info})</div>', unsafe_allow_html=True)
                with c_head_2:
                    if st.button("✖️", key="close_maid"):
                        st.session_state['show_maid_window'] = False
                        st.rerun()
                
                # 歷史訊息區 (顯示最近 5 則)
                st.markdown('<div class="maid-body">', unsafe_allow_html=True)
                # 反轉順序顯示，讓對話感覺像是由下往上堆疊 (或是直接顯示)
                # 這裡我們用標準順序
                for chat in chat_history:
                    role_cls = "user" if chat["Role"] == "user" else "ai"
                    st.markdown(f"""
                        <div class="msg-row {role_cls}">
                            <div class="msg-bubble {role_cls}">{chat["Message"]}</div>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True) # End body
                
                # 輸入區
                with st.form("maid_chat_float", clear_on_submit=True):
                    c_in, c_send = st.columns([3, 1])
                    with c_in:
                        user_in = st.text_input("輸入...", label_visibility="collapsed", placeholder="說點什麼...")
                    with c_send:
                        submitted = st.form_submit_button("➤")
                    
                    if submitted and user_in:
                        save_chat_log("user", user_in)
                        reply = chat_with_maid(user_in, chat_history, context_info)
                        save_chat_log("assistant", reply)
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True) # End window
            
            st.markdown('</div>', unsafe_allow_html=True) # End float container

        # B. 縮小的圓形按鈕 (只有當視窗關閉時顯示，或者一直顯示)
        else:
            # 這裡我們用一個 trick：
            # 產生一個透明的 st.button，然後用 CSS 把圖片蓋在上面
            # 當使用者點擊圖片時，其實是點到了按鈕
            
            st.markdown(f"""
            <div class="maid-float-container">
                <div class="maid-bubble-btn">
                    <img src="{maid_img}">
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 這個按鈕是隱形的，但位置重疊在上面的 div 上 (透過 CSS 調整)
            # 為了簡單起見，我們直接在右下角放一個 st.button，並用 CSS 把它變成圓形圖片
            
            # 這是真的按鈕，負責觸發 open
            # 我們給它一個獨特的 key，並用 CSS 選取器去美化它
            
            # 使用自訂 CSS 類別來包覆按鈕
            # 這裡需要一點黑魔法：Streamlit 的按鈕很難完全客製化成圖片
            # 所以我們用最簡單的方案：按鈕顯示文字 "💬"，然後用 CSS 把它變圓、變大、移到右下角
            
            # 注入 CSS 來覆蓋這個特定按鈕的樣式
            st.markdown("""
            <style>
            div.stButton.maid-toggle-btn {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 10000;
            }
            div.stButton.maid-toggle-btn > button {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background-color: #2b2b2b;
                border: 2px solid #00CC99;
                color: white;
                font-size: 24px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            }
            div.stButton.maid-toggle-btn > button:hover {
                border-color: #FFD700;
                transform: scale(1.1);
            }
            </style>
            """, unsafe_allow_html=True)
            
            # 透過 container 加上 class
            c_btn = st.container()
            c_btn.markdown('<div class="stButton maid-toggle-btn">', unsafe_allow_html=True)
            if c_btn.button("💬", key="open_maid_btn"):
                st.session_state['show_maid_window'] = True
                st.rerun()
            c_btn.markdown('</div>', unsafe_allow_html=True)