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

# --- 通用編輯器邏輯 (核心優化) ---
def handle_data_editor(df, sheet, key_prefix, df_session_key):
    if df.empty:
        st.info("目前沒有資料。")
        return

    # 1. 準備資料
    df_display = df.tail(20).copy()
    
    week_data = {}
    if 'Week' in df_display.columns:
        week_data = df_display['Week'].to_dict()
        df_display = df_display.drop(columns=['Week'])

    if 'Date' in df_display.columns:
        df_display['Date'] = pd.to_datetime(df_display['Date'], errors='coerce')

    df_display.insert(0, "刪除", False)

    # 3. 顯示編輯器
    edited_df = st.data_editor(
        df_display,
        key=f"{key_prefix}_editor",
        use_container_width=True,
        hide_index=True,
        column_config={
            "刪除": st.column_config.CheckboxColumn("刪除?", width="small", default=False),
            "Date": st.column_config.DateColumn("日期", format="YYYY-MM-DD", step=1),
            "Amount": st.column_config.NumberColumn("金額", min_value=0),
            "Price": st.column_config.NumberColumn("金額", min_value=0),
        }
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
                        for idx in deleted_rows.index:
                            rows_to_delete.append(idx + 2)
                        for row_num in sorted(rows_to_delete, reverse=True):
                            sheet.delete_rows(row_num)
                        st.toast(f"已刪除 {len(rows_to_delete)} 筆資料")

                    for idx, row in edited_df.iterrows():
                        if row["刪除"]: continue 
                        original_row = df_display.loc[idx]
                        cols = [c for c in edited_df.columns if c != "刪除"]
                        changes_found = False
                        row_values = []
                        for col in cols:
                            new_val = row[col]
                            old_val = original_row[col]
                            if isinstance(new_val, (datetime, pd.Timestamp)):
                                new_val = new_val.strftime("%Y-%m-%d")
                            if isinstance(old_val, (datetime, pd.Timestamp)):
                                old_val = old_val.strftime("%Y-%m-%d")
                            if str(new_val) != str(old_val):
                                changes_found = True
                            row_values.append(new_val)
                        
                        if week_data:
                            original_week = week_data.get(idx, "")
                            row_values.insert(1, original_week)

                        if changes_found:
                            row_num = idx + 2
                            sheet.update(range_name=f"A{row_num}", values=[row_values])
                            st.toast(f"已更新第 {row_num} 列資料")

                    load_all_finance_data.clear() 
                    if "fin_data_loaded" in st.session_state:
                        del st.session_state["fin_data_loaded"]
                    st.success("同步完成！")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"更新失敗: {e}")

# --- 頁面顯示函式 ---

def show_income_tab(sheet_income, df_income):
    st.subheader("💰 收入金庫")
    
    with st.expander("➕ 新增收入", expanded=False):
        with st.form("add_income"):
            i_date = st.date_input("日期", datetime.now())
            i_item = st.text_input("項目", placeholder="ex: 薪資")
            i_amount = st.number_input("金額", min_value=0, step=1000)
            i_type = st.selectbox("類別", ["薪資", "獎金", "投資", "其他"])
            i_note = st.text_input("備註")
            if st.form_submit_button("📥 存入"):
                if sheet_income:
                    row_data = [str(i_date), i_item, i_amount, i_type, i_note]
                    sheet_income.append_row(row_data)
                    new_row = pd.DataFrame([row_data], columns=['Date', 'Item', 'Amount', 'Type', 'Note'])
                    if 'df_income' in st.session_state:
                        st.session_state['df_income'] = pd.concat([st.session_state['df_income'], new_row], ignore_index=True)
                    st.success("已存入！")
                    st.rerun()
                else: st.error("找不到 Income 分頁")
    
    st.markdown("### 📝 管理最近收入")
    handle_data_editor(df_income, sheet_income, "income", "df_income")


def show_expense_tab(sheet_fin, df_fin, type1_list, type2_list):
    st.subheader("📝 支出櫃台")
    
    with st.expander("💸 新增支出", expanded=True): 
        
        f_date = st.date_input("日期", datetime.now())
        f_item = st.text_input("項目", placeholder="ex: 午餐")
        f_price = st.number_input("金額", min_value=0, step=10)
        
        ADD_NEW = "➕ 新增類別..."
        t1_opts = type1_list + [ADD_NEW]
        t2_opts = type2_list + [ADD_NEW]
        
        c1, c2 = st.columns(2)
        sel_t1 = c1.selectbox("主分類", t1_opts)
        new_t1 = None
        if sel_t1 == ADD_NEW:
            new_t1 = c1.text_input("輸入新主分類名稱", placeholder="ex: 娛樂")

        sel_t2 = c2.selectbox("子分類", t2_opts)
        new_t2 = None
        if sel_t2 == ADD_NEW:
            new_t2 = c2.text_input("輸入新子分類名稱", placeholder="ex: 電影")
        
        if st.button("💸 記帳"):
            if sheet_fin:
                final_t1 = sel_t1
                if sel_t1 == ADD_NEW:
                    if new_t1: final_t1 = new_t1
                    else: 
                        st.error("請輸入新主分類名稱！")
                        st.stop()

                final_t2 = sel_t2
                if sel_t2 == ADD_NEW:
                    if new_t2: final_t2 = new_t2
                    else:
                        st.error("請輸入新子分類名稱！")
                        st.stop()

                wk = f_date.isocalendar()[1]
                row_data = [str(f_date), wk, f_item, f_price, final_t1, final_t2]
                
                sheet_fin.append_row(row_data)
                
                new_row = pd.DataFrame([row_data], columns=['Date', 'Week', 'Item', 'Price', 'Type1', 'Type2'])
                if 'df_fin' in st.session_state:
                    st.session_state['df_fin'] = pd.concat([st.session_state['df_fin'], new_row], ignore_index=True)

                settings_updated = False
                if sel_t1 == ADD_NEW and new_t1 and new_t1 not in type1_list:
                    update_setting_value("Type1_Options", ",".join(type1_list + [new_t1]))
                    settings_updated = True
                    
                if sel_t2 == ADD_NEW and new_t2 and new_t2 not in type2_list:
                    update_setting_value("Type2_Options", ",".join(type2_list + [new_t2]))
                    settings_updated = True
                
                if settings_updated:
                    st.toast("已自動將新類別加入設定！")
                    
                st.success("已記錄！")
                
                load_all_finance_data.clear()
                if "fin_data_loaded" in st.session_state:
                    del st.session_state["fin_data_loaded"]
                    
                st.rerun()
            else: st.error("找不到 Finance 分頁")

    st.markdown("### 📝 管理最近支出")
    handle_data_editor(df_fin, sheet_fin, "expense", "df_fin")