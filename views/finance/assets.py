import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

from utils import get_worksheet, update_setting_value, load_all_finance_data

def show_fixed_tab(sheet_fixed, df_fixed, total_fixed, fixed_types, pay_methods):
    st.subheader("🏛️ 固定開銷管理")
    
    # --- 1. 管理付款方式 (刪除功能) ---
    with st.expander("⚙️ 管理付款方式 (刪除舊卡片)"):
        del_pay = st.selectbox("選擇要刪除的付款方式", ["請選擇..."] + pay_methods)
        if del_pay != "請選擇..." and st.button(f"刪除 {del_pay}"):
            new_list = [p for p in pay_methods if p != del_pay]
            update_setting_value("Payment_Methods", ",".join(new_list))
            st.success(f"已刪除付款方式：{del_pay}")
            # 強制重新整理以更新下方選單
            load_all_finance_data.clear()
            if "fin_data_loaded" in st.session_state: del st.session_state["fin_data_loaded"]
            st.rerun()

    st.divider()

    col_add, col_view = st.columns([1, 2])
    
    # --- 2. 新增固定開銷 ---
    with col_add:
        with st.container():
            st.write("#### ➕ 新增項目")
            fx_item = st.text_input("項目名稱", placeholder="ex: Netflix")
            
            # 動態類型
            ADD_NEW_TYPE = "➕ 新增類型..."
            type_opts = fixed_types + [ADD_NEW_TYPE]
            sel_type = st.selectbox("類型", type_opts)
            new_type = None
            if sel_type == ADD_NEW_TYPE:
                new_type = st.text_input("輸入新類型")

            fx_amt = st.number_input("金額 (該週期的總額)", min_value=0)
            
            # 動態付款方式
            ADD_NEW_PAY = "➕ 新增方式..."
            pay_opts = pay_methods + [ADD_NEW_PAY]
            sel_pay = st.selectbox("付款方式", pay_opts)
            new_pay = None
            if sel_pay == ADD_NEW_PAY:
                new_pay = st.text_input("輸入新付款方式 (ex: 國泰Cube)")

            # 週期設定
            fx_cycle = st.selectbox("扣款週期", ["每月", "每半年", "每年"])
            
            # 根據週期顯示不同輸入框
            fx_detail = ""
            no_date = st.checkbox("無特定扣款日")
            
            if not no_date:
                if fx_cycle == "每月":
                    day = st.number_input("每月幾號扣款", 1, 31, 5)
                    fx_detail = f"{day}號"
                elif fx_cycle == "每半年":
                    start_month = st.selectbox("起始月份", range(1, 7))
                    day = st.number_input("幾號扣款", 1, 31, 5)
                    fx_detail = f"{start_month}月起, {day}號"
                elif fx_cycle == "每年":
                    date = st.date_input("起算日", datetime.now())
                    fx_detail = date.strftime("%m-%d")
            else:
                fx_detail = "無"

            if st.button("確認新增"):
                if sheet_fixed:
                    # 處理新類型
                    final_type = new_type if sel_type == ADD_NEW_TYPE and new_type else sel_type
                    if final_type == ADD_NEW_TYPE: final_type = "未分類"
                    
                    # 處理新付款方式
                    final_pay = new_pay if sel_pay == ADD_NEW_PAY and new_pay else sel_pay
                    if final_pay == ADD_NEW_PAY: final_pay = "未指定"

                    # 寫入 (Item, Type, Amount, PaidBy, Cycle, CycleDetail)
                    sheet_fixed.append_row([fx_item, final_type, fx_amt, final_pay, fx_cycle, fx_detail])
                    
                    # 更新 Setting
                    updated = False
                    if sel_type == ADD_NEW_TYPE and new_type and new_type not in fixed_types:
                        update_setting_value("Fixed_Types", ",".join(fixed_types + [new_type]))
                        updated = True
                    
                    if sel_pay == ADD_NEW_PAY and new_pay and new_pay not in pay_methods:
                        update_setting_value("Payment_Methods", ",".join(pay_methods + [new_pay]))
                        updated = True
                    
                    if updated: st.toast("已更新分類設定！")

                    st.success("已新增")
                    load_all_finance_data.clear()
                    if "fin_data_loaded" in st.session_state: del st.session_state["fin_data_loaded"]
                    st.rerun()
                else: st.error("找不到 FixedExpenses 分頁")

    # --- 3. 檢視列表 ---
    with col_view:
        if not df_fixed.empty:
            # 顯示攤提後的月平均總額
            st.write(f"📊 攤提後月固定支出: **${total_fixed:,}**")
            
            for i, row in df_fixed.iterrows():
                # 顯示資訊字串
                cycle_str = row.get('Cycle', '每月')
                detail_str = row.get('CycleDetail', '')
                pay_str = row.get('PaidBy', '')
                
                with st.expander(f"{row['Item']} - ${row['Amount']:,} ({cycle_str})"):
                    st.write(f"**類型**: {row['Type']}")
                    st.write(f"**付款**: {pay_str}")
                    st.write(f"**週期**: {cycle_str} / **細節**: {detail_str}")
                    
                    if st.button("🗑️ 刪除", key=f"del_fx_{i}"):
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
                    load_all_finance_data.clear()
                    if "fin_data_loaded" in st.session_state: del st.session_state["fin_data_loaded"]
                    st.rerun()
                else: st.error("找不到 ReserveFund 分頁")
    with c_hist:
        if not df_reserve.empty:
            st.caption("📜 金庫進出紀錄")
            st.dataframe(df_reserve[::-1], use_container_width=True, hide_index=True)