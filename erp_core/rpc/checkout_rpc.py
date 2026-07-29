# ==============================================================================
# erp_core/rpc/checkout_rpc.py
# ERP ENTERPRISE CHECKOUT RPC
# FINAL PRODUCTION v12.1
# ==============================================================================


from typing import (
    Any,
    Dict,
    List,
    Optional
)


from ..base_repo import (
    db,
    log_error
)


from ..context import (
    CacheManager
)




def checkout_sale_rpc(

    cart: List[Dict[str, Any]],

    paid_amount: Any = 0,

    warehouse_id: Optional[int] = None,

    cashier_id: Optional[str] = None,

    counter_id: int = 1,

    payment_method: str = "CASH",

    tax_rate: Any = 0,

    discount: Any = 0

):


    try:


        if not cart:

            return {
                "success":False,
                "message":"Cart is empty."
            }



        if warehouse_id is None:

            return {
                "success":False,
                "message":"Warehouse missing."
            }



        if cashier_id is None:

            return {
                "success":False,
                "message":"Cashier missing."
            }



        rpc_cart=[]



        for item in cart:


            rpc_cart.append(

                {

                    "id":
                        int(
                            item.get(
                                "id"
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





        payload={


            "p_cart":
                rpc_cart,


            "p_paid_amount":
                float(
                    paid_amount
                ),


            "p_warehouse_id":
                int(
                    warehouse_id
                ),


            "p_cashier_id":
                cashier_id,


            "p_counter_id":
                int(
                    counter_id
                ),


            "p_payment_method":
                str(
                    payment_method
                ).upper(),


            "p_tax_rate":
                float(
                    tax_rate
                ),


            "p_discount":
                float(
                    discount
                )

        }





        response=(

            db()

            .rpc(

                "checkout_sale_rpc",

                payload

            )

            .execute()

        )



        result=response.data





        if isinstance(
            result,
            list
        ):


            if len(result)==1 and isinstance(
                result[0],
                dict
            ):

                result=result[0]


            else:

                result={

                    "success":True,

                    "data":result

                }





        if not isinstance(
            result,
            dict
        ):

            return {

                "success":True,

                "data":result

            }





        if result.get(
            "success",
            False
        ):


            try:

                CacheManager.refresh_inventory()

            except Exception:

                pass



            try:

                CacheManager.refresh_products()

            except Exception:

                pass




        return result




    except Exception as e:


        log_error(

            message="checkout_sale_rpc failed",

            exception=e

        )


        return {


            "success":False,

            "message":str(e)

        }
