# ==============================================================================
# erp_pages/pos/payment.py
# ERP ENTERPRISE POS PAYMENT MODULE v14.0
#
# Mobile Payment Account Master Integrated
# KBZ Pay / Wave Pay / AYA Pay
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


from .engine import (
    get_default_tax_rate
)

from erp_core.payments.payment_qr_service import (
    PaymentQRService
)

from database import (
    generate_payment_qr
)


from erp_core.repositories.payment_account_repository import (
    get_payment_account
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



    # ==========================================================================
    # SUMMARY
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



    tax_rate = get_default_tax_rate()



    tax_amount = (
        subtotal
        *
        tax_rate
        /
        100
    )



    c1, c2, c3 = st.columns(3)


    with c1:

        st.caption("Items")

        st.write(
            len(cart)
        )


    with c2:

        st.caption("Total Qty")

        st.write(
            total_qty
        )


    with c3:

        st.caption("Subtotal")

        st.write(
            money(subtotal)
        )



    st.caption(
        f"🧾 Tax {tax_rate:.2f}% : {money(tax_amount)}"
    )



    # ==========================================================================
    # DISCOUNT
    # ==========================================================================


    discount = st.number_input(

        "Discount (MMK)",

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



    # ==========================================================================
    # TOTAL
    # ==========================================================================


    grand_total = max(

        0,

        subtotal
        +
        tax_amount
        -
        discount

    )



    st.markdown(
        f"""
### 💰 Total Payable

# {money(grand_total)}
"""
    )


    st.caption(
        f"""
Subtotal : {money(subtotal)}

Tax : {money(tax_amount)}

Discount : {money(discount)}
"""
    )



    # ==========================================================================
    # PAYMENT METHOD
    # ==========================================================================


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



    # ==========================================================================
    # MOBILE PAYMENT
    # ==========================================================================


    if payment_method == "MOBILE":


        provider = st.selectbox(

            "Mobile Provider",

            [
                "KBZ Pay",
                "Wave Pay",
                "AYA Pay"
            ]

        )


        # --------------------------------------------------------------
        # LOAD ACCOUNT MASTER
        # --------------------------------------------------------------


        branch_id = st.session_state.get(
            "branch_id",
            1
        )


        account = get_payment_account(

            provider,

            branch_id=branch_id

        )


        if not account:


            st.error(
                f"{provider} account not configured"
            )


            return



        account_name = account.get(

            "account_name",

            "ERP SHOP"

        )


        account_no = account.get(

            "account_no",

            ""

        )



        # --------------------------------------------------------------
        # QR GENERATE
        # --------------------------------------------------------------


if provider == "KBZ Pay":
    # --------------------------------------------------------------
    # QR GENERATE (STATIC / DYNAMIC)
    # --------------------------------------------------------------
    
    qr_mode = account.get(
        "qr_mode",
        "DYNAMIC"
    )
    
    
    if qr_mode == "STATIC":
    
        qr_buffer = PaymentQRService.generate_qr(
            raw_payload=account.get(
                "qr_payload_template"
            )
        )
    
    
    else:
    
        qr_buffer = PaymentQRService.generate_qr(
            provider=provider,
            account_name=account_name,
            account_no=account_no,
            amount=grand_total,
            sale_id="TEMP"
        )



        st.image(

            qr_buffer,

            caption=f"Scan to pay with {provider}",

            width=250

        )


        st.info(

            f"Pay MMK {grand_total:,.0f} to {account_name} ({account_no})"

        )


        mobile_txn = st.text_input(

            "Transaction ID",

            placeholder="Enter mobile banking transaction number"

        )


        st.session_state.mobile_provider = provider

        st.session_state.mobile_txn = mobile_txn

            # ==========================================================================
    # RECEIVED AMOUNT
    # ==========================================================================


    if payment_method == "MOBILE":


        received = grand_total


        st.success(

            f"Mobile payment expected: {money(received)}"

        )


    else:


        received = st.number_input(

            "Received Amount",

            min_value=0.0,

            step=100.0

        )



    change = max(

        0,

        received - grand_total

    )



    st.caption(

        f"""
Received : {money(received)}

Change : {money(change)}
"""

    )



    # ==========================================================================
    # COMPLETE SALE
    # ==========================================================================


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



                sale_data = result.get(

                    "data",

                    {}

                )



                sale_data.update({


                    "subtotal":

                        subtotal,


                    "discount":

                        discount,


                    "tax":

                        tax_amount,


                    "tax_rate":

                        tax_rate,


                    "total":

                        grand_total,


                    "paid_amount":

                        received,


                    "change_amount":

                        change,


                    "payment_method":

                        payment_method,


                    "items":

                        cart


                })




                # MOBILE PAYMENT INFO
                # --------------------------------------------------


                if payment_method == "MOBILE":


                    sale_data.update({


                        "mobile_provider":

                            st.session_state.get(

                                "mobile_provider"

                            ),


                        "mobile_txn":

                            st.session_state.get(

                                "mobile_txn"

                            )


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
