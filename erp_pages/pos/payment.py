# ==============================================================================
# erp_pages/pos/payment.py
# ERP ENTERPRISE POS PAYMENT MODULE v12.9 FINAL
#
# Responsibilities:
# - Payment input
# - Discount handling
# - Checkout trigger
# - Receipt preparation
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


from .engine import (
    get_default_tax_rate
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
    # SUBTOTAL & TAX FROM SETTINGS (AUTOMATIC)
    # --------------------------------------------------


    subtotal = calculate_subtotal(

        cart

    )



    tax_rate = get_default_tax_rate()



    tax_amount = (

        subtotal

        *

        tax_rate

        /

        100

    )





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





    grand_total = max(

        0,

        subtotal

        +

        tax_amount

        -

        float(discount)

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
