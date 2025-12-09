import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 路徑修正
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# [修改 1] 移除 generate_reward 的引用
from utils import get_worksheet, update_setting_value, load_sheet_data

def show_quest_board(quest_types):
    # [修改 2] 移除 Google Fonts 的 Long Cang，改用 CSS 定義系統楷體
    st.markdown("""
    <style>
    /* 定義楷體優先，若無則使用明體 */
    .kaiti-font {
        font-family: 'KaiTi', 'DFKai-SB', 'BiauKai', '楷體', '標楷體', serif;
    }
    
    /* 牛皮紙紋理 */
    .kraft-texture {
        background-image: url("https://www.transparenttextures.com/patterns/cardboard.png");
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="corkboard-title">🛡️ 任務看板 (Quest Board)</div>', unsafe_allow_html=True)
    sheet_qb = get_worksheet("QuestBoard")
    
    # --- 發布區 (動態新增類型) ---
    with st.expander("➕ 張貼新委託 (Post Quest)", expanded=False):
        q_name = st.text_input("任務名稱")
        
        # 動態類型選單
        ADD_NEW = "➕ 新增類型..."
        q_opts = quest_types + [ADD_NEW]
        sel_type = st.selectbox("任務類型 (決定紙張顏色)", q_opts)
        new_type = None
        if sel_type == ADD_NEW:
            new_type = st.text_input("輸入新類型名稱")

        q_content = st.text_area("任務內容")
        
        c3, c4 = st.columns(2)
        with c3:
            q_dead = st.date_input("期限", datetime.now() + timedelta(days=7))
            no_dead = st.checkbox("無期限")
        with c4: 
            # [修改 3] 移除 AI 獎勵生成的提示，改為固定文字或隱藏
            st.caption("📝 獎勵系統暫時關閉，專注於任務本身。")
        
        if st.button("📌 釘上佈告欄"):
            if sheet_qb:
                with st.spinner("張貼中..."):
                    deadline = "無" if no_dead else str(q_dead)
                    final_type = new_type if sel_type == ADD_NEW and new_type else sel_type
                    if final_type == ADD_NEW: final_type = "其他"

                    # [修改 4] 不再生成獎勵，寫入固定值 "無" 以維持資料庫格式
                    rew = "無"
                    
                    sheet_qb.append_row([q_name, q_content, final_type, "待接取", deadline, rew])
                    
                    if sel_type == ADD_NEW and new_type and new_type not in quest_types:
                        new_list_str = ",".join(quest_types + [new_type])
                        update_setting_value("Quest_Types", new_list_str)
                        st.toast(f"已新增類型：{new_type}")

                    st.success(f"已發布任務：{q_name}")
                    load_sheet_data.clear()
                    st.rerun()
            else: st.error("QuestBoard 讀取失敗")

    # --- 讀取並顯示 ---
    try:
        df_qb = load_sheet_data("QuestBoard")
        if not df_qb.empty:
            if "Status" in df_qb.columns and "Type" in df_qb.columns:
                todo_tasks = df_qb[df_qb['Status'] == '待接取']
                
                if not todo_tasks.empty:
                    cols = st.columns(4)
                    for i, (index, row) in enumerate(todo_tasks.iterrows()):
                        col = cols[i % 4]
                        with col:
                            # --- 視覺邏輯 ---
                            q_type = row.get('Type', '其他')
                            
                            # 配色
                            bg_color = "#E6D2B5" # 深牛皮
                            text_color = "#3E2723"
                            
                            if q_type == "工作":
                                bg_color = "#FFF9C4" # 淡黃
                                text_color = "#333333"
                            elif q_type == "禪行":
                                bg_color = "#E1BEE7" # 淡紫
                                text_color = "#4A148C"
                            elif q_type == "採購":
                                bg_color = "#C8E6C9" # 淡綠
                                text_color = "#1B5E20"
                            
                            # 旋轉
                            rot = (i % 5 - 2) * 1.5
                            
                            # CSS 變數
                            card_css = f"background-color: {bg_color}; color: {text_color}; padding: 20px; margin: 10px 0; border-radius: 2px; box-shadow: 4px 4px 10px rgba(0,0,0,0.2); position: relative; border-top: 1px solid rgba(255,255,255,0.4); min-height: 260px; transform: rotate({rot}deg); background-image: url('https://www.transparenttextures.com/patterns/cardboard.png');"
                            
                            pin_css = "position: absolute; top: -15px; left: 50%; transform: translateX(-50%); font-size: 30px; text-shadow: 2px 2px 2px rgba(0,0,0,0.3);"
                            
                            # [修改 5] 字體改為楷體 (kaiti-font)
                            title_css = f"font-family: 'KaiTi', 'DFKai-SB', '楷體', serif; font-size: 28px; font-weight: bold; border-bottom: 2px dashed {text_color}; padding-bottom: 8px; margin-bottom: 12px; text-align: center;"
                            
                            content_css = "font-family: 'KaiTi', 'DFKai-SB', '楷體', serif; font-size: 22px; line-height: 1.5; margin-bottom: 20px;"
                            
                            meta_css = "font-size: 13px; opacity: 0.8; margin-top: auto; font-family: sans-serif; line-height: 1.6;"
                            
                            stamp_css = f"position: absolute; bottom: 15px; right: 15px; width: 60px; height: 60px; border: 3px double {text_color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'KaiTi', 'DFKai-SB', '楷體', serif; font-size: 20px; font-weight: bold; transform: rotate(-15deg); opacity: 0.7; mask-image: url('https://www.transparenttextures.com/patterns/grunge-wall.png');"

                            # 組合 HTML
                            # [修改 6] 移除獎勵顯示行
                            html_code = f"""
                            <div style="{card_css}">
                                <div style="{pin_css}">📌</div>
                                <div style="{title_css}">{row['Name']}</div>
                                <div style="{content_css}">{row['Content']}</div>
                                <div style="{meta_css}">
                                    📅 期限: {row['Deadline']}<br>
                                </div>
                                <div style="{stamp_css}">
                                    {q_type}
                                </div>
                            </div>
                            """
                            
                            st.markdown(html_code, unsafe_allow_html=True)
                            
                            # 按鈕區
                            c_take, c_cancel = st.columns(2)
                            with c_take:
                                if st.button(f"🖐️ 接取", key=f"take_{index}"):
                                    sheet_qb.update_cell(index + 2, 4, "進行中")
                                    st.balloons()
                                    st.success(f"已接取：{row['Name']}")
                                    load_sheet_data.clear()
                                    st.rerun()
                            with c_cancel:
                                if st.button(f"❌ 撤下", key=f"del_{index}"):
                                    sheet_qb.delete_rows(index + 2)
                                    st.toast("委託已撕毀。")
                                    load_sheet_data.clear()
                                    st.rerun()
                else:
                    st.info("佈告欄目前空空如也。")
            else:
                st.error("QuestBoard 欄位標題錯誤 (需英文 Status, Type)")
    except Exception as e: st.error(f"Error: {e}")

def show_tracking():
    st.title("⚔️ 任務追蹤")
    sheet_qb = get_worksheet("QuestBoard")
    try:
        df_qb = load_sheet_data("QuestBoard")
        if not df_qb.empty:
            if "Status" in df_qb.columns:
                doing = df_qb[df_qb['Status'] == '進行中']
                if not doing.empty:
                    for idx, row in doing.iterrows():
                        q_type = row.get('Type', '其他')
                        with st.container():
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                badge_color = "#eee"
                                if q_type == "工作": badge_color = "#fff9c4"
                                elif q_type == "禪行": badge_color = "#e1bee7"
                                elif q_type == "採購": badge_color = "#c8e6c9"
                                
                                st.markdown(f"""
                                <div style="display:flex; align-items:center; gap:10px;">
                                    <h3 style="margin:0;">{row['Name']}</h3>
                                    <span style='background:{badge_color}; padding:4px 8px; font-size:14px; border-radius:12px; border:1px solid #999;'>{q_type}</span>
                                </div>
                                """, unsafe_allow_html=True)
                                st.write(f"**內容**: {row['Content']}")
                                # [修改 7] 追蹤區塊也移除獎勵顯示
                                st.write(f"**期限**: {row['Deadline']}")
                            with c2:
                                if st.button("✅ 完成", key=f"done_{idx}"):
                                    sheet_qb.update_cell(idx+2, 4, "已完成")
                                    st.success("完成！")
                                    load_sheet_data.clear()
                                    st.rerun()
                                if st.button("🏳️ 放棄", key=f"drop_{idx}"):
                                    sheet_qb.update_cell(idx+2, 4, "待接取")
                                    st.warning("已放棄")
                                    load_sheet_data.clear()
                                    st.rerun()
                            st.divider()
                else: st.info("沒有進行中的任務。")
    except: pass