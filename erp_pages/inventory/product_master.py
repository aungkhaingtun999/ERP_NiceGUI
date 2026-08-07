# ==============================================================================
# erp_pages/inventory/product_master.py
# ERP ENTERPRISE PRODUCT MASTER VIEW v1.0
#
# Inventory Tab 1
#
# Responsibilities:
# - Product List Display
# - Inventory Master Table
#
# ==============================================================================


import streamlit as st



from utils.ui import (
    show_table
)





# ==============================================================================
# PRODUCT MASTER RENDER
# ==============================================================================


def render_product_master(

    products

):


    st.subheader(

        "📋 Product Master"

    )




    # --------------------------------------------------------------------------
    # DATA CHECK
    # --------------------------------------------------------------------------


    if not products:


        st.info(

            "No products found"

        )


        return





    # --------------------------------------------------------------------------
    # DISPLAY TABLE
    # --------------------------------------------------------------------------


    show_table(

        products

    )