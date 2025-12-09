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
    st.title("📖 冒險日誌 (Adventure Log)")

    # --- CSS 美化 ---
    st.markdown(
        """
    <style>
    a { text-decoration: none !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #2b2b2b;
        border: 1px solid #444;
        border-radius: 15px;
        transition: transform 0.2s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #FFD700;
        transform: translateY(-3px);
    }
    .adv-title {
        font-size: 18px; font-weight: bold; color: #FFD700;
        margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .adv-desc {
        font-size: 12px; color: #ccc; height: 40px;
        overflow: hidden; line-height: 1.4; margin-bottom: 10px;
    }
    div[data-testid="stLinkButton"] > a {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white !important; border: none; font-weight: bold;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # --- 資料庫連線 ---
    sheet_adv = get_worksheet("Adventures")
    if not sheet_adv:
        sheet_adv = get_worksheet("Sheet1")  # 相容舊版

    if not sheet_adv:
        st.error("❌ 找不到 Adventures 分頁")
        st.stop()

    # --- 1. 啟動新冒險 (新增區) ---
    with st.expander("✨ 撰寫新篇章 (Start New Adventure)", expanded=False):
        c1, c2 = st.columns([2, 1])
        a_name = c1.text_input("冒險名稱", placeholder="例如: 練習馬拉松")
        a_type = c2.selectbox(
            "冒險類型", ["♾️ 持續型 (無盡)", "⚔️ 副本型 (有終點)"]
        )

        a_desc = st.text_area("序章 (冒險簡介)", placeholder="寫下你的初衷...")
        a_date = st.date_input("啟程日", datetime.now())

        if st.button("🚀 展開冒險"):
            final_type = "Continuous" if "持續" in a_type else "Instance"
            # 欄位順序: Name, Description, Status, StartDate, NotionLink, Type
            sheet_adv.append_row(
                [a_name, a_desc, "進行中", str(a_date), "", final_type]
            )
            st.success(f"篇章「{a_name}」已建立！")
            load_sheet_data.clear()
            st.rerun()

    st.divider()

    # --- 2. 顯示邏輯 (分區顯示) ---
    try:
        df_adv = load_sheet_data("Adventures")
        if df_adv.empty:
            df_adv = load_sheet_data("Sheet1")

        if not df_adv.empty:
            # === 資料前處理 ===
            # 如果欄位還沒讀到，先建立一個假的以免報錯
            if "Type" not in df_adv.columns:
                df_adv["Type"] = "Instance"

            # 確保 Type 欄位皆為字串，並填補空值
            df_adv["Type"] = df_adv["Type"].astype(str).fillna("Instance")

            # === [核心] 強制拆分成兩個 DataFrame ===
            # 1. 持續型：包含 'Continuous' 字眼的
            df_cont = df_adv[
                df_adv["Type"].str.contains("Continuous", case=False, na=False)
            ]

            # 2. 副本型：不包含 'Continuous' 的其他所有項目
            df_inst = df_adv[
                ~df_adv["Type"].str.contains(
                    "Continuous", case=False, na=False
                )
            ]

            # --- 定義渲染函式 ---
            def render_adventure_grid(dataframe, section_title, section_icon):
                if dataframe.empty:
                    return

                st.subheader(f"{section_icon} {section_title}")
                cols = st.columns(4)

                # 這裡使用 reset_index 確保迴圈順暢，但保留原始 index 供按鈕操作使用
                for i, (idx, row) in enumerate(
                    dataframe.sort_index(ascending=False).iterrows()
                ):
                    col = cols[i % 4]
                    with col:
                        # 取得原始資料的 index (這對應 Google Sheet 的 Row)
                        original_index = idx

                        notion_link = str(row.get("NotionLink", "")).strip()
                        has_link = len(notion_link) > 5

                        with st.container(border=True):
                            # 標題區
                            st.markdown(
                                f"""
                            <div class="adv-title">{row['Name']}</div>
                            <div class="adv-desc">{row.get('Description', '')}</div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # 連結或輸入框
                            if has_link:
                                st.link_button(
                                    "🔮 進入世界",
                                    notion_link,
                                    use_container_width=True,
                                )
                            else:
                                new_key = st.text_input(
                                    "輸入 Notion 網址",
                                    key=f"k_{original_index}",
                                    label_visibility="collapsed",
                                    placeholder="貼上連結...",
                                )
                                if st.button(
                                    "✨ 啟動",
                                    key=f"b_{original_index}",
                                    use_container_width=True,
                                ):
                                    sheet_adv.update_cell(
                                        original_index + 2, 5, new_key
                                    )
                                    load_sheet_data.clear()
                                    st.rerun()

                            # 設定區
                            with st.expander("⚙️ 設定"):
                                edit_link = st.text_input(
                                    "修正連結",
                                    value=notion_link,
                                    key=f"e_{original_index}",
                                )
                                if edit_link != notion_link:
                                    if st.button(
                                        "更新連結", key=f"up_{original_index}"
                                    ):
                                        sheet_adv.update_cell(
                                            original_index + 2, 5, edit_link
                                        )
                                        load_sheet_data.clear()
                                        st.rerun()

                                current_status = row.get("Status", "進行中")
                                new_status = st.selectbox(
                                    "狀態",
                                    ["進行中", "已完成", "暫停"],
                                    index=["進行中", "已完成", "暫停"].index(
                                        current_status
                                    ),
                                    key=f"s_{original_index}",
                                )
                                if new_status != current_status:
                                    if st.button(
                                        "更新狀態", key=f"ups_{original_index}"
                                    ):
                                        sheet_adv.update_cell(
                                            original_index + 2, 3, new_status
                                        )
                                        load_sheet_data.clear()
                                        st.rerun()

                                if st.button(
                                    "🗑️ 刪除", key=f"d_{original_index}"
                                ):
                                    sheet_adv.delete_rows(original_index + 2)
                                    st.success("已刪除")
                                    load_sheet_data.clear()
                                    st.rerun()

            # --- 分開渲染兩個區塊 ---

            # 1. 先顯示持續型
            render_adventure_grid(df_cont, "持續修練 (Continuous)", "♾️")

            # 2. 分隔線 (如果兩者都有資料才顯示，美觀一點)
            if not df_cont.empty and not df_inst.empty:
                st.divider()

            # 3. 再顯示副本型
            render_adventure_grid(df_inst, "副本挑戰 (Instances)", "⚔️")

        else:
            st.info("目前還沒有冒險篇章，快去上方建立一個吧！")

    except Exception as e:
        st.error(f"讀取錯誤: {e}")
