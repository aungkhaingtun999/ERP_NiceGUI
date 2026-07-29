# ==============================================================================
# erp_pages/pos/payment.py
# ERP ENTERPRISE POS PAYMENT MODULE v12.9 FINAL
#
# Responsibilities:
# - Payment input
# - Tax calculation
# - Discount handling
# - Checkout trigger
# - Receipt preparation
#
# Flow:
#
# CART
#   ↓
# SUBTOTAL
#   ↓
# TAX + DISCOUNT
#   ↓
# PAYMENT
#   ↓
# CHECKOUT RPC
#   ↓
# RECEIPT
#
# ==============================================================================


import streamlit as st


from .session import (
    start_processing,
    stop_processing
)


from .checkout import (
    process_checkout
)


from .cart import (
    calculate_subtotal
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
# TOTAL CALCULATION
# ==============================================================================


def calculate_total(

    subtotal,

    tax_rate,

    discount

):


    tax_amount = (

        float(subtotal)

        *

        float(tax_rate)

        /

        100

    )


    total = (

        float(subtotal)

        +

        tax_amount

        -

        float(discount)

    )


    if total < 0:

        total = 0



    return {


        "tax_amount":

            round(

                tax_amount,

                2

            ),



        "grand_total":

            round(

                total,

                2

            )

    }





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

        "💳 Payment"

    )





    # --------------------------------------------------
    # SUBTOTAL
    # --------------------------------------------------


    subtotal = calculate_subtotal(

        cart

    )



    tax_rate = float(

        st.session_state.get(

            "tax_rate",

            0

        )

    )





    # --------------------------------------------------
    # TAX
    # --------------------------------------------------


    tax_rate = st.number_input(


        "Tax Rate (%)",


        min_value=0.0,


        max_value=100.0,


        value=float(tax_rate),


        step=0.5,


        key="payment_tax_rate"

    )



    st.session_state.tax_rate = tax_rate





    # --------------------------------------------------
    # DISCOUNT
    # --------------------------------------------------


    discount_policy = st.session_state.get(

        "discount_policy",

        "allowed"

    )



    discount = 0.0



    if discount_policy == "allowed":



        discount = st.number_input(


            "Discount Amount (MMK)",


            min_value=0.0,


            value=float(

                st.session_state.get(

                    "discount",

                    0

                )

            ),


            step=100.0,


            key="payment_discount"

        )



        st.session_state.discount = discount



    else:


        st.info(

            "Discount is restricted by system policy."

        )







    totals = calculate_total(

        subtotal,

        tax_rate,

        discount

    )





    tax_amount = totals[

        "tax_amount"

    ]


    grand_total = totals[

        "grand_total"

    ]





    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------


    st.success(

        f"""

Subtotal:

{money(subtotal)}



Tax:

{money(tax_amount)}



Discount:

{money(discount)}



====================



TOTAL:

{money(grand_total)}

"""

    )





    # --------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------


    payment_method = st.selectbox(


        "Payment Method",


        [

            "CASH",

            "BANK",

            "MOBILE",

            "CREDIT"

        ],


        index=0

    )



    st.session_state.payment_method = payment_method





    # --------------------------------------------------
    # RECEIVED MONEY
    # --------------------------------------------------


    received = st.number_input(


        "Received Amount",


        min_value=0.0,


        value=float(

            st.session_state.get(

                "received_amount",

                0

            )

        ),


        step=100.0

    )



    st.session_state.received_amount = received





    change = max(

        0,

        received - grand_total

    )



    st.info(

        f"""

Received:

{money(received)}



Change:

{money(change)}

"""

    )







    # --------------------------------------------------
    # CHECKOUT BUTTON
    # --------------------------------------------------


    if st.button(


        "✅ Complete Sale",


        use_container_width=True,


        type="primary"


    ):



        if received < grand_total:


            st.error(

                "Insufficient payment amount."

            )


            return





        if st.session_state.get(

            "processing",

            False

        ):


            st.warning(

                "Processing..."

            )


            return





        start_processing()



        try:



            result = process_checkout(


                cart=cart,


                paid_amount=received,


                warehouse_id=warehouse_id,


                cashier_id=st.session_state.get(

                    "user",

                    {}

                ).get(

                    "id"

                ),


                payment_method=payment_method,


                tax_rate=tax_rate,


                discount=discount


            )





            if result.get(

                "success",

                False

            ):



                st.session_state.sale_data = result.get(

                    "data"

                )



                st.session_state.show_receipt = True



                st.success(

                    "Sale completed successfully."

                )



                st.rerun()





            else:



                st.error(

                    result.get(

                        "message",

                        "Checkout Failed"

                    )

                )



        except Exception as e:



            st.error(

                f"Checkout Error : {e}"

            )



        finally:



            stop_processing()
