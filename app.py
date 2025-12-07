import streamlit as st
import utils
from views import home, finance, quest, diary, setting, maid

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="Life Adventure OS", page_icon="🛡️", layout="wide")

# --- 2. CSS 樣式 ---
st.markdown("""
<style>
    .main { font-family: '微軟正黑體', sans-serif; }
    
    /* 側邊欄佈局控制 */
    /* 讓側邊欄內容變成 Flex column */
    section[data-testid="stSidebar"] .block-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
    }
    
    /* 讓中間的 Spacer 自動長高，把 Setting 推到底部 */
    .sidebar-spacer {
        flex-grow: 1;
    }
    
    /* 設定按鈕樣式 */
    div.stButton.setting-btn > button {
        width: 100%;
        border: 1px solid #555;
        background-color: transparent;
        color: #aaa;
    }
    div.stButton.setting-btn > button:hover {
        border-color: #00CC99;
        color: #00CC99;
    }

    /* 其他通用樣式 */
    .greeting-box { background: linear-gradient(135deg, #2C3E50 0%, #000000 100%); padding: 30px; border-radius: 15px; color: white; margin-bottom: 20px; border-left: 8px solid #00CC99; }
    .goal-box { background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #444; margin-bottom: 30px; }
    .goal-text { font-size: 24px; font-weight: bold; color: #FFF; }
    .adventure-card { background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #00CC99; }
    .ai-comment { font-size: 15px; color: #00CC99; font-weight: bold; margin-top: 15px; border-top: 1px solid #555; padding-top: 10px; background-color: rgba(0, 204, 153, 0.1); padding: 10px; border-radius: 5px; }
    .corkboard-title { font-size: 30px; font-weight: bold; color: #E0E0E0; text-align: center; border-bottom: 2px solid #8B4513; margin-bottom: 20px; padding-bottom: 10px; }
    .quest-paper { background-color: #FDF5E6; color: #2F4F4F; padding: 20px; margin: 10px; border-radius: 2px; box-shadow: 3px 3px 5px rgba(0,0,0,0.3); position: relative; border-top: 1px solid #FFF; border-bottom: 1px solid #CCC; transition: transform 0.2s; }
    .quest-paper:hover { transform: scale(1.02); }
    .pin { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); font-size: 24px; z-index: 10; text-shadow: 2px 2px 2px rgba(0,0,0,0.3); }
    .priority-stamp { position: absolute; bottom: 10px; right: 10px; font-size: 20px; font-weight: bold; border: 2px solid; padding: 2px 8px; border-radius: 5px; transform: rotate(-10deg); opacity: 0.8; }
    .p-S { color: #FF0000; border-color: #FF0000; } .p-A { color: #FF8C00; border-color: #FF8C00; }
    .p-B { color: #0000FF; border-color: #0000FF; } .p-C { color: #008000; border-color: #008000; }
    .paper-title { font-size: 18px; font-weight: bold; border-bottom: 1px dashed #aaa; padding-bottom: 5px; margin-bottom: 10px; }
    .metric-card { background-color: #1E1E1E; border: 1px solid #333; padding: 15px; border-radius: 8px; margin-bottom: 10px; text-align: center; }
    .metric-value { font-size: 24px; font-weight: bold; color: #00CC99; }
    .metric-label { font-size: 14px; color: #AAA; }
    .budget-label { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 讀取設定 ---
SETTINGS = utils.get_settings()
CUR_CITY = SETTINGS.get('Location', 'Taipei,TW')
CUR_GOAL = SETTINGS.get('LifeGoal', '未設定')

TYPE1 = SETTINGS.get('Type1_Options', '').split(',')
TYPE2 = SETTINGS.get('Type2_Options', '').split(',')
INCOME_TYPES = SETTINGS.get('Income_Types', '').split(',')
FIXED_TYPES = SETTINGS.get('Fixed_Types', '').split(',')
PAY_METHODS = SETTINGS.get('Payment_Methods', '').split(',')
QUEST_TYPES = SETTINGS.get('Quest_Types', '').split(',')

TYPE1_STR = SETTINGS.get('Type1_Options', '')
TYPE2_STR = SETTINGS.get('Type2_Options', '')

# --- 4. 側邊欄佈局 (Layout) ---
with st.sidebar:
    st.title("🧭 導航地圖")
    
    # A. 上方：主要導航
    # 如果還沒有選過，預設首頁
    if "fin_nav" not in st.session_state: st.session_state["fin_nav"] = "我的小屋"
    
    # 這裡只放主要功能，不放 Setting
    main_options = ["我的小屋", "冒險日誌", "商會", "任務看板", "接取任務追蹤"]
    
    # 如果目前的狀態是 Setting，選單要顯示什麼？
    # 為了避免 Radio 報錯 (選項不在列表內)，如果目前是 Setting，我們暫時選第一個，或是顯示空白
    # 簡單做法：我們讓 Setting 也是 Radio 的一個選項，但用 CSS 把它藏起來？
    # 不，最簡單做法：Setting 也是 Radio 的一部分，但我們用 "分段" 的方式呈現
    
    # 修正策略：全部都放進 Radio，但利用 CSS 把它推到底部
    # 因為 Streamlit 的元件順序很難插入 spacer
    
    page = st.radio(
        "Menu", 
        main_options, 
        key="fin_nav_main",
        label_visibility="collapsed"
    )
    
    # B. 中間：女僕區塊
    maid.render_maid_sidebar()
    
    # C. 墊高區塊 (Spacer)
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)
    st.markdown("<br><br><br>", unsafe_allow_html=True) # 物理墊高，確保有距離
    
    # D. 底部：設定按鈕 (手動跳轉)
    # 我們用 Button 來切換頁面狀態
    # 為了讓按鈕看起來像選單，我們用 CSS class "setting-btn"
    st.markdown('<div class="stButton setting-btn">', unsafe_allow_html=True)
    if st.button("⚙️ 系統設定"):
        st.session_state["fin_nav_main"] = "Setting_Hidden" # 給一個不存在的值，讓 Radio 取消選取(視覺上)
        st.session_state["current_page"] = "Setting"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.caption("Life Adventure OS v3.0")

# --- 5. 頁面路由 ---
# 優先讀取按鈕觸發的 page，如果沒有，才讀取 Radio
target_page = st.session_state.get("current_page", page)

# 如果 Radio 被點擊了，更新 current_page
if page != st.session_state.get("last_radio_selection", ""):
    target_page = page
    st.session_state["current_page"] = page
    st.session_state["last_radio_selection"] = page

# 路由判斷
if target_page == "我的小屋":
    home.show_home_page(CUR_CITY, CUR_GOAL)

elif target_page == "冒險日誌":
    diary.show_diary_page()

elif target_page == "商會":
    finance.show_finance_page(CUR_CITY, CUR_GOAL, TYPE1, TYPE2, INCOME_TYPES, FIXED_TYPES, PAY_METHODS)

elif target_page == "任務看板":
    quest.show_quest_board(QUEST_TYPES)

elif target_page == "接取任務追蹤":
    quest.show_tracking()

elif target_page == "Setting":
    setting.show_setting_page(CUR_GOAL, CUR_CITY, utils.CITY_OPTIONS, TYPE1_STR, TYPE2_STR)