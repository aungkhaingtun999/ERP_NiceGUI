# ==============================================================================
# app.py
# ERP ENTERPRISE APPLICATION CONTROLLER
# SAFE PAGE ROUTER
# MULTI-TENANT READY
# ==============================================================================

import os
import sys
import importlib.util

import streamlit as st


# ==============================================================================
# BASE PATH
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
# ERP CORE
# ==============================================================================

import erp_core


# ==============================================================================
# AUTH
# ==============================================================================

from auth import (
    login_page,
    is_authenticated,
)


# ==============================================================================
# SIDEBAR
# ==============================================================================

from sidebar import (
    show_sidebar,
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
# PAGE ALIASES
#
# Old / temporary profile routes are redirected to the new
# Multi-Tenant Profile page.
# ==============================================================================

PAGE_ALIASES = {

    "PROFILE": "13_Profile",

    "__PROFILE__": "13_Profile",

}


# ==============================================================================
# PAGE LOADER
# ==============================================================================

def load_page(
    page_id
):

    # ------------------------------------------------------------------
    # Normalize old page IDs
    # ------------------------------------------------------------------

    page_id = PAGE_ALIASES.get(
        page_id,
        page_id
    )

    # ------------------------------------------------------------------
    # Build page file path
    # ------------------------------------------------------------------

    page_file = os.path.join(
        BASE_DIR,
        "erp_pages",
        f"{page_id}.py"
    )

    # ------------------------------------------------------------------
    # File existence
    # ------------------------------------------------------------------

    if not os.path.exists(
        page_file
    ):

        st.error(
            f"Page file not found:\n{page_file}"
        )

        return

    try:

        module_name = (
            f"erp_pages.dynamic_{page_id}"
        )

        # --------------------------------------------------------------
        # Remove previous dynamic page module
        # --------------------------------------------------------------

        if module_name in sys.modules:

            del sys.modules[
                module_name
            ]

        # --------------------------------------------------------------
        # Load page specification
        # --------------------------------------------------------------

        spec = (
            importlib.util
            .spec_from_file_location(
                module_name,
                page_file
            )
        )

        if spec is None:

            raise ImportError(
                f"Cannot load page: {page_id}"
            )

        # --------------------------------------------------------------
        # Create module
        # --------------------------------------------------------------

        module = (
            importlib.util
            .module_from_spec(
                spec
            )
        )

        sys.modules[
            module_name
        ] = module

        # --------------------------------------------------------------
        # Execute module
        # --------------------------------------------------------------

        spec.loader.exec_module(
            module
        )

        # --------------------------------------------------------------
        # Page entry point
        # --------------------------------------------------------------

        if hasattr(
            module,
            "run"
        ):

            module.run()

        elif hasattr(
            module,
            "main"
        ):

            module.main()

        else:

            st.warning(
                f"{page_id}.py has no run() or main()"
            )

    except Exception as e:

        st.error(
            f"Page Load Error : {e}"
        )

        with st.expander(
            "Debug Trace"
        ):

            st.exception(e)


# ==============================================================================
# ROUTER
# ==============================================================================

def page_router():

    # ------------------------------------------------------------------
    # Authentication guard
    # ------------------------------------------------------------------

    if not st.session_state.get(
        "user"
    ):

        st.warning(
            "Please login first."
        )

        return

    # ------------------------------------------------------------------
    # Current page
    # ------------------------------------------------------------------

    page_id = st.session_state.get(
        "active_page",
        "1_POS"
    )

    # ------------------------------------------------------------------
    # Normalize legacy profile routes
    #
    # This protects users who already have PROFILE or __PROFILE__
    # stored in their Streamlit session.
    # ------------------------------------------------------------------

    normalized_page = PAGE_ALIASES.get(
        page_id,
        page_id
    )

    if normalized_page != page_id:

        st.session_state[
            "active_page"
        ] = normalized_page

        page_id = normalized_page

    # ------------------------------------------------------------------
    # Load normal ERP page
    # ------------------------------------------------------------------

    load_page(
        page_id
    )


# ==============================================================================
# MAIN
# ==============================================================================

def main():

    # ------------------------------------------------------------------
    # Initialize session
    # ------------------------------------------------------------------

    init_state()

    # ------------------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------------------

    if not is_authenticated():

        login_page()

        st.stop()

    # ------------------------------------------------------------------
    # SIDEBAR
    # ------------------------------------------------------------------

    try:

        show_sidebar()

    except Exception as e:

        st.sidebar.error(
            f"Sidebar Error : {e}"
        )

    # ------------------------------------------------------------------
    # PAGE
    # ------------------------------------------------------------------

    page_router()


# ==============================================================================
# START
# ==============================================================================

if __name__ == "__main__":

    main()
