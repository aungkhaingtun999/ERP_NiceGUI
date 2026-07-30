# ==============================================================================
# app.py
# ERP ENTERPRISE APPLICATION CONTROLLER
# SAFE PAGE ROUTER v30.15
# ==============================================================================

import os
import sys
import importlib.util

import streamlit as st
# ERP CORE INITIALIZE
import erp_core


# ==============================================================================
# PAGE CONFIG
# MUST BE FIRST STREAMLIT COMMAND
# ==============================================================================
st.set_page_config(
    page_title="Myanmar ERP Enterprise",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==============================================================================
# PATH
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
# CORE IMPORT
# ==============================================================================
from auth import (
    login_page,
    is_authenticated
)

from sidebar import (
    show_sidebar
)


# ==============================================================================
# SESSION
# ==============================================================================
def init_state():
    defaults = {
        "user": None,
        "active_page": "1_POS",
        "language": "English",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==============================================================================
# PAGE LOADER
# ==============================================================================
def load_page(page_id):
    page_file = os.path.join(
        BASE_DIR,
        "erp_pages",
        f"{page_id}.py"
    )

    if not os.path.exists(page_file):
        st.error(
            f"Page file not found:\n{page_file}"
        )
        return

    try:
        module_name = f"erp_pages.dynamic_{page_id}"

        # Remove old cached module
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(
            module_name,
            page_file
        )

        if spec is None:
            raise ImportError(
                f"Cannot load {page_id}"
            )

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        spec.loader.exec_module(module)

        # --------------------------------------------------
        # ONE ENTRY ONLY
        # --------------------------------------------------
        if hasattr(module, "run"):
            module.run()
        elif hasattr(module, "main"):
            module.main()
        else:
            st.warning(
                f"{page_id}.py has no run() or main()"
            )

    except Exception as e:
        st.error(
            f"Page Load Error : {e}"
        )
        with st.expander("Debug Trace"):
            st.exception(e)


# ==============================================================================
# ROUTER
# ==============================================================================
def page_router():
    if not st.session_state.get("user"):
        st.warning(
            "Please login first."
        )
        return

    page_id = st.session_state.get(
        "active_page",
        "1_POS"
    )

    load_page(page_id)


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    init_state()

    # LOGIN
    if not is_authenticated():
        login_page()
        st.stop()

    # SIDEBAR
    try:
        show_sidebar()
    except Exception as e:
        st.sidebar.error(
            f"Sidebar Error : {e}"
        )

    # PAGE
    page_router()


# ==============================================================================
# START
# ==============================================================================
if __name__ == "__main__":
    main()
