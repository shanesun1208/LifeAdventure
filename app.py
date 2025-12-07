import streamlit as st
import utils
from views import home, finance, quest, diary, setting

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="Life Adventure OS", page_icon="🛡️", layout="wide")

# --- 2. CSS 樣式 (介面靈魂) ---
st.markdown("""
<style>
    .main { font-family: '微軟正黑體', sans-serif; }
    
    /* === 側邊欄排版優化 (關鍵修改) === */
    /* 讓側邊欄選單的最後一個選項 (Setting) 往下推，並加上分隔線 */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:last-child {
        margin-top: 50px;       /* 與上方選項的距離 */
        padding-top: 20px;      /* 內距 */
        border-top: 1px solid #555; /* 分隔線顏色 */
    }
    
    /* 側邊欄標題美化 */
    section[data-testid="stSidebar"] .stRadio > label {
        color: #00CC99 !important;
        font-weight: bold;
    }

    /* === 其他通用樣式 === */
    .greeting-box { background: linear-gradient(135deg, #2C3E50 0%, #000000 100%); padding: 30px; border-radius: 15px; color: white; margin-bottom: 20px; border-left: 8px solid #00CC99; }
    .goal-box { background-color: #262730; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #444; margin-bottom: 30px; }
    .goal-text { font-size: 24px; font-weight: bold; color: #FFF; }
    .adventure-card { background-color: #262730; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid #00CC99; }
    .ai-comment { font-size: 15px; color: #00CC99; font-weight: bold; margin-top: 15px; border-top: 1px solid #555; padding-top: 10px; background-color: rgba(0, 204, 153, 0.1); padding: 10px; border-radius: 5px; }
    
    /* 任務看板 */
    .corkboard-title { font-size: 30px; font-weight: bold; color: #E0E0E0; text-align: center; border-bottom: 2px solid #8B4513; margin-bottom: 20px; padding-bottom: 10px; }
    .quest-paper { background-color: #FDF5E6; color: #2F4F4F; padding: 20px; margin: 10px; border-radius: 2px; box-shadow: 3px 3px 5px rgba(0,0,0,0.3); position: relative; border-top: 1px solid #FFF; border-bottom: 1px solid #CCC; transition: transform 0.2s; }
    .quest-paper:hover { transform: scale(1.02); }
    .pin { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); font-size: 24px; z-index: 10; text-shadow: 2px 2px 2px rgba(0,0,0,0.3); }
    .priority-stamp { position: absolute; bottom: 10px; right: 10px; font-size: 20px; font-weight: bold; border: 2px solid; padding: 2px 8px; border-radius: 5px; transform: rotate(-10deg); opacity: 0.8; }
    
    /* 財務 */
    .metric-card { background-color: #1E1E1E; border: 1px solid #333; padding: 15px; border-radius: 8px; margin-bottom: 10px; text-align: center; }
    .metric-value { font-size: 24px; font-weight: bold; color: #00CC99; }
    .metric-label { font-size: 14px; color: #AAA; }
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

# --- 4. 側邊欄導航 ---
with st.sidebar:
    st.title("🧭 導航地圖")
    if "fin_nav" not in st.session_state:
        st.session_state["fin_nav"] = "📊 總覽"

    # [關鍵] Setting 必須放在最後一個，CSS 才會對它生效
    page = st.radio(
        "導航選單", 
        ["我的小屋", "冒險日誌", "商會", "任務看板", "接取任務追蹤", "Setting"],
        label_visibility="collapsed"
    )
    
    # 這裡可以放版本號或 Logo，會顯示在 Setting 下方
    st.markdown("---")
    st.caption("Life Adventure OS v2.7")

# --- 5. 頁面路由 ---
if page == "我的小屋":
    home.show_home_page(CUR_CITY, CUR_GOAL)

elif page == "冒險日誌":
    diary.show_diary_page()

elif page == "商會":
    finance.show_finance_page(CUR_CITY, CUR_GOAL, TYPE1, TYPE2, INCOME_TYPES, FIXED_TYPES, PAY_METHODS)

elif page == "任務看板":
    quest.show_quest_board(QUEST_TYPES)

elif page == "接取任務追蹤":
    quest.show_tracking()

elif page == "Setting":
    setting.show_setting_page(CUR_GOAL, CUR_CITY, utils.CITY_OPTIONS, TYPE1_STR, TYPE2_STR)