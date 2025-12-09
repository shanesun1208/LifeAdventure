import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# 路徑修正
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

from utils import update_setting_value, load_all_finance_data


# --- 通用編輯器邏輯 ---
def handle_data_editor(df, sheet, key_prefix, df_session_key):
    """
    df: 已經排序或切片過的 DataFrame
    """
    if df.empty:
        st.info("目前沒有資料。")
        return

    # 1. 準備資料
    df_display = df.copy()

    # 處理週數 (如果有 Week 欄位就暫存並隱藏)
    week_data = {}
    if "Week" in df_display.columns:
        week_data = df_display["Week"].to_dict()
        df_display = df_display.drop(columns=["Week"])

    # 處理日期格式 (確保是 datetime 物件，避免編輯器報錯)
    if "Date" in df_display.columns:
        df_display["Date"] = pd.to_datetime(
            df_display["Date"], errors="coerce"
        )

    # 加入刪除勾選框
    df_display.insert(0, "刪除", False)

    # 3. 顯示編輯器
    edited_df = st.data_editor(
        df_display,
        key=f"{key_prefix}_editor",
        use_container_width=True,
        hide_index=True,
        column_config={
            "刪除": st.column_config.CheckboxColumn(
                "刪除?", width="small", default=False
            ),
            "Date": st.column_config.DateColumn(
                "日期", format="YYYY-MM-DD", step=1
            ),
            "Amount": st.column_config.NumberColumn("金額", min_value=0),
            "Price": st.column_config.NumberColumn("金額", min_value=0),
        },
    )

    # 4. 變更偵測
    if not edited_df.equals(df_display):
        col_btn, col_msg = st.columns([1, 2])
        with col_btn:
            if st.button("💾 確認修改", key=f"{key_prefix}_save"):
                try:
                    rows_to_delete = []
                    deleted_rows = edited_df[edited_df["刪除"] == True]

                    if not deleted_rows.empty:
                        # 取得原始 Index
                        for idx in deleted_rows.index:
                            rows_to_delete.append(
                                idx + 2
                            )  # GSheet Row = Index + 2

                        # 倒序刪除，避免 Row Number 跑掉
                        for row_num in sorted(rows_to_delete, reverse=True):
                            sheet.delete_rows(row_num)

                        st.toast(f"已刪除 {len(rows_to_delete)} 筆資料")

                    # 處理修改
                    for idx, row in edited_df.iterrows():
                        if row["刪除"]:
                            continue

                        # 比對原始資料
                        original_row = df_display.loc[idx]

                        cols = [c for c in edited_df.columns if c != "刪除"]
                        changes_found = False
                        row_values = []

                        for col in cols:
                            new_val = row[col]
                            old_val = original_row[col]

                            # 格式化日期比對
                            if isinstance(new_val, (datetime, pd.Timestamp)):
                                new_val = new_val.strftime("%Y-%m-%d")
                            if isinstance(old_val, (datetime, pd.Timestamp)):
                                old_val = old_val.strftime("%Y-%m-%d")

                            if str(new_val) != str(old_val):
                                changes_found = True

                            row_values.append(new_val)

                        # 把週數塞回去
                        if week_data:
                            original_week = week_data.get(idx, "")
                            row_values.insert(1, original_week)

                        if changes_found:
                            row_num = idx + 2
                            sheet.update(
                                range_name=f"A{row_num}", values=[row_values]
                            )
                            st.toast(f"已更新第 {row_num} 列資料")

                    # 清除快取並重整
                    load_all_finance_data.clear()
                    if "fin_data_loaded" in st.session_state:
                        del st.session_state["fin_data_loaded"]
                    st.success("同步完成！")
                    st.rerun()

                except Exception as e:
                    st.error(f"更新失敗: {e}")


# --- 頁面顯示函式 ---


def show_income_tab(sheet_income, df_income, income_types):
    st.subheader("💰 收入金庫")

    # [修正] 移除 st.form 以支援動態互動
    with st.expander("➕ 新增收入", expanded=False):
        # 這裡直接放置元件，不再包在 with st.form 裡面
        c1, c2 = st.columns([1, 1])
        i_date = c1.date_input("日期", datetime.now(), key="inc_date")
        i_amount = c2.number_input(
            "金額", min_value=0, step=1000, key="inc_amt"
        )

        i_item = st.text_input(
            "項目", placeholder="ex: 6月薪資", key="inc_item"
        )

        # --- 動態新增類別邏輯 ---
        ADD_NEW_INC = "➕ 新增來源..."
        inc_opts = income_types + [ADD_NEW_INC]

        # 因為移除了 form，這個 selectbox 一改變，頁面就會立刻 rerun，下方的 if 就會生效
        sel_type = st.selectbox("類別", inc_opts, key="inc_type_sel")

        new_type = None
        if sel_type == ADD_NEW_INC:
            new_type = st.text_input(
                "輸入新來源名稱",
                placeholder="ex: 股利",
                key="inc_new_type_val",
            )
        # ---------------------------

        i_note = st.text_input("備註", key="inc_note")

        # 按鈕改用一般的 st.button
        if st.button("📥 存入", key="inc_submit_btn"):
            if sheet_income:
                # 決定寫入的類別
                final_type = (
                    new_type
                    if sel_type == ADD_NEW_INC and new_type
                    else sel_type
                )
                if final_type == ADD_NEW_INC:
                    final_type = "未分類"

                row_data = [str(i_date), i_item, i_amount, final_type, i_note]
                sheet_income.append_row(row_data)

                # 更新 Session
                new_row = pd.DataFrame(
                    [row_data],
                    columns=["Date", "Item", "Amount", "Type", "Note"],
                )
                if "df_income" in st.session_state:
                    st.session_state["df_income"] = pd.concat(
                        [st.session_state["df_income"], new_row],
                        ignore_index=True,
                    )

                # 更新 Setting 設定檔 (如果是新類別)
                if (
                    sel_type == ADD_NEW_INC
                    and new_type
                    and new_type not in income_types
                ):
                    update_setting_value(
                        "Income_Types", ",".join(income_types + [new_type])
                    )
                    st.toast(f"已記憶新類別：{new_type}")

                st.success("已存入！")
                st.rerun()
            else:
                st.error("找不到 Income 分頁")

    st.markdown("### 📝 管理收入明細")

    # [排序與顯示邏輯]
    if not df_income.empty:
        # 1. 確保日期格式正確以便排序
        df_income["Date"] = pd.to_datetime(df_income["Date"], errors="coerce")
        # 2. 排序：新的在上面
        df_sorted = df_income.sort_values(by="Date", ascending=False)

        # 3. 切換顯示模式
        col_txt, col_check = st.columns([4, 1])
        with col_check:
            show_all = st.checkbox("檢視全部", key="show_all_inc")

        if show_all:
            handle_data_editor(df_sorted, sheet_income, "income", "df_income")
        else:
            st.caption("僅顯示最近 5 筆")
            handle_data_editor(
                df_sorted.head(5), sheet_income, "income", "df_income"
            )
    else:
        st.info("目前沒有收入紀錄。")


