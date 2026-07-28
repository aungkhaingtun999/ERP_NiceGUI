# ==============================================================================
# erp_core/loaders/product_loader.py
# ERP ENTERPRISE PRODUCT LOADER v30.3 FINAL
#
# Database
#      ↓
# Repository
#      ↓
# Loader
#      ↓
# POS / Inventory / Sales
#
# ==============================================================================


from typing import (
    List,
    Dict,
    Any,
    Optional
)


import streamlit as st



from erp_core.base_repo import (
    db,
    log_error
)


from erp_core.context import (
    CacheManager
)


from erp_core.config import (
    DEFAULT_PAGE_SIZE,
    CACHE_KEYS
)


from erp_core.repositories import (
    RepositoryCoordinator
)





# ==============================================================================
# CACHE QUERY
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

            message=

            "Product cache query failed",

            exception=e

        )


        return []







# ==============================================================================
# NORMALIZE PRODUCT
# ==============================================================================


def normalize_product(

    product: Dict[str, Any],

    warehouse_id=None

):


    if not product:

        return None




    return {


        # --------------------------------------------------
        # BASIC INFO
        # --------------------------------------------------

        "id":

            product.get("id"),


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

                "barcode",

                ""

            ),



        "category_id":

            product.get(

                "category_id"

            ),


        "category":

            product.get(

                "category"

            ),




        # --------------------------------------------------
        # COST
        # --------------------------------------------------

        "purchase_price":

            product.get(

                "purchase_price",

                0

            ),




        # --------------------------------------------------
        # PRICE ENGINE
        # --------------------------------------------------

        "selling_price":

            product.get(

                "selling_price",

                0

            ),



        "owner_selling_price":

            product.get(

                "owner_selling_price"

            ),




        "owner_price_locked":

            product.get(

                "owner_price_locked",

                False

            ),




        "final_selling_price":

            product.get(

                "final_selling_price",

                product.get(

                    "selling_price",

                    0

                )

            ),




        "price_source":

            product.get(

                "price_source",

                "SYSTEM"

            ),





        # --------------------------------------------------
        # STOCK
        # --------------------------------------------------

        "warehouse_id":

            product.get(

                "warehouse_id",

                warehouse_id

            ),




        "qty":

            product.get(

                "qty",

                0

            ),



        "reserved_qty":

            product.get(

                "reserved_qty",

                0

            ),




        "available_qty":

            product.get(

                "available_qty",

                product.get(

                    "stock",

                    0

                )

            ),




        "minimum_stock":

            product.get(

                "minimum_stock",

                0

            ),




        "is_active":

            product.get(

                "is_active",

                True

            )


    }







# ==============================================================================
# MAIN PRODUCT LOADER
# ==============================================================================


def get_products(

    warehouse_id=None,

    offset=0,

    limit=DEFAULT_PAGE_SIZE

) -> List[Dict[str, Any]]:


    products = _get_products_cached(

        warehouse_id,

        offset,

        limit,


        CacheManager.get_version(

            CACHE_KEYS["inventory"]

        )

    )




    return [

        normalize_product(

            product,

            warehouse_id

        )

        for product in products

        if product

    ]







# ==============================================================================
# POS PRODUCT LOADER
# ==============================================================================


def get_pos_products(

    warehouse_id=None,

    search: Optional[str]=None

):


    products = get_products(

        warehouse_id,

        0,

        DEFAULT_PAGE_SIZE

    )





    if search:


        keyword = str(

            search

        ).lower().strip()




        products = [

            p

            for p in products

            if (

                keyword in str(

                    p.get(

                        "name",

                        ""

                    )

                ).lower()



                or



                keyword in str(

                    p.get(

                        "sku",

                        ""

                    )

                ).lower()



                or



                keyword in str(

                    p.get(

                        "barcode",

                        ""

                    )

                ).lower()

            )

        ]





    return products







# ==============================================================================
# ACTIVE PRODUCTS
# ==============================================================================


def get_active_products():


    products = get_products()



    return [

        p

        for p in products

        if p.get(

            "is_active",

            True

        )

    ]







# ==============================================================================
# CACHE REFRESH
# ==============================================================================


def refresh_products_cache():


    try:


        CacheManager.bump(

            CACHE_KEYS["inventory"]

        )


        CacheManager.bump(

            CACHE_KEYS["products"]

        )



        CacheManager.bump(

            CACHE_KEYS["pricing"]

        )




        _get_products_cached.clear()




    except Exception as e:


        log_error(

            message=

            "Product cache refresh failed",

            exception=e

        )
