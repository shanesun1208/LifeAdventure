import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 路徑修正
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_worksheet, get_weather, get_ai_greeting

def show_home_page(current_city, current_goal):
    now = datetime.utcnow() + timedelta(hours=8)
    weather_info = get_weather(current_city)
    greeting = get_ai_greeting(now.hour, weather_info)

    st.markdown(f"""
    <div class="greeting-box">
        <div style="font-size: 48px; font-weight: bold;">{now.strftime("%H:%M")}</div>
        <div style="font-size: 28px; font-weight: bold;">{greeting}</div>
        <div>{now.strftime("%Y年%m月%d日")} | {weather_info}</div>
    </div>
    <div class="goal-box"><div style="color:#00CC99;">CURRENT TARGET</div><div class="goal-text">「{current_goal}」</div></div>
    """, unsafe_allow_html=True)
    
    # 簡易儀表板
    sheet_fin = get_worksheet("Finance")
    sheet_qb = get_worksheet("QuestBoard")
    
    df_fin = pd.DataFrame(sheet_fin.get_all_records()) if sheet_fin else pd.DataFrame()
    df_qb = pd.DataFrame(sheet_qb.get_all_records()) if sheet_qb else pd.DataFrame()
    
    st.subheader("📊 戰略指揮中心")
    c1, c2, c3 = st.columns(3)
    
    current_month = now.strftime("%Y-%m")
    total_spent = 0
    if not df_fin.empty and 'Date' in df_fin.columns and 'Price' in df_fin.columns:
        df_fin['Date'] = df_fin['Date'].astype(str)
        month_data = df_fin[df_fin['Date'].str.contains(current_month)]
        month_data['Price'] = pd.to_numeric(month_data['Price'], errors='coerce').fillna(0)
        total_spent = month_data['Price'].sum()
    c1.metric("💰 本月支出", f"${int(total_spent)}")
    
    active_quests = len(df_qb[df_qb['Status'] == '進行中']) if not df_qb.empty and 'Status' in df_qb.columns else 0
    c2.metric("⚔️ 進行中任務", f"{active_quests} 個")
    
    todo_quests = len(df_qb[df_qb['Status'] == '待接取']) if not df_qb.empty and 'Status' in df_qb.columns else 0
    c3.metric("📌 待接取委託", f"{todo_quests} 個")