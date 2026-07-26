# ==============================================================================
# 1_POS.py
# ERP ENTERPRISE POS v11.0
# PART 1/4
#
# CORE ENGINE
# PRODUCT SEARCH
# OWNER PRICE PRIORITY
#
# OWNER PRICE
#       ↓
# PRODUCT MARKUP
#       ↓
# CATEGORY MARKUP
#       ↓
# GLOBAL MARKUP
#
# ==============================================================================


import sys
import os

import pandas as pd
import streamlit as st


from datetime import datetime


from utils.timezone import format_datetime

from utils.receipt_pdf import generate_pdf

from utils.thermal_receipt import print_thermal



# ==============================================================================
# ROOT PATH
# ==============================================================================

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)



# ==============================================================================
# ERP CORE
# ==============================================================================


from erp_core import (

    get_products,

    get_setting,

    get_default_warehouse_id,

    checkout_sale_rpc

)



from auth import is_authenticated

from language import (
    t,
    language_selector
)



# ==============================================================================
# MAIN
# ==============================================================================


def run():



    # ==========================================================================
    # LANGUAGE
    # ==========================================================================


    language_selector()



    # ==========================================================================
    # AUTH
    # ==========================================================================


    if not is_authenticated():

        st.warning(
            "Please login first."
        )

        st.stop()



    # ==========================================================================
    # SESSION STATE
    # ==========================================================================


    DEFAULT_STATE = {


        "cart": [],


        "sale_data": None,


        "show_receipt": False,


        "processing": False


    }



    for key,value in DEFAULT_STATE.items():


        if key not in st.session_state:


            st.session_state[key] = value





    # ==========================================================================
    # SETTINGS
    # ==========================================================================


    try:

        st.session_state.tax_rate = float(

            get_setting(
                "default_tax_rate",
                0
            )

        )


    except:


        st.session_state.tax_rate = 0





    try:

        st.session_state.discount_policy = (

            get_setting(
                "discount_policy",
                "allowed"
            )

        )


    except:


        st.session_state.discount_policy = "allowed"





    # ==========================================================================
    # WAREHOUSE
    # ==========================================================================


    warehouse_id = get_default_warehouse_id()



    if not warehouse_id:


        st.error(
            "Default warehouse missing."
        )

        st.stop()





    # ==========================================================================
    # LOAD PRODUCTS
    # ==========================================================================


    try:


        products = get_products(

            warehouse_id=warehouse_id

        )


    except Exception as e:


        st.error(

            f"Product Load Error : {e}"

        )

        st.stop()





    if not products:


        st.warning(
            "No products available."
        )

        st.stop()





    # ==========================================================================
    # TITLE
    # ==========================================================================


    st.title(

        f"🛒 {t('app.pos_system')}"

    )



    st.caption(

        """
ERP Enterprise Pricing Engine

OWNER PRICE
↓
PRODUCT MARKUP
↓
CATEGORY MARKUP
↓
GLOBAL MARKUP

POS uses FINAL SELLING PRICE
"""

    )





    # ==========================================================================
    # PRODUCT SEARCH
    # ==========================================================================


    if not st.session_state.show_receipt:



        col1,col2 = st.columns(2)



        with col1:


            name_search = st.text_input(

                "🔍 Product Name"

            )



        with col2:


            barcode_search = st.text_input(

                "📦 SKU / Barcode"

            )





        matches = []



        for product in products:



            name = str(

                product.get(
                    "name",
                    ""
                )

            )



            sku = str(

                product.get(
                    "sku",
                    ""
                )

            )



            barcode = str(

                product.get(
                    "barcode",
                    ""
                )

            )



            name_ok = True

            code_ok = True





            if name_search:


                name_ok = (

                    name_search.lower()

                    in

                    name.lower()

                )





            if barcode_search:


                search = barcode_search.lower()



                code_ok = (

                    search in sku.lower()

                    or

                    search in barcode.lower()

                )





            if name_ok and code_ok:


                matches.append(product)





        # ======================================================================
        # SELECT PRODUCT
        # ======================================================================


        if matches:



            selected = st.selectbox(


                "Select Product",


                matches,


                format_func=lambda x:

                (

                    f"{x.get('sku','')} | "

                    f"{x.get('name')} | "

                    f"Stock: "

                    f"{x.get('available_qty',0)} | "

                    f"Price: "

                    f"{float(x.get('final_selling_price',0)):,.0f}"

                )


            )





            qty = st.number_input(


                "Quantity",


                min_value=1,


                value=1,


                step=1


            )





            # ==============================================================
            # PRICE ENGINE
            # ==============================================================


            final_price = float(


                selected.get(


                    "final_selling_price",


                    selected.get(

                        "selling_price",

                        0

                    )

                )


            )





            price_source = selected.get(

                "price_source",

                "SYSTEM"

            )





            st.info(

                f"""

Selling Price:

{final_price:,.0f} MMK


Price Source:

{price_source}

"""

            )





            if st.button(

                "➕ Add To Cart",

                use_container_width=True

            ):



                available = int(

                    selected.get(

                        "available_qty",

                        0

                    )

                )



                existing_qty = sum(

                    item["qty"]

                    for item in st.session_state.cart

                    if item["id"]

                    ==

                    selected["id"]

                )





                if existing_qty + qty > available:


                    st.error(

                        f"Stock not enough. Available {available}"

                    )



                else:


                    found=False



                    for item in st.session_state.cart:



                        if item["id"] == selected["id"]:



                            item["qty"] += int(qty)

                            found=True

                            break





                    if not found:


                        st.session_state.cart.append(


                            {

                            "id":

                                selected["id"],


                            "name":

                                selected["name"],


                            "sku":

                                selected.get(

                                    "sku",

                                    ""

                                ),


                            "selling_price":

                                final_price,


                            "price_source":

                                price_source,


                            "qty":

                                int(qty)


                            }


                        )



                    st.success(

                        "Added to cart"

                    )



                    st.rerun()
                        # ==========================================================================
    # PART 2/4
    # CART ENGINE + PAYMENT ENGINE
    # ==========================================================================


    if (
        not st.session_state.show_receipt
        and st.session_state.cart
    ):


        st.divider()


        st.subheader(
            "🛒 Shopping Cart"
        )



        # ==============================================================
        # CART TABLE
        # ==============================================================


        cart_rows = []



        for item in st.session_state.cart:



            amount = (

                item["selling_price"]

                *

                item["qty"]

            )



            cart_rows.append(


                {


                "Product":

                    item["name"],


                "Qty":

                    item["qty"],


                "Price Source":

                    item.get(

                        "price_source",

                        "SYSTEM"

                    ),


                "Unit Price":

                    f"{item['selling_price']:,.0f} MMK",


                "Amount":

                    f"{amount:,.0f} MMK"


                }


            )





        df = pd.DataFrame(cart_rows)



        st.dataframe(

            df,

            use_container_width=True,

            hide_index=True

        )





        # ==============================================================
        # TOTAL
        # ==============================================================


        subtotal = sum(


            item["selling_price"]

            *

            item["qty"]


            for item in st.session_state.cart


        )



        total_qty = sum(


            item["qty"]


            for item in st.session_state.cart


        )





        st.info(

            f"""

Items:

{len(st.session_state.cart)}


Quantity:

{total_qty}


Subtotal:

{subtotal:,.0f} MMK

"""

        )





        # ==============================================================
        # REMOVE ITEM
        # ==============================================================


        st.subheader(

            "❌ Remove Product"

        )



        for index,item in enumerate(

            st.session_state.cart

        ):



            c1,c2 = st.columns(

                [5,1]

            )



            with c1:


                st.write(

                    f"{item['name']} × {item['qty']}"

                )



            with c2:


                if st.button(

                    "❌",

                    key=f"remove_{index}"

                ):


                    st.session_state.cart.pop(index)

                    st.rerun()





        st.divider()



        # ==============================================================
        # PAYMENT
        # ==============================================================


        st.subheader(

            "💰 Payment"

        )





        st.info(

            f"""

System Tax Rate:

{st.session_state.tax_rate}%


Discount Policy:

{st.session_state.discount_policy}

"""

        )





        # ==============================================================
        # DISCOUNT CONTROL
        # ==============================================================


        policy = str(

            st.session_state.discount_policy

        ).lower().strip()





        if policy == "restricted":



            discount = st.number_input(

                "Discount",

                min_value=0.0,

                value=0.0,

                step=100.0,

                disabled=True

            )



            st.error(

                "⛔ Discount disabled by administrator"

            )



        else:



            discount = st.number_input(

                "Discount",

                min_value=0.0,

                value=0.0,

                step=100.0

            )



            st.success(

                "✅ Discount allowed"

            )





        # ==============================================================
        # TAX + TOTAL
        # ==============================================================


        tax_amount = round(

            subtotal

            *

            st.session_state.tax_rate

            /

            100,

            2

        )





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

