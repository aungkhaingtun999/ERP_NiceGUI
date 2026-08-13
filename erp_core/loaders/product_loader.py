# ==============================================================================
# erp_core/loaders/product_loader.py
# ERP ENTERPRISE PRODUCT LOADER v32.0 FINAL
#
# POS
#     ↓
# get_pos_products()
#     ↓
# ProductRepository.get_pos_products()
#     ↓
# pos_products_view
#
# ==============================================================================


from typing import (
    List,
    Dict,
    Any,
    Optional,
)


import streamlit as st


from erp_core.base_repo import (
    db,
    log_error,
)


from erp_core.context import (
    CacheManager,
)


from erp_core.config import (
    DEFAULT_PAGE_SIZE,
    CACHE_KEYS,
)


from erp_core.repositories import (
    RepositoryCoordinator,
)


# ==============================================================================
# POS PRODUCT QUERY CACHE
# ==============================================================================


@st.cache_data(
    show_spinner=False
)
def _get_pos_products_cached(
    warehouse_id,
    keyword,
    limit,
    version,
):

    try:

        with RepositoryCoordinator(
            db()
        ) as coord:

            return coord.products.get_pos_products(
                warehouse_id=warehouse_id,
                keyword=keyword,
                limit=limit,
            )

    except Exception as e:

        log_error(
            message=
                "POS product cache query failed",
            exception=e,
        )

        return []


# ==============================================================================
# PRODUCT MASTER QUERY CACHE
# ==============================================================================


@st.cache_data(
    show_spinner=False
)
def _get_products_cached(
    warehouse_id,
    offset,
    limit,
    version,
):

    try:

        with RepositoryCoordinator(
            db()
        ) as coord:

            return coord.products.get_products(
                warehouse_id=warehouse_id,
                offset=offset,
                limit=limit,
            )

    except Exception as e:

        log_error(
            message=
                "Product Master cache query failed",
            exception=e,
        )

        return []


# ==============================================================================
# NORMALIZE PRODUCT
# ==============================================================================


def normalize_product(
    product: Dict[str, Any],
    warehouse_id=None,
):

    if not product:

        return None

    return {

        "id":
            product.get("id"),

        "name":
            product.get(
                "name",
                "",
            ),

        "sku":
            product.get(
                "sku",
                "",
            ),

        "barcode":
            product.get(
                "barcode",
                "",
            ),

        "category_id":
            product.get(
                "category_id"
            ),

        "category":
            product.get(
                "category"
            ),

        "purchase_price":
            product.get(
                "purchase_price",
                0,
            ),

        "selling_price":
            product.get(
                "selling_price",
                0,
            ),

        "owner_selling_price":
            product.get(
                "owner_selling_price"
            ),

        "owner_price_locked":
            product.get(
                "owner_price_locked",
                False,
            ),

        "final_selling_price":
            product.get(
                "final_selling_price",
                product.get(
                    "selling_price",
                    0,
                ),
            ),

        "price_source":
            product.get(
                "price_source",
                "SYSTEM",
            ),

        "warehouse_id":
            product.get(
                "warehouse_id",
                warehouse_id,
            ),

        "qty":
            product.get(
                "qty",
                0,
            ),

        "reserved_qty":
            product.get(
                "reserved_qty",
                0,
            ),

        "available_qty":
            product.get(
                "available_qty",
                0,
            ),

        "minimum_stock":
            product.get(
                "minimum_stock",
                0,
            ),

        # ------------------------------------------------------------------
        # IMPORTANT
        # ------------------------------------------------------------------
        # pos_products_view does NOT have is_active.
        #
        # We keep this compatibility value in Python only.
        # ------------------------------------------------------------------

        "is_active":
            product.get(
                "is_active",
                True,
            ),

    }


# ==============================================================================
# PRODUCT MASTER
# ==============================================================================


def get_products(
    warehouse_id=None,
    offset=0,
    limit=DEFAULT_PAGE_SIZE,
) -> List[Dict[str, Any]]:

    products = _get_products_cached(

        warehouse_id,

        offset,

        limit,

        CacheManager.get_version(
            CACHE_KEYS["inventory"]
        ),

    )

    return [

        normalize_product(
            product,
            warehouse_id,
        )

        for product in products

        if product

    ]


# ==============================================================================
# POS PRODUCTS
# ==============================================================================


def get_pos_products(
    warehouse_id=None,
    search: Optional[str] = None,
):

    products = _get_pos_products_cached(

        warehouse_id,

        search or "",

        DEFAULT_PAGE_SIZE,

        CacheManager.get_version(
            CACHE_KEYS["inventory"]
        ),

    )

    return [

        normalize_product(
            product,
            warehouse_id,
        )

        for product in products

        if product

    ]


# ==============================================================================
# ACTIVE PRODUCTS
# ==============================================================================


def get_active_products(
    warehouse_id=None,
):

    products = get_pos_products(
        warehouse_id
    )

    return [

        product

        for product in products

        if product.get(
            "is_active",
            True,
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

        _get_pos_products_cached.clear()

        _get_products_cached.clear()

    except Exception as e:

        log_error(
            message=
                "Product cache refresh failed",
            exception=e,
        )


# ==============================================================================
# PUBLIC
# ==============================================================================

__all__ = [
    "get_products",
    "get_pos_products",
    "get_active_products",
    "refresh_products_cache",
    "normalize_product",
]
