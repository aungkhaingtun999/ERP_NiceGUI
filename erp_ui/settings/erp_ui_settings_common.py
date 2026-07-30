# ==============================================================================
# erp_ui/settings/common.py
# ERP SETTINGS UI COMMON HELPERS
# ==============================================================================


import streamlit as st


# ==============================================================================
# SAVE RESULT HANDLER
# ==============================================================================


def show_save_success(message):

    st.success(message)



def show_save_error(message):

    st.error(message)



# ==============================================================================
# NUMBER SAFE CONVERTER
# ==============================================================================


def safe_float(value, default=0.0):

    try:

        return float(value)

    except Exception:

        return default



# ==============================================================================
# BOOL SAFE CONVERTER
# ==============================================================================


def safe_bool(value, default=False):

    if value is None:

        return default


    if isinstance(value, bool):

        return value


    return str(value).lower() in (

        "true",
        "1",
        "yes"

    )