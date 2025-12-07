import streamlit as st
import utils
from views import home, finance, quest, diary, setting

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="Life Adventure OS", page_icon="🛡️", layout="wide")

# --- 2. CSS 樣式 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Long+Cang&display=swap');
    
    .main { font-family: '微軟正黑體', sans-serif; }
    .greeting-box { background: linear-gradient(135deg, #2C3E50 0%, #000000 100%); padding: 30px; border-radius: 15px; color: white; margin-bottom: 20px; border-left: 8px solid #00CC99; }
    .goal-box { background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #444; margin-bottom: 30px; }
    .goal-text { font-size: 24px; font-weight: bold; color: #FFF; }
    .adventure-card { background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #00CC99; }
    .ai-comment { font-size: 15px; color: #00CC99; font-weight: bold; margin-top: 15px; border-top: 1px solid #555; padding-top: 10px; background-color: rgba(0, 204, 153, 0.1); padding: 10px; border-radius: 5px; }
    
    /* 任務看板 (更新版) */
    .corkboard-title { 
        font-family: 'Long Cang', cursive; /* 標題用手寫體 */
        font-size: 36px; font-weight: bold; color: #E0E0E0; text-align: center; border-bottom: 2px solid #8B4513; margin-bottom: 20px; padding-bottom: 10px; 
    }
    
    /* 財務 */
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
QUEST_TYPES = SETTINGS.get('Quest_Types', '').split(',') # 新增

TYPE1_STR = SETTINGS.get('Type1_Options', '')
TYPE2_STR = SETTINGS.get('Type2_Options', '')

# --- 4. 側邊欄導航 ---
with st.sidebar:
    st.title("🧭 導航地圖")
    if "fin_nav" not in st.session_state:
        st.session_state["fin_nav"] = "📊 總覽"

    page = st.radio(
        "導航選單", 
        ["我的小屋", "冒險日誌", "商會", "任務看板", "接取任務追蹤", "Setting"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("Life Adventure OS v2.6")

# --- 5. 頁面路由 ---
if page == "我的小屋":
    home.show_home_page(CUR_CITY, CUR_GOAL)

elif page == "冒險日誌":
    diary.show_diary_page()

elif page == "商會":
    finance.show_finance_page(CUR_CITY, CUR_GOAL, TYPE1, TYPE2, INCOME_TYPES, FIXED_TYPES, PAY_METHODS)

# 修改點：傳入 QUEST_TYPES
elif page == "任務看板":
    quest.show_quest_board(QUEST_TYPES)

elif page == "接取任務追蹤":
    quest.show_tracking()

elif page == "Setting":
    setting.show_setting_page(CUR_GOAL, CUR_CITY, utils.CITY_OPTIONS, TYPE1_STR, TYPE2_STR)