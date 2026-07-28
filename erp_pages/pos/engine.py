# ==============================================================================
# erp_pages/pos/engine.py
# ERP ENTERPRISE POS PRICE ENGINE v12.0
#
# RESPONSIBILITY
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


from typing import (
    Dict,
    Any
)



# ==============================================================================
# SAFE NUMBER
# ==============================================================================


def safe_float(
    value,
    default=0.0
):

    try:

        if value is None:

            return default


        return float(value)


    except Exception:

        return default





# ==============================================================================
# MONEY FORMAT
# ==============================================================================


def money(
    value
):

    """
    Myanmar Kyat formatter

    Example:

    1500
    =>
    1,500 MMK

    """

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
    POS Selling Price Priority


    1. OWNER MANUAL PRICE

    2. FINAL SELLING PRICE
       (Product/Category/System markup result)

    3. CURRENT SELLING PRICE


    """



    # ==============================================================
    # OWNER LOCKED PRICE
    # ==============================================================


    owner_locked = product.get(

        "owner_price_locked",

        False

    )


    owner_price = product.get(

        "owner_selling_price"

    )



    if owner_locked and owner_price is not None:


        return {


            "price":

                safe_float(

                    owner_price

                ),


            "source":

                "OWNER"


        }





    # ==============================================================
    # OWNER PRICE WITHOUT LOCK
    # ==============================================================


    if owner_price is not None:


        return {


            "price":

                safe_float(

                    owner_price

                ),


            "source":

                "OWNER"


        }





    # ==============================================================
    # FINAL ENGINE PRICE
    # ==============================================================


    final_price = product.get(

        "final_selling_price"

    )



    if final_price is not None:


        return {


            "price":

                safe_float(

                    final_price

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

            "CURRENT_PRICE"


    }





# ==============================================================================
# PRICE DISPLAY
# ==============================================================================


def get_price_label(
    product
):


    price_data = get_final_price(

        product

    )


    return (

        money(

            price_data["price"]

        )

        +

        " | "

        +

        str(

            price_data["source"]

        )

    )
