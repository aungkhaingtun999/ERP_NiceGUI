# ==============================================================================
# erp_pages/inventory/product_search.py
# MOBILE INVENTORY v3
# Product Search Engine
# ==============================================================================


import streamlit as st

from database import get_products



def search_product(keyword):

    if not keyword:

        return None


    keyword = str(keyword).strip()


    products = get_products()


    for p in products:


        barcode = str(
            p.get("barcode", "")
        ).strip()


        sku = str(
            p.get("sku", "")
        ).strip()


        name = str(
            p.get("name", "")
        ).lower()



        # Barcode exact match

        if barcode == keyword:

            return p



        # SKU exact match

        if sku == keyword:

            return p



        # Product name search

        if keyword.lower() in name:

            return p



    return None
