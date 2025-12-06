import streamlit as st
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import update_setting_value

def show_setting_page(current_goal, current_city, city_opts, type1_str, type2_str):
    st.title("⚙️ Setting")
    
    with st.form("settings_form"):
        st.subheader("🌍 基本設定")
        n_goal = st.text_input("人生目標", current_goal)
        
        # 城市選單
        idx = 0
        if current_city in city_opts:
            idx = city_opts.index(current_city)
        n_city = st.selectbox("城市", city_opts, index=idx)
        
        # --- 修改點：原本的財務分類設定區塊已隱藏 ---
        # 我們現在直接在記帳時動態新增，不需要在這裡手動改字串了
        
        if st.form_submit_button("💾 儲存設定"):
            update_setting_value("LifeGoal", n_goal)
            update_setting_value("Location", n_city)
            # Type1 和 Type2 保持原樣，不覆蓋
            
            st.success("設定已更新！")
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    st.info("💡 財務預算 (Budget) 請直接至 Google Sheet 修改金額。")
    st.info("💡 新增消費分類：請直接在「商會 > 支出櫃台」的下拉選單選擇「新增類別」即可。")