# ==============================================================================
# erp_pages/pos/payment.py
# ERP ENTERPRISE POS PAYMENT ENGINE v12.1
#
# Cart
#   ↓
# Tax
#   ↓
# Discount
#   ↓
# Payment
#   ↓
# Checkout RPC
#
# ==============================================================================


import streamlit as st



from .cart import (
    calculate_subtotal
)



from .checkout import (
    process_checkout
)



from .session import (
    start_processing,
    stop_processing
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
# TAX
# ==============================================================================


def calculate_tax(
    subtotal,
    tax_rate
):


    return round(

        float(subtotal)
        *
        float(tax_rate)
        /
        100,

        2

    )







# ==============================================================================
# TOTAL
# ==============================================================================


def calculate_total(

    subtotal,

    tax_amount,

    discount

):


    return max(

        0,

        float(subtotal)
        +
        float(tax_amount)
        -
        float(discount)

    )







# ==============================================================================
# PAYMENT UI
# ==============================================================================


def render_payment(

    warehouse_id

):


    cart = st.session_state.get(

        "cart",

        []

    )



    if not cart:

        return







    st.divider()


    st.subheader(

        "💰 Payment"

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



    tax_amount = calculate_tax(

        subtotal,

        tax_rate

    )







    # ==========================================================================
    # DISCOUNT
    # ==========================================================================


    policy = str(

        st.session_state.get(

            "discount_policy",

            "allowed"

        )

    ).lower()



    if policy == "restricted":


        discount = 0


        st.warning(

            "Discount restricted"

        )


    else:


        discount = st.number_input(

            "Discount",

            min_value=0.0,

            value=0.0,

            step=100.0

        )







    total = calculate_total(

        subtotal,

        tax_amount,

        discount

    )







    st.success(

        f"""

Subtotal :

{money(subtotal)}



Tax :

{money(tax_amount)}



Discount :

{money(discount)}



====================

TOTAL :

{money(total)}

====================

        """

    )







    # ==========================================================================
    # PAYMENT METHOD
    # ==========================================================================


    payment_method = st.selectbox(

        "Payment Method",

        [

            "CASH",

            "CARD",

            "MOBILE"

        ]

    )



    st.session_state.payment_method = payment_method







    # ==========================================================================
    # RECEIVED
    # ==========================================================================


    if payment_method == "CASH":


        received = st.number_input(

            "Received Amount",

            min_value=float(total),

            value=float(total),

            step=100.0

        )


    else:


        received = total







    st.session_state.received_amount = received





    change = max(

        0,

        received - total

    )



    st.info(

        f"Change : {money(change)}"

    )







    # ==========================================================================
    # CHECKOUT
    # ==========================================================================


    if st.button(

        "✅ Confirm Sale",

        use_container_width=True,

        disabled=st.session_state.get(

            "processing",

            False

        )

    ):



        start_processing()



        try:



            cashier_id = (

                st.session_state.get(

                    "user_id"

                )

                or

                st.session_state.get(

                    "id"

                )

            )



            if not cashier_id:


                st.error(

                    "Cashier ID missing"

                )


                stop_processing()

                return







            result = process_checkout(

                cart=cart,

                paid_amount=received,

                warehouse_id=warehouse_id,

                cashier_id=cashier_id,

                payment_method=payment_method,

                tax_rate=tax_rate,

                discount=discount

            )







            if result.get(

                "success",

                False

            ):



                st.session_state.sale_data = result.get(

                    "data",

                    {}

                )



                st.session_state.show_receipt = True



                stop_processing()



                st.rerun()







            else:


                st.error(

                    result.get(

                        "message",

                        "Checkout Failed"

                    )

                )



                stop_processing()







        except Exception as e:


            stop_processing()


            st.error(

                f"Payment Error : {e}"

            )
