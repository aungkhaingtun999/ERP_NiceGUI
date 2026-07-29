# ==============================================================================
# erp_pages/pos/receipt.py
# ERP ENTERPRISE POS RECEIPT MODULE v12.5 FINAL
#
# - Receipt display
# - Safe data mapping
# - PDF
# - Thermal
# - New Sale reset
#
# ==============================================================================


import pandas as pd
import streamlit as st


from utils.receipt_pdf import generate_pdf
from utils.thermal_receipt import print_thermal
from utils.timezone import format_datetime



# ==============================================================================
# MONEY
# ==============================================================================

def money(value):

    try:
        return f"{float(value):,.0f} MMK"

    except Exception:
        return "0 MMK"





# ==============================================================================
# BUILD ITEMS
# ==============================================================================

def build_receipt_rows(items):

    rows = []

    for item in items:

        name = (
            item.get("name")
            or
            item.get("product_name")
            or
            "Unknown Product"
        )


        qty = int(
            item.get("quantity")
            or
            item.get("qty")
            or
            0
        )


        price = float(
            item.get("unit_price")
            or
            item.get("selling_price")
            or
            item.get("price")
            or
            0
        )


        amount = float(
            item.get("total")
            or
            item.get("amount")
            or
            (price * qty)
        )


        rows.append(
            {
                "Product": name,

                "Qty": qty,

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

    rows = []


    for item in items:


        qty = int(
            item.get(
                "quantity",
                item.get(
                    "qty",
                    0
                )
            )
        )


        price = float(
            item.get(
                "unit_price",
                item.get(
                    "selling_price",
                    0
                )
            )
        )


        amount = float(
            item.get(
                "total",
                price * qty
            )
        )


        rows.append(

            {

                "Product":
                    item.get(
                        "name",
                        ""
                    ),


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
# RECEIPT DISPLAY
# ==============================================================================

def render_receipt():


    data = st.session_state.get(
        "sale_data",
        {}
    )
with st.expander("DEBUG RECEIPT DATA"):
    st.json(data)

    if not data:


        st.error(
            "Receipt data missing"
        )

        return





    st.divider()


    st.title(
        "🧾 Sales Receipt"
    )





    # ------------------------------------------------------------------
    # SAFE DATA
    # ------------------------------------------------------------------

    invoice_no = data.get(
        "invoice_no",
        data.get(
            "invoice",
            "-"
        )
    )


    date = data.get(
        "date",
        format_datetime()
    )


    cashier = data.get(
        "cashier",
        "Admin"
    )


    items = data.get(
        "items",
        []
    )


    subtotal = float(
        data.get(
            "subtotal",
            0
        )
    )


    tax_rate = float(
        data.get(
            "tax_rate",
            st.session_state.get(
                "tax_rate",
                0
            )
        )
    )


    tax_amount = float(
        data.get(
            "tax_amount",
            0
        )
    )


    discount = float(
        data.get(
            "discount",
            0
        )
    )


    total = float(
        data.get(
            "grand_total",
            subtotal + tax_amount - discount
        )
    )


    paid = float(
        data.get(
            "paid",
            st.session_state.get(
                "received_amount",
                0
            )
        )
    )


    change = float(
        data.get(
            "change",
            max(
                0,
                paid-total
            )
        )
    )





    # ------------------------------------------------------------------
    # HEADER
    # ------------------------------------------------------------------

    st.info(

        f"""
Invoice No:
{invoice_no}


Date:
{date}


Cashier:
{cashier}
"""

    )





    # ------------------------------------------------------------------
    # ITEMS TABLE
    # ------------------------------------------------------------------

    rows = build_receipt_rows(
        items
    )


    if rows:


        st.dataframe(

            pd.DataFrame(rows),

            use_container_width=True,

            hide_index=True

        )


    else:

        st.warning(
            "No items in receipt"
        )





    # ------------------------------------------------------------------
    # TOTAL
    # ------------------------------------------------------------------

    st.success(

        f"""
Subtotal :
{money(subtotal)}


Tax Rate :
{tax_rate:.2f}%


Tax Amount :
{money(tax_amount)}


Discount :
{money(discount)}


====================

GRAND TOTAL :
{money(total)}

====================


Paid :
{money(paid)}


Change :
{money(change)}
"""

    )





    # ------------------------------------------------------------------
    # BUTTONS
    # ------------------------------------------------------------------

    c1,c2,c3 = st.columns(3)



    with c1:


        if st.button(

            "🖨 Print Receipt",

            use_container_width=True

        ):


            try:

                print_thermal(data)

                st.success(
                    "Printed"
                )

            except Exception as e:

                st.error(
                    f"Printer Error : {e}"
                )





    with c2:


        if st.button(

            "📄 Generate PDF",

            use_container_width=True

        ):


            try:

                pdf_bytes, filename = generate_pdf(
                    data
                )


                if pdf_bytes:


                    st.download_button(

                        "⬇ Download PDF",

                        data=pdf_bytes,

                        file_name=f"{filename}.pdf",

                        mime="application/pdf",

                        use_container_width=True

                    )


            except Exception as e:

                st.error(
                    f"PDF Error : {e}"
                )





    with c3:


        if st.button(

            "🆕 New Sale",

            use_container_width=True

        ):


            reset_pos()





# ==============================================================================
# RESET
# ==============================================================================

def reset_pos():


    st.session_state.cart = []


    st.session_state.sale_data = None


    st.session_state.show_receipt = False


    st.session_state.processing = False


    # keep tax

    st.session_state.tax_rate = st.session_state.get(
        "tax_rate",
        0
    )


    st.success(
        "New Sale Ready"
    )


    st.rerun()
