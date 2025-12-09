import streamlit as st
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import update_setting_value, get_settings


def show_setting_page(
    current_goal, current_city, city_opts, type1_str, type2_str
):
    st.title("⚙️ Setting")

    with st.form("settings_form"):
        st.subheader("🌍 基本設定")
        n_goal = st.text_input("人生目標", current_goal)

        idx = 0
        if current_city in city_opts:
            idx = city_opts.index(current_city)
        n_city = st.selectbox("城市", city_opts, index=idx)

        # [修改] 移除女僕外觀設定區塊

        if st.form_submit_button("💾 儲存所有設定"):
            update_setting_value("LifeGoal", n_goal)
            update_setting_value("Location", n_city)

            st.success("設定已更新！")
            st.cache_data.clear()
            st.rerun()

    st.divider()
    st.info("💡 財務預算 (Budget) 請直接至 Google Sheet 修改金額。")
