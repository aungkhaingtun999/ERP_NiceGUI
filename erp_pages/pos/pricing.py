# ==============================================================================
# erp_pages/pos/pricing.py
# ERP ENTERPRISE POS PRICING ENGINE v12.0
#
# OWNER PRICE
#       ↓
# PRODUCT MARKUP
#       ↓
# CATEGORY MARKUP
#       ↓
# GLOBAL MARKUP
#       ↓
# FINAL PRICE
#
# ==============================================================================


from decimal import Decimal


# ==============================================================================
# MONEY CONVERTER
# ==============================================================================

def to_float(value, default=0):

    try:

        if value is None:
            return float(default)

        return float(value)

    except Exception:

        return float(default)



# ==============================================================================
# PRICE FORMAT
# ==============================================================================

def money(value):

    try:

        return f"{float(value):,.0f} MMK"

    except Exception:

        return "0 MMK"



# ==============================================================================
# MAIN PRICE ENGINE
# ==============================================================================

def calculate_final_price(product):

    """
    ERP PRICE PRIORITY ENGINE


    OWNER MANUAL PRICE
            ↓
    PRODUCT MARKUP
            ↓
    CATEGORY MARKUP
            ↓
    GLOBAL MARKUP
            ↓
    CURRENT SELLING PRICE


    Return:

    {
        price: float,
        source: str
    }

    """



    # ==========================================================
    # 1. OWNER LOCK PRICE
    # ==========================================================

    owner_locked = product.get(
        "owner_price_locked",
        False
    )


    owner_price = product.get(
        "owner_selling_price"
    )


    if owner_locked and owner_price is not None:


        return {

            "price": to_float(
                owner_price
            ),

            "source": "OWNER"

        }





    # ==========================================================
    # 2. FINAL SELLING PRICE FROM DATABASE VIEW
    # ==========================================================

    final_price = product.get(
        "final_selling_price"
    )


    if final_price is not None:


        return {

            "price": to_float(
                final_price
            ),

            "source": product.get(
                "price_source",
                "SYSTEM"
            )

        }





    # ==========================================================
    # 3. PRODUCT MARKUP FALLBACK
    # ==========================================================

    purchase_price = to_float(

        product.get(
            "purchase_price"
        )

    )


    product_markup = to_float(

        product.get(
            "product_markup"
        )

    )


    if purchase_price > 0 and product_markup > 0:


        price = (

            purchase_price

            +

            (
                purchase_price
                *
                product_markup
                /
                100
            )

        )


        return {

            "price": price,

            "source": "PRODUCT_MARKUP"

        }





    # ==========================================================
    # 4. CURRENT SELLING PRICE
    # ==========================================================

    selling_price = product.get(
        "selling_price",
        0
    )


    return {

        "price": to_float(
            selling_price
        ),

        "source": "CURRENT_PRICE"

    }




# ==============================================================================
# CART UNIT PRICE HELPER
# ==============================================================================

def get_unit_price(product):

    result = calculate_final_price(
        product
    )

    return result["price"]




# ==============================================================================
# PRICE SOURCE DISPLAY
# ==============================================================================

def get_price_source(product):

    result = calculate_final_price(
        product
    )

    return result["source"]
