import os
import sys
import importlib.util
import streamlit as st

from auth import login_page, is_authenticated
from sidebar import show_sidebar

# လိုအပ်သော Database နှင့် POS sync module များကို import လုပ်ခြင်း
try:
    from database import supabase
except ImportError:
    supabase = None

try:
    from pos_sync import render_pos_sync_sidebar, get_cached_products
except ImportError:
    render_pos_sync_sidebar = None
    get_cached_products = None


# ==========================================
# PAGE CONFIG (MUST BE FIRST)
# ==========================================
st.set_page_config(
    page_title="Myanmar ERP Enterprise",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# SESSION INIT
# ==========================================
def init_state():
    defaults = {
        "user": None,
        "active_page": "1_POS",
        "language": "English",
        "auth_checked": False
    }
    for k, v in defaults.items():  
        st.session_state.setdefault(k, v)

init_state()

# ==========================================
# DYNAMIC FILE LOADER (PRODUCTION ENGINE)
# ==========================================
def page_router():
    # Security Gate: Login မရှိပါက Page Load မပေးပါ
    if not st.session_state.get("user"):
        st.error("Please login first")
        return

    # Sidebar မှလာသော page_id ကိုရယူခြင်း
    page_id = st.session_state.get("active_page", "1_POS")

    # Dashboard Logic
    if page_id == "dashboard":
        st.title("🏭 ERP Control Dashboard")
        st.info("Welcome to Enterprise Core.")
        return

    # POS Screen Logic (active_page က 1_POS ဖြစ်နေလျှင်)
    if page_id == "1_POS":
        st.title("POS အရောင်းမျက်နှာပြင်")
        
        if supabase and render_pos_sync_sidebar and get_cached_products:
            # 1. Sidebar ထဲတွင် Sync ခလုတ် ထည့်သွင်းခြင်း
            render_pos_sync_sidebar(supabase)

            # 2. POS Screen အတွက် Product စာရင်းများကို Cache ထဲမှ ယူသုံးခြင်း
            products = get_cached_products(supabase)

            # 3. Product များကို POS Screen ပေါ်တွင် ပြသခြင်း
            if products:
                for p in products:
                    st.write(f"ပစ္စည်းအမည်: {p.get('name')} | လက်ကျန်: {p.get('stock')}")
            else:
                st.info("ပြရန် Product များ မရှိသေးပါ။")
        else:
            st.error("Database သို့မဟုတ် POS Sync module ချိတ်ဆက်မှု အမှားရှိနေပါသည်။")
        return

    # Absolute Path တည်ဆောက်ခြင်း
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "erp_pages", f"{page_id}.py")

    # File တည်ရှိမှု စစ်ဆေးခြင်း
    if not os.path.exists(file_path):
        st.error(f"Page file not found: {file_path}")
        return

    try:
        # Load Module Dynamically
        spec = importlib.util.spec_from_file_location("erp_page", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Execute Page Logic (Support run(), main(), or Legacy)
        if hasattr(module, "run"):
            module.run()
        elif hasattr(module, "main"):
            module.main()
        else:
            st.warning(f"{page_id}.py has no run() or main() function.")

    except Exception as e:
        st.error(f"Page Load Error: {e}")

# ==========================================
# MAIN CONTROLLER
# ==========================================
def main():
    # 1. Login Gate
    if not is_authenticated():
        login_page()
        st.stop()

    # 2. Render Sidebar
    try:
        show_sidebar()
    except Exception as e:
        st.sidebar.error("Sidebar loading error.")

    # 3. Render Main Page
    page_router()

if __name__ == "__main__":
    main()
