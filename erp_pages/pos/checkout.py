# ==============================================================================
# ERP POS CHECKOUT ENGINE v12.1 FINAL
# ==============================================================================


from erp_core import (
    checkout_sale_rpc
)


from erp_core.context import (
    CacheManager
)


from erp_core.config import (
    CACHE_KEYS
)





def build_cart_payload(cart):


    return [

        {

            "id":
                int(item["id"]),


            "qty":
                int(item["qty"]),


            "selling_price":
                float(item["selling_price"])

        }

        for item in cart

    ]







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




        if result.get(
            "success",
            False
        ):



            CacheManager.bump(

                CACHE_KEYS["inventory"]

            )



            CacheManager.bump(

                CACHE_KEYS["products"]

            )



            CacheManager.bump(

                CACHE_KEYS["sales"]

            )




            return {

                "success":

                    True,


                "data":

                    result.get(
                        "data",
                        {}
                    )

            }





        return {


            "success":

                False,


            "message":

                result.get(
                    "message",
                    "Checkout Failed"
                )

        }





    except Exception as e:


        return {


            "success":

                False,


            "message":

                str(e)

        }