Subtotal:

{subtotal:,.0f} MMK


Tax:

{tax_amount:,.0f} MMK


Discount:

{discount:,.0f} MMK



====================

TOTAL:

{grand_total:,.0f} MMK

====================

"""

        )





        # ==============================================================
        # PAYMENT METHOD
        # ==============================================================


        payment_method = st.selectbox(

            "Payment Method",

            [

                "Cash",

                "Card",

                "Mobile"

            ]

        )





        if payment_method == "Cash":


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

            f"Change : {change:,.0f} MMK"

        )





        # ==============================================================
        # CONFIRM BUTTON
        # ==============================================================


        if st.button(

            "✅ Confirm Sale",

            disabled=

            st.session_state.processing,

            use_container_width=True

        ):



            st.session_state.processing = True



            st.rerun()
            # ==========================================================================
# PART 3/4
# CHECKOUT ENGINE
# ==========================================================================


        if st.button(

            "✅ Confirm Sale",

            disabled=

            st.session_state.processing,

            use_container_width=True

        ):


            st.session_state.processing = True



            try:



                # ==========================================================
                # CREATE CART PAYLOAD
                # ==========================================================


                cart_payload = []



                for item in st.session_state.cart:



                    cart_payload.append(


                        {

                        "id":

                            item["id"],


                        "name":

                            item["name"],


                        "qty":

                            int(

                                item["qty"]

                            ),


                        "selling_price":

                            float(

                                item["selling_price"]

                            ),


                        "price_source":

                            item.get(

                                "price_source",

                                "SYSTEM"

                            )


                        }


                    )





                # ==========================================================
                # CALL CHECKOUT RPC
                # ==========================================================


                result = checkout_sale_rpc(


                    cart=

                    cart_payload,


                    paid_amount=

                    received,


                    cashier_id=

                    st.session_state.get(

                        "user_id"

                    ),


                    warehouse_id=

                    warehouse_id,


                    payment_method=

                    payment_method,


                    tax_rate=

                    st.session_state.tax_rate,


                    discount=

                    discount


                )





                # ==========================================================
                # SUCCESS
                # ==========================================================


                if result.get(

                    "success",

                    False

                ):



                    data = result.get(

                        "data",

                        {}

                    )



                    if isinstance(

                        data,

                        list

                    ):


                        data = (

                            data[0]

                            if data

                            else {}

                        )





                    invoice_no = (

                        data.get(

                            "invoice_no"

                        )

                        or

                        data.get(

                            "sale_no"

                        )

                        or

                        (

                        "INV-"

                        +

                        datetime.now()

                        .strftime(

                            "%Y%m%d%H%M%S"

                        )

                        )

                    )





                    # ======================================================
                    # RECEIPT ITEMS
                    # ======================================================


                    receipt_items = []



                    for item in st.session_state.cart:



                        qty = int(

                            item["qty"]

                        )



                        price = float(

                            item["selling_price"]

                        )



                        receipt_items.append(


                            {


                            "name":

                                item["name"],


                            "product_id":

                                item["id"],


                            "quantity":

                                qty,


                            "unit_price":

                                price,


                            "price_source":

                                item.get(

                                    "price_source",

                                    "SYSTEM"

                                ),


                            "total":

                                qty *

                                price


                            }


                        )





                    # ======================================================
                    # SAVE SALE DATA
                    # ======================================================


                    st.session_state.sale_data = {


                        "invoice_no":

                            invoice_no,


                        "date":

                            format_datetime(),


                        "cashier":

                            st.session_state.get(

                                "username",

                                "Unknown"

                            ),


                        "items":

                            receipt_items,


                        "subtotal":

                            subtotal,


                        "tax_rate":

                            st.session_state.tax_rate,


                        "tax_amount":

                            tax_amount,


                        "discount":

                            discount,


                        "grand_total":

                            grand_total,


                        "paid":

                            received,


                        "change":

                            change


                    }





                    st.session_state.show_receipt = True


                    st.session_state.processing = False



                    st.rerun()





                else:



                    st.error(

                        result.get(

                            "message",

                            "Sale Failed"

                        )

                    )



                    st.session_state.processing = False





            except Exception as e:



                st.session_state.processing = False



                st.error(

                    f"Checkout Error : {e}"

                    )
# ==========================================================================
# PART 4/4
# RECEIPT ENGINE + PRINT + RESET
# ==========================================================================


    if st.session_state.show_receipt:


        data = st.session_state.sale_data



        if not data:


            st.error(

                "Receipt data missing"

            )

            st.stop()





        st.divider()



        st.title(

            "🧾 Sales Receipt"

        )





        st.info(

            f"""
