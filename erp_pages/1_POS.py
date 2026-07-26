# ==============================================================================
# 1_POS.py
# ERP ENTERPRISE POS v12.0
# PART 1/4
#
# CORE ENGINE
# AUTH
# SESSION
# PRODUCT PRICE ENGINE
#
# OWNER PRICE
#       ↓
# PRODUCT MARKUP
#       ↓
# CATEGORY MARKUP
#       ↓
# SYSTEM PRICE
#
# ==============================================================================


import sys
import os

import pandas as pd
import streamlit as st

from datetime import datetime


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
# UTILITIES
# ==============================================================================

from utils.timezone import format_datetime
from utils.receipt_pdf import generate_pdf
from utils.thermal_receipt import print_thermal



# ==============================================================================
# ERP CORE
# ==============================================================================

from erp_core import (

    get_products,

    get_setting,

    get_default_warehouse_id,

    checkout_sale_rpc

)



# ==============================================================================
# AUTH
# ==============================================================================

from auth import is_authenticated



# ==============================================================================
# LANGUAGE
# ==============================================================================

from language import (

    t,

    language_selector

)



# ==============================================================================
# PRICE FORMAT
# ==============================================================================

def money(value):

    try:

        return f"{float(value):,.0f} MMK"

    except Exception:

        return "0 MMK"





# ==============================================================================
# PRICE ENGINE
# ==============================================================================

def get_final_price(product):

    """
    OWNER PRICE PRIORITY ENGINE

    OWNER
        ↓
    PRODUCT MARKUP
        ↓
    CATEGORY MARKUP
        ↓
    SYSTEM PRICE

    """



    # ==========================================================
    # OWNER MANUAL PRICE
    # ==========================================================

    owner_price = product.get(
        "owner_selling_price"
    )


    if owner_price is not None:

        return {

            "price": float(owner_price),

            "source": "OWNER"

        }



    # ==========================================================
    # CALCULATED FINAL PRICE
    # ==========================================================

    final_price = product.get(
        "final_selling_price"
    )


    if final_price is not None:

        return {

            "price": float(final_price),

            "source": product.get(
                "price_source",
                "SYSTEM"
            )

        }



    # ==========================================================
    # FALLBACK
    # ==========================================================

    return {

        "price": float(
            product.get(
                "selling_price",
                0
            )
        ),

        "source": "SYSTEM"

    }





# ==============================================================================
# MAIN
# ==============================================================================

