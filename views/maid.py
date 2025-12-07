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
    image_path = get_daily_maid_image()
    
    # --- 3. 顯示女僕 (已移除 caption) ---
    st.markdown("---")
    
    # [修正] 移除 caption 參數，這樣就不會顯示文字了
    st.image(image_path, use_container_width=True)
    
    # 按鈕：開啟/關閉對話
    if st.button("💬 開啟/關閉對話", use_container_width=True):
        st.session_state['maid_chat_open'] = not st.session_state['maid_chat_open']
        st.rerun()

    # --- 4. 對話框邏輯 ---
    if st.session_state['maid_chat_open']:
        st.markdown("##### 💬 貼身秘書")
        
        # 載入歷史
        if not st.session_state['local_chat_history']:
            all_data = load_all_finance_data()
            df_chat = all_data.get("ChatHistory", pd.DataFrame())
            if not df_chat.empty:
                for _, row in df_chat.tail(5).iterrows():
                    st.session_state['local_chat_history'].append({
                        "Role": row['Role'], 
                        "Message": row['Message']
                    })

        # 顯示訊息 (使用原生 chat_message)
        for msg in st.session_state['local_chat_history'][-5:]:
            role_name = "user" if msg['Role'] == 'user' else "assistant"
            # 注意：這裡 assistant 的頭像可以不用設定，讓它用預設的機器人圖示，或是您想用女僕圖也可以
            with st.chat_message(role_name):
                st.write(msg["Message"])
        
        # 輸入框
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
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    reply = chat_with_maid(user_input, st.session_state['local_chat_history'], context)
                    st.write(reply)
            
            # 存檔
            st.session_state['local_chat_history'].append({"Role": "model", "Message": reply})
            save_chat_log("user", user_input)
            save_chat_log("model", reply)