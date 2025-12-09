import streamlit as st
import pandas as pd
from datetime import datetime
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
    [新版] 小秘書主頁面介面
    """
    # [修改] 標題改為 "專屬小秘書"，既親切又安全
    st.title("🎀 專屬小秘書")
    st.caption("在這裡與您的 AI 助手討論冒險規劃...")
    st.markdown("---")

    # 初始化聊天歷史
    if "local_chat_history" not in st.session_state:
        st.session_state["local_chat_history"] = []
        # 如果是空的，嘗試從 Sheet 載入最後 5 筆，延續記憶
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

    # 簡單計算財務狀況
    all_data = load_all_finance_data()
    df_budget = all_data.get("Budget", pd.DataFrame())
    df_quest = all_data.get("QuestBoard", pd.DataFrame())

    # 取得本月預算餘額
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

    # 組合給 AI 的情報
    context_info = (
        f"現在時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"所在城市天氣: {weather_info}\n"
        f"主人預算總剩餘: {budget_summary}\n"
        f"進行中任務數: {active_quests} 個"
    )

    # --- 頁面佈局 (左右兩欄) ---
    col_img, col_chat = st.columns([1, 2], gap="large")

    # [左欄] 秘書形象與狀態
    with col_img:
        st.markdown("### 📋 今日簡報")
        image_path = get_daily_maid_image()
        # 顯示圖片
        st.image(
            image_path, caption="專屬小秘書待命中", use_container_width=True
        )

        st.info(
            f"""
        **📍 環境與狀態**
        * **天氣**: {weather_info.split('|')[-1].strip() if '|' in weather_info else weather_info}
        * **任務**: {active_quests} 個進行中
        * **財庫**: {budget_summary}
        """
        )

    # [右欄] 對話視窗
    with col_chat:
        st.markdown("### 💬 會談記錄")

        # 建立捲軸容器
        chat_container = st.container(height=500)

        with chat_container:
            # 顯示歷史訊息
            for msg in st.session_state["local_chat_history"]:
                role = msg["Role"]
                st_role = "user" if role == "user" else "assistant"
                with st.chat_message(st_role):
                    st.write(msg["Message"])

        # 輸入框
        if user_input := st.chat_input("請吩咐 (例如: 幫我看看財務狀況?)..."):

            # 1. 顯示使用者輸入
            st.session_state["local_chat_history"].append(
                {"Role": "user", "Message": user_input}
            )
            with chat_container:
                with st.chat_message("user"):
                    st.write(user_input)

            # 2. 呼叫 AI
            with col_chat:
                with st.spinner("小秘書正在查詢資料..."):
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

            # 4. 刷新
            st.rerun()
