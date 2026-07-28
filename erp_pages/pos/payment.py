# ==============================================================================
# erp_pages/pos/payment.py
# ERP ENTERPRISE POS PAYMENT ENGINE v12.0
#
# RESPONSIBILITY
#
# Cart
#   ↓
# Tax
#   ↓
# Discount
#   ↓
# Payment
#   ↓
# Checkout
#
# ==============================================================================


import streamlit as st



from .cart import (
    calculate_subtotal
)


from .checkout import (
    process_checkout
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
# TAX CALCULATION
# ==============================================================================


def calculate_tax(
    subtotal,
    tax_rate
):

    return round(

        subtotal
        *
        float(tax_rate)
        /
        100,

        2

    )





# ==============================================================================
# TOTAL CALCULATION
# ==============================================================================


def calculate_total(

    subtotal,

    tax_amount,

    discount

):

    return max(

        0,

        subtotal
        +
        tax_amount
        -
        discount

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





    # ==============================================================
    # CART TOTAL
    # ==============================================================

    subtotal = calculate_subtotal(

        cart

    )





    # ==============================================================
    # TAX
    # ==============================================================

    tax_rate = st.session_state.get(

        "tax_rate",

        0

    )


    tax_amount = calculate_tax(

        subtotal,

        tax_rate

    )





    # ==============================================================
    # DISCOUNT
    # ==============================================================


    policy = str(

        st.session_state.get(

            "discount_policy",

            "allowed"

        )

    ).lower()



    if policy == "restricted":


        discount = st.number_input(

            "Discount",

            min_value=0.0,

            value=0.0,

            disabled=True

        )


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





    grand_total = calculate_total(

        subtotal,

        tax_amount,

        discount

    )





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

====================

        """

    )





    # ==============================================================
    # PAYMENT METHOD
    # ==============================================================


    payment_method = st.selectbox(

        "Payment Method",

        [

            "CASH",

            "CARD",

            "MOBILE"

        ]

    )





    # ==============================================================
    # RECEIVED
    # ==============================================================


    if payment_method == "CASH":


        received = st.number_input(

            "Received Amount",

            min_value=float(grand_total),

            value=float(grand_total),

            step=100.0

        )


    else:


        received = grand_total





    change = max(

        0,

        received - grand_total

    )





    st.write(

        f"Change : {money(change)}"

    )





    # ==============================================================
    # CONFIRM SALE
    # ==============================================================


    if st.button(

        "✅ Confirm Sale",

        use_container_width=True,

        disabled=st.session_state.get(

            "processing",

            False

        )

    ):


        st.session_state.processing = True



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

                st.session_state.processing = False

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


                st.session_state.processing = False


                st.rerun()



            else:


                st.error(

                    result.get(

                        "message",

                        "Checkout Failed"

                    )

                )


                st.session_state.processing = False





        except Exception as e:


            st.session_state.processing = False


            st.error(

                f"Payment Error : {e}"

            )
