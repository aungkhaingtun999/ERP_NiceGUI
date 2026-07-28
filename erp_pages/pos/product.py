# ==============================================================================
# erp_pages/pos/product.py
# ERP ENTERPRISE POS PRODUCT MODULE v12.0
#
# Responsibilities:
# - Load POS products
# - Search product
# - Barcode / SKU lookup
# - Product validation
#
# Database Access:
# POS
#   ↓
# Product Loader
#   ↓
# Repository
#   ↓
# Database
#
# ==============================================================================


from typing import List, Dict, Any, Optional


from erp_core.loaders.product_loader import (
    get_products
)



# ==============================================================================
# PRODUCT CACHE LOADER
# ==============================================================================


def load_pos_products(
    warehouse_id=None
) -> List[Dict[str, Any]]:
    """
    Load products for POS

    Single source of truth:
    erp_core product loader

    """

    try:

        products = get_products(
            warehouse_id=warehouse_id
        )

        return products or []


    except Exception:

        return []





# ==============================================================================
# PRODUCT SEARCH
# ==============================================================================


def search_products(
    products: List[Dict[str, Any]],
    keyword: str = ""
):


    if not keyword:

        return products



    keyword = keyword.lower().strip()


    results = []



    for product in products:


        name = str(
            product.get(
                "name",
                ""
            )
        ).lower()



        sku = str(
            product.get(
                "sku",
                ""
            )
        ).lower()



        barcode = str(
            product.get(
                "barcode",
                ""
            )
        ).lower()



        if (

            keyword in name

            or

            keyword in sku

            or

            keyword in barcode

        ):

            results.append(product)



    return results





# ==============================================================================
# FIND BY ID
# ==============================================================================


def get_product_by_id(
    products,
    product_id
):


    for product in products:


        if int(product.get("id")) == int(product_id):

            return product



    return None





# ==============================================================================
# STOCK CHECK
# ==============================================================================


def check_stock(
    product,
    qty
):


    available = int(

        product.get(

            "available_qty",

            0

        )

    )


    return qty <= available





# ==============================================================================
# PRODUCT DISPLAY
# ==============================================================================


def product_label(product):


    return (

        f"{product.get('sku','')} | "

        f"{product.get('name','')} | "

        f"Stock: "

        f"{product.get('available_qty',0)}"

  )
