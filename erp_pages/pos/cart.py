# ==============================================================================
# erp_pages/pos/cart.py
# ERP ENTERPRISE POS CART ENGINE v12.2
#
# Responsibilities:
# - Add product
# - Merge duplicate item
# - Remove item
# - Update quantity
# - Calculate totals
#
# ==============================================================================


from typing import (
    List,
    Dict,
    Any
)





# ==============================================================================
# ADD TO CART
# ==============================================================================


def add_to_cart(

    cart: List[Dict[str, Any]],

    product: Dict[str, Any],

    qty: int,

    price: float,

    price_source: str = "SYSTEM"

):


    product_id = product.get(

        "id"

    )



    qty = int(qty)

    price = float(price)





    # ==============================================================
    # MERGE EXISTING ITEM
    # ==============================================================


    for item in cart:


        if item.get("id") == product_id:


            item["qty"] += qty


            item["unit_price"] = price


            item["selling_price"] = price


            item["price_source"] = price_source



            return cart





    # ==============================================================
    # NEW CART ITEM
    # ==============================================================


    cart.append(

        {


            "id":

                product_id,



            "name":

                product.get(

                    "name",

                    ""

                ),



            "sku":

                product.get(

                    "sku",

                    ""

                ),



            "barcode":

                product.get(

                    "barcode"

                ),



            "qty":

                qty,



            "unit_price":

                price,



            # backward compatibility

            "selling_price":

                price,



            "price_source":

                price_source



        }

    )



    return cart







# ==============================================================================
# REMOVE ITEM
# ==============================================================================


def remove_from_cart(

    cart,

    index

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

    cart,

    index,

    qty

):


    try:


        qty = int(qty)



        if qty <= 0:


            cart.pop(index)



        else:


            cart[index]["qty"] = qty



    except Exception:

        pass



    return cart
    # ==============================================================================
# INCREASE QUANTITY
# ==============================================================================

def increase_quantity(

    cart,

    index,

    step=1

):

    try:

        cart[index]["qty"] = int(
            cart[index].get(
                "qty",
                0
            )
        ) + int(step)


    except Exception:

        pass


    return cart





# ==============================================================================
# DECREASE QUANTITY
# ==============================================================================

def decrease_quantity(

    cart,

    index,

    step=1

):

    try:


        current_qty = int(

            cart[index].get(

                "qty",

                0

            )

        )


        new_qty = current_qty - int(step)



        if new_qty <= 0:


            cart.pop(index)


        else:


            cart[index]["qty"] = new_qty



    except Exception:


        pass



    return cart







# ==============================================================================
# SUBTOTAL
# ==============================================================================


def calculate_subtotal(

    cart: List[Dict[str, Any]]

):


    total = 0



    for item in cart:


        price = float(

            item.get(

                "unit_price",

                item.get(

                    "selling_price",

                    0

                )

            )

        )



        qty = int(

            item.get(

                "qty",

                0

            )

        )



        total += price * qty





    return round(

        total,

        2

    )







# ==============================================================================
# TOTAL QUANTITY
# ==============================================================================


def calculate_total_qty(

    cart

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







# ==============================================================================
# CART COUNT
# ==============================================================================


def cart_count(

    cart

):

    return len(cart)







# ==============================================================================
# STOCK VALIDATION
# ==============================================================================


def check_available_stock(

    cart,

    product_id,

    available_qty,

    add_qty

):


    current_qty = sum(

        int(

            item.get(

                "qty",

                0

            )

        )

        for item in cart

        if item.get(

            "id"

        ) == product_id

    )



    return (

        current_qty + int(add_qty)

        <=

        int(

            available_qty

        )

    )







# ==============================================================================
# CART TABLE DATA
# ==============================================================================


def get_cart_rows(

    cart

):


    rows = []



    for item in cart:


        price = float(

            item.get(

                "unit_price",

                item.get(

                    "selling_price",

                    0

                )

            )

        )


        qty = int(

            item.get(

                "qty",

                0

            )

        )



        rows.append(

            {


                "Product":

                    item.get(

                        "name",

                        ""

                    ),



                "Qty":

                    qty,



                "Price Source":

                    item.get(

                        "price_source",

                        "SYSTEM"

                    ),



                "Unit Price":

                    price,



                "Amount":

                    price * qty


            }

        )



    return rows
