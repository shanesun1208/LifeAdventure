import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_worksheet, ask_gemini

def show_diary_page():
    st.title("📖 冒險日誌")
    sheet = get_worksheet("Sheet1")
    
    with st.expander("✍️ 撰寫新紀錄", expanded=False):
        with st.form("log_form"):
            c1, c2 = st.columns(2)
            d_val = c1.date_input("日期", datetime.now())
            t_val = c1.selectbox("類型", ["里程碑成就", "毅力成就", "挑戰與探索", "日常切片"])
            s_val = c2.selectbox("心情", ["進行中", "已完成", "開心", "疲累", "平靜"])
            c_val = st.text_area("內容", height=80)
            if st.form_submit_button("寫入紀錄"):
                if sheet:
                    reply = ask_gemini(c_val, s_val)
                    sheet.append_row([str(d_val), t_val, c_val, s_val, reply])
                    st.success(f"已儲存！{reply}")
                    st.rerun()
                else: st.error("找不到日記分頁")
    
    st.divider()
    df = pd.DataFrame(sheet.get_all_records()) if sheet else pd.DataFrame()
    if not df.empty:
        for idx, row in df.iloc[::-1].iterrows():
            ai_html = f'<div class="ai-comment">🤖 {row.get("AI回應","")}</div>' if row.get("AI回應") else ""
            st.markdown(f"""<div class="adventure-card"><div>{row['日期']} | {row['狀態/心情']}</div>
            <div style="font-size:18px; font-weight:bold; color:white;">{row['類型']}</div>
            <div>{row['內容']}</div>{ai_html}</div>""", unsafe_allow_html=True)