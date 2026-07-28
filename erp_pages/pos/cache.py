# ==============================================================================
# erp_pages/pos/cache.py
# ERP ENTERPRISE POS CACHE CONTROLLER v12.0
#
# POS Cache
# Inventory Refresh
# Product Refresh
# Streamlit Cache Control
#
# ==============================================================================


import streamlit as st


from erp_core.context import (
    CacheManager
)





# ==============================================================================
# INVENTORY CACHE
# ==============================================================================

def refresh_inventory():

    """
    After sale / transfer / adjustment
    """

    return CacheManager.bump(
        "inventory_version"
    )







# ==============================================================================
# PRODUCT CACHE
# ==============================================================================

def refresh_products():

    """
    Product price / stock refresh
    """

    return CacheManager.bump(
        "product_version"
    )







# ==============================================================================
# SALES CACHE
# ==============================================================================

def refresh_sales():

    return CacheManager.bump(
        "sales_version"
    )







# ==============================================================================
# FULL POS REFRESH
# ==============================================================================

def refresh_pos():

    """
    After checkout success
    """

    refresh_inventory()

    refresh_products()

    refresh_sales()


    # Streamlit local cache clear

    st.cache_data.clear()







# ==============================================================================
# GET CACHE VERSION
# ==============================================================================

def get_inventory_version():

    return CacheManager.get_version(
        "inventory_version"
    )





def get_product_version():

    return CacheManager.get_version(
        "product_version"
    )





def get_sales_version():

    return CacheManager.get_version(
        "sales_version"
    )







# ==============================================================================
# CLEAR SESSION CART CACHE
# ==============================================================================

def clear_pos_session():

    keys = [

        "cart",

        "sale_data",

        "show_receipt",

        "processing"

    ]


    for key in keys:

        if key in st.session_state:

            del st.session_state[key]
