# ==============================================================================
# erp_pages/pos/engine.py
# ERP ENTERPRISE POS PRICE ENGINE v12.1
#
# PRICE PRIORITY
#
# OWNER LOCK
#      ↓
# FINAL SELLING PRICE
#      ↓
# SELLING PRICE
#
# ==============================================================================


from typing import Dict, Any





# ==============================================================================
# SAFE NUMBER
# ==============================================================================


def safe_float(value, default=0.0):

    try:

        if value is None:

            return default


        return float(value)


    except Exception:

        return default






# ==============================================================================
# MONEY FORMAT
# ==============================================================================


def money(value):

    try:

        return f"{float(value):,.0f} MMK"


    except Exception:

        return "0 MMK"







# ==============================================================================
# FINAL PRICE ENGINE
# ==============================================================================


def get_final_price(
    product: Dict[str, Any]
):


    """
    POS price source resolver


    Priority:


    1. OWNER LOCKED PRICE


    2. ERP FINAL SELLING PRICE


    3. SELLING PRICE


    """



    # ==============================================================
    # OWNER LOCKED PRICE
    # ==============================================================


    if (

        product.get(
            "owner_price_locked",
            False
        )

        and

        product.get(
            "owner_selling_price"
        )
        is not None

    ):


        return {


            "price":

                safe_float(

                    product.get(
                        "owner_selling_price"
                    )

                ),


            "source":

                "OWNER"


        }







    # ==============================================================
    # ERP PRICE ENGINE RESULT
    # ==============================================================


    if product.get(
        "final_selling_price"
    ) is not None:


        return {


            "price":

                safe_float(

                    product.get(
                        "final_selling_price"
                    )

                ),


            "source":

                product.get(

                    "price_source",

                    "SYSTEM"

                )


        }







    # ==============================================================
    # FALLBACK
    # ==============================================================


    return {


        "price":

            safe_float(

                product.get(

                    "selling_price",

                    0

                )

            ),


        "source":

            "MANUAL"


    }







# ==============================================================================
# SIMPLE PRICE ONLY
# ==============================================================================


def get_price(product):


    return get_final_price(
        product
    )["price"]







# ==============================================================================
# PRICE LABEL
# ==============================================================================


def get_price_label(product):


    data = get_final_price(
        product
    )


    return (

        money(

            data["price"]

        )

        +

        " | "

        +

        str(

            data["source"]

        )

    )