def run():



    # ==========================================================================
    # LANGUAGE
    # ==========================================================================

    language_selector()



    # ==========================================================================
    # AUTH CHECK
    # ==========================================================================

    if not is_authenticated():

        st.warning(
            "Please login first."
        )

        st.stop()





    # ==========================================================================
    # SESSION STATE
    # ==========================================================================

    default_state = {

        "cart": [],

        "sale_data": None,

        "show_receipt": False,

        "processing": False

    }



    for key, value in default_state.items():

        if key not in st.session_state:

            st.session_state[key] = value





    # ==========================================================================
    # SETTINGS
    # ==========================================================================

    try:

        tax_setting = get_setting(
        "DEFAULT_TAX_RATE",
        0
    )

        st.session_state.tax_rate = float(
        tax_setting
    )


    except Exception:

       st.session_state.tax_rate = 0

       st.error(
        f"Tax Load Error: {e}"
    )





    try:

        st.session_state.discount_policy = str(

            get_setting(

                "DISCOUNT_POLICY"

                "allowed"

            )

        )

    except Exception:

        st.session_state.discount_policy = "allowed"





    # ==========================================================================
    # WAREHOUSE
    # ==========================================================================

    warehouse_id = get_default_warehouse_id()



    if not warehouse_id:

        st.error(

            "Default warehouse not configured."

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

            "No Products Found"

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
ERP ENTERPRISE POS

Pricing Engine

OWNER PRICE
↓
PRODUCT MARKUP
↓
CATEGORY MARKUP
↓
SYSTEM PRICE

POS uses FINAL SELLING PRICE

        """

    )



    # PART 2/4 CONTINUES HERE
      # ==============================================================================
    # PART 2/4
    #
    # PRODUCT SEARCH
    # CART ENGINE
    # STOCK CONTROL
    #
    # ==============================================================================


    # ==========================================================================
    # PRODUCT SEARCH
    # ==========================================================================

    if not st.session_state.show_receipt:


        col1, col2 = st.columns(2)



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

                        f"{x.get('name','')} | "

                        f"Stock: "

                        f"{x.get('available_qty',0)} | "

                        f"Price: "

                        f"{money(get_final_price(x)['price'])}"

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


            price_data = get_final_price(

                selected

            )


            final_price = price_data["price"]


            price_source = price_data["source"]





            st.info(

                f"""

Product:

{selected.get('name')}


Selling Price:

{money(final_price)}


Price Source:

{price_source}

                """

            )





            # ==============================================================
            # ADD CART
            # ==============================================================


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





                current_qty = sum(


                    item["qty"]


                    for item in st.session_state.cart


                    if item["id"] == selected["id"]


                )





                if current_qty + qty > available:



                    st.error(

                        f"""

Insufficient Stock


Available:

{available}

                        """

                    )





                else:



                    exists = False





                    for item in st.session_state.cart:



                        if item["id"] == selected["id"]:



                            item["qty"] += int(qty)


                            exists = True


                            break





                    if not exists:



                        st.session_state.cart.append(


                            {


                                "id":

                                    selected["id"],



                                "name":

                                    selected.get(

                                        "name",

                                        ""

                                    ),



                                "sku":

                                    selected.get(

                                        "sku",

                                        ""

                                    ),



                                "qty":

                                    int(qty),



                                "selling_price":

                                    final_price,



                                "price_source":

                                    price_source



                            }


                        )





                    st.success(

                        "Added to cart"

                    )


                    st.rerun()







    # ==========================================================================
    # CART DISPLAY
    # ==========================================================================


    if (

        not st.session_state.show_receipt

        and

        st.session_state.cart

    ):



        st.divider()



        st.subheader(

            "🛒 Shopping Cart"

        )





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

                        money(

                            item["selling_price"]

                        ),



                    "Amount":

                        money(

                            amount

                        )


                }


            )





        cart_df = pd.DataFrame(

            cart_rows

        )





        st.dataframe(


            cart_df,


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

Total Items:

{len(st.session_state.cart)}


Total Quantity:

{total_qty}


Subtotal:

{money(subtotal)}

            """

        )







        # ==============================================================
        # REMOVE ITEM
        # ==============================================================


        st.subheader(

            "❌ Remove Product"

        )





        for index, item in enumerate(

            st.session_state.cart

        ):



            c1, c2 = st.columns(

                [5, 1]

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
                      # ==============================================================================
    # PART 3/4
    #
    # PAYMENT ENGINE
    # CHECKOUT RPC
    # SALE PROCESS
    #
    # ==============================================================================



    if (

        not st.session_state.show_receipt

        and

        st.session_state.cart

    ):


        st.divider()


        st.subheader(

            "💰 Payment"

        )





        # ==============================================================
        # DISCOUNT POLICY
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

                "⛔ Discount restricted"

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
        # SUBTOTAL
        # ==============================================================


        subtotal = sum(


            item["selling_price"]

            *

            item["qty"]


            for item in st.session_state.cart


        )





        # ==============================================================
        # TAX ENGINE
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


            disabled=st.session_state.processing,


            use_container_width=True


        ):



            st.session_state.processing = True





            try:



                # ======================================================
                # CREATE RPC CART PAYLOAD
                # ======================================================


                cart_payload = []





                for item in st.session_state.cart:



                    cart_payload.append(


                        {


                            "id":

                                item["id"],



                            "qty":

                                int(item["qty"]),



                            "selling_price":

                                float(

                                    item["selling_price"]

                                )


                        }


                    )








                # ======================================================
                # CASHIER UUID RESOLVE
                # ======================================================


                cashier_id = (


                    st.session_state.get(

                        "user_id"

                    )


                    or


                    st.session_state.get(

                        "id"

                    )


                    or


                    st.session_state.get(

                        "user",

                        {}

                    ).get(

                        "id"

                    )


                )





                if not cashier_id:



                    st.error(

                        "Cashier ID missing. Please login again."

                    )


                    st.session_state.processing = False


                    st.stop()







                # ======================================================
                # CHECKOUT RPC
                # ======================================================


                result = checkout_sale_rpc(



                    cart=

                        cart_payload,



                    paid_amount=

                        received,



                    warehouse_id=

                        warehouse_id,



                    cashier_id=

                        cashier_id,



                    counter_id=

                        1,



                    payment_method=

                        payment_method,



                    tax_rate=
                    st.session_state.tax_rate,



                    discount=

                        discount



                )








                # ======================================================
                # SUCCESS
                # ======================================================


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



                        data = data[0] if data else {}







                    invoice_no = (


                        data.get(

                            "invoice_no"

                        )


                        or


                        (

                            "INV-"

                            +

                            datetime.now().strftime(

                                "%Y%m%d%H%M%S"

                            )

                        )


                    )







                    receipt_items = []





                    for item in st.session_state.cart:



                        receipt_items.append(



                            {


                                "name":

                                    item["name"],



                                "product_id":

                                    item["id"],



                                "quantity":

                                    item["qty"],



                                "unit_price":

                                    item["selling_price"],



                                "price_source":

                                    item.get(

                                        "price_source",

                                        "SYSTEM"

                                    ),



                                "total":

                                    item["qty"]

                                    *

                                    item["selling_price"]



                            }


                        )








                    st.session_state.sale_data = {



                        "invoice_no":

                            invoice_no,



                        "date":

                            format_datetime(),



                        "cashier":


                            (

                                st.session_state.get(

                                    "username"

                                )


                                or


                                st.session_state.get(

                                    "full_name"

                                )


                                or


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

                            "Checkout Failed"

                        )

                    )



                    st.session_state.processing = False







            except Exception as e:



                st.session_state.processing = False



                st.error(

                    f"Checkout Error : {e}"

                )
                  # ==============================================================================
    # PART 4/4
    #
    # RECEIPT ENGINE
    # PRINT
    # PDF
    # RESET
    #
    # ==============================================================================



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







        # ==============================================================
        # RECEIPT HEADER
        # ==============================================================


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



                    "Price Source":

                        item.get(

                            "price_source",

                            "SYSTEM"

                        ),



                    "Unit Price":

                        money(

                            item["unit_price"]

                        ),



                    "Amount":

                        money(

                            item["total"]

                        )


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







        # ==============================================================
        # PAYMENT SUMMARY
        # ==============================================================


        st.success(

            f"""

Subtotal:

{money(data['subtotal'])}



Tax ({data['tax_rate']}%):

{money(data['tax_amount'])}



Discount:

{money(data['discount'])}



=========================

GRAND TOTAL

{money(data['grand_total'])}

=========================



Paid:

{money(data['paid'])}



Change:

{money(data['change'])}

            """

        )







        c1, c2, c3 = st.columns(3)







        # ==============================================================
        # THERMAL PRINT
        # ==============================================================


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








        # ==============================================================
        # PDF GENERATE
        # ==============================================================


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










        # ==============================================================
        # NEW SALE
        # ==============================================================


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

                    "DEFAULT_TAX_RATE",

                    0

    )

)

                except Exception:



                    st.session_state.tax_rate = 0






                st.success(

                    "New Sale Ready"

                )



                st.rerun()





# ==============================================================================
# APPLICATION START
# ==============================================================================


if __name__ == "__main__":


    run()
  
