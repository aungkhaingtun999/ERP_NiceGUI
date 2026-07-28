# ==============================================================================
# erp_pages/pos/utils.py
# ERP ENTERPRISE POS UTILITY ENGINE v12.0
#
# Common POS Helpers
# Money
# Number Conversion
# Calculation
#
# ==============================================================================


from typing import Any, Dict, List





# ==============================================================================
# MONEY FORMAT
# ==============================================================================

def money(value: Any) -> str:
    """
    Format Myanmar Currency

    Example:
    1500 -> 1,500 MMK
    """

    try:

        return f"{float(value):,.0f} MMK"


    except Exception:

        return "0 MMK"







# ==============================================================================
# SAFE CONVERSION
# ==============================================================================

def safe_float(
    value: Any,
    default: float = 0.0
) -> float:


    try:

        return float(value)


    except Exception:

        return default






def safe_int(
    value: Any,
    default: int = 0
) -> int:


    try:

        return int(value)


    except Exception:

        return default







# ==============================================================================
# PRODUCT VALUE GETTER
# ==============================================================================

def get_value(
    data: Dict,
    key: str,
    default=None
):


    if not isinstance(
        data,
        dict
    ):

        return default



    return data.get(
        key,
        default
    )







# ==============================================================================
# CART CALCULATION
# ==============================================================================

def calculate_cart_total(
    cart: List[Dict]
):

    total = 0


    for item in cart:


        price = safe_float(

            item.get(
                "selling_price",
                0
            )

        )


        qty = safe_int(

            item.get(
                "qty",
                0
            )

        )


        total += price * qty



    return total







# ==============================================================================
# CART QUANTITY
# ==============================================================================

def calculate_cart_qty(
    cart: List[Dict]
):


    total = 0


    for item in cart:

        total += safe_int(

            item.get(
                "qty",
                0
            )

        )


    return total







# ==============================================================================
# CART ITEM COUNT
# ==============================================================================

def count_cart_items(
    cart: List[Dict]
):

    return len(cart)







# ==============================================================================
# PRODUCT DISPLAY NAME
# ==============================================================================

def product_label(
    product: Dict
):


    name = product.get(
        "name",
        ""
    )


    sku = product.get(
        "sku",
        ""
    )


    if sku:

        return f"{sku} | {name}"


    return name
