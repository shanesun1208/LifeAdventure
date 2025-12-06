import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

from utils import get_worksheet

def show_fixed_tab(sheet_fixed, df_fixed, total_fixed):
    st.subheader("🏛️ 固定開銷管理")
    col_add, col_view = st.columns([1, 2])
    with col_add:
        with st.form("add_fix"):
            fx_item = st.text_input("項目")
            fx_type = st.selectbox("類型", ["訂閱", "房租", "保險", "其他"])
            fx_amt = st.number_input("金額", min_value=0)
            fx_pay = st.text_input("付款方式")
            fx_day = st.number_input("扣款日", 1, 31)
            if st.form_submit_button("➕ 新增"):
                if sheet_fixed:
                    sheet_fixed.append_row([fx_item, fx_type, fx_amt, fx_pay, fx_day])
                    st.success("已新增")
                    st.cache_data.clear()
                    st.rerun()
    with col_view:
        if not df_fixed.empty:
            st.write(f"總計: **${total_fixed:,}**")
            for i, row in df_fixed.iterrows():
                with st.expander(f"{row['Item']} - ${row['Amount']:,}"):
                    st.write(f"扣款: {row['PaidDay']}號 | 方式: {row['PaidBy']}")
                    if st.button("刪除", key=f"del_fx_{i}"):
                        sheet_fixed.delete_rows(i+2)
                        st.cache_data.clear()
                        st.rerun()

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
                    st.cache_data.clear()
                    st.rerun()
    with c_hist:
        if not df_reserve.empty:
            st.dataframe(df_reserve[::-1], use_container_width=True, hide_index=True)