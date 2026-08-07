# ==============================================================================
# ERP INVENTORY MODULE
# ERP ENTERPRISE v31.1 STABLE
#
# Core:
# - Inventory Service
# - Warehouse Support
# - Stock Management
# - Safe Error Handling
# - Cache Support
# ==============================================================================

import streamlit as st

from erp_core.services.inventory_service import InventoryService
from erp_core import (
    get_inventory_view,
    get_warehouses,
    get_default_warehouse_id,
    log_error
)

# ==============================================================================
# SERVICE INSTANCE
# ==============================================================================

@st.cache_resource
def get_inventory_service():
    """
    Create InventoryService only once per Streamlit session.
    """
    try:
        return InventoryService()

    except Exception as e:
        log_error(f"InventoryService init error: {e}")
        return None


# ==============================================================================
# INVENTORY LOADER
# ==============================================================================

@st.cache_data(ttl=300)
def load_inventory():
    """
    Load inventory summary from database.
    Cached for 5 minutes.
    """
    try:
        data = get_inventory_view()

        if data is None:
            return []

        return data

    except Exception as e:
        log_error(f"Inventory load error: {e}")
        return []


def refresh_inventory_cache():
    """
    Clear inventory cache after stock changes.
    """
    load_inventory.clear()


# ==============================================================================
# WAREHOUSE
# ==============================================================================

@st.cache_data(ttl=600)
def load_default_warehouse():
    """
    Get default warehouse ID.
    Cached for 10 minutes.
    """
    try:
        return get_default_warehouse_id()

    except Exception as e:
        log_error(f"default warehouse error: {e}")
        return None


@st.cache_data(ttl=600)
def load_warehouses():
    """
    Load warehouse list.
    Cached for 10 minutes.
    """
    try:
        data = get_warehouses()

        if data is None:
            return []

        return data

    except Exception as e:
        log_error(f"warehouse loading error: {e}")
        return []


def refresh_warehouse_cache():
    """
    Clear warehouse cache if warehouse setup changes.
    """
    load_warehouses.clear()
    load_default_warehouse.clear()
