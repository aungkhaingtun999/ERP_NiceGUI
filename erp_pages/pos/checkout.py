# ==============================================================================
# erp_pages/pos/checkout.py
# ERP ENTERPRISE POS CHECKOUT ENGINE v12.0
#
# RESPONSIBILITY
# - Cart payload builder
# - Checkout RPC caller
# - Inventory cache refresh
# - Sale result handler
# ==============================================================================


from typing import (
    List,
    Dict,
    Any,
    Optional
)


# ==============================================================================
# ERP CORE
# ==============================================================================

from erp_core import (
    checkout_sale_rpc
)


from erp_core.context import (
    CacheManager
)



# ==============================================================================
# BUILD CHECKOUT PAYLOAD
# ==============================================================================


def build_cart_payload(
    cart: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    """
    Convert POS cart
    into ERP RPC payload format

    Output:

    [
        {
            id: product_id,
            qty: quantity,
            selling_price: price
        }
    ]

    """

    payload = []


    for item in cart:


        payload.append(

            {

                "id":
                    int(
                        item["id"]
                    ),


                "qty":
                    int(
                        item["qty"]
                    ),


                "selling_price":
                    float(
                        item["selling_price"]
                    )

            }

        )


    return payload





# ==============================================================================
# EXECUTE CHECKOUT
# ==============================================================================


def process_checkout(

    cart,

    paid_amount,

    warehouse_id,

    cashier_id,

    payment_method="CASH",

    counter_id=1,

    tax_rate=0,

    discount=0

):


    try:


        payload = build_cart_payload(

            cart

        )



        result = checkout_sale_rpc(

            cart=

                payload,


            paid_amount=

                paid_amount,


            warehouse_id=

                warehouse_id,


            cashier_id=

                cashier_id,


            counter_id=

                counter_id,


            payment_method=

                payment_method,


            tax_rate=

                tax_rate,


            discount=

                discount

        )




        # ==============================================================
        # SUCCESS
        # ==============================================================

        if result.get(
            "success",
            False
        ):


            # Refresh ERP Cache

            CacheManager.bump(

                "inventory_version"

            )


            CacheManager.bump(

                "product_version"

            )


            CacheManager.bump(

                "sales_version"

            )



            return {


                "success":

                    True,


                "data":

                    result.get(
                        "data",
                        {}
                    ),


                "message":

                    "Checkout completed"

            }





        return {


            "success":

                False,


            "message":

                result.get(

                    "message",

                    "Checkout failed"

                )

        }




    except Exception as e:


        return {


            "success":

                False,


            "message":

                str(e)

        }






# ==============================================================================
# RECEIPT DATA HELPER
# ==============================================================================


def normalize_checkout_result(
    result
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


    return data
