# ==============================================================================
# erp_core/loaders/product_loader.py
# ERP ENTERPRISE PRODUCT LOADER v30.1
#
# Product Source Of Truth
#
# Database
#    ↓
# Repository
#    ↓
# Loader
#    ↓
# POS / Inventory / Sales
#
# ==============================================================================


from typing import Any, Dict, List


import streamlit as st



from erp_core.base_repo import (
    db,
    log_error
)


from erp_core.context import (
    CacheManager
)


from erp_core.config import (
    DEFAULT_PAGE_SIZE
)


from erp_core.repositories import (
    RepositoryCoordinator
)





# ==============================================================================
# INTERNAL CACHE QUERY
# ==============================================================================


@st.cache_data
def _get_products_cached(
    warehouse_id,
    offset,
    limit,
    version
):

    try:

        with RepositoryCoordinator(
            db()
        ) as coord:


            return coord.products.get_products(

                warehouse_id,

                offset,

                limit

            )


    except Exception as e:


        log_error(

            f"product loader error: {e}"

        )


        return []







# ==============================================================================
# MAIN PRODUCT LOADER
# ==============================================================================


def get_products(

    warehouse_id=None,

    offset=0,

    limit=DEFAULT_PAGE_SIZE

):


    return _get_products_cached(

        warehouse_id,

        offset,

        limit,


        CacheManager.get_version(

            "inventory_version"

        )

    )







# ==============================================================================
# CACHE REFRESH
# ==============================================================================


def refresh_products_cache():

    """
    Force POS / Inventory product refresh

    After:
        - Sale
        - Refund
        - Stock Transfer
        - Adjustment

    """

    try:


        CacheManager.bump(

            "inventory_version"

        )


        _get_products_cached.clear()



    except Exception as e:


        log_error(

            f"refresh product cache error: {e}"

        )







# ==============================================================================
# ACTIVE PRODUCTS
# ==============================================================================


def get_active_products():


    return get_products(

        warehouse_id=None,

        offset=0,

        limit=DEFAULT_PAGE_SIZE

    )







# ==============================================================================
# POS PRODUCT LOADER
# ==============================================================================


def get_pos_products(

    warehouse_id=None,

    search=None

):


    products = get_products(

        warehouse_id=warehouse_id,

        offset=0,

        limit=DEFAULT_PAGE_SIZE

    )




    if search:


        keyword = str(search).lower().strip()



        products = [

            p

            for p in products

            if (

                keyword in str(
                    p.get("name","")
                ).lower()


                or


                keyword in str(
                    p.get("sku","")
                ).lower()


                or


                keyword in str(
                    p.get("barcode","")
                ).lower()

            )

        ]





    pos_products = []




    for p in products:


        if not p:

            continue




        pos_products.append({


            "id":

                p.get("id"),



            "name":

                p.get("name"),



            "sku":

                p.get("sku"),



            "barcode":

                p.get("barcode"),



            "purchase_price":

                p.get(
                    "purchase_price",
                    0
                ),



            "selling_price":

                p.get(
                    "selling_price",
                    0
                ),



            "owner_selling_price":

                p.get(
                    "owner_selling_price"
                ),



            "final_selling_price":

                p.get(
                    "final_selling_price",
                    p.get(
                        "selling_price",
                        0
                    )
                ),



            "price_source":

                p.get(
                    "price_source",
                    "SYSTEM"
                ),



            "owner_price_locked":

                p.get(
                    "owner_price_locked",
                    False
                ),



            "available_qty":

                p.get(

                    "available_qty",

                    p.get(
                        "stock",
                        0
                    )

                ),



            "warehouse_id":

                warehouse_id


        })



    return pos_products
