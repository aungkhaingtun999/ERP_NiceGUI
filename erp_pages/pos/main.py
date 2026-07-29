# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v12.6
# CLEAN SINGLE RENDER + TAX ENGINE
# ==============================================================================


import streamlit as st
import pandas as pd


from erp_core import (
    get_default_warehouse_id,
    get_setting
)


from .session import init_pos_session
from .product import render_products
from .cart import calculate_subtotal
from .payment import render_payment
from .receipt import render_receipt


from auth import is_authenticated

from language import language_selector





# ==============================================================================
# MONEY
# ==============================================================================

def money(value):

    try:

        return f"{float(value):,.0f} MMK"

    except Exception:

        return "0 MMK"






# ==============================================================================
# TAX LOAD
# ==============================================================================

def load_tax_setting():

    try:

        tax = get_setting(
            "DEFAULT_TAX_RATE",
            0
        )

        return float(tax or 0)


    except Exception:

        return 0





# ==============================================================================
# POS RUN
# ==============================================================================

def run():


    # --------------------------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------------------------

    try:

        language_selector()

    except Exception:

        pass




    # --------------------------------------------------------------------------
    # AUTH
    # --------------------------------------------------------------------------

    if not is_authenticated():

        st.warning(
            "Please login first."
        )

        st.stop()





    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------

    init_pos_session()





    # --------------------------------------------------------------------------
    # TAX INITIALIZE
    # --------------------------------------------------------------------------

    if (

        "tax_loaded"

        not

        in

        st.session_state

    ):


        st.session_state.tax_rate = load_tax_setting()

        st.session_state.tax_loaded = True






    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    warehouse_id = get_default_warehouse_id()


    if not warehouse_id:

        st.error(
            "Default warehouse not configured."
        )

        st.stop()






    # --------------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------------

    st.title(
        "🛒 ERP Enterprise POS"
    )


    st.caption(
"""
OWNER PRICE
↓
PRODUCT MARKUP
↓
CATEGORY MARKUP
↓
SYSTEM PRICE

POS uses FINAL SELLING PRICE
"""
    )





    # --------------------------------------------------------------------------
    # RECEIPT
    # --------------------------------------------------------------------------

    if st.session_state.get(
        "show_receipt",
        False
    ):


        render_receipt()

        return






    # --------------------------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------------------------

    render_products(

        warehouse_id

    )






    # --------------------------------------------------------------------------
    # CART
    # --------------------------------------------------------------------------

    cart = st.session_state.get(

        "cart",

        []

    )



    if not cart:

        st.info(
            "Cart is empty."
        )

        return






    st.divider()


    st.subheader(
        "🛒 Cart Summary"
    )





    # ==========================================================================
    # CART TABLE
    # ==========================================================================

    rows=[]



    for item in cart:


        qty=int(

            item.get(

                "qty",

                0

            )

        )


        price=float(

            item.get(

                "unit_price",

                item.get(

                    "selling_price",

                    0

                )

            )

        )



        rows.append(

            {

                "Product":

                    item.get(

                        "name",

                        ""

                    ),


                "SKU":

                    item.get(

                        "sku",

                        ""

                    ),


                "Qty":

                    qty,


                "Price Source":

                    item.get(

                        "price_source",

                        "SYSTEM"

                    ),


                "Unit Price":

                    money(price),


                "Amount":

                    money(

                        price * qty

                    )

            }

        )





    st.dataframe(

        pd.DataFrame(rows),

        use_container_width=True,

        hide_index=True

    )







    # ==========================================================================
    # TOTAL
    # ==========================================================================


    subtotal = calculate_subtotal(

        cart

    )


    tax_rate = st.session_state.get(

        "tax_rate",

        0

    )


    tax_amount = round(

        subtotal

        *

        float(tax_rate)

        /

        100,

        2

    )



    total = subtotal + tax_amount





    total_qty=sum(

        int(

            item.get(

                "qty",

                0

            )

        )

        for item in cart

    )






    st.info(

f"""
Items      : {len(cart)}

Total Qty  : {total_qty}

Subtotal   : {money(subtotal)}

Tax Rate   : {tax_rate:.2f} %

Tax Amount : {money(tax_amount)}

---------------------

Total      : {money(total)}

"""
    )







    # --------------------------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------------------------

    render_payment(

        warehouse_id

    )
