import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_weather, load_all_finance_data

def show_home_page(current_city, current_goal):
    now = datetime.utcnow() + timedelta(hours=8)
    weather_info = get_weather(current_city)
    
    # 標題區
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color:#00CC99; font-family:'微軟正黑體';">🏠 我的小屋 (My Home)</h1>
        <p style="color:#aaa;">{now.strftime("%Y年%m月%d日 %H:%M")} | {weather_info}</p>
    </div>
    """, unsafe_allow_html=True)

    # 顯示人生目標
    st.markdown(f"""
    <div class="goal-box">
        <div style="color:#00CC99; font-size:12px; letter-spacing:2px;">CURRENT TARGET</div>
        <div class="goal-text">「{current_goal}」</div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- 準備數據 (儀表板用) ---
    all_data = load_all_finance_data()
    
    df_fin = all_data.get("Finance", pd.DataFrame())
    df_income = all_data.get("Income", pd.DataFrame())
    df_fixed = all_data.get("FixedExpenses", pd.DataFrame())
    df_budget = all_data.get("Budget", pd.DataFrame())
    df_qb = all_data.get("QuestBoard", pd.DataFrame())
    
    current_month_str = now.strftime("%Y-%m")
    
    # 簡單計算 (僅供首頁顯示用)
    total_income = 0
    if not df_income.empty and 'Date' in df_income.columns:
        df_income['Date'] = df_income['Date'].astype(str)
        inc = df_income[df_income['Date'].str.contains(current_month_str)]
        inc['Amount'] = pd.to_numeric(inc['Amount'], errors='coerce').fillna(0)
        total_income = int(inc['Amount'].sum())
        
    total_fixed = 0
    if not df_fixed.empty:
        df_fixed['Amount'] = pd.to_numeric(df_fixed['Amount'], errors='coerce').fillna(0)
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

    urgent_count = 0
    active_count = 0
    if not df_qb.empty and 'Status' in df_qb.columns:
        urgent_count = len(df_qb[df_qb['Status'] == '待接取'])
        active_count = len(df_qb[df_qb['Status'] == '進行中'])

    # 簡易儀表板
    st.subheader("📊 戰略指揮中心")
    c1, c2, c3 = st.columns(3)
    
    c1.metric("💰 本月支出", f"${int(total_spent):,}")
    c2.metric("⚔️ 進行中任務", f"{active_count} 個")
    c3.metric("📌 待接取委託", f"{urgent_count} 個")