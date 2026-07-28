# ==============================================================================
# erp_core/loaders/product_loader.py
# ERP ENTERPRISE PRODUCT LOADER v30
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


    if not search:

        return products



    search = search.lower()



    return [

        p

        for p in products

        if search in str(
            p.get("name","")
        ).lower()

        or search in str(
            p.get("sku","")
        ).lower()

        or search in str(
            p.get("barcode","")
        ).lower()

    ]
    # ==============================================================================
# POS PRODUCT LOADER
# ==============================================================================

def get_pos_products(
    warehouse_id=None
):

    """
    POS Product Source

    Single Source Of Truth
    Used By:
        - POS
        - Inventory
        - Sales

    """

    products = get_products(

        warehouse_id=warehouse_id,

        offset=0,

        limit=DEFAULT_PAGE_SIZE

    )


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


            "selling_price":
                p.get("selling_price",0),


            "stock":
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
