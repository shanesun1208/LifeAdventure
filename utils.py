import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)

from utils import get_worksheet, load_all_finance_data

from . import dashboard, ledger, assets, budget

def show_finance_page(current_city, current_goal, type1_list, type2_list, income_types, fixed_types, pay_methods):
    st.title("💰 商會 (Merchant Guild)")
    
    # --- Loading ---
    # [修改] 移除 get_loading_message，改用靜態文字
    if "fin_data_loaded" not in st.session_state:
        with st.spinner("⏳ 正在核對商會帳本..."):
            all_data = load_all_finance_data()
            st.session_state['df_fin'] = all_data.get("Finance", pd.DataFrame())
            st.session_state['df_fixed'] = all_data.get("FixedExpenses", pd.DataFrame())
            st.session_state['df_income'] = all_data.get("Income", pd.DataFrame())
            st.session_state['df_budget'] = all_data.get("Budget", pd.DataFrame())
            st.session_state['df_reserve'] = all_data.get("ReserveFund", pd.DataFrame())
            st.session_state['fin_data_loaded'] = True
    
    df_fin = st.session_state['df_fin']
    df_fixed = st.session_state['df_fixed']
    df_income = st.session_state['df_income']
    df_budget = st.session_state['df_budget']
    df_reserve = st.session_state['df_reserve']
    
    sheet_fin = get_worksheet("Finance")
    sheet_fixed = get_worksheet("FixedExpenses")
    sheet_income = get_worksheet("Income")
    sheet_budget = get_worksheet("Budget")
    sheet_reserve = get_worksheet("ReserveFund")

    # --- 數據計算 ---
    current_month_str = datetime.now().strftime("%Y-%m")
    
    # A. 收入
    total_income = 0
    if not df_income.empty and 'Date' in df_income.columns:
        calc_df = df_income.copy()
        calc_df['Date'] = calc_df['Date'].astype(str)
        inc_month = calc_df[calc_df['Date'].str.contains(current_month_str)]
        inc_month['Amount'] = pd.to_numeric(inc_month['Amount'], errors='coerce').fillna(0)
        total_income = int(inc_month['Amount'].sum())

    # B. 固定開銷 (計畫總額)
    total_fixed_plan = 0
    if not df_fixed.empty and 'Amount' in df_fixed.columns:
        for _, row in df_fixed.iterrows():
            try:
                amt = float(row['Amount'])
                cycle = str(row.get('Cycle', '每月'))
                if cycle == "每年": total_fixed_plan += amt / 12
                elif cycle == "每半年": total_fixed_plan += amt / 6
                else: total_fixed_plan += amt
            except: pass
        total_fixed_plan = int(total_fixed_plan)

    # C. 實際變動支出 (含已入帳的固定開銷)
    total_actual_spent = 0
    actual_fixed_spent = 0 # 已經入帳的固定開銷金額
    spent_by_category = {}
    
    if not df_fin.empty and 'Date' in df_fin.columns:
        calc_df = df_fin.copy()
        calc_df['Date'] = calc_df['Date'].astype(str)
        fin_month = calc_df[calc_df['Date'].str.contains(current_month_str)]
        fin_month['Price'] = pd.to_numeric(fin_month['Price'], errors='coerce').fillna(0)
        total_actual_spent = int(fin_month['Price'].sum())
        
        if 'Type1' in fin_month.columns:
            spent_by_category = fin_month.groupby('Type1')['Price'].sum().to_dict()
            actual_fixed_spent = spent_by_category.get("固定開銷", 0)

    # D. 預算資料
    reserve_goal = 0
    budget_dict = {}
    existing_items = []
    if not df_budget.empty and 'Item' in df_budget.columns:
        calc_df = df_budget.copy()
        calc_df['Budget'] = pd.to_numeric(calc_df['Budget'], errors='coerce').fillna(0)
        for _, row in calc_df.iterrows():
            item = row['Item']
            amt = int(row['Budget'])
            budget_dict[item] = amt
            existing_items.append(item)
            if "預備金" in item: reserve_goal = amt

    # E. 預備金金庫
    curr_res_bal = 0
    if not df_reserve.empty and 'Amount' in df_reserve.columns:
        calc_df = df_reserve.copy()
        calc_df['Amount'] = pd.to_numeric(calc_df['Amount'], errors='coerce').fillna(0)
        dep = calc_df[calc_df['Type']=='存入']['Amount'].sum()
        wit = calc_df[calc_df['Type']=='取出']['Amount'].sum()
        curr_res_bal = int(dep - wit)

    # F. 自由現金流計算
    remaining_unpaid_fixed = max(0, total_fixed_plan - actual_fixed_spent)
    free_cash = total_income - total_actual_spent - remaining_unpaid_fixed - reserve_goal

    # --- 3. 介面導航 ---
    nav_options = ["📊 總覽", "💰 收入", "📝 支出", "🏛️ 固定", "📅 預算", "🏦 預備金"]
    if "fin_nav" not in st.session_state: st.session_state["fin_nav"] = "📊 總覽"
    selected_tab = st.radio("商會分頁", nav_options, key="fin_nav", label_visibility="collapsed", horizontal=True)
    st.divider()

    # --- 4. 顯示模組 ---
    if selected_tab == "📊 總覽":
        dashboard.show_dashboard(current_month_str, total_income, total_fixed_plan, total_actual_spent, free_cash, curr_res_bal, reserve_goal, budget_dict, spent_by_category, df_reserve, remaining_unpaid_fixed)
        
        if st.button("🔄 強制同步雲端資料"):
            for key in ['df_fin', 'df_fixed', 'df_income', 'df_budget', 'df_reserve', 'fin_data_loaded']:
                if key in st.session_state: del st.session_state[key]
            load_all_finance_data.clear()
            st.rerun()
    
    elif selected_tab == "💰 收入":
        ledger.show_income_tab(sheet_income, df_income, income_types)
        
    elif selected_tab == "📝 支出":
        ledger.show_expense_tab(sheet_fin, df_fin, type1_list, type2_list)
        
    elif selected_tab == "🏛️ 固定":
        assets.show_fixed_tab(sheet_fixed, df_fixed, total_fixed_plan, fixed_types, pay_methods, sheet_fin, df_fin)
        
    elif selected_tab == "📅 預算":
        budget.show_budget_tab(sheet_budget, df_budget, type1_list, existing_items, budget_dict)
        
    elif selected_tab == "🏦 預備金":
        assets.show_reserve_tab(sheet_reserve, df_reserve, curr_res_bal)