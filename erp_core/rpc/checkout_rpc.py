==============================================================================

erp_core/rpc/checkout_rpc.py

ERP ENTERPRISE CHECKOUT RPC ENGINE v12.2 FINAL



Responsibilities:

- Validate checkout request

- Normalize cart payload

- Call Supabase RPC

- Handle response safely

- Refresh ERP cache



Database Function:



checkout_sale_rpc(

p_cart,

p_paid_amount,

p_warehouse_id,

p_cashier_id,

p_counter_id,

p_payment_method,

p_tax_rate,

p_discount

)



==============================================================================

from typing import (

Any,  
Dict,  
List,  
Optional

)

from ..base_repo import (
    db,
)

from ..config import (
    CACHE_KEYS,
    log_error,
)

from ..context import (

CacheManager

)


==============================================================================

SAFE CONVERTER

==============================================================================

def safe_float(

value,  

default=0

):

try:  

    return float(value)  


except Exception:  

    return float(default)

def safe_int(

value,  

default=0

):

try:  

    return int(value)  


except Exception:  

    return int(default)

==============================================================================

CART NORMALIZER

==============================================================================

def normalize_cart(

cart: List[Dict[str, Any]]

):

result = []  



for item in cart:  



    if not item.get(  

        "id"  

    ):  

        continue  





    result.append(  

        {  


            "id":  

                safe_int(  

                    item.get(  

                        "id"  

                    )  

                ),  



            "qty":  

                safe_int(  

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



return result

==============================================================================

CACHE REFRESH

==============================================================================

def refresh_checkout_cache():

try:  


    CacheManager.bump(  

        CACHE_KEYS["inventory"]  

    )  



except Exception:  

    pass  





try:  


    CacheManager.bump(  

        CACHE_KEYS["products"]  

    )  



except Exception:  

    pass  





try:  


    CacheManager.bump(  

        CACHE_KEYS["sales"]  

    )  



except Exception:  

    pass

==============================================================================

CHECKOUT RPC

==============================================================================

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



    # ----------------------------------------------------------  
    # VALIDATION  
    # ----------------------------------------------------------  


    if not cart:  



        return {  


            "success":  

                False,  


            "message":  

                "Cart is empty."  

        }  






    if warehouse_id is None:  



        return {  


            "success":  

                False,  


            "message":  

                "Warehouse not selected."  

        }  






    if not cashier_id:  



        return {  


            "success":  

                False,  


            "message":  

                "Cashier not found."  

        }  







    # ----------------------------------------------------------  
    # CART  
    # ----------------------------------------------------------  


    rpc_cart = normalize_cart(  

        cart  

    )  



    if not rpc_cart:  



        return {  


            "success":  

                False,  


            "message":  

                "Invalid cart data."  

        }  







    # ----------------------------------------------------------  
    # PAYLOAD  
    # ----------------------------------------------------------  


    payload = {  



        "p_cart":  

            rpc_cart,  



        "p_paid_amount":  

            safe_float(  

                paid_amount  

            ),  



        "p_warehouse_id":  

            safe_int(  

                warehouse_id  

            ),  



        "p_cashier_id":  

            cashier_id,  



        "p_counter_id":  

            safe_int(  

                counter_id  

            ),  



        "p_payment_method":  

            str(  

                payment_method  

            ).upper(),  



        "p_tax_rate":  

            safe_float(  

                tax_rate  

            ),  



        "p_discount":  

            safe_float(  

                discount  

            )  

    }  








    # ----------------------------------------------------------  
    # EXECUTE SUPABASE RPC  
    # ----------------------------------------------------------  


    response = (  

        db()  

        .rpc(  

            "checkout_sale_rpc",  

            payload  

        )  

        .execute()  

    )  







    result = getattr(  

        response,  

        "data",  

        response  

    )  







    # ----------------------------------------------------------  
    # DICT RESPONSE  
    # ----------------------------------------------------------  


    if isinstance(  

        result,  

        dict  

    ):  



        if result.get(  

            "success",  

            False  

        ):  


            refresh_checkout_cache()  



        return result  







    # ----------------------------------------------------------  
    # LIST RESPONSE  
    # ----------------------------------------------------------  


    if isinstance(  

        result,  

        list  

    ):  



        if len(result) == 1 and isinstance(  

            result[0],  

            dict  

        ):  



            if result[0].get(  

                "success",  

                False  

            ):  


                refresh_checkout_cache()  



            return result[0]  





        return {  


            "success":  

                True,  


            "data":  

                result  

        }  







    # ----------------------------------------------------------  
    # EMPTY  
    # ----------------------------------------------------------  


    if result is None:  



        return {  


            "success":  

                False,  


            "message":  

                "Empty RPC response."  

        }  







    # ----------------------------------------------------------  
    # OTHER TYPE  
    # ----------------------------------------------------------  


    return {  


        "success":  

            True,  


        "data":  

            result  

    }  







except Exception as e:  



    log_error(  

        message=  

            "checkout_sale_rpc failed",  

        exception=  

            e,  

        rpc=  

            "checkout_sale_rpc"  

    )  



    return {  


        "success":  

            False,  


        "message":  

            str(e)  

    }
