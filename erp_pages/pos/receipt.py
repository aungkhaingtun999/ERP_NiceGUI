# ==============================================================================
# erp_pages/pos/receipt.py
# ERP ENTERPRISE POS RECEIPT MODULE v12.0
#
# Responsibilities:
# - Receipt display
# - PDF generation
# - Thermal printing
# - New sale reset
#
# ==============================================================================


import pandas as pd
import streamlit as st



from utils.receipt_pdf import (
    generate_pdf
)


from utils.thermal_receipt import (
    print_thermal
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
# RECEIPT TABLE
# ==============================================================================


def build_receipt_rows(items):


    rows = []


    for item in items:


        rows.append(

            {

                "Product":

                    item.get(
                        "name",
                        ""
                    ),


                "Qty":

                    item.get(
                        "quantity",
                        0
                    ),


                "Price Source":

                    item.get(
                        "price_source",
                        "SYSTEM"
                    ),


                "Unit Price":

                    money(

                        item.get(
                            "unit_price",
                            0
                        )

                    ),


                "Amount":

                    money(

                        item.get(
                            "total",
                            0
                        )

                    )

            }

        )


    return rows





# ==============================================================================
# DISPLAY RECEIPT
# ==============================================================================


def render_receipt():


    data = st.session_state.get(

        "sale_data"

    )


    if not data:


        st.error(

            "Receipt data missing"

        )

        return





    st.divider()


    st.title(

        "🧾 Sales Receipt"

    )





    # ==============================================================
    # HEADER
    # ==============================================================

    st.info(

        f"""

Invoice No:

{data.get('invoice_no','')}


Date:

{data.get('date',format_datetime())}


Cashier:

{data.get('cashier','Unknown')}

        """

    )





    # ==============================================================
    # ITEMS
    # ==============================================================


    rows = build_receipt_rows(

        data.get(
            "items",
            []
        )

    )


    if rows:


        df = pd.DataFrame(

            rows

        )


        st.dataframe(

            df,

            use_container_width=True,

            hide_index=True

        )





    # ==============================================================
    # TOTAL
    # ==============================================================


    st.success(

        f"""

Subtotal:

{money(data.get('subtotal',0))}


Tax:

{money(data.get('tax_amount',0))}


Discount:

{money(data.get('discount',0))}


====================

TOTAL:

{money(data.get('grand_total',0))}


Paid:

{money(data.get('paid',0))}


Change:

{money(data.get('change',0))}

====================

        """

    )





    # ==============================================================
    # ACTION BUTTONS
    # ==============================================================


    c1, c2, c3 = st.columns(3)





    # ------------------------------------------------------------------
    # THERMAL PRINT
    # ------------------------------------------------------------------

    with c1:


        if st.button(

            "🖨 Print Receipt",

            use_container_width=True

        ):


            try:


                print_thermal(

                    data

                )


                st.success(

                    "Receipt sent to printer"

                )


            except Exception as e:


                st.error(

                    f"Printer Error: {e}"

                )





    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------

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

                        label="⬇ Download PDF",

                        data=pdf_bytes,

                        file_name=f"{filename}.pdf",

                        mime="application/pdf",

                        use_container_width=True

                    )


            except Exception as e:


                st.error(

                    f"PDF Error: {e}"

                )





    # ------------------------------------------------------------------
    # NEW SALE
    # ------------------------------------------------------------------

    with c3:


        if st.button(

            "🆕 New Sale",

            use_container_width=True

        ):


            reset_pos()






# ==============================================================================
# RESET POS
# ==============================================================================


def reset_pos():


    st.session_state.cart = []


    st.session_state.sale_data = None


    st.session_state.show_receipt = False


    st.session_state.processing = False



    st.success(

        "New Sale Ready"

    )


    st.rerun()
