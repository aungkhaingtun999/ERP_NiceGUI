# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v12.4
# CLEAN SINGLE RENDER VERSION
# ==============================================================================


import streamlit as st



from erp_core import get_default_warehouse_id


from .session import init_pos_session
from .product import render_products
from .cart import calculate_subtotal
from .payment import render_payment
from .receipt import render_receipt



from auth import is_authenticated


from language import language_selector




# ==============================================================================
# MONEY FORMAT
# ==============================================================================

def money(value):

    try:

        return f"{float(value):,.0f} MMK"


    except Exception:

        return "0 MMK"




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
    # CART DETAIL TABLE
    # ==========================================================================

    import pandas as pd


    cart_rows = []


    for item in cart:


        qty = int(
            item.get(
                "qty",
                0
            )
        )


        price = float(

            item.get(

                "unit_price",

                item.get(

                    "selling_price",

                    0

                )

            )

        )


        cart_rows.append(

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



    if cart_rows:


        cart_df = pd.DataFrame(
            cart_rows
        )


        st.dataframe(

            cart_df,

            use_container_width=True,

            hide_index=True

        )



    # ==========================================================================
    # TOTAL
    # ==========================================================================


    subtotal = calculate_subtotal(
        cart
    )


    total_qty = sum(

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
"""

    )





    # --------------------------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------------------------

    render_payment(
        warehouse_id
    )



# ==============================================================================
# END
# ==============================================================================
