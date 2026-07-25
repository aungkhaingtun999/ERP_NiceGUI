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


@st.cache_data(ttl=300)
def _get_products_cached(
    warehouse_id,
    offset,
    limit,
    version
) -> List[Dict[str, Any]]:

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
