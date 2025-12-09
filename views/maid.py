import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 引入 utils
from utils import (
    get_settings,
    load_all_finance_data,
    get_weather,
    chat_with_maid,
    save_chat_log,
    get_daily_maid_image,
)


def render_maid_page():
    """
    [新版] 小秘書主頁面介面 (修正時區 + 色塊對話框)
    """
    st.title("🎀 專屬小秘書")
    st.caption("在這裡與您的 AI 助手討論冒險規劃...")

    # --- CSS 樣式: 定義淡藍與淡粉對話框 ---
    st.markdown(
        """
    <style>
        /* 對話外層容器: 用 flex 控制左右對齊 */
        .chat-row {
            display: flex;
            margin-bottom: 12px;
            width: 100%;
        }
        
        /* 主人靠右 */
        .user-row {
            justify-content: flex-end;
        }
        
        /* 秘書靠左 */
        .maid-row {
            justify-content: flex-start;
        }
        
        /* 訊息氣泡本體 */
        .msg-bubble {
            padding: 10px 16px;
            border-radius: 15px;
            max-width: 75%;
            font-size: 16px;
            line-height: 1.5;
            box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
            position: relative;
        }
        
        /* 主人樣式: 淡藍色 + 右下角尖角 */
        .user-bg {
            background-color: #D1E8FF; 
            color: #1e1e1e;
            border-bottom-right-radius: 2px;
        }
        
        /* 秘書樣式: 淡粉色 + 左下角尖角 */
        .maid-bg {
            background-color: #FFD1DC;
            color: #1e1e1e;
            border-bottom-left-radius: 2px;
        }
        
        /* 隱藏原生 Streamlit 元素的多餘間距 */
        .block-container {
            padding-top: 2rem;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 初始化聊天歷史
    if "local_chat_history" not in st.session_state:
        st.session_state["local_chat_history"] = []
        # 從 Sheet 載入最後 5 筆
        all_data = load_all_finance_data()
        df_chat = all_data.get("ChatHistory", pd.DataFrame())
        if not df_chat.empty:
            for _, row in df_chat.tail(5).iterrows():
                st.session_state["local_chat_history"].append(
                    {"Role": row["Role"], "Message": row["Message"]}
                )

    # --- 準備資料 ---
    settings = get_settings()
    current_city = settings.get("Location", "Taipei,TW")
    weather_info = get_weather(current_city)

    # [修正點 1] 強制鎖定台灣時間 (UTC+8)
    # 不管伺服器在哪，都手動加 8 小時，避免半夜被當成早上
    tw_time = datetime.utcnow() + timedelta(hours=8)
    time_str = tw_time.strftime("%Y-%m-%d %H:%M")

    # 簡單計算財務狀況
    all_data = load_all_finance_data()
    df_budget = all_data.get("Budget", pd.DataFrame())
    df_quest = all_data.get("QuestBoard", pd.DataFrame())

    budget_summary = "資料讀取中"
    if not df_budget.empty and "Remaining" in df_budget.columns:
        try:
            total_remain = df_budget["Remaining"].astype(float).sum()
            budget_summary = f"{total_remain:,.0f} G"
        except:
            budget_summary = "計算錯誤"

    active_quests = 0
    if not df_quest.empty and "Status" in df_quest.columns:
        active_quests = len(df_quest[df_quest["Status"] == "進行中"])

    # 組合給 AI 的情報 (使用修正後的台灣時間)
    context_info = (
        f"現在時間 (台灣): {time_str}\n"
        f"所在城市天氣: {weather_info}\n"
        f"主人預算總剩餘: {budget_summary}\n"
        f"進行中任務數: {active_quests} 個"
    )

    # --- 頁面佈局 ---
    col_img, col_chat = st.columns([1, 2], gap="large")

    # [左欄] 秘書形象
    with col_img:
        st.markdown("### 📋 今日簡報")
        image_path = get_daily_maid_image()
        st.image(
            image_path, caption="專屬小秘書待命中", use_container_width=True
        )

        st.info(
            f"""
        **📍 環境與狀態**
        * **時間**: {time_str}
        * **天氣**: {weather_info.split('|')[-1].strip() if '|' in weather_info else weather_info}
        * **任務**: {active_quests} 個進行中
        * **財庫**: {budget_summary}
        """
        )

    # [右欄] 對話視窗 (使用自定義 CSS 渲染)
    with col_chat:
        st.markdown("### 💬 會談記錄")

        # 建立捲軸容器
        chat_container = st.container(height=500)

        with chat_container:
            # [修正點 2] 放棄 st.chat_message，改用 HTML/CSS 畫氣泡
            for msg in st.session_state["local_chat_history"]:
                role = msg["Role"]
                content = msg["Message"]

                if role == "user":
                    # 主人: 靠右 + 淡藍色
                    st.markdown(
                        f"""
                    <div class="chat-row user-row">
                        <div class="msg-bubble user-bg">
                            {content}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    # 秘書: 靠左 + 淡粉色
                    st.markdown(
                        f"""
                    <div class="chat-row maid-row">
                        <div class="msg-bubble maid-bg">
                            {content}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # 輸入框
        if user_input := st.chat_input("請吩咐..."):

            # 1. 顯示使用者輸入 (先暫時寫入 Session)
            st.session_state["local_chat_history"].append(
                {"Role": "user", "Message": user_input}
            )

            # 為了即時感，手動先畫出主人的訊息 (因為 chat_input 回調前還沒重繪)
            with chat_container:
                st.markdown(
                    f"""
                    <div class="chat-row user-row">
                        <div class="msg-bubble user-bg">
                            {user_input}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # 2. 呼叫 AI
            with col_chat:
                with st.spinner("小秘書正在思考中..."):
                    reply = chat_with_maid(
                        user_input,
                        st.session_state["local_chat_history"],
                        context_info,
                    )

            # 3. 存入紀錄
            st.session_state["local_chat_history"].append(
                {"Role": "model", "Message": reply}
            )
            save_chat_log("user", user_input)
            save_chat_log("model", reply)

            # 4. 刷新頁面 (顯示完整對話)
            st.rerun()
