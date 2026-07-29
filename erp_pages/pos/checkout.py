# ==============================================================================
# erp_pages/pos/checkout.py
# ERP ENTERPRISE POS CHECKOUT ENGINE v12.9 FINAL
#
# Responsibilities:
# - Cart validation
# - RPC checkout bridge
# - Receipt data builder
# - Cache refresh
#
# Flow:
#
# CART
#   ↓
# CHECKOUT RPC
#   ↓
# SALE RESULT
#   ↓
# RECEIPT DATA
#
# ==============================================================================


from datetime import datetime


from erp_core import checkout_sale_rpc


from erp_core.context import (
    CacheManager
)


from erp_core.config import (
    CACHE_KEYS
)





# ==============================================================================
# SAFE NUMBER
# ==============================================================================


def safe_float(

    value,

    default=0

):

    try:

        return float(value)


    except Exception:

        return float(default)





# ==============================================================================
# CART PAYLOAD
# ==============================================================================


def build_cart_payload(cart):


    payload = []



    for item in cart:


        payload.append(

            {


                "id":

                    int(

                        item.get(

                            "id",

                            0

                        )

                    ),



                "qty":

                    int(

                        item.get(

                            "qty",

                            0

                        )

                    ),



                "selling_price":

                    safe_float(

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



    subtotal = 0


    items = []



    for item in cart:


        price = safe_float(

            item.get(

                "selling_price",

                item.get(

                    "unit_price",

                    0

                )

            )

        )


        qty = int(

            item.get(

                "qty",

                0

            )

        )


        amount = price * qty



        subtotal += amount



        items.append(

            {


                "name":

                    item.get(

                        "name",

                        "Unknown"

                    ),



                "product_id":

                    item.get(

                        "id"

                    ),



                "quantity":

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

                    amount


            }

        )





    tax_amount = (

        subtotal

        *

        safe_float(tax_rate)

        /

        100

    )





    grand_total = max(

        0,

        subtotal

        +

        tax_amount

        -

        safe_float(discount)

    )





    invoice_no = (

        rpc_data.get(

            "invoice_no"

        )

        or

        rpc_data.get(

            "invoice"

        )

        or

        "INV-"

        +

        datetime.now().strftime(

            "%Y%m%d%H%M%S"

        )

    )





    return {



        "invoice_no":

            invoice_no,



        "date":

            datetime.now().strftime(

                "%Y-%m-%d %H:%M:%S"

            ),



        "cashier":

            "Admin",



        "items":

            items,



        "subtotal":

            round(

                subtotal,

                2

            ),



        "tax_rate":

            safe_float(

                tax_rate

            ),



        "tax_amount":

            round(

                tax_amount,

                2

            ),



        "discount":

            safe_float(

                discount

            ),



        "grand_total":

            round(

                grand_total,

                2

            ),



        "paid":

            safe_float(

                paid_amount

            ),



        "change":

            max(

                0,

                safe_float(

                    paid_amount

                )

                -

                grand_total

            ),



        "sale_id":

            rpc_data.get(

                "sale_id"

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



        if not cart:


            return {


                "success":

                    False,


                "message":

                    "Cart is empty."

            }







        result = checkout_sale_rpc(


            cart=

                build_cart_payload(

                    cart

                ),



            paid_amount=

                paid_amount,



            warehouse_id=

                warehouse_id,



            cashier_id=

                cashier_id,



            payment_method=

                payment_method,



            tax_rate=

                tax_rate,



            discount=

                discount

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

                        "Checkout failed."

                    )

            }







        # ----------------------------------------------------------
        # CACHE UPDATE
        # ----------------------------------------------------------


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





        rpc_data = result.get(

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
