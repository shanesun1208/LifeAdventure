import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 引入 update_setting_value 以便存回新分類
from utils import get_worksheet, load_sheet_data, update_setting_value

def show_finance_page(current_city, current_goal, type1_list, type2_list):
    st.title("💰 商會 (Merchant Guild)")
    
    # --- 1. 使用快取讀取資料 ---
    df_fin = load_sheet_data("Finance")
    df_fixed = load_sheet_data("FixedExpenses")
    df_income = load_sheet_data("Income")
    df_budget = load_sheet_data("Budget")
    df_reserve = load_sheet_data("ReserveFund")

    # --- 2. 數據計算核心 ---
    current_month_str = datetime.now().strftime("%Y-%m")
    
    # A. 收入
    total_income = 0
    if not df_income.empty and 'Date' in df_income.columns:
        df_income['Date'] = df_income['Date'].astype(str)
        inc_month = df_income[df_income['Date'].str.contains(current_month_str)]
        inc_month['Amount'] = pd.to_numeric(inc_month['Amount'], errors='coerce').fillna(0)
        total_income = int(inc_month['Amount'].sum())

    # B. 固定開銷
    total_fixed = 0
    if not df_fixed.empty and 'Amount' in df_fixed.columns:
        df_fixed['Amount'] = pd.to_numeric(df_fixed['Amount'], errors='coerce').fillna(0)
        total_fixed = int(df_fixed['Amount'].sum())

    # C. 變動支出
    total_variable = 0
    spent_by_category = {}
    if not df_fin.empty and 'Date' in df_fin.columns:
        df_fin['Date'] = df_fin['Date'].astype(str)
        fin_month = df_fin[df_fin['Date'].str.contains(current_month_str)]
        fin_month['Price'] = pd.to_numeric(fin_month['Price'], errors='coerce').fillna(0)
        total_variable = int(fin_month['Price'].sum())
        if 'Type1' in fin_month.columns:
            spent_by_category = fin_month.groupby('Type1')['Price'].sum().to_dict()

    # D. 預算資料
    reserve_budget_goal = 0
    budget_dict = {}
    existing_budget_items = []
    
    if not df_budget.empty and 'Item' in df_budget.columns:
        df_budget['Budget'] = pd.to_numeric(df_budget['Budget'], errors='coerce').fillna(0)
        for _, row in df_budget.iterrows():
            item = row['Item']
            amt = int(row['Budget'])
            budget_dict[item] = amt
            existing_budget_items.append(item)
            if "預備金" in item:
                reserve_budget_goal = amt

    # E. 預備金金庫
    current_reserve_balance = 0
    if not df_reserve.empty and 'Amount' in df_reserve.columns:
        df_reserve['Amount'] = pd.to_numeric(df_reserve['Amount'], errors='coerce').fillna(0)
        deposits = df_reserve[df_reserve['Type'] == '存入']['Amount'].sum()
        withdrawals = df_reserve[df_reserve['Type'] == '取出']['Amount'].sum()
        current_reserve_balance = int(deposits - withdrawals)

    # F. 自由現金流
    free_cash = total_income - total_fixed - total_variable - reserve_budget_goal

    # --- 3. 介面呈現 ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 總覽", "💰 收入", "📝 支出", "🏛️ 固定", "📅 預算", "🏦 預備金"])

    # === Tab 1: 總覽 ===
    with tab1:
        st.subheader(f"📊 {current_month_str} 商會戰略看板")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("本月收入", f"${total_income:,}")
        c2.metric("固定開銷", f"${total_fixed:,}")
        c3.metric("實際支出", f"${total_variable:,}")
        c4.metric("自由現金流", f"${free_cash:,}", delta="扣除預算目標後")

        st.divider()
        col_res, col_space = st.columns([1, 2])
        col_res.metric("🏦 預備金金庫總額", f"${current_reserve_balance:,}", delta="累計資產")
        
        st.divider()
        st.subheader("🎯 預算執行率")
        
        if reserve_budget_goal > 0:
            this_month_saved = 0
            if not df_reserve.empty:
                df_reserve['Date'] = df_reserve['Date'].astype(str)
                res_month = df_reserve[df_reserve['Date'].str.contains(current_month_str)]
                this_month_saved = res_month[res_month['Type'] == '存入']['Amount'].sum()
            p_saved = min(this_month_saved / reserve_budget_goal, 1.0)
            st.write(f"🏦 **本月預備金存款目標**: ${int(this_month_saved):,} / ${reserve_budget_goal:,}")
            st.progress(p_saved)
        
        for item, budget_amt in budget_dict.items():
            if "預備金" in item: continue
            spent = spent_by_category.get(item, 0)
            percent = 0
            if budget_amt > 0: percent = min(spent / budget_amt, 1.0)
            remain = budget_amt - spent
            
            c_label, c_val = st.columns([3, 1])
            c_label.write(f"**{item}** (剩餘: ${remain:,})")
            c_val.write(f"${spent:,} / ${budget_amt:,}")
            
            st.progress(percent)
            if spent > budget_amt:
                st.caption(f"⚠️ {item} 已超支 ${spent - budget_amt:,} ！")

    # === Tab 2: 收入 ===
    with tab2:
        st.subheader("💰 登記收入")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.form("add_income"):
                i_date = st.date_input("日期", datetime.now())
                i_item = st.text_input("項目", placeholder="ex: 薪資")
                i_amount = st.number_input("金額", min_value=0, step=1000)
                i_type = st.selectbox("類別", ["薪資", "獎金", "投資", "其他"])
                i_note = st.text_input("備註")
                if st.form_submit_button("📥 存入"):
                    sheet = get_worksheet("Income")
                    if sheet:
                        sheet.append_row([str(i_date), i_item, i_amount, i_type, i_note])
                        st.success("已存入！")
                        st.cache_data.clear()
                        st.rerun()
        with c2:
            if not df_income.empty:
                st.dataframe(df_income[::-1], use_container_width=True, hide_index=True)

    # === Tab 3: 支出 (重點修改: 動態新增分類) ===
    with tab3:
        st.subheader("📝 日常記帳")
        c1, c2 = st.columns([1, 1.5])
        with c1:
            with st.form("add_exp"):
                f_date = st.date_input("日期", datetime.now())
                f_item = st.text_input("項目", placeholder="ex: 午餐")
                f_price = st.number_input("金額", min_value=0, step=10)
                
                # --- 動態分類邏輯 ---
                # 1. 在選單最後加入「新增選項」
                ADD_NEW_OPT = "➕ 新增類別..."
                
                t1_options = type1_list + [ADD_NEW_OPT]
                t2_options = type2_list + [ADD_NEW_OPT]
                
                sel_t1 = st.selectbox("主分類 (Type1)", t1_options)
                # 如果選了新增，就顯示輸入框，否則隱藏
                new_t1_val = None
                if sel_t1 == ADD_NEW_OPT:
                    new_t1_val = st.text_input("輸入新主分類名稱", placeholder="ex: 娛樂")

                sel_t2 = st.selectbox("子分類 (Type2)", t2_options)
                new_t2_val = None
                if sel_t2 == ADD_NEW_OPT:
                    new_t2_val = st.text_input("輸入新子分類名稱", placeholder="ex: 電影")

                # --- 提交邏輯 ---
                if st.form_submit_button("💸 記帳"):
                    sheet = get_worksheet("Finance")
                    if sheet:
                        # 決定最終使用的分類名稱
                        final_t1 = new_t1_val if sel_t1 == ADD_NEW_OPT and new_t1_val else sel_t1
                        final_t2 = new_t2_val if sel_t2 == ADD_NEW_OPT and new_t2_val else sel_t2
                        
                        # 防呆：如果選了新增但沒打字，就存成"未分類"
                        if final_t1 == ADD_NEW_OPT: final_t1 = "未分類"
                        if final_t2 == ADD_NEW_OPT: final_t2 = "未分類"

                        # 1. 寫入記帳
                        wk = f_date.isocalendar()[1]
                        sheet.append_row([str(f_date), wk, f_item, f_price, final_t1, final_t2])
                        
                        # 2. 檢查是否需要更新 Setting (Type1)
                        updated_setting = False
                        if sel_t1 == ADD_NEW_OPT and new_t1_val:
                            if new_t1_val not in type1_list:
                                # 將新項目加入舊列表，並用逗號組合成字串
                                new_list_str = ",".join(type1_list + [new_t1_val])
                                update_setting_value("Type1_Options", new_list_str)
                                updated_setting = True
                                st.toast(f"已新增主分類：{new_t1_val}")

                        # 3. 檢查是否需要更新 Setting (Type2)
                        if sel_t2 == ADD_NEW_OPT and new_t2_val:
                            if new_t2_val not in type2_list:
                                new_list_str = ",".join(type2_list + [new_t2_val])
                                update_setting_value("Type2_Options", new_list_str)
                                updated_setting = True
                                st.toast(f"已新增子分類：{new_t2_val}")

                        st.success(f"已記錄：{f_item} ${f_price}")
                        st.cache_data.clear() # 清除快取，確保下次選單更新
                        st.rerun()
                    else: st.error("找不到 Finance 分頁")
        with c2:
            if not df_fin.empty:
                st.dataframe(df_fin.tail(10)[::-1], use_container_width=True, hide_index=True)

    # === Tab 4: 固定開銷 ===
    with tab4:
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
                    sheet = get_worksheet("FixedExpenses")
                    if sheet:
                        sheet.append_row([fx_item, fx_type, fx_amt, fx_pay, fx_day])
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
                            sheet = get_worksheet("FixedExpenses")
                            sheet.delete_rows(i+2)
                            st.cache_data.clear()
                            st.rerun()

    # === Tab 5: 預算規劃 ===
    with tab5:
        st.subheader("📅 預算額度設定")
        # 這裡的 type1_list 此時還是舊的，因為 rerun 才會更新
        all_possible_items = type1_list + ["預備金"]
        items_to_add = [item for item in all_possible_items if item not in existing_budget_items]
        items_to_edit = [item for item in all_possible_items if item in existing_budget_items]
        
        col_new, col_edit = st.columns(2)
        with col_new:
            st.markdown("#### 🆕 新增")
            if items_to_add:
                with st.form("new_budget_form"):
                    new_item = st.selectbox("選擇項目", items_to_add)
                    new_amount = st.number_input("預算金額", min_value=0, step=1000)
                    if st.form_submit_button("➕ 新增"):
                        sheet = get_worksheet("Budget")
                        if sheet:
                            sheet.append_row([new_item, new_amount])
                            st.success(f"已新增 {new_item}")
                            st.cache_data.clear()
                            st.rerun()
            else: st.success("所有類別都已設定！")

        with col_edit:
            st.markdown("#### ✏️ 修改")
            if items_to_edit:
                target_item = st.selectbox("選擇修改項目", items_to_edit)
                current_val = budget_dict.get(target_item, 0)
                with st.form("edit_budget_form"):
                    edit_amount = st.number_input(f"調整 {target_item}", value=current_val, min_value=0, step=1000)
                    if st.form_submit_button("💾 更新"):
                        sheet = get_worksheet("Budget")
                        if sheet:
                            cell = sheet.find(target_item)
                            sheet.update_cell(cell.row, 2, edit_amount)
                            st.success(f"已更新")
                            st.cache_data.clear()
                            st.rerun()

        st.divider()
        with st.expander("🗑️ 刪除預算"):
            if items_to_edit:
                del_target = st.selectbox("選擇刪除", ["請選擇..."] + items_to_edit)
                if del_target != "請選擇...":
                    if st.button(f"確認刪除 {del_target}"):
                        sheet = get_worksheet("Budget")
                        cell = sheet.find(del_target)
                        sheet.delete_rows(cell.row)
                        st.success("已刪除")
                        st.cache_data.clear()
                        st.rerun()
        
        st.divider()
        st.subheader("📋 目前預算清單")
        if not df_budget.empty:
            st.dataframe(df_budget, use_container_width=True, hide_index=True)

    # === Tab 6: 預備金金庫 ===
    with tab6:
        st.subheader("🏦 預備金金庫 (Reserve Fund)")
        st.markdown(f"""<div style="padding:15px; border:1px solid #FFD700; border-radius:10px; background-color:rgba(255, 215, 0, 0.1); text-align:center;"><h2 style="color:#FFD700; margin:0;">💰 金庫餘額: ${current_reserve_balance:,}</h2></div>""", unsafe_allow_html=True)
        st.write("")

        c_op, c_hist = st.columns([1, 1.5])
        with c_op:
            with st.form("reserve_op"):
                r_type = st.radio("操作", ["存入", "取出"], horizontal=True)
                r_date = st.date_input("日期", datetime.now())
                r_amount = st.number_input("金額", min_value=0, step=1000)
                r_note = st.text_input("備註")
                if st.form_submit_button("確認"):
                    sheet = get_worksheet("ReserveFund")
                    if sheet:
                        sheet.append_row([str(r_date), r_type, r_amount, r_note])
                        if r_type == "存入": st.balloons()
                        st.success(f"已{r_type}")
                        st.cache_data.clear()
                        st.rerun()
        with c_hist:
            if not df_reserve.empty:
                st.dataframe(df_reserve[::-1], use_container_width=True, hide_index=True)