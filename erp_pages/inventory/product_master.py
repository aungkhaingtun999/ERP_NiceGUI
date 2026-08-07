# ==============================================================================
# erp_pages/inventory/product_master.py
# ERP ENTERPRISE PRODUCT MASTER VIEW v1.1
#
# Inventory Tab 1
#
# Owner First Pricing Compatible
#
# ==============================================================================


import streamlit as st


from utils.ui import show_table




# ==============================================================================
# PRODUCT MASTER RENDER
# ==============================================================================


def render_product_master(
    products
):


    st.subheader(
        "📋 Product Master"
    )



    if not products:


        st.info(
            "No products found"
        )

        return




    # --------------------------------------------------------------------------
    # FILTER SUMMARY
    # --------------------------------------------------------------------------

    st.caption(
        f"Total Products : {len(products)}"
    )




    # --------------------------------------------------------------------------
    # TABLE DATA
    # --------------------------------------------------------------------------

    display_rows = []



    for p in products:


        display_rows.append({

            "ID":
            p.get("id"),


            "Product":
            p.get("name"),


            "SKU":
            p.get("sku"),


            "Barcode":
            p.get("barcode"),


            "Cost":
            p.get("purchase_price"),



            "Owner Price":
            p.get(
                "owner_selling_price"
            ),



            "Final Price":
            p.get(
                "final_selling_price",
                p.get(
                    "selling_price"
                )
            ),



            "Price Source":
            p.get(
                "price_source",
                "DEFAULT"
            ),



            "Markup %":
            p.get(
                "markup_percent",
                0
            ),



            "Stock":
            p.get(
                "available_qty",
                p.get(
                    "qty",
                    0
                )
            ),



            "Unit":
            p.get(
                "unit"
            ),



            "Status":
            "Active"
            if p.get(
                "is_active",
                True
            )
            else "Inactive"

        })




    # --------------------------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------------------------


    show_table(
        display_rows
    )
