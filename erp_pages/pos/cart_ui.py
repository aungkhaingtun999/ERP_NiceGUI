# ==============================================================================
# erp_pages/pos/cart_ui.py
# ERP ENTERPRISE POS CART UI v1.1
#
# - Center Button Alignment
# - Compact Cart Row
# - Button Styling Ready
# ==============================================================================


import streamlit as st


from .cart import (
    increase_quantity,
    decrease_quantity,
    remove_from_cart
)



# ==============================================================================
# CART UI STYLE
# ==============================================================================


def cart_button_style():

    st.markdown(
        """
        <style>

        div[data-testid="stHorizontalBlock"] div.stButton > button {

            display:flex;
            justify-content:center;
            align-items:center;

            height:2rem;
            width:100%;

            font-size:16px;

            padding:0;

        }


        </style>
        """,
        unsafe_allow_html=True
    )



# ==============================================================================
# CART CONTROL
# ==============================================================================


def render_cart_control(cart):


    if not cart:

        return



    cart_button_style()



    st.caption(
        "Quantity Control"
    )



    for index, item in enumerate(cart):


        col1, col2, col3, col4 = st.columns(
            [5, 1, 1, 1]
        )



        with col1:

            st.write(
                f"{item.get('name','')}  x {item.get('qty',0)}"
            )



        with col2:

            if st.button(
                "➕",
                key=f"cart_plus_{index}",
                use_container_width=True
            ):

                increase_quantity(
                    cart,
                    index
                )

                st.session_state.cart = cart

                st.rerun()



        with col3:

            if st.button(
                "➖",
                key=f"cart_minus_{index}",
                use_container_width=True
            ):

                decrease_quantity(
                    cart,
                    index
                )

                st.session_state.cart = cart

                st.rerun()



        with col4:

            if st.button(
                "🗑",
                key=f"cart_delete_{index}",
                use_container_width=True
            ):

                remove_from_cart(
                    cart,
                    index
                )

                st.session_state.cart = cart

                st.rerun()
