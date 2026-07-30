# ==============================================================================
# erp_pages/pos/receipt.py
# ERP ENTERPRISE POS RECEIPT MODULE v12.9 FINAL
#
# Responsibilities:
# - Receipt display
# - Safe receipt mapping
# - PDF generation
# - Thermal printing
# - New sale reset
#
# Flow:
#
# CHECKOUT
#    ↓
# SALE DATA
#    ↓
# RECEIPT DISPLAY
#    ↓
# PDF / PRINT
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
# RECEIPT ITEM NORMALIZER
# ==============================================================================


def build_receipt_rows(items):


    rows = []



    for item in items or []:



        name = (

            item.get(

                "name"

            )

            or

            item.get(

                "product_name"

            )

            or

            "Unknown Product"

        )



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





    # --------------------------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------------------------


    with st.expander(

        "DEBUG RECEIPT DATA"

    ):


        st.json(data)





    # --------------------------------------------------------------------------
    # SAFE DATA
    # --------------------------------------------------------------------------


    invoice_no = data.get(

        "invoice_no",

        "-"

    )



    # --------------------------------------------------------------------------
    # SAFE DATA
    # --------------------------------------------------------------------------

    invoice_no = data.get(
        "invoice_no",
        "-"
    )


    # --------------------------------------------------------------------------
    # DATE
    # --------------------------------------------------------------------------

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



    subtotal = float(

        data.get(

            "subtotal",

            0

        )

    )



    tax_rate = float(

        data.get(

            "tax_rate",

            0

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



    grand_total = float(

        data.get(

            "grand_total",

            0

        )

    )



    paid = float(

        data.get(

            "paid",

            0

        )

    )



    change = float(

        data.get(

            "change",

            0

        )

    )







    # --------------------------------------------------------------------------
    # HEADER
    # --------------------------------------------------------------------------


    st.info(

        f"""

Invoice No:

{invoice_no}



Date:

{sale_date}



Cashier:

{cashier}

"""

    )







    # --------------------------------------------------------------------------
    # ITEMS
    # --------------------------------------------------------------------------


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

            "No items found."

        )







    # --------------------------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------------------------


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

{money(grand_total)}



====================



Paid :

{money(paid)}



Change :

{money(change)}

"""

    )







    # --------------------------------------------------------------------------
    # ACTION BUTTONS
    # --------------------------------------------------------------------------


    c1, c2, c3 = st.columns(3)





    # PRINT
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

                    "Receipt printed."

                )



            except Exception as e:



                st.error(

                    f"Printer Error : {e}"

                )







    # PDF
    with c2:



        if st.button(

            "📄 Generate PDF",

            use_container_width=True

        ):



            try:



                result = generate_pdf(

                    data

                )



                if result:



                    pdf_bytes, filename = result



                    st.download_button(


                        label=

                            "⬇ Download PDF",


                        data=

                            pdf_bytes,


                        file_name=

                            f"{filename}.pdf",


                        mime=

                            "application/pdf",


                        use_container_width=True

                    )



            except Exception as e:



                st.error(

                    f"PDF Error : {e}"

                )







    # NEW SALE
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



    st.session_state.received_amount = 0



    st.session_state.discount = 0



    st.success(

        "New Sale Ready"

    )



    st.rerun()
