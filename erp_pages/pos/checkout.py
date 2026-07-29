# ==============================================================================
# ERP POS CHECKOUT ENGINE v12.6 FINAL
#
# Cart
#   ↓
# Checkout RPC
#   ↓
# Receipt Builder
#   ↓
# Receipt Ready
#
# ==============================================================================


from datetime import datetime


import streamlit as st


from erp_core import checkout_sale_rpc


from erp_core.context import CacheManager

from erp_core.config import CACHE_KEYS





# ==============================================================================
# CART PAYLOAD
# ==============================================================================

def build_cart_payload(cart):

    payload = []


    for item in cart:


        payload.append(

            {

                "id":
                    int(item.get("id")),


                "qty":
                    int(item.get("qty",0)),


                "selling_price":
                    float(

                        item.get(

                            "selling_price",

                            item.get(

                                "unit_price",

                                0

                            )

                        )

                    )

            }

        )


    return payload






# ==============================================================================
# RECEIPT BUILDER
# ==============================================================================

def build_receipt_data(

    cart,

    rpc_data,

    paid_amount,

    tax_rate,

    discount

):


    subtotal = sum(

        float(

            item.get(

                "selling_price",

                item.get(

                    "unit_price",

                    0

                )

            )

        )

        *

        int(

            item.get(

                "qty",

                0

            )

        )

        for item in cart

    )





    tax_rate = float(tax_rate or 0)


    discount = float(discount or 0)





    tax_amount = round(

        subtotal

        *

        tax_rate

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





    items=[]



    for item in cart:


        price=float(

            item.get(

                "selling_price",

                item.get(

                    "unit_price",

                    0

                )

            )

        )


        qty=int(

            item.get(

                "qty",

                0

            )

        )


        items.append(

            {


                "name":

                    item.get(

                        "name",

                        ""

                    ),



                "product_id":

                    item.get(

                        "id"

                    ),



                "quantity":

                    qty,



                "qty":

                    qty,



                "unit_price":

                    price,



                "selling_price":

                    price,



                "price_source":

                    item.get(

                        "price_source",

                        "SYSTEM"

                    ),



                "total":

                    price * qty


            }

        )






    user = st.session_state.get(

        "user",

        {}

    )


    if isinstance(user,dict):

        cashier = (

            user.get("full_name")

            or

            user.get("username")

            or

            "Admin"

        )

    else:

        cashier="Admin"







    return {


        "invoice_no":

            rpc_data.get(

                "invoice_no",

                rpc_data.get(

                    "invoice",

                    "INV-"

                    +

                    datetime.now().strftime(

                        "%Y%m%d%H%M%S"

                    )

                )

            ),



        "date":

            datetime.now().strftime(

                "%Y-%m-%d %H:%M:%S"

            ),



        "cashier":

            cashier,



        "items":

            items,



        "subtotal":

            subtotal,



        "tax_rate":

            tax_rate,



        "tax_amount":

            tax_amount,



        "discount":

            discount,



        "grand_total":

            grand_total,



        "paid":

            float(paid_amount),



        "change":

            max(

                0,

                float(paid_amount)

                -

                grand_total

            )

    }





# ==============================================================================
# PROCESS CHECKOUT
# ==============================================================================

def process_checkout(

    cart,

    paid_amount,

    warehouse_id,

    cashier_id,

    payment_method="CASH",

    tax_rate=0,

    discount=0

):


    try:


        result = checkout_sale_rpc(


            cart=

                build_cart_payload(cart),



            paid_amount=

                float(paid_amount),



            warehouse_id=

                warehouse_id,



            cashier_id=

                cashier_id,



            payment_method=

                payment_method,



            tax_rate=

                float(tax_rate),



            discount=

                float(discount)

        )






        if not result.get(

            "success",

            False

        ):


            return {


                "success":

                    False,


                "message":

                    result.get(

                        "message",

                        "Checkout Failed"

                    )

            }






        # ==============================================================
        # CACHE REFRESH
        # ==============================================================

        try:


            CacheManager.bump(

                CACHE_KEYS["inventory"]

            )


            CacheManager.bump(

                CACHE_KEYS["products"]

            )


            CacheManager.bump(

                CACHE_KEYS["sales"]

            )


        except Exception:

            pass






        rpc_data=result.get(

            "data",

            {}

        )



        if isinstance(

            rpc_data,

            list

        ):


            rpc_data = (

                rpc_data[0]

                if rpc_data

                else {}

            )






        receipt_data = build_receipt_data(

            cart,

            rpc_data,

            paid_amount,

            tax_rate,

            discount

        )






        return {


            "success":

                True,


            "data":

                receipt_data


        }





    except Exception as e:


        return {


            "success":

                False,


            "message":

                str(e)

        }
