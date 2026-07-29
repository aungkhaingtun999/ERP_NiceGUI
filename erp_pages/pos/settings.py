# ==============================================================================
# erp_pages/pos/settings.py
# ERP ENTERPRISE POS SETTINGS MODULE v12.0
#
# POS CONFIGURATION
#
# DEFAULT TAX RATE
# DISCOUNT POLICY
#
# settings table
#       ↓
# POS SESSION
#       ↓
# PAYMENT ENGINE
#       ↓
# RECEIPT
#
# ==============================================================================


import streamlit as st


from erp_core import get_setting


# ==============================================================================
# MONEY SAFE
# ==============================================================================

def safe_float(value, default=0):

    try:

        return float(value)

    except Exception:

        return default





# ==============================================================================
# LOAD POS SETTINGS
# ==============================================================================

def load_pos_settings():


    # --------------------------------------------------------------
    # TAX
    # --------------------------------------------------------------

    try:

        tax_rate = get_setting(
            "DEFAULT_TAX_RATE",
            0
        )


        st.session_state.tax_rate = safe_float(
            tax_rate
        )


    except Exception:


        st.session_state.tax_rate = 0





    # --------------------------------------------------------------
    # DISCOUNT POLICY
    # --------------------------------------------------------------

    try:

        policy = get_setting(
            "DISCOUNT_POLICY",
            "allowed"
        )


        st.session_state.discount_policy = str(
            policy
        ).lower()


    except Exception:


        st.session_state.discount_policy = "allowed"






# ==============================================================================
# SETTINGS DISPLAY
# ==============================================================================

def render_pos_settings():


    load_pos_settings()


    st.subheader(
        "⚙️ POS Settings"
    )



    st.info(

        f"""
Tax Rate :

{st.session_state.get('tax_rate',0):.2f}%


Discount Policy :

{st.session_state.get('discount_policy','allowed')}

"""

    )



# ==============================================================================
# END
# ==============================================================================