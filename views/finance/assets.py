import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

from utils import get_worksheet, update_setting_value, load_all_finance_data

def show_fixed_tab(sheet_fixed, df_fixed, total_fixed, fixed_types):
    st.subheader("🏛️ 固定開銷管理")
    
    col_add, col_view = st.columns([1, 2])
    with col_add:
        # 移除 st.form
        with st.container():
            st.write("#### ➕ 新增項目")
            fx_item = st.text_input("項目", key="fx_item")
            
            # 動態分類
            ADD_NEW = "➕ 新增類別..."
            type_opts = fixed_types + [ADD_NEW]
            sel_type = st.selectbox("類型", type_opts, key="fx_type")
            new_type = None
            if sel_type == ADD_NEW:
                new_type = st.text_input("輸入新類型", key="fx_new_type")

            fx_amt = st.number_input("金額", min_value=0, key="fx_amt")
            fx_pay = st.text_input("付款方式", key="fx_pay")
            fx_day = st.number_input("扣款日", 1, 31, key="fx_day")
            
            if st.button("確認新增"):
                if sheet_fixed:
                    final_type = new_type if sel_type == ADD_NEW and new_type else sel_type
                    if final_type == ADD_NEW: final_type = "未分類"

                    sheet_fixed.append_row([fx_item, final_type, fx_amt, fx_pay, fx_day])
                    
                    # 更新 Setting
                    if sel_type == ADD_NEW and new_type and new_type not in fixed_types:
                        update_setting_value("Fixed_Types", ",".join(fixed_types + [new_type]))
                        st.toast(f"已新增固定開銷分類：{new_type}")

                    st.success("已新增")
                    load_all_finance_data.clear() # 強制重讀
                    if "fin_data_loaded" in st.session_state: del st.session_state["fin_data_loaded"]
                    st.rerun()
                else: st.error("找不到 FixedExpenses 分頁")

    with col_view:
        if not df_fixed.empty:
            st.write(f"📊 每月固定支出總計: **${total_fixed:,}**")
            for i, row in df_fixed.iterrows():
                with st.expander(f"{row['Item']} - ${row['Amount']:,}"):
                    st.write(f"類型: {row['Type']} | 扣款: {row['PaidDay']}號 | 方式: {row['PaidBy']}")
                    if st.button("刪除", key=f"del_fx_{i}"):
                        sheet_fixed.delete_rows(i+2)
                        st.success("已刪除")
                        load_all_finance_data.clear()
                        if "fin_data_loaded" in st.session_state: del st.session_state["fin_data_loaded"]
                        st.rerun()
        else:
            st.info("目前沒有固定開銷。")

def show_reserve_tab(sheet_reserve, df_reserve, current_balance):
    st.subheader("🏦 預備金金庫 (Reserve Fund)")
    st.markdown(f"""<div style="padding:15px; border:1px solid #FFD700; border-radius:10px; background-color:rgba(255, 215, 0, 0.1); text-align:center;"><h2 style="color:#FFD700; margin:0;">💰 金庫餘額: ${current_balance:,}</h2></div>""", unsafe_allow_html=True)
    st.write("")

    c_op, c_hist = st.columns([1, 1.5])
    with c_op:
        with st.form("reserve_op"):
            r_type = st.radio("操作", ["存入", "取出"], horizontal=True)
            r_date = st.date_input("日期", datetime.now())
            r_amount = st.number_input("金額", min_value=0, step=1000)
            r_note = st.text_input("備註")
            if st.form_submit_button("確認"):
                if sheet_reserve:
                    sheet_reserve.append_row([str(r_date), r_type, r_amount, r_note])
                    if r_type == "存入": st.balloons()
                    st.success(f"已{r_type}")
                    load_all_finance_data.clear() # 強制重讀
                    if "fin_data_loaded" in st.session_state: del st.session_state["fin_data_loaded"]
                    st.rerun()
                else: st.error("找不到 ReserveFund 分頁")
    with c_hist:
        if not df_reserve.empty:
            st.caption("📜 金庫進出紀錄")
            st.dataframe(df_reserve[::-1], use_container_width=True, hide_index=True)