# ==============================================================================
# erp_pages/6_Receipt_Viewer.py
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

    get_sale_items

)



# ==============================================================================
# TIMEZONE ENGINE
# ==============================================================================

from utils.timezone import (

    format_db_datetime

)



# ==============================================================================
# MAIN
# ==============================================================================


def run():



    # --------------------------------------------------------------------------
    # AUTH
    # --------------------------------------------------------------------------

    if not st.session_state.get("user"):

        st.warning(
            "⛔ Please log in first."
        )

        st.stop()



    st.title(
        "🧾 ERP Enterprise Receipt Viewer"
    )



    # --------------------------------------------------------------------------
    # SAFE NUMBER
    # --------------------------------------------------------------------------

    def safe_float(value):

        try:

            return float(
                value or 0
            )

        except Exception:

            return 0.0



    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------

    if "receipt_data" not in st.session_state:

        st.session_state.receipt_data = None



    if "selected_invoice" not in st.session_state:

        st.session_state.selected_invoice = None




    # --------------------------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------------------------

    search_query = st.text_input(

        "🔍 Search Invoice No",

        value=(
            st.session_state.selected_invoice
            or ""
        ),

        placeholder="INV-20260726081229"

    )




    if search_query:



        matches = search_receipts(

            search_query

        )



        if not matches:


            st.error(

                f"No invoice found: {search_query}"

            )

            st.stop()




        # --------------------------------------------------
        # SELECT RECEIPT
        # --------------------------------------------------


        if len(matches) > 1:



            options = {



                f"{r.get('invoice_no','-')} | "
                f"{safe_float(r.get('total')):,.0f} MMK":

                r



                for r in matches



            }



            selected = st.selectbox(

                "Select Invoice",

                list(options.keys())

            )



            sale = options[selected]



        else:



            sale = matches[0]



            st.success(

                f"Found: {sale.get('invoice_no')}"

            )




        if st.button(

            "📥 Load Receipt"

        ):



            receipt = get_receipt(

                sale.get(
                    "invoice_no"
                )

            )


            st.session_state.receipt_data = receipt


            st.session_state.selected_invoice = (

                sale.get(
                    "invoice_no"
                )

            )


            st.rerun()




    # --------------------------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------------------------


    receipt = st.session_state.receipt_data



    if not receipt:


        st.info(

            "🔎 Search and load receipt"

        )

        st.stop()




    # --------------------------------------------------------------------------
    # LOAD ITEMS
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
    # SUMMARY
    # --------------------------------------------------------------------------


    st.divider()


    st.subheader(

        f"🧾 Invoice: {receipt.get('invoice_no','-')}"

    )




    col1, col2, col3 = st.columns(3)



    total = safe_float(

        receipt.get(
            "total"
        )

    )


    paid = safe_float(

        receipt.get(
            "paid_amount"
        )

    )


    change = safe_float(

        receipt.get(
            "change_amount",
            paid-total
        )

    )



    col1.metric(

        "Total",

        f"{total:,.0f} MMK"

    )



    col2.metric(

        "Paid",

        f"{paid:,.0f} MMK"

    )



    col3.metric(

        "Change",

        f"{change:,.0f} MMK"

    )




    # --------------------------------------------------------------------------
    # DATE (MYANMAR TIME)
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



        qty = safe_float(

            item.get(
                "quantity"
            )

        )


        price = safe_float(

            item.get(
                "unit_price"
            )

        )


        amount = safe_float(

            item.get(
                "total"
            )

        )



        if amount == 0:


            amount = qty * price




        rows.append(

            {

                "Product ID":

                    item.get(
                        "product_id"
                    ),


                "Qty":

                    qty,


                "Unit Price":

                    f"{price:,.0f}",


                "Amount":

                    f"{amount:,.0f}"

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
    # VERIFY TOTAL
    # --------------------------------------------------------------------------


    calculated_total = sum(

        safe_float(
            i.get("quantity")
        )

        *

        safe_float(
            i.get("unit_price")
        )

        for i in items

    )



    st.info(

        f"Calculated Items Total: "
        f"{calculated_total:,.0f} MMK"

    )





    # --------------------------------------------------------------------------
    # CLEAR
    # --------------------------------------------------------------------------


    if st.button(

        "🆕 Clear"

    ):


        st.session_state.receipt_data = None

        st.session_state.selected_invoice = None

        st.rerun()





# ==============================================================================
# ENTRY
# ==============================================================================


if __name__ == "__main__":

    run()
