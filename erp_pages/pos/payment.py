# ==============================================================================
# erp_pages/pos/payment.py
# ERP ENTERPRISE POS PAYMENT MODULE v12.9 TAX SETTINGS CONTROLLED
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



    # ==========================================================
    # TAX FROM ERP SETTINGS
    # ==========================================================


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




    st.info(

f"""

🧾 ERP Tax Rate

{tax_rate:.2f}%



Tax Amount

{money(tax_amount)}

"""

    )




    # ==========================================================
    # DISCOUNT
    # ==========================================================


    discount = st.number_input(

        "Discount Amount (MMK)",

        min_value=0.0,

        value=float(

            st.session_state.get(

                "discount",

                0

            )

        ),

        step=100.0

    )



    st.session_state.discount = discount





    grand_total = max(

        0,

        subtotal

        +

        tax_amount

        -

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



Total Payable :

{money(grand_total)}

"""

    )




    # ==========================================================
    # PAYMENT METHOD
    # ==========================================================


    payment_method = st.selectbox(

        "Payment Method",

        [

            "CASH",

            "BANK",

            "MOBILE",

            "CREDIT"

        ]

    )


    st.session_state.payment_method = payment_method





    # ==========================================================
    # RECEIVED
    # ==========================================================


    received = st.number_input(

        "Received Amount",

        min_value=0.0,

        step=100.0

    )



    change = max(

        0,

        received - grand_total

    )



    st.info(

f"""

Received :

{money(received)}



Change :

{money(change)}

"""

    )





    # ==========================================================
    # CHECKOUT
    # ==========================================================


    if st.button(

        "✅ Complete Sale",

        use_container_width=True,

        type="primary"

    ):



        if received < grand_total:


            st.error(

                "Insufficient payment."

            )

            return



        start_processing()



        try:


            result = process_checkout(

                cart=cart,

                paid_amount=received,

                warehouse_id=warehouse_id,

                cashier_id=

                    st.session_state.get(

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


    sale_data = result.get(
        "data",
        {}
    )


    # ==================================================
    # RECEIPT DATA COMPLETE MAPPING
    # ==================================================

    sale_data.update({

        "subtotal": subtotal,

        "discount": discount,

        "tax": tax_amount,

        "tax_rate": tax_rate,

        "total": grand_total,

        "paid_amount": received,

        "change_amount": change,

        "payment_method": payment_method,

        "items": cart

    })


    st.session_state.sale_data = sale_data


    st.session_state.show_receipt = True


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
