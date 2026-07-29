# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v12.9 FINAL
#
# Responsibilities:
# - POS page controller
# - Authentication
# - Session initialization
# - Warehouse loading
# - Product rendering
# - Cart summary
# - Payment rendering
# - Receipt rendering
#
# Flow:
#
# LOGIN
#   ↓
# SESSION
#   ↓
# PRODUCT
#   ↓
# CART
#   ↓
# PAYMENT
#   ↓
# RECEIPT
#
# ==============================================================================


import pandas as pd
import streamlit as st



from erp_core import (
    get_default_warehouse_id
)



from .session import (
    init_pos_session
)



from .product import (
    render_products
)



from .cart import (
    calculate_subtotal,
    calculate_total_qty,
    get_cart_rows
)







from .payment import (
    render_payment
)



from .receipt import (
    render_receipt
)



from auth import (
    is_authenticated
)



from language import (
    language_selector
)





# ==============================================================================
# MONEY FORMAT
# ==============================================================================


def money(value):


    try:


        return f"{float(value):,.0f} MMK"


    except Exception:


        return "0 MMK"





# ==============================================================================
# POS MAIN RUN
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
    # WAREHOUSE
    # --------------------------------------------------------------------------


    warehouse_id = get_default_warehouse_id()



    if not warehouse_id:



        st.error(

            "Default warehouse not configured."

        )


        st.stop()







    # --------------------------------------------------------------------------
    # RECEIPT MODE
    # --------------------------------------------------------------------------


    if st.session_state.get(

        "show_receipt",

        False

    ):



        render_receipt()


        return







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

GLOBAL MARKUP

↓

FINAL SELLING PRICE


ERP POS FINAL PRICE ENGINE ACTIVE

"""

    )





    st.divider()







    # --------------------------------------------------------------------------
    # PRODUCT MODULE
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

            "🛒 Cart is empty."

        )


        return







    st.divider()



    st.subheader(

        "🛒 Cart Summary"

    )







    # --------------------------------------------------------------------------
    # CART TABLE
    # --------------------------------------------------------------------------


    rows = get_cart_rows(

        cart

    )



    if rows:



        cart_df = pd.DataFrame(

            rows

        )



        cart_df["Unit Price"] = (

            cart_df["Unit Price"]

            .apply(

                money

            )

        )



        cart_df["Amount"] = (

            cart_df["Amount"]

            .apply(

                money

            )

        )



        st.dataframe(

            cart_df,

            use_container_width=True,

            hide_index=True

        )








# --------------------------------------------------------------------------
# CART TOTAL
# --------------------------------------------------------------------------

subtotal = calculate_subtotal(
    cart
)


total_qty = calculate_total_qty(
    cart
)


st.success(

f"""

Items :

{len(cart)}



Total Qty :

{total_qty}



Subtotal :

{money(subtotal)}



🧾 Tax :

Controlled by ERP Settings



💳 Final Total :

Calculated in Payment Module


"""

)
    # --------------------------------------------------------------------------
    # TAX FROM SETTINGS
    # --------------------------------------------------------------------------

    tax_rate = get_default_tax_rate()


    tax_amount = (

        subtotal

        *

        tax_rate

        /

        100

    )



    st.success(

        f"""

Items :

{len(cart)}



Total Qty :

{total_qty}



Subtotal :

{money(subtotal)}



🧾 System Tax Rate :

{tax_rate:.2f}%



Tax Amount :

{money(tax_amount)}



Grand Total :

{money(subtotal + tax_amount)}

"""

    )







    # --------------------------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------------------------


    render_payment(

        warehouse_id

    )
