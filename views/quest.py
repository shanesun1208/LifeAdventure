import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_worksheet, generate_reward

def show_quest_board():
    st.markdown('<div class="corkboard-title">🛡️ 任務看板 (Quest Board)</div>', unsafe_allow_html=True)
    sheet_qb = get_worksheet("QuestBoard")
    
    with st.expander("➕ 張貼新委託", expanded=False):
        with st.form("post_quest"):
            c1, c2 = st.columns([3, 1])
            q_name = c1.text_input("任務名稱")
            q_prio = c2.selectbox("等級", ["S", "A", "B", "C"])
            q_content = st.text_area("內容")
            c3, c4 = st.columns(2)
            with c3:
                q_dead = st.date_input("期限", datetime.now()+timedelta(days=7))
                no_dead = st.checkbox("無期限")
            with c4: st.info("🎁 獎勵由 AI 生成...")
            
            if st.form_submit_button("📌 釘上佈告欄"):
                if sheet_qb:
                    with st.spinner("AI 評估中..."):
                        deadline = "無" if no_dead else str(q_dead)
                        rew = generate_reward(q_name, q_content, q_prio)
                        sheet_qb.append_row([q_name, q_content, q_prio, "待接取", deadline, rew])
                        st.success(f"已發布！獎勵：{rew}")
                        st.rerun()
                else: st.error("QuestBoard 讀取失敗")

    try:
        raw = sheet_qb.get_all_records() if sheet_qb else []
        if raw:
            df_qb = pd.DataFrame(raw)
            if "Status" in df_qb.columns:
                todo = df_qb[df_qb['Status'] == '待接取']
                if not todo.empty:
                    cols = st.columns(3)
                    for i, (idx, row) in enumerate(todo.iterrows()):
                        with cols[i%3]:
                            st.markdown(f"""<div class="quest-paper"><div class="pin">📌</div>
                            <div class="paper-title">{row['Name']}</div><div class="paper-content">{row['Content']}</div>
                            <div class="paper-meta">📅 {row['Deadline']} | 💰 {row['Reward']}</div>
                            <div class="priority-stamp p-{row['Priority']}">{row['Priority']}級</div></div>""", unsafe_allow_html=True)
                            if st.button(f"🖐️ 撕下接取", key=f"take_{idx}"):
                                sheet_qb.update_cell(idx+2, 4, "進行中")
                                st.balloons()
                                st.rerun()
                else: st.info("目前沒有委託。")
    except Exception as e: st.error(f"Error: {e}")

def show_tracking():
    st.title("⚔️ 任務追蹤")
    sheet_qb = get_worksheet("QuestBoard")
    try:
        raw = sheet_qb.get_all_records() if sheet_qb else []
        if raw:
            df_qb = pd.DataFrame(raw)
            if "Status" in df_qb.columns:
                doing = df_qb[df_qb['Status'] == '進行中']
                if not doing.empty:
                    for idx, row in doing.iterrows():
                        with st.container():
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                st.markdown(f"### {row['Name']} (Rank {row['Priority']})")
                                st.write(f"內容: {row['Content']}")
                                st.write(f"獎勵: {row['Reward']} | 期限: {row['Deadline']}")
                            with c2:
                                if st.button("✅ 完成", key=f"done_{idx}"):
                                    sheet_qb.update_cell(idx+2, 4, "已完成")
                                    st.success("完成！")
                                    st.rerun()
                                if st.button("🏳️ 放棄", key=f"drop_{idx}"):
                                    sheet_qb.update_cell(idx+2, 4, "待接取")
                                    st.warning("已放棄")
                                    st.rerun()
                            st.divider()
                else: st.info("沒有進行中的任務。")
    except: pass