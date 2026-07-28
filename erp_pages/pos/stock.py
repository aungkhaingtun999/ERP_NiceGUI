# ==============================================================================
# erp_pages/pos/stock.py
# ERP ENTERPRISE POS STOCK ENGINE v12.0
#
# Stock Validation
# Inventory Check
# Warehouse Control
#
# ==============================================================================


from typing import Dict, Any, List


# ==============================================================================
# STOCK VALUE
# ==============================================================================

def get_available_qty(product: Dict[str, Any]) -> int:
    """
    Get current available stock
    """

    try:

        return int(
            product.get(
                "available_qty",
                0
            )
        )

    except Exception:

        return 0





# ==============================================================================
# STOCK CHECK
# ==============================================================================

def check_stock(
    product: Dict[str, Any],
    qty: int
) -> Dict[str, Any]:
    """
    Check single product stock
    """

    available = get_available_qty(
        product
    )


    requested = int(qty)


    if requested <= available:

        return {

            "success": True,

            "available": available,

            "requested": requested,

            "message": "Stock available"

        }



    return {

        "success": False,

        "available": available,

        "requested": requested,

        "message": (

            f"Insufficient stock. "

            f"Available: {available}"

        )

    }





# ==============================================================================
# CART STOCK VALIDATION
# ==============================================================================

def validate_cart_stock(
    cart: List[Dict[str, Any]],
    products: List[Dict[str, Any]]
):

    """
    Validate whole cart before checkout

    """


    product_map = {

        p["id"]: p

        for p in products

    }


    errors = []



    for item in cart:


        product = product_map.get(
            item["id"]
        )


        if not product:


            errors.append({

                "product_id": item["id"],

                "message": "Product not found"

            })

            continue



        result = check_stock(

            product,

            item["qty"]

        )



        if not result["success"]:


            errors.append({

                "product_id": item["id"],

                "product": product.get(
                    "name",
                    ""
                ),

                "message": result["message"]

            })




    return {


        "success":

            len(errors) == 0,


        "errors":

            errors

    }





# ==============================================================================
# DISPLAY HELPER
# ==============================================================================

def stock_status_text(product):


    qty = get_available_qty(
        product
    )


    if qty <= 0:

        return "❌ Out of Stock"


    if qty <= int(
        product.get(
            "minimum_stock",
            0
        )
    ):

        return "⚠ Low Stock"



    return "✅ Available"
