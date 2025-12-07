import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

from utils import get_worksheet, update_setting_value, load_all_finance_data

def show_fixed_tab(sheet_fixed, df_fixed, total_fixed, fixed_types, pay_methods, sheet_fin, df_fin):
    st.subheader("🏛️ 固定開銷管理")
    
    # --- [New] 一鍵入帳功能 ---
    with st.expander("⚡ 本月固定開銷結算 (一鍵入帳)", expanded=True):
        if not df_fixed.empty:
            # 1. 找出本月已經記帳的項目 (比對 Item 名稱)
            current_month_str = datetime.now().strftime("%Y-%m")
            recorded_items = []
            if not df_fin.empty and 'Date' in df_fin.columns:
                df_fin['Date'] = df_fin['Date'].astype(str)
                fin_month = df_fin[df_fin['Date'].str.contains(current_month_str)]
                if 'Item' in fin_month.columns:
                    recorded_items = fin_month['Item'].tolist()
            
            # 2. 篩選出還沒記的
            unpaid_items = []
            for _, row in df_fixed.iterrows():
                # 簡單比對：項目名稱是否存在於本月記帳中
                if row['Item'] not in recorded_items:
                    unpaid_items.append(row)
            
            if unpaid_items:
                st.warning(f"本月尚有 {len(unpaid_items)} 筆固定開銷未入帳")
                
                # 顯示列表
                for item in unpaid_items:
                    st.write(f"- **{item['Item']}**: ${item['Amount']} ({item['PaidBy']})")
                
                if st.button("⚡ 全部寫入支出記帳"):
                    if sheet_fin:
                        new_rows_df = []
                        today_str = datetime.now().strftime("%Y-%m-%d")
                        wk = datetime.now().isocalendar()[1]
                        
                        for item in unpaid_items:
                            # 欄位: Date, Week, Item, Price, Type1, Type2
                            # Type1 強制設為 "固定開銷"，方便總覽計算
                            # Type2 設為原本的 Type (如訂閱/房租)
                            row_data = [today_str, wk, item['Item'], item['Amount'], "固定開銷", item['Type']]
                            sheet_fin.append_row(row_data)
                            
                            # 更新本地 session state
                            new_row = pd.DataFrame([row_data], columns=['Date', 'Week', 'Item', 'Price', 'Type1', 'Type2'])
                            new_rows_df.append(new_row)
                        
                        # 更新 Session
                        if new_rows_df and 'df_fin' in st.session_state:
                            combined_new = pd.concat(new_rows_df, ignore_index=True)
                            st.session_state['df_fin'] = pd.concat([st.session_state['df_fin'], combined_new], ignore_index=True)
                        
                        st.success(f"已成功寫入 {len(unpaid_items)} 筆支出！")
                        load_all_finance_data.clear() # 清除快取
                        st.rerun()
                    else: st.error("找不到 Finance 分頁")
            else:
                st.success("✅ 本月所有固定開銷皆已入帳！")
        else:
            st.info("尚未設定固定開銷。")

    st.divider()

    # --- 下方：管理介面 (新增/刪除) ---
    col_add, col_view = st.columns([1, 2])
    
    with col_add:
        with st.container():
            st.write("#### ➕ 新增項目")
            fx_item = st.text_input("項目名稱", placeholder="ex: Netflix", key="fx_item")
            
            ADD_NEW_TYPE = "➕ 新增類型..."
            type_opts = fixed_types + [ADD_NEW_TYPE]
            sel_type = st.selectbox("類型", type_opts, key="fx_type")
            new_type = st.text_input("輸入新類型", key="fx_new_type") if sel_type == ADD_NEW_TYPE else None

            fx_amt = st.number_input("金額 (該週期的總額)", min_value=0, key="fx_amt")
            
            ADD_NEW_PAY = "➕ 新增方式..."
            pay_opts = pay_methods + [ADD_NEW_PAY]
            sel_pay = st.selectbox("付款方式", pay_opts, key="fx_pay_sel")
            new_pay = st.text_input("輸入新付款方式", key="fx_new_pay") if sel_pay == ADD_NEW_PAY else None

            fx_cycle = st.selectbox("扣款週期", ["每月", "每半年", "每年"], key="fx_cyc")
            
            fx_detail = ""
            if not st.checkbox("無特定扣款日", key="fx_no_date"):
                if fx_cycle == "每月":
                    day = st.number_input("每月幾號", 1, 31, 5, key="fx_d")
                    fx_detail = f"{day}號"
                elif fx_cycle == "每半年":
                    fx_detail = "半年繳" # 簡化
                elif fx_cycle == "每年":
                    fx_detail = "年繳"

            if st.button("確認新增", key="fx_add_btn"):
                if sheet_fixed:
                    final_type = new_type if sel_type == ADD_NEW_TYPE and new_type else sel_type
                    if final_type == ADD_NEW_TYPE: final_type = "未分類"
                    
                    final_pay = new_pay if sel_pay == ADD_NEW_PAY and new_pay else sel_pay
                    if final_pay == ADD_NEW_PAY: final_pay = "未指定"

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

    with col_view:
        if not df_fixed.empty:
            st.write(f"📊 攤提後月固定支出: **${total_fixed:,}**")
            for i, row in df_fixed.iterrows():
                with st.expander(f"{row['Item']} - ${row['Amount']:,} ({row.get('Cycle','每月')})"):
                    st.write(f"類型: {row['Type']} | 支付: {row['PaidBy']}")
                    if st.button("🗑️ 刪除", key=f"del_fx_{i}"):
                        sheet_fixed.delete_rows(i+2)
                        st.success("已刪除")
                        load_all_finance_data.clear()
                        if "fin_data_loaded" in st.session_state: del st.session_state["fin_data_loaded"]
                        st.rerun()
        else:
            st.info("目前沒有固定開銷。")

def show_reserve_tab(sheet_reserve, df_reserve, current_balance):
    # (保持原樣，僅需貼上原有的程式碼)
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