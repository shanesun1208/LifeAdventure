import streamlit as st
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils import update_setting_value, get_settings

def show_setting_page(current_goal, current_city, city_opts, type1_str, type2_str):
    st.title("⚙️ Setting")
    
    # 重新讀取設定以獲取圖片 URL
    settings = get_settings()
    current_img = settings.get('Maid_Image_URL', "")
    
    with st.form("settings_form"):
        st.subheader("🌍 基本設定")
        n_goal = st.text_input("人生目標", current_goal)
        
        idx = 0
        if current_city in city_opts:
            idx = city_opts.index(current_city)
        n_city = st.selectbox("城市", city_opts, index=idx)
        
        st.subheader("👧 女僕外觀設定")
        n_img = st.text_input("圖片網址 (URL)", value=current_img, placeholder="請貼上圖片連結 (jpg/png)...")
        st.caption("建議找正方形或直向的圖片，貼上網址即可更換首頁角色。")
        
        if st.form_submit_button("💾 儲存所有設定"):
            update_setting_value("LifeGoal", n_goal)
            update_setting_value("Location", n_city)
            update_setting_value("Maid_Image_URL", n_img)
            
            st.success("設定已更新！")
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    st.info("💡 財務預算 (Budget) 請直接至 Google Sheet 修改金額。")