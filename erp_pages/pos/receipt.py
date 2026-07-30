# ==============================================================================
# erp_pages/pos/receipt.py
# ERP ENTERPRISE POS RECEIPT MODULE v13.0 FINAL
#
# Responsibilities:
# - Receipt display
# - Safe receipt mapping
# - Myanmar Time
# - PDF generation
# - Thermal printing
# - New sale reset
#
# FLOW:
#
# CHECKOUT
#    ↓
# SALE DATA
#    ↓
# RECEIPT DISPLAY
#    ↓
# PDF / THERMAL PRINT
#
# ==============================================================================


import pandas as pd
import streamlit as st



# ==============================================================================
# RECEIPT ENGINE
# ==============================================================================


from utils.receipt_pdf import (
    generate_pdf
)


from utils.thermal_receipt import (
    print_thermal,
    build_receipt_data
)


from utils.timezone import (
    format_datetime
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
# SAFE FLOAT
# ==============================================================================


def safe_float(value):

    try:

        return float(value or 0)

    except Exception:

        return 0.0







# ==============================================================================
# RECEIPT ITEM NORMALIZER
# ==============================================================================


def build_receipt_rows(items):


    rows = []


    for item in items or []:


        name = (

            item.get("name")

            or

            item.get("product_name")

            or

            "Unknown Product"

        )



        qty = safe_float(

            item.get(

                "quantity",

                item.get(

                    "qty",

                    0

                )

            )

        )



        price = safe_float(

            item.get(

                "unit_price",

                item.get(

                    "selling_price",

                    0

                )

            )

        )



        amount = safe_float(

            item.get(

                "total",

                qty * price

            )

        )



        rows.append(

            {

                "Product":

                    name,


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

                    money(amount)

            }

        )



    return rows







# ==============================================================================
# RECEIPT RENDER
# ==============================================================================


def render_receipt():


    data = st.session_state.get(

        "sale_data",

        None

    )


    if not data:


        st.error(

            "Receipt data missing."

        )

        return




    st.divider()



    st.title(

        "🧾 Sales Receipt"

    )




    # ==========================================================================
    # DEBUG
    # ==========================================================================


    with st.expander(

        "🔎 DEBUG RECEIPT DATA"

    ):

        st.json(data)





    # ==========================================================================
    # SAFE DATA MAPPING
    # ==========================================================================


    invoice_no = data.get(

        "invoice_no",

        "-"

    )



    raw_date = (

        data.get("date")

        or

        data.get("created_at")

    )



    if raw_date:


        sale_date = format_datetime(

            raw_date

        )


    else:


        sale_date = "-"





    cashier = data.get(

        "cashier",

        "Admin"

    )



    items = data.get(

        "items",

        []

    )

        # --------------------------------------------------------------------------
    # TOTAL DATA MAPPING FIX
    # --------------------------------------------------------------------------

    subtotal = float(
        data.get(
            "subtotal",
            0
        )
        or 0
    )


    discount = float(
        data.get(
            "discount",
            0
        )
        or 0
    )


    tax_rate = float(
        data.get(
            "tax_rate",
            0
        )
        or 0
    )


    tax_amount = float(
        data.get(
            "tax_amount",
            data.get(
                "tax",
                0
            )
        )
        or 0
    )


    # ===============================
    # GRAND TOTAL FIX
    # ===============================

    grand_total = float(

        data.get("grand_total")

        or

        data.get("total")

        or

        data.get("final_total")

        or

        data.get("amount")

        or

        (
            subtotal
            -
            discount
            +
            tax_amount
        )

        or 0

    )



    # ===============================
    # PAYMENT FIX
    # ===============================

    paid = float(

        data.get("paid")

        or

        data.get("paid_amount")

        or

        data.get("received_amount")

        or

        data.get("payment")

        or 0

    )



    # ===============================
    # CHANGE FIX
    # ===============================

    change = float(

        data.get("change")

        or

        data.get("change_amount")

        or

        data.get("balance")

        or

        (
            paid
            -
            grand_total
        )

        or 0

    )







                
