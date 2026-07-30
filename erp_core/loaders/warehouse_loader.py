# ==============================================================================
# erp_core/loaders/warehouse_loader.py
# ERP ENTERPRISE WAREHOUSE LOADER v30
# ==============================================================================


import streamlit as st


from ..base_repo import (
    db,
    log_error
)


from ..config import (
    Tables
)


from ..context import (
    CacheManager
)


from ..repositories import (
    RepositoryCoordinator
)





@st.cache_data(ttl=300)
def _get_warehouses_cached(
    version: int
):

    try:

        with RepositoryCoordinator(
            db()
        ) as coord:

            return coord.warehouses.get_active_warehouses()


    except Exception as e:

        log_error(
            f"warehouse loader error: {e}"
        )

        return []





def get_warehouses():

    return _get_warehouses_cached(

        CacheManager.get_version(
            "inventory_version"
        )

    )





def get_default_warehouse_id():


    try:


        result = (

            db()

            .table(
                Tables.SETTINGS
            )

            .select(
                "value"
            )

            .eq(
                "key",
                "DEFAULT_WAREHOUSE_ID"
            )

            .limit(1)

            .execute()

        )


        if result.data:


            return int(
                result.data[0]["value"]
            )


    except Exception as e:


        log_error(
            f"default warehouse setting error: {e}"
        )



    # fallback
    warehouses = get_warehouses()


    if warehouses:

        return warehouses[0].get(
            "id",
            1
        )


    return None
