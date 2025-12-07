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
    
    # --- CSS 美化: 方塊傳送門風格 ---
    st.markdown("""
    <style>
    /* 1. 已解鎖的傳送門 (魔法方塊) */
    .portal-card {
        display: block;
        width: 100%;
        height: 220px; /* 固定高度，讓它像正方形 */
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); /* 深邃星空藍 */
        border: 2px solid #FFD700; /* 金框 */
        border-radius: 15px;
        padding: 20px;
        text-decoration: none; /* 去除超連結底線 */
        transition: transform 0.3s, box-shadow 0.3s;
        position: relative;
        overflow: hidden;
        color: white !important;
    }
    .portal-card:hover {
        transform: translateY(-5px); /* 浮起效果 */
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.6); /* 金色發光 */
        border-color: #fff;
    }
    .portal-title {
        font-size: 20px;
        font-weight: bold;
        color: #FFD700;
        margin-bottom: 10px;
        border-bottom: 1px dashed rgba(255,255,255,0.3);
        padding-bottom: 5px;
    }
    .portal-desc {
        font-size: 13px;
        color: #ddd;
        line-height: 1.4;
        height: 80px; /* 限制高度 */
        overflow: hidden;
    }
    .portal-icon {
        position: absolute;
        bottom: 10px;
        right: 15px;
        font-size: 40px;
        opacity: 0.2;
    }

    /* 2. 未解鎖的石板 (封印方塊) */
    .locked-card {
        height: 220px;
        background-color: #2b2b2b; /* 深灰石頭 */
        border: 2px dashed #666;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .locked-title {
        color: #aaa;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    /* 調整 Streamlit 內部 spacing */
    div[data-testid="column"] {
        padding: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- 資料庫連線 ---
    target_sheet_name = "Adventures"
    sheet_adv = get_worksheet("Adventures")
    
    if not sheet_adv:
        # 相容舊版
        sheet_check = get_worksheet("Sheet1")
        if sheet_check:
            target_sheet_name = "Sheet1"
            sheet_adv = sheet_check
        else:
            st.error("❌ 找不到 'Adventures' 分頁，請先去 Google Sheet 建立。")
            st.stop()

    # --- 1. 啟動新冒險 (置頂區塊) ---
    with st.expander("✨ 撰寫新篇章 (Start New Adventure)", expanded=False):
        with st.form("new_adventure"):
            c1, c2 = st.columns([2, 1])
            a_name = c1.text_input("冒險名稱", placeholder="例如: 發表頂級期刊論文")
            a_status = c2.selectbox("目前狀態", ["進行中", "已完成", "暫停"])
            a_desc = st.text_area("序章 (冒險簡介/初衷)", placeholder="簡短描述這場冒險的目標...")
            a_date = st.date_input("啟程日", datetime.now())
            
            st.caption("💡 建立後，下方會出現一個「封印方塊」，輸入 Notion 連結即可解鎖。")
            
            if st.form_submit_button("🚀 展開冒險"):
                if sheet_adv:
                    # 欄位: Name, Description, Status, StartDate, NotionLink
                    sheet_adv.append_row([a_name, a_desc, a_status, str(a_date), ""])
                    st.success(f"篇章「{a_name}」已建立！")
                    load_sheet_data.clear()
                    st.rerun()

    st.divider()

    # --- 2. 冒險方塊顯示區 ---
    try:
        df_adv = load_sheet_data(target_sheet_name)

        if not df_adv.empty and "Name" in df_adv.columns:
            
            # 建立 3 欄網格
            cols = st.columns(3)
            
            # 倒序顯示 (最新的在最前面)
            for i, (index, row) in enumerate(df_adv.sort_index(ascending=False).iterrows()):
                col = cols[i % 3] # 循環放入 column 0, 1, 2
                
                notion_link = str(row.get('NotionLink', '')).strip()
                has_link = len(notion_link) > 5 
                
                with col:
                    if has_link:
                        # === 狀態 A: 傳送門已開啟 (整張卡片可點) ===
                        # 使用 HTML <a> 標籤包覆 div，達成全卡片點擊
                        card_html = f"""
                        <a href="{notion_link}" target="_blank" class="portal-card">
                            <div class="portal-title">🛡️ {row['Name']}</div>
                            <div class="portal-desc">{row.get('Description', '無描述...')}</div>
                            <div style="font-size:12px; margin-top:20px; opacity:0.7;">
                                📅 {row['StartDate']}<br>
                                🚩 {row['Status']}
                            </div>
                            <div class="portal-icon">🌀</div>
                        </a>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # 維護功能 (放在卡片下方)
                        with st.expander("⚙️", expanded=False):
                            new_link = st.text_input("修正連結", value=notion_link, key=f"lk_{index}")
                            if st.button("更新", key=f"up_{index}"):
                                sheet_adv.update_cell(index + 2, 5, new_link)
                                st.success("已更新")
                                load_sheet_data.clear()
                                st.rerun()
                            if st.button("刪除", key=f"del_{index}"):
                                sheet_adv.delete_rows(index + 2)
                                st.success("已刪除")
                                load_sheet_data.clear()
                                st.rerun()

                    else:
                        # === 狀態 B: 封印石板 (需要輸入鑰匙) ===
                        # 使用 Streamlit 容器模擬卡片外觀
                        with st.container(border=True):
                            st.markdown(f"**🔒 {row['Name']}**")
                            st.caption(f"{row.get('Description', '')[:30]}...")
                            
                            key_input = st.text_input("插入鑰匙 (Notion URL)", key=f"in_{index}", label_visibility="collapsed", placeholder="https://notion.so/...")
                            
                            if st.button("✨ 解鎖", key=f"btn_{index}", use_container_width=True):
                                if key_input:
                                    sheet_adv.update_cell(index + 2, 5, key_input)
                                    st.balloons()
                                    load_sheet_data.clear()
                                    st.rerun()
                                else:
                                    st.error("請輸入網址")
                        
                        # 為了讓高度對齊，加一點空白
                        st.write("") 

        else:
            st.info("目前還沒有冒險篇章，快去上方建立一個吧！")
            
    except Exception as e:
        st.error(f"讀取錯誤: {e}")