import streamlit as st
import pandas as pd

def show_dashboard(current_month_str, total_income, total_fixed_plan, total_actual_spent, free_cash, current_reserve_balance, reserve_goal, budget_dict, spent_by_category, df_reserve, remaining_unpaid_fixed):
    st.subheader(f"📊 {current_month_str} 商會戰略看板")
    
    # 核心指標
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("本月收入", f"${total_income:,}")
    # 這裡顯示計畫總額
    c2.metric("固定開銷 (計畫)", f"${total_fixed_plan:,}")
    # 實際支出
    c3.metric("實際總支出", f"${total_actual_spent:,}")
    
    # 自由現金流 (考慮未付固定開銷)
    c4.metric("可支配餘額", f"${free_cash:,}", delta="扣除預算與未付固定")

    # 提醒未付固定開銷
    if remaining_unpaid_fixed > 0:
        st.warning(f"⚠️ 尚有 **${remaining_unpaid_fixed:,}** 的固定開銷尚未入帳！請至「固定開銷」分頁處理。")
    else:
        st.success("✅ 本月固定開銷已全數入帳。")

    st.divider()
    col_res, col_space = st.columns([1, 2])
    col_res.metric("🏦 預備金金庫總額", f"${current_reserve_balance:,}", delta="累計資產")
    
    st.divider()
    st.subheader("🎯 預算執行率")
    
    # 預備金進度
    if reserve_goal > 0:
        this_month_saved = 0
        if not df_reserve.empty:
            df_reserve['Date'] = df_reserve['Date'].astype(str)
            res_month = df_reserve[df_reserve['Date'].str.contains(current_month_str)]
            this_month_saved = res_month[res_month['Type'] == '存入']['Amount'].sum()
        p_saved = min(this_month_saved / reserve_goal, 1.0)
        st.write(f"🏦 **本月預備金存款目標**: ${int(this_month_saved):,} / ${reserve_goal:,}")
        st.progress(p_saved)
    
    # 一般預算進度
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