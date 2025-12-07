import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# 路徑修正
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_worksheet, generate_reward, update_setting_value, load_sheet_data

def show_quest_board(quest_types):
    # 引入手寫字體 & 牛皮紙質感 CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Long+Cang&display=swap');
    
    /* 牛皮紙紋理效果 */
    .kraft-texture {
        background-color: #f0e6d2;
        background-image: url("https://www.transparenttextures.com/patterns/cardboard.png");
        /* 如果網路圖片跑不出來，會顯示底色 */
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
        with c4: st.info("🎁 獎勵由 AI 生成...")
        
        if st.button("📌 釘上佈告欄"):
            if sheet_qb:
                with st.spinner("AI 評估中..."):
                    deadline = "無" if no_dead else str(q_dead)
                    
                    final_type = new_type if sel_type == ADD_NEW and new_type else sel_type
                    if final_type == ADD_NEW: final_type = "其他"

                    rew = generate_reward(q_name, q_content, final_type)
                    
                    # 寫入資料
                    sheet_qb.append_row([q_name, q_content, final_type, "待接取", deadline, rew])
                    
                    # 更新 Setting
                    if sel_type == ADD_NEW and new_type and new_type not in quest_types:
                        new_list_str = ",".join(quest_types + [new_type])
                        update_setting_value("Quest_Types", new_list_str)
                        st.toast(f"已新增類型：{new_type}")

                    st.success(f"已發布！獎勵：{rew}")
                    
                    # [關鍵修正] 清除快取，讓下次讀取能抓到新任務
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
                    cols = st.columns(3)
                    for i, (index, row) in enumerate(todo_tasks.iterrows()):
                        col = cols[i % 3]
                        with col:
                            # --- 視覺邏輯 ---
                            q_type = row.get('Type', '其他')
                            
                            # 預設：深色牛皮紙
                            bg_color = "#dcbfa6" 
                            text_color = "#3E2723"
                            
                            if q_type == "工作":
                                bg_color = "#fff59d" # 亮黃色便利貼
                                text_color = "#212121"
                            elif q_type == "禪行":
                                bg_color = "#e1bee7" # 淡紫色
                                text_color = "#4a148c"
                            elif q_type == "採購":
                                bg_color = "#b2dfdb" # 淡綠色
                                text_color = "#004d40"
                            
                            # CSS 樣式組合
                            font_style = "font-family: 'Long Cang', cursive;"
                            
                            # [修正] 這裡使用 f-string 時要小心，不要斷行斷在奇怪的地方
                            card_html = f"""
                            <div style="
                                background-color: {bg_color};
                                color: {text_color};
                                padding: 20px;
                                margin: 10px 0;
                                border-radius: 2px;
                                box-shadow: 5px 5px 10px rgba(0,0,0,0.3);
                                position: relative;
                                border-top: 1px solid rgba(255,255,255,0.4);
                                border-bottom: 1px solid rgba(0,0,0,0.1);
                                min-height: 250px;
                                transform: rotate({(i%5 - 2)}deg);
                                background-image: url('https://www.transparenttextures.com/patterns/cardboard.png');
                            ">
                                <div style="
                                    position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
                                    font-size: 28px; text-shadow: 2px 2px 2px rgba(0,0,0,0.3);
                                ">📌</div>
                                
                                <div style="{font_style} font-size: 26px; font-weight: bold; border-bottom: 2px dashed {text_color}; padding-bottom: 5px; margin-bottom: 10px;">
                                    {row['Name']}
                                </div>
                                
                                <div style="{font_style} font-size: 22px; line-height: 1.4; margin-bottom: 20px;">
                                    {row['Content']}
                                </div>
                                
                                <div style="font-size: 14px; opacity: 0.8; margin-top: auto; font-family: sans-serif;">
                                    📅 {row['Deadline']}<br>
                                    💰 {row['Reward']}
                                </div>
                                
                                <div style="
                                    position: absolute; bottom: 10px; right: 10px;
                                    font-size: 14px; font-weight: bold;
                                    border: 2px solid {text_color};
                                    padding: 2px 8px; border-radius: 5px;
                                    transform: rotate(-10deg); opacity: 0.6;
                                    font-family: sans-serif;
                                ">
                                    {q_type}
                                </div>
                            </div>
                            """
                            st.markdown(card_html, unsafe_allow_html=True)
                            
                            # 按鈕區
                            c_take, c_cancel = st.columns(2)
                            with c_take:
                                if st.button(f"🖐️ 接取", key=f"take_{index}"):
                                    sheet_qb.update_cell(index + 2, 4, "進行中")
                                    st.balloons()
                                    st.success(f"已接取：{row['Name']}！")
                                    load_sheet_data.clear() # [關鍵] 清除快取
                                    st.rerun()
                            
                            with c_cancel:
                                if st.button(f"❌ 撤下", key=f"del_{index}"):
                                    sheet_qb.delete_rows(index + 2)
                                    st.toast("委託已撕毀。")
                                    load_sheet_data.clear() # [關鍵] 清除快取
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
                        with st.container():
                            c1, c2 = st.columns([3, 1])
                            with c1:
                                q_type = row.get('Type', '其他')
                                st.markdown(f"### {row['Name']} <span style='background:#ddd;padding:2px 5px;font-size:14px;border-radius:4px;'>{q_type}</span>", unsafe_allow_html=True)
                                st.write(f"**內容**: {row['Content']}")
                                st.write(f"**獎勵**: {row['Reward']} | **期限**: {row['Deadline']}")
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