Invoice No:

{data['invoice_no']}


Date:

{data['date']}


Cashier:

{data['cashier']}

"""

        )





        # ==============================================================
        # RECEIPT TABLE
        # ==============================================================


        receipt_rows = []



        for item in data["items"]:



            receipt_rows.append(


                {


                "Product":

                    item["name"],


                "Qty":

                    item["quantity"],


                "Price":

                    f"{item['unit_price']:,.0f}",


                "Source":

                    item.get(

                        "price_source",

                        "SYSTEM"

                    ),


                "Amount":

                    f"{item['total']:,.0f} MMK"


                }


            )





        receipt_df = pd.DataFrame(

            receipt_rows

        )





        st.dataframe(

            receipt_df,

            use_container_width=True,

            hide_index=True

        )





        st.divider()



        # ==============================================================
        # PAYMENT SUMMARY
        # ==============================================================


        st.success(

            f"""

Subtotal:

{data['subtotal']:,.0f} MMK


Tax ({data['tax_rate']}%)

{data['tax_amount']:,.0f} MMK


Discount:

{data['discount']:,.0f} MMK



======================

GRAND TOTAL

{data['grand_total']:,.0f} MMK

======================



Paid:

{data['paid']:,.0f} MMK


Change:

{data['change']:,.0f} MMK

"""

        )





        # ==============================================================
        # PRINT BUTTONS
        # ==============================================================


        c1,c2,c3 = st.columns(3)





        # --------------------------------------------------------------
        # THERMAL PRINT
        # --------------------------------------------------------------


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

                        f"Printer Error : {e}"

                    )







        # --------------------------------------------------------------
        # PDF
        # --------------------------------------------------------------


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







        # --------------------------------------------------------------
        # NEW SALE
        # --------------------------------------------------------------


        with c3:


            if st.button(

                "🆕 New Sale",

                use_container_width=True

            ):



                st.session_state.cart = []


                st.session_state.sale_data = None


                st.session_state.show_receipt = False


                st.session_state.processing = False



                try:


                    st.session_state.tax_rate = float(

                        get_setting(

                            "default_tax_rate",

                            0

                        )

                    )


                except:


                    st.session_state.tax_rate = 0





                st.rerun()
