import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 路徑修正
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import get_worksheet, load_sheet_data

def show_diary_page():
    st.title("📖 冒險篇章 (Adventure Log)")
    st.caption("記載著那些偉大的旅程，以及通往異世界的入口...")

    # --- CSS 美化 ---
    st.markdown("""
    <style>
    .adventure-title {
        font-size: 22px;
        font-weight: bold;
        color: #FFD700;
        margin-bottom: 5px;
    }
    .adventure-desc {
        color: #ddd;
        font-size: 14px;
        margin-bottom: 15px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- 1. 決定要用哪個分頁 (關鍵修正) ---
    # 先找 Adventures，找不到才找 Sheet1
    target_sheet_name = "Adventures"
    sheet_adv = get_worksheet("Adventures")
    
    if not sheet_adv:
        # 如果真的找不到 Adventures，再試試看 Sheet1
        sheet_check = get_worksheet("Sheet1")
        if sheet_check:
            target_sheet_name = "Sheet1"
            sheet_adv = sheet_check
        else:
            # 兩個都找不到，就報錯並停止
            st.error("❌ 找不到資料表！請去 Google Sheet 新增一個分頁，命名為 'Adventures'。")
            st.stop()

    # --- 2. 啟動新冒險 (新增區) ---
    with st.expander("✨ 撰寫新篇章 (Start New Adventure)", expanded=False):
        with st.form("new_adventure"):
            c1, c2 = st.columns([2, 1])
            a_name = c1.text_input("冒險名稱", placeholder="例如: 發表頂級期刊論文")
            a_status = c2.selectbox("目前狀態", ["進行中", "已完成", "暫停"])
            a_desc = st.text_area("序章 (冒險簡介/初衷)", placeholder="為什麼要開始這場冒險？")
            a_date = st.date_input("啟程日", datetime.now())
            
            st.info("💡 Notion 傳送門連結可以在建立後，於下方卡片中填入。")
            
            if st.form_submit_button("🚀 展開冒險"):
                # 欄位: Name, Description, Status, StartDate, NotionLink
                sheet_adv.append_row([a_name, a_desc, a_status, str(a_date), ""])
                st.success(f"篇章「{a_name}」已建立！")
                load_sheet_data.clear() # 清快取
                st.rerun()

    st.divider()

    # --- 3. 讀取並顯示 ---
    try:
        # 只讀取剛剛確認存在的那一個分頁
        df_adv = load_sheet_data(target_sheet_name)

        if not df_adv.empty:
            # 確保欄位存在
            if "Name" in df_adv.columns:
                
                # 倒序顯示，新的在上面
                for i, (index, row) in enumerate(df_adv.sort_index(ascending=False).iterrows()):
                    
                    notion_link = str(row.get('NotionLink', '')).strip()
                    has_link = len(notion_link) > 5 
                    
                    # 卡片容器
                    with st.container():
                        c_info, c_portal = st.columns([3, 2])
                        
                        with c_info:
                            st.markdown(f"""
                            <div class="adventure-title">🛡️ {row['Name']}</div>
                            <div class="adventure-desc">{row.get('Description', '')}</div>
                            <div style="font-size:12px; color:#aaa;">📅 啟程: {row['StartDate']} | 🚩 狀態: {row['Status']}</div>
                            """, unsafe_allow_html=True)

                        with c_portal:
                            st.write("") # Spacer
                            
                            if has_link:
                                # === 門是開的 ===
                                st.success("🌀 傳送門已開啟")
                                st.link_button("🔮 進入 Notion 冒險世界", notion_link, use_container_width=True)
                                
                                # 修改區
                                with st.expander("⚙️ 設定"):
                                    new_link_edit = st.text_input("修正連結", value=notion_link, key=f"edit_link_{index}")
                                    if st.button("更新", key=f"btn_upd_{index}"):
                                        # 更新資料庫 (Row = index + 2)
                                        sheet_adv.update_cell(index + 2, 5, new_link_edit)
                                        st.toast("連結已更新！")
                                        load_sheet_data.clear()
                                        st.rerun()
                                    
                                    if st.button("🗑️ 刪除篇章", key=f"del_adv_{index}"):
                                        sheet_adv.delete_rows(index + 2)
                                        st.success("篇章已刪除")
                                        load_sheet_data.clear()
                                        st.rerun()

                            else:
                                # === 門是關的 ===
                                st.warning("🚪 傳送門緊閉中...")
                                input_link = st.text_input("🔑 插入鑰匙 (輸入 Notion 連結)", key=f"input_{index}", placeholder="https://notion.so/...")
                                
                                if st.button("✨ 啟動傳送門", key=f"activate_{index}"):
                                    if input_link:
                                        sheet_adv.update_cell(index + 2, 5, input_link)
                                        st.balloons()
                                        st.success("能量注入！傳送門開啟中...")
                                        load_sheet_data.clear()
                                        st.rerun()
                                    else:
                                        st.error("請輸入有效的連結！")
                        
                        st.markdown("---") # 分隔線

            else:
                st.error(f"資料表欄位錯誤：請確認 {target_sheet_name} 的標題列包含 Name, Description, Status, StartDate, NotionLink")
        else:
            st.info("目前還沒有任何冒險篇章，快去寫下第一章吧！")
            
    except Exception as e:
        st.error(f"讀取錯誤: {e}")