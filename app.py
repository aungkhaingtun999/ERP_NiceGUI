# ==============================================================================
# app.py
# ERP ENTERPRISE APPLICATION CONTROLLER
# SAFE PAGE ROUTER v30.12
# ==============================================================================


import os
import sys
import importlib.util

import streamlit as st


from auth import (
    login_page,
    is_authenticated
)


from sidebar import (
    show_sidebar
)

from utils.notification import (
    show_notification
)
import streamlit as st
# သင့် Project ထဲက Supabase client ကို import လုပ်ပါ (ဥပမာ - from database import supabase)
from pos_sync import render_pos_sync_sidebar, get_cached_products

st.title("POS အရောင်းမျက်နှာပြင်")

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
    

# ==============================================================================
# PATH SETUP
# ==============================================================================


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


if BASE_DIR not in sys.path:

    sys.path.insert(
        0,
        BASE_DIR
    )



# ==============================================================================
# PAGE CONFIG
# ==============================================================================


st.set_page_config(

    page_title="Myanmar ERP Enterprise",

    page_icon="🏭",

    layout="wide",

    initial_sidebar_state="expanded"

)



# ==============================================================================
# SESSION INITIALIZER
# ==============================================================================


def init_state():


    defaults = {


        "user": None,


        "active_page":
            "1_POS",


        "language":
            "English",


        "auth_checked":
            False


    }


    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value






# ==============================================================================
# SAFE PAGE LOADER
# ==============================================================================


def load_page(page_id):


    page_folder = os.path.join(

        BASE_DIR,

        "erp_pages"

    )


    file_path = os.path.join(

        page_folder,

        f"{page_id}.py"

    )



    if not os.path.exists(file_path):

        st.error(

            f"Page file not found:\n{file_path}"

        )

        return





    try:


        module_name = (

            f"erp_pages.{page_id}"

        )



        spec = importlib.util.spec_from_file_location(

            module_name,

            file_path

        )



        if spec is None:

            raise ImportError(

                f"Cannot load module {module_name}"

            )



        module = importlib.util.module_from_spec(

            spec

        )



        # Important:
        # Register module before execute
        # to support relative imports


        sys.modules[module_name] = module



        spec.loader.exec_module(

            module

        )





        if hasattr(module, "run"):


            module.run()



        elif hasattr(module, "main"):


            module.main()



        else:


            st.warning(

                f"{page_id}.py loaded without run() or main()"

            )





    except Exception as e:


        st.error(

            f"Page Load Error: {e}"

        )


        with st.expander(
            "Debug Trace"
        ):

            st.exception(e)







# ==============================================================================
# PAGE ROUTER
# ==============================================================================


def page_router():


    if not st.session_state.get(
        "user"
    ):


        st.error(

            "Please login first"

        )

        return





    page_id = st.session_state.get(

        "active_page",

        "1_POS"

    )





    if page_id == "dashboard":


        st.title(

            "🏭 ERP Control Dashboard"

        )


        st.info(

            "Welcome to Enterprise Core."

        )


        return





    load_page(

        page_id

    )







# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

def main():

    init_state()

    if not is_authenticated():

        login_page()

        st.stop()

    # ==========================================
    # GLOBAL NOTIFICATION
    # ==========================================

    show_notification()

    try:

        show_sidebar()

    except Exception as e:


        st.sidebar.error(

            "Sidebar loading error"

        )


        with st.sidebar.expander(
            "Debug"
        ):

            st.exception(e)





    page_router()







# ==============================================================================
# ENTRY POINT
# ==============================================================================


if __name__ == "__main__":


    main()
