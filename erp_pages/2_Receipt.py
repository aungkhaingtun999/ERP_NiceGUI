# ==============================================================================
# erp_pages/2_Receipt.py
# ERP ENTERPRISE RECEIPT VIEWER v4.0
# ERP CORE CONNECTED
# Myanmar Time Supported
# ==============================================================================


import streamlit as st
import pandas as pd


# ==============================================================================
# ERP DATABASE BRIDGE
# ==============================================================================

from database import (
    search_receipts,
    get_receipt,
    get_sale_items,
)


# ==============================================================================
# TIME ENGINE
# ==============================================================================

from utils.timezone import (
    format_db_datetime
)


# ==============================================================================
# PDF / RECEIPT
# ==============================================================================

from utils.receipt_pdf import generate_pdf
from utils.thermal_receipt import build_receipt_data



# ==============================================================================
# PAGE
# ==============================================================================


def run():


    # --------------------------------------------------------------------------
    # AUTH
    # --------------------------------------------------------------------------

    if not st.session_state.get("user"):

        st.warning(
            "⛔ Please login first"
        )

        st.stop()



    st.title(
        "🧾 ERP Enterprise Receipt Viewer"
    )



    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------

    if "selected_receipt" not in st.session_state:

        st.session_state.selected_receipt = None


    if "receipt_data" not in st.session_state:

        st.session_state.receipt_data = None



    # --------------------------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------------------------

    keyword = st.text_input(
        "🔍 Search Invoice No"
    )



    if keyword:


        results = search_receipts(
            keyword
        )


        if not results:

            st.error(
                "No receipt found"
            )

            st.stop()



        options = {

            f"{r.get('invoice_no')} | "
            f"{float(r.get('total',0)):,.0f} MMK":
            r

            for r in results

        }



        selected = st.selectbox(

            "Select Receipt",

            list(options.keys())

        )



        receipt_short = options[selected]



        if st.button(
            "📥 Load Receipt"
        ):


            receipt = get_receipt(

                receipt_short.get(
                    "invoice_no"
                )

            )


            st.session_state.receipt_data = receipt


            st.rerun()





    # --------------------------------------------------------------------------
    # LOAD
    # --------------------------------------------------------------------------

    receipt = st.session_state.receipt_data



    if not receipt:

        st.info(
            "Search and load receipt"
        )

        st.stop()



    # --------------------------------------------------------------------------
    # ITEMS
    # --------------------------------------------------------------------------

    sale_id = receipt.get(
        "id"
    )


    items = []


    if sale_id:


        items = get_sale_items(

            str(sale_id)

        )



    # --------------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------------

    st.divider()


    st.subheader(
        "🧾 Receipt Summary"
    )



    c1,c2,c3 = st.columns(3)



    with c1:

        st.metric(

            "Invoice No",

            receipt.get(
                "invoice_no",
                "-"
            )

        )



    with c2:

        st.metric(

            "Total",

            f"{float(receipt.get('total',0)):,.0f} MMK"

        )



    with c3:

        st.metric(

            "Status",

            receipt.get(
                "status",
                "-"
            )

        )





    # --------------------------------------------------------------------------
    # MYANMAR TIME DISPLAY
    # --------------------------------------------------------------------------


    if receipt.get(
        "created_at"
    ):


        st.write(

            "📅 Date:",

            format_db_datetime(

                receipt[
                    "created_at"
                ]

            )

        )




    # --------------------------------------------------------------------------
    # ITEMS
    # --------------------------------------------------------------------------


    st.divider()


    st.subheader(
        "🛒 Sale Items"
    )



    rows = []



    for item in items:


        qty = float(

            item.get(
                "quantity",
                0
            )

        )


        price = float(

            item.get(
                "unit_price",
                0
            )

        )



        total = float(

            item.get(
                "total",
                qty * price
            )

        )



        rows.append(

            {

                "Product ID":
                    item.get(
                        "product_id"
                    ),


                "Quantity":
                    qty,


                "Unit Price":
                    f"{price:,.0f}",


                "Amount":
                    f"{total:,.0f}"

            }

        )



    if rows:


        st.dataframe(

            pd.DataFrame(rows),

            use_container_width=True,

            hide_index=True

        )


    else:


        st.warning(
            "No items found"
        )




    # --------------------------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------------------------


    st.divider()


    st.subheader(
        "💰 Payment Details"
    )



    col1,col2,col3 = st.columns(3)



    with col1:


        st.write(

            "Subtotal:",

            f"{float(receipt.get('subtotal',0)):,.0f} MMK"

        )



    with col2:


        st.write(

            "Tax:",

            f"{float(receipt.get('tax',0)):,.0f} MMK"

        )



    with col3:


        st.write(

            "Grand Total:",

            f"{float(receipt.get('total',0)):,.0f} MMK"

        )





    # --------------------------------------------------------------------------
    # PDF
    # --------------------------------------------------------------------------


    st.divider()



    if st.button(
        "📄 Generate PDF"
    ):


        data = build_receipt_data(

            receipt,

            items

        )


        result = generate_pdf(

            data

        )


        if result:


            pdf_bytes, filename = result



            st.download_button(

                "⬇ Download Receipt",

                pdf_bytes,

                file_name=f"{filename}.pdf",

                mime="application/pdf"

            )





    # --------------------------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------------------------


    if st.button(
        "🆕 Clear"
    ):


        st.session_state.receipt_data = None

        st.session_state.selected_receipt = None

        st.rerun()





if __name__ == "__main__":

    run()
