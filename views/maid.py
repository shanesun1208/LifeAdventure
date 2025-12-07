import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 引入 utils
from utils import get_settings, load_all_finance_data, get_weather, chat_with_maid, save_chat_log, get_daily_maid_image

def render_maid_sidebar():
    # --- 1. 初始化狀態 ---
    if 'maid_chat_open' not in st.session_state:
        st.session_state['maid_chat_open'] = False

    if 'local_chat_history' not in st.session_state:
        st.session_state['local_chat_history'] = []

    # --- 2. 取得圖片路徑 ---
    # 這是從 utils 拿到的絕對路徑
    image_path = get_daily_maid_image()
    
    # --- 3. [除錯區] ---
    # 如果圖片沒出來，請截圖這兩行字給我看
    st.sidebar.caption(f"🔍 偵測路徑: `{image_path}`")
    if os.path.exists(image_path):
        st.sidebar.success("✅ 檔案存在！")
    else:
        st.sidebar.error("❌ 找不到檔案，請檢查資料夾結構")

    # --- 4. 顯示女僕 (使用原生元件，放棄 CSS 按鈕) ---
    st.markdown("---")
    
    # 使用 st.image 直接顯示，這是最穩定的方法
    # caption 可以當作狀態列
    st.image(image_path, caption="您的專屬冒險助手", use_container_width=True)
    
    # 用一個普通的按鈕來開關對話框
    if st.button("💬 開啟/關閉對話", use_container_width=True):
        st.session_state['maid_chat_open'] = not st.session_state['maid_chat_open']
        st.rerun()

    # --- 5. 對話框邏輯 (保持不變) ---
    if st.session_state['maid_chat_open']:
        st.markdown("##### 💬 貼身秘書")
        
        # 1. 載入歷史
        if not st.session_state['local_chat_history']:
            all_data = load_all_finance_data()
            df_chat = all_data.get("ChatHistory", pd.DataFrame())
            if not df_chat.empty:
                for _, row in df_chat.tail(5).iterrows():
                    st.session_state['local_chat_history'].append({
                        "Role": row['Role'], 
                        "Message": row['Message']
                    })

        # 2. 顯示訊息
        # 這裡為了簡單，我們直接用 st.chat_message (Streamlit 新版原生對話框)
        # 如果您的 Streamlit 版本夠新 (1.24+)，這會比 CSS 漂亮很多
        for msg in st.session_state['local_chat_history'][-5:]:
            role_name = "user" if msg['Role'] == 'user' else "assistant"
            with st.chat_message(role_name):
                st.write(msg["Message"])
        
        # 3. 輸入框
        # 使用原生 chat_input (如果不行的話我們再換回 text_input)
        if user_input := st.chat_input("請吩咐..."):
            
            # 顯示使用者訊息
            st.session_state['local_chat_history'].append({"Role": "user", "Message": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # 準備 Context
            settings = get_settings()
            current_city = settings.get('Location', 'Taipei,TW')
            now = datetime.now()
            weather_info = get_weather(current_city)
            context = f"時間:{now.strftime('%H:%M')}, 天氣:{weather_info}"
            
            # 呼叫 AI
            # 顯示載入中動畫
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    reply = chat_with_maid(user_input, st.session_state['local_chat_history'], context)
                    st.write(reply)
            
            # 存檔
            st.session_state['local_chat_history'].append({"Role": "model", "Message": reply})
            save_chat_log("user", user_input)
            save_chat_log("model", reply)
            
            # chat_input 不需要 rerun，它會自動更新