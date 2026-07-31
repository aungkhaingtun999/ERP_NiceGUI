# ==============================================================================
# ERP INVENTORY MODULE
# ERP ENTERPRISE v31
#
# Core:
# - Inventory Service
# - Warehouse Support
# - Stock Management
#
# ==============================================================================


import streamlit as st


from erp_core.services.inventory_service import (
    InventoryService
)


from erp_core import (
    get_inventory_view,
    get_warehouses,
    get_default_warehouse_id,
    log_error
)





# ==============================================================================
# SERVICE INSTANCE
# ==============================================================================


def get_inventory_service():

    try:

        return InventoryService()


    except Exception as e:

        log_error(
            f"InventoryService init error: {e}"
        )

        return None





# ==============================================================================
# INVENTORY LOADER
# ==============================================================================


@st.cache_data(ttl=300)
def load_inventory():

    try:

        return get_inventory_view()


    except Exception as e:

        log_error(
            f"Inventory load error: {e}"
        )

        return []





# ==============================================================================
# WAREHOUSE
# ==============================================================================


def load_default_warehouse():

    try:

        return get_default_warehouse_id()


    except Exception as e:

        log_error(
            f"default warehouse error: {e}"
        )

        return None





def load_warehouses():

    try:

        return get_warehouses()


    except Exception as e:

        log_error(
            f"warehouse loading error: {e}"
        )

        return []
