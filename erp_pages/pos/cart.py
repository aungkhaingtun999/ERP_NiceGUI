# ==============================================================================
# erp_pages/pos/cart.py
# ERP ENTERPRISE POS CART ENGINE v12.0
#
# Responsibilities:
# - Add product to cart
# - Merge duplicate items
# - Remove cart item
# - Update quantity
# - Calculate totals
#
# ==============================================================================


from typing import List, Dict, Any


# ==============================================================================
# ADD ITEM
# ==============================================================================

def add_to_cart(
    cart: List[Dict[str, Any]],
    product: Dict[str, Any],
    qty: int,
    price: float,
    price_source: str = "SYSTEM"
):
    """
    Add product into cart.

    If product already exists:
        increase quantity

    Else:
        create new cart row
    """


    product_id = product.get("id")


    for item in cart:

        if item.get("id") == product_id:

            item["qty"] += int(qty)

            return cart



    cart.append(

        {

            "id": product_id,

            "name": product.get(
                "name",
                ""
            ),

            "sku": product.get(
                "sku",
                ""
            ),

            "qty": int(qty),

            "selling_price": float(price),

            "price_source": price_source

        }

    )


    return cart





# ==============================================================================
# REMOVE ITEM
# ==============================================================================

def remove_from_cart(
    cart: List[Dict[str, Any]],
    index: int
):

    try:

        cart.pop(index)

    except Exception:

        pass


    return cart





# ==============================================================================
# CLEAR CART
# ==============================================================================

def clear_cart():

    return []





# ==============================================================================
# UPDATE QUANTITY
# ==============================================================================

def update_quantity(
    cart: List[Dict[str, Any]],
    index: int,
    qty: int
):


    try:

        if qty <= 0:

            cart.pop(index)

        else:

            cart[index]["qty"] = int(qty)


    except Exception:

        pass


    return cart





# ==============================================================================
# CART TOTAL
# ==============================================================================

def calculate_subtotal(
    cart: List[Dict[str, Any]]
):


    total = 0


    for item in cart:

        total += (

            float(
                item.get(
                    "selling_price",
                    0
                )
            )

            *

            int(
                item.get(
                    "qty",
                    0
                )
            )

        )


    return round(
        total,
        2
    )





def calculate_total_qty(
    cart: List[Dict[str, Any]]
):


    return sum(

        int(
            item.get(
                "qty",
                0
            )
        )

        for item in cart

    )





def cart_count(
    cart: List[Dict[str, Any]]
):

    return len(cart)





# ==============================================================================
# STOCK CHECK
# ==============================================================================

def check_available_stock(
    cart,
    product_id,
    available_qty,
    add_qty
):


    current_qty = sum(

        item["qty"]

        for item in cart

        if item["id"] == product_id

    )


    return (

        current_qty + add_qty

        <=

        int(available_qty)

    )





# ==============================================================================
# CART TABLE DATA
# ==============================================================================

def get_cart_rows(cart):


    rows = []


    for item in cart:


        rows.append(

            {

                "Product":
                    item.get(
                        "name",
                        ""
                    ),


                "Qty":
                    item.get(
                        "qty",
                        0
                    ),


                "Price Source":
                    item.get(
                        "price_source",
                        "SYSTEM"
                    ),


                "Unit Price":
                    item.get(
                        "selling_price",
                        0
                    ),


                "Amount":

                    (

                        item.get(
                            "selling_price",
                            0
                        )

                        *

                        item.get(
                            "qty",
                            0
                        )

                    )

            }

        )


    return rows
