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
    [升級版] 小秘書主頁面：強化資料餵食，解決牛頭不對馬嘴
    """
    st.title("🎀 專屬小秘書")
    st.caption("已連線至 Life Adventure 資料庫，請吩咐...")

    # CSS 樣式 (維持不變)
    st.markdown(
        """
    <style>
        .chat-row { display: flex; margin-bottom: 12px; width: 100%; }
        .user-row { justify-content: flex-end; }
        .maid-row { justify-content: flex-start; }
        .msg-bubble { padding: 10px 16px; border-radius: 15px; max-width: 75%; font-size: 16px; line-height: 1.5; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); position: relative; }
        .user-bg { background-color: #D1E8FF; color: #1e1e1e; border-bottom-right-radius: 2px; }
        .maid-bg { background-color: #FFD1DC; color: #1e1e1e; border-bottom-left-radius: 2px; }
        .block-container { padding-top: 2rem; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 初始化聊天歷史
    if "local_chat_history" not in st.session_state:
        st.session_state["local_chat_history"] = []
        all_data = load_all_finance_data()
        df_chat = all_data.get("ChatHistory", pd.DataFrame())
        if not df_chat.empty:
            for _, row in df_chat.tail(5).iterrows():
                st.session_state["local_chat_history"].append(
                    {"Role": row["Role"], "Message": row["Message"]}
                )

    # --- [關鍵修改] 準備更詳細的資料 ---
    settings = get_settings()
    current_city = settings.get("Location", "Taipei,TW")
    weather_info = get_weather(current_city)
    tw_time = datetime.utcnow() + timedelta(hours=8)
    time_str = tw_time.strftime("%Y-%m-%d %H:%M")

    all_data = load_all_finance_data()
    df_budget = all_data.get("Budget", pd.DataFrame())
    df_quest = all_data.get("QuestBoard", pd.DataFrame())
    df_finance = all_data.get("Finance", pd.DataFrame())  # 讀取支出紀錄

    # 1. 財務摘要
    budget_summary = "無法讀取"
    if not df_budget.empty and "Remaining" in df_budget.columns:
        try:
            total_remain = df_budget["Remaining"].astype(float).sum()
            budget_summary = f"{total_remain:,.0f} G"
        except:
            pass

    # 2. [新增] 近期支出 (讓她知道你剛花過什麼錢)
    recent_expenses = "無近期支出"
    if (
        not df_finance.empty
        and "Item" in df_finance.columns
        and "Price" in df_finance.columns
    ):
        # 取最後 3 筆
        last_3 = df_finance.tail(3)
        recent_expenses = ", ".join(
            [f"{row['Item']}(${row['Price']})" for _, row in last_3.iterrows()]
        )

    # 3. [新增] 待辦任務清單 (讓她知道你該忙什麼)
    active_quests_summary = "目前無進行中任務"
    active_count = 0
    if not df_quest.empty and "Status" in df_quest.columns:
        active_df = df_quest[df_quest["Status"] == "進行中"]
        active_count = len(active_df)
        if active_count > 0:
            # 取前 3 個任務名稱
            tasks = active_df.head(3)["TaskName"].tolist()
            active_quests_summary = "、".join(tasks)
            if active_count > 3:
                active_quests_summary += f" ...等共 {active_count} 項"

    # 4. 組合強力情報 Context
    context_info = (
        f"【系統時間】{time_str}\n"
        f"【所在環境】{weather_info}\n"
        f"【財務狀態】總預算剩餘: {budget_summary}。\n"
        f"【近期消費】{recent_expenses}\n"
        f"【待辦任務】{active_quests_summary}"
    )

    # --- 頁面佈局 ---
    col_img, col_chat = st.columns([1, 2], gap="large")

    with col_img:
        st.markdown("### 📋 狀態監控")
        image_path = get_daily_maid_image()
        st.image(image_path, caption="系統運作中", use_container_width=True)

        # 顯示更具體的資訊
        st.info(
            f"""
        **📊 關鍵數據**
        * **時間**: {time_str}
        * **任務**: {active_count} 個待辦
        * **焦點**: {active_quests_summary[:10]}...
        * **財庫**: {budget_summary}
        """
        )

    with col_chat:
        st.markdown("### 💬 戰術會議")

        chat_container = st.container(height=500)

        with chat_container:
            for msg in st.session_state["local_chat_history"]:
                role = msg["Role"]
                content = msg["Message"]
                if role == "user":
                    st.markdown(
                        f'<div class="chat-row user-row"><div class="msg-bubble user-bg">{content}</div></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="chat-row maid-row"><div class="msg-bubble maid-bg">{content}</div></div>',
                        unsafe_allow_html=True,
                    )

        if user_input := st.chat_input(
            "請輸入指令 (例: 我最近花了什麼錢? 我該先做哪個任務?)..."
        ):
            st.session_state["local_chat_history"].append(
                {"Role": "user", "Message": user_input}
            )
            with chat_container:
                st.markdown(
                    f'<div class="chat-row user-row"><div class="msg-bubble user-bg">{user_input}</div></div>',
                    unsafe_allow_html=True,
                )

            with col_chat:
                with st.spinner("分析數據中..."):
                    reply = chat_with_maid(
                        user_input,
                        st.session_state["local_chat_history"],
                        context_info,
                    )

            st.session_state["local_chat_history"].append(
                {"Role": "model", "Message": reply}
            )
            save_chat_log("user", user_input)
            save_chat_log("model", reply)
            st.rerun()
