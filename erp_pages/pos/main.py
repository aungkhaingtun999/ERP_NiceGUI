# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v13.0 COMPACT EDITION
#
# Responsibilities:
# - POS Controller
# - Compact Layout
# - Product / Cart Side By Side
# - Payment Integration
#
# Flow:
#
# LOGIN
#   ↓
# SESSION
#   ↓
# PRODUCT + CART
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
    get_cart_rows,
    remove_from_cart,
    increase_quantity,
    decrease_quantity
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
# MONEY
# ==============================================================================


def money(value):

    try:

        return f"{float(value):,.0f} MMK"


    except Exception:

        return "0 MMK"







# ==============================================================================
# RUN POS
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
        "Fast Compact Sales System v13"
    )


    st.divider()





    # ==========================================================================
    # MAIN COMPACT AREA
    #
    # LEFT 60%
    # PRODUCT
    #
    # RIGHT 40%
    # CART
    #
    # ==========================================================================


    product_col, cart_col = st.columns(
        [6,4]
    )





    # ==========================================================================
    # PRODUCT PANEL
    # ==========================================================================


    with product_col:


        st.subheader(
            "📦 Products"
        )


        render_products(
            warehouse_id
        )





    # ==========================================================================
    # CART PANEL START
    # ==========================================================================


    with cart_col:


        st.subheader(
            "🛒 Cart"
        )


        cart = st.session_state.get(
            "cart",
            []
        )


        if not cart:


            st.info(
                "Cart is empty."
            )


        else:


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

                    height=250,

                    use_container_width=True,

                    hide_index=True

                )


# ==============================================================================
# CART ITEM CONTROL (COMPACT)
# ==============================================================================


        if cart:


            st.divider()


            st.caption(
                "Quantity Control"
            )



            for index, item in enumerate(cart):


                c1, c2, c3, c4 = st.columns(
                    [5,1,1,1]
                )



                with c1:


                    st.write(

                        f"{item.get('name','')} "
                        f"x {item.get('qty',0)}"

                    )



                with c2:


                    if st.button(

                        "➕",

                        key=f"compact_add_{index}"

                    ):


                        increase_quantity(

                            cart,

                            index

                        )


                        st.session_state.cart = cart


                        st.rerun()





                with c3:


                    if st.button(

                        "➖",

                        key=f"compact_minus_{index}"

                    ):


                        decrease_quantity(

                            cart,

                            index

                        )


                        st.session_state.cart = cart


                        st.rerun()





                with c4:


                    if st.button(

                        "🗑",

                        key=f"compact_remove_{index}"

                    ):


                        remove_from_cart(

                            cart,

                            index

                        )


                        st.session_state.cart = cart


                        st.rerun()








# ==============================================================================
# PAYMENT AREA
# ==============================================================================


    cart = st.session_state.get(

        "cart",

        []

    )



    if not cart:


        return






    st.divider()



    st.subheader(

        "💳 Payment"

    )



    render_payment(

        warehouse_id

    )
