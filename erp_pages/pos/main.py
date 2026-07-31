# ==============================================================================
# erp_pages/pos/main.py
# ERP ENTERPRISE POS MAIN CONTROLLER v13.1 FINAL COMPACT
#
# UI:
# - Compact POS Layout
# - Product + Cart Side Layout
# - Minimal Vertical Space
#
# Logic:
# - Existing Checkout
# - Existing Payment Engine
# - Existing Pricing Engine
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
# COMPACT CSS
# ==============================================================================


def compact_css():

    st.markdown(
        """
        <style>

        .block-container {

            padding-top: 0.8rem;

            padding-bottom: 0.8rem;

        }


        div[data-testid="stVerticalBlock"] {

            gap: 0.25rem;

        }


        div[data-testid="stHorizontalBlock"] {

            gap: 0.4rem;

        }


        h1 {

            margin-bottom:0.2rem;

            font-size:1.8rem;

        }


        h2 {

            margin-bottom:0.1rem;

            font-size:1.3rem;

        }


        h3 {

            margin-bottom:0.1rem;

            font-size:1.1rem;

        }


        .stButton button {

            min-height:2rem;

            padding-top:0.1rem;

            padding-bottom:0.1rem;

        }


        </style>
        """,

        unsafe_allow_html=True

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
# MAIN RUN
# ==============================================================================


def run():


    # --------------------------------------------------------------------------
    # UI COMPACT MODE
    # --------------------------------------------------------------------------

    compact_css()





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
    # RECEIPT
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

    st.markdown(

        "### 🛒 ERP Enterprise POS"

    )


    st.caption(

        "Fast Compact Sales System v13.1"

    )






    # ==========================================================================
    # PRODUCT + CART AREA
    # ==========================================================================


    product_area, cart_area = st.columns(

        [6,4]

    )





    # ==========================================================================
    # PRODUCT
    # ==========================================================================


    with product_area:


        st.markdown(

            "**📦 Products**"

        )


        render_products(

            warehouse_id
        )

    # ==========================================================================
    # CART PANEL
    # ==========================================================================


    with cart_area:


        st.markdown(

            "**🛒 Cart**"

        )


        cart = st.session_state.get(

            "cart",

            []

        )



        if not cart:


            st.info(

                "Cart empty"

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

                    height=220,

                    use_container_width=True,

                    hide_index=True

                )





            # ------------------------------------------------------------------
            # QUICK CART CONTROL
            # ------------------------------------------------------------------


            st.caption(

                "Qty Control"

            )



            for index, item in enumerate(cart):


                c1, c2, c3, c4 = st.columns(

                    [5,1,1,1]

                )



                with c1:

                    st.write(

                        f"{item.get('name','')} "

                        f"x{item.get('qty',0)}"

                    )



                with c2:


                    if st.button(

                        "+",

                        key=f"plus_{index}"

                    ):


                        increase_quantity(

                            cart,

                            index

                        )


                        st.session_state.cart = cart


                        st.rerun()





                with c3:


                    if st.button(

                        "-",

                        key=f"minus_{index}"

                    ):


                        decrease_quantity(

                            cart,

                            index

                        )


                        st.session_state.cart = cart


                        st.rerun()





                with c4:


                    if st.button(

                        "X",

                        key=f"del_{index}"

                    ):


                        remove_from_cart(

                            cart,

                            index

                        )


                        st.session_state.cart = cart


                        st.rerun()





    # ==========================================================================
    # PAYMENT
    #
    # IMPORTANT:
    # Do not add st.subheader here.
    # payment.py already owns Payment UI.
    # ==========================================================================



    cart = st.session_state.get(

        "cart",

        []

    )



    if cart:


        render_payment(

            warehouse_id

        )
