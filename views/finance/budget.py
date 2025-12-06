import streamlit as st
import pandas as pd
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.append(root_dir)

from utils import get_worksheet

def show_budget_tab(sheet_budget, df_budget, type1_list, existing_items, budget_dict):
    st.subheader("📅 預算額度設定")
    all_possible = type1_list + ["預備金"]
    items_to_add = [i for i in all_possible if i not in existing_items]
    items_to_edit = [i for i in all_possible if i in existing_items]
    
    col_new, col_edit = st.columns(2)
    with col_new:
        st.markdown("#### 🆕 新增")
        if items_to_add:
            with st.form("new_budget"):
                new_i = st.selectbox("項目", items_to_add)
                new_a = st.number_input("金額", min_value=0, step=1000)
                if st.form_submit_button("➕ 新增"):
                    if sheet_budget:
                        sheet_budget.append_row([new_i, new_a])
                        st.success("已新增")
                        st.cache_data.clear()
                        st.rerun()
        else: st.success("已全部設定！")

    with col_edit:
        st.markdown("#### ✏️ 修改")
        if items_to_edit:
            target = st.selectbox("選擇項目", items_to_edit)
            curr_val = budget_dict.get(target, 0)
            with st.form("edit_budget"):
                edit_a = st.number_input(f"調整 {target}", value=curr_val, min_value=0, step=1000)
                if st.form_submit_button("💾 更新"):
                    if sheet_budget:
                        cell = sheet_budget.find(target)
                        sheet_budget.update_cell(cell.row, 2, edit_a)
                        st.success("已更新")
                        st.cache_data.clear()
                        st.rerun()

    st.divider()
    with st.expander("🗑️ 刪除預算"):
        if items_to_edit:
            del_t = st.selectbox("刪除項目", ["請選擇..."] + items_to_edit)
            if del_t != "請選擇..." and st.button("確認刪除"):
                if sheet_budget:
                    cell = sheet_budget.find(del_t)
                    sheet_budget.delete_rows(cell.row)
                    st.success("已刪除")
                    st.cache_data.clear()
                    st.rerun()
    
    st.divider()
    if not df_budget.empty:
        st.subheader("📋 預算清單")
        st.dataframe(df_budget, use_container_width=True, hide_index=True)