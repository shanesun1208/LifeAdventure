import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 路徑修正
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_worksheet, get_weather, get_maid_briefing, load_all_finance_data

def show_home_page(current_city, current_goal):
    now = datetime.utcnow() + timedelta(hours=8)
    weather_info = get_weather(current_city)
    
    # --- 1. 準備數據給 AI 女僕 ---
    # 為了讓女僕知道狀況，我們需要先偷看一眼資料庫
    # 這裡使用 load_all_finance_data 讀取快取，速度很快
    all_data = load_all_finance_data()
    
    # 算財務
    df_fin = all_data.get("Finance", pd.DataFrame())
    df_income = all_data.get("Income", pd.DataFrame())
    df_fixed = all_data.get("FixedExpenses", pd.DataFrame())
    df_budget = all_data.get("Budget", pd.DataFrame())
    
    current_month_str = now.strftime("%Y-%m")
    
    # 簡單計算自由現金 (邏輯簡化版，只為了給AI參考)
    total_income = 0
    if not df_income.empty and 'Date' in df_income.columns:
        df_income['Date'] = df_income['Date'].astype(str)
        inc = df_income[df_income['Date'].str.contains(current_month_str)]
        inc['Amount'] = pd.to_numeric(inc['Amount'], errors='coerce').fillna(0)
        total_income = int(inc['Amount'].sum())
        
    total_fixed = 0
    if not df_fixed.empty:
        df_fixed['Amount'] = pd.to_numeric(df_fixed['Amount'], errors='coerce').fillna(0)
        # 這裡簡單抓總額，不細算攤提，只求大概
        total_fixed = int(df_fixed['Amount'].sum())
        
    total_spent = 0
    if not df_fin.empty and 'Date' in df_fin.columns:
        df_fin['Date'] = df_fin['Date'].astype(str)
        fin = df_fin[df_fin['Date'].str.contains(current_month_str)]
        fin['Price'] = pd.to_numeric(fin['Price'], errors='coerce').fillna(0)
        total_spent = int(fin['Price'].sum())
        
    reserve_goal = 0
    if not df_budget.empty:
        df_budget['Budget'] = pd.to_numeric(df_budget['Budget'], errors='coerce').fillna(0)
        for _, row in df_budget.iterrows():
            if "預備金" in str(row['Item']): reserve_goal = int(row['Budget'])

    free_cash = total_income - total_fixed - total_spent - reserve_goal

    # 算任務
    df_qb = all_data.get("QuestBoard", pd.DataFrame())
    urgent_count = 0
    active_count = 0
    if not df_qb.empty and 'Status' in df_qb.columns:
        urgent_count = len(df_qb[df_qb['Status'] == '待接取'])
        active_count = len(df_qb[df_qb['Status'] == '進行中'])

    # --- 2. 呼叫 AI 女僕 ---
    maid_msg = get_maid_briefing(now.hour, weather_info, free_cash, urgent_count, active_count)

    # --- 3. 介面顯示 ---
    
    # CSS: 對話框樣式
    st.markdown("""
    <style>
    .maid-container {
        background-color: #2b2b2b;
        border-radius: 15px;
        border: 2px solid #e1bee7; /* 淡紫色邊框 */
        padding: 20px;
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(225, 190, 231, 0.2);
    }
    .maid-avatar {
        font-size: 50px;
    }
    .maid-text {
        font-size: 16px;
        line-height: 1.5;
        color: #fff;
        font-family: '微軟正黑體', sans-serif;
    }
    .status-badge {
        background-color: rgba(255,255,255,0.1);
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        color: #aaa;
        margin-right: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 顯示歡迎區塊 (結合女僕對話)
    st.markdown(f"""
    <div class="maid-container">
        <div class="maid-avatar">👧</div>
        <div>
            <div style="font-size: 24px; font-weight: bold; color: #e1bee7; margin-bottom: 5px;">
                {now.strftime("%H:%M")} | {weather_info}
            </div>
            <div class="maid-text">
                {maid_msg}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 人生目標
    st.markdown(f"""
    <div class="goal-box">
        <div style="color:#00CC99; font-size:12px; letter-spacing:2px;">CURRENT TARGET</div>
        <div class="goal-text">「{current_goal}」</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 簡易儀表板
    st.subheader("📊 戰略指揮中心")
    c1, c2, c3 = st.columns(3)
    
    c1.metric("💰 本月支出", f"${int(total_spent):,}")
    c2.metric("⚔️ 進行中任務", f"{active_count} 個")
    c3.metric("📌 待接取委託", f"{urgent_count} 個")
    
    # 提供一個按鈕讓女僕重新說話 (清除快取)
    if st.button("💬 與女僕對話 (重新生成建議)"):
        get_maid_briefing.clear()
        st.rerun()