def show_expense_tab(sheet_fin, df_fin, type1_list, type2_list):
    st.subheader("📝 支出櫃台")

    # [保持不變] 支出這部分原本就有互動邏輯，如果也想即時反應，也可以考慮移除 form
    # 但為了不改動太多，這裡先維持原樣，或是您希望也一併移除 form？
    # 支出通常欄位多，用 form 包著比較不會一直閃爍，但動態新增類別會比較卡。
    # 這裡我先幫您把支出的 form 也拿掉，體驗會比較一致！

    with st.expander("💸 新增支出", expanded=True):
        c1, c2 = st.columns([1, 1])
        f_date = c1.date_input("日期", datetime.now(), key="exp_date")
        f_price = c2.number_input(
            "金額", min_value=0, step=10, key="exp_price"
        )

        f_item = st.text_input("項目", placeholder="ex: 午餐", key="exp_item")

        ADD_NEW = "➕ 新增類別..."
        t1_opts = type1_list + [ADD_NEW]
        t2_opts = type2_list + [ADD_NEW]

        c3, c4 = st.columns(2)
        sel_t1 = c3.selectbox("主分類", t1_opts, key="exp_t1_sel")
        new_t1 = (
            c3.text_input("新主分類", key="exp_new_t1")
            if sel_t1 == ADD_NEW
            else None
        )

        sel_t2 = c4.selectbox("子分類", t2_opts, key="exp_t2_sel")
        new_t2 = (
            c4.text_input("新子分類", key="exp_new_t2")
            if sel_t2 == ADD_NEW
            else None
        )

        if st.button("💸 記帳", key="exp_submit"):
            if sheet_fin:
                final_t1 = new_t1 if sel_t1 == ADD_NEW and new_t1 else sel_t1
                final_t2 = new_t2 if sel_t2 == ADD_NEW and new_t2 else sel_t2
                if final_t1 == ADD_NEW:
                    final_t1 = "未分類"
                if final_t2 == ADD_NEW:
                    final_t2 = "未分類"

                wk = f_date.isocalendar()[1]
                row_data = [
                    str(f_date),
                    wk,
                    f_item,
                    f_price,
                    final_t1,
                    final_t2,
                ]
                sheet_fin.append_row(row_data)

                new_row = pd.DataFrame(
                    [row_data],
                    columns=[
                        "Date",
                        "Week",
                        "Item",
                        "Price",
                        "Type1",
                        "Type2",
                    ],
                )
                if "df_fin" in st.session_state:
                    st.session_state["df_fin"] = pd.concat(
                        [st.session_state["df_fin"], new_row],
                        ignore_index=True,
                    )

                # 更新設定檔
                if sel_t1 == ADD_NEW and new_t1 and new_t1 not in type1_list:
                    update_setting_value(
                        "Type1_Options", ",".join(type1_list + [new_t1])
                    )
                if sel_t2 == ADD_NEW and new_t2 and new_t2 not in type2_list:
                    update_setting_value(
                        "Type2_Options", ",".join(type2_list + [new_t2])
                    )

                st.success("已記錄！")
                load_all_finance_data.clear()
                if "fin_data_loaded" in st.session_state:
                    del st.session_state["fin_data_loaded"]
                st.rerun()
            else:
                st.error("找不到 Finance 分頁")

    st.markdown("### 📝 管理支出明細")

    # [排序與顯示邏輯 - 支出版]
    if not df_fin.empty:
        # 1. 轉日期格式
        df_fin["Date"] = pd.to_datetime(df_fin["Date"], errors="coerce")
        # 2. 排序
        df_sorted = df_fin.sort_values(by="Date", ascending=False)

        # 3. 顯示控制
        col_txt, col_check = st.columns([4, 1])
        with col_check:
            # 使用 checkbox 讓切換更直覺
            show_all_exp = st.checkbox("檢視全部", key="show_all_exp")

        if show_all_exp:
            handle_data_editor(df_sorted, sheet_fin, "expense", "df_fin")
        else:
            st.caption("僅顯示最近 5 筆")
            # 只傳前 5 筆進去
            handle_data_editor(
                df_sorted.head(5), sheet_fin, "expense", "df_fin"
            )
    else:
        st.info("目前沒有支出紀錄。")
