# ==============================================================================
# erp_pages/inventory/page.py
#
# ERP ENTERPRISE INVENTORY PAGE CONTROLLER v1.6
#
# PRODUCT MASTER
# ADD PRODUCT
# APPROVAL QUEUE
# EDIT PRODUCT
# PRODUCT MASTER BULK IMPORT
# INVENTORY IN
# STOCK ADJUSTMENT
# DASHBOARD
#
# MAKER-CHECKER ENABLED
# MOBILE READY
#
# IMPORTANT
# ------------------------------------------------------------------------------
# Product Master Import and Inventory In are DIFFERENT workflows.
#
# Product Import
#     ↓
# request_product_create_rpc()
#     ↓
# product_create_requests
#     ↓
# PENDING
#     ↓
# Checker Approval
#     ↓
# approve_product_create_rpc()
#     ↓
# products + warehouse_stock + FIFO
#
# Inventory In
#     ↓
# Existing Product Stock Entry
#
# ==============================================================================

import streamlit as st


# ==============================================================================
# DATABASE
# ==============================================================================

from database import (
    db,
    get_inventory_view,
    get_warehouses,
)


# ==============================================================================
# SERVICES
# ==============================================================================

from erp_core.services.inventory_service import InventoryService
from erp_core.services.pricing_service import PricingService


# ==============================================================================
# INVENTORY UI MODULES
# ==============================================================================

from .warehouse import render_warehouse_selector

from .product_master import (
    render_product_master,
)

from .product_create import (
    render_product_create,
)

from .product_approval import (
    render_product_approval_queue,
)

from .product_edit import (
    render_product_edit,
)


# ==============================================================================
# PRODUCT MASTER BULK IMPORT
# ------------------------------------------------------------------------------
# CSV / Excel
# Maker-Checker
# ==============================================================================

from .product_import import (
    render_product_import,
)


# ==============================================================================
# INVENTORY IN
# ------------------------------------------------------------------------------
# IMPORTANT:
# This is NOT Product Master Import.
# ==============================================================================

from .inventory_import import (
    render_inventory_import,
)


# ==============================================================================
# STOCK ADJUSTMENT
# ==============================================================================

from .stock_adjustment import (
    render_stock_adjustment,
)


# ==============================================================================
# DASHBOARD
# ==============================================================================

from .dashboard import (
    render_inventory_dashboard,
)


# ==============================================================================
# TAB DEFINITIONS
# ==============================================================================

INVENTORY_TABS = [
    "Product Master",
    "Add Product",
    "Approval Queue",
    "Edit Product",
    "Product Import",
    "Inventory In",
    "Stock Adjustment",
    "Dashboard",
]


# ==============================================================================
# TAB ICONS
# ==============================================================================

INVENTORY_TAB_ICONS = [
    "📋",
    "➕",
    "🟡",
    "✏️",
    "📦",
    "📥",
    "🔧",
    "📊",
]


# ==============================================================================
# SESSION STATE
# ==============================================================================

def _get_active_tab():
    """
    Return currently selected Inventory tab.

    Default:
        Product Master
    """

    if "inventory_active_tab" not in st.session_state:

        st.session_state.inventory_active_tab = (
            "Product Master"
        )

    current_tab = (
        st.session_state.inventory_active_tab
    )

    # Safety
    if current_tab not in INVENTORY_TABS:

        current_tab = "Product Master"

        st.session_state.inventory_active_tab = (
            current_tab
        )

    return current_tab


# ==============================================================================
# SET ACTIVE TAB
# ==============================================================================

def _set_active_tab(tab_name):
    """
    Safely update active Inventory tab.
    """

    if tab_name in INVENTORY_TABS:

        st.session_state.inventory_active_tab = (
            tab_name
        )


# ==============================================================================
# TAB NAVIGATION
# ==============================================================================

def _render_tab_navigation():
    """
    Render Inventory navigation.

    Uses radio instead of st.tabs so the selected
    section can persist across Streamlit reruns.
    """

    active_tab = _get_active_tab()

    labels = [
        f"{icon} {name}"
        for icon, name in zip(
            INVENTORY_TAB_ICONS,
            INVENTORY_TABS,
        )
    ]

    try:

        current_index = INVENTORY_TABS.index(
            active_tab
        )

    except ValueError:

        current_index = 0

        active_tab = "Product Master"

        _set_active_tab(active_tab)

    selected_label = st.radio(
        "Inventory Section",
        labels,
        index=current_index,
        horizontal=True,
        key="inventory_tab_navigation",
        label_visibility="collapsed",
    )

    selected_tab = INVENTORY_TABS[
        labels.index(selected_label)
    ]

    if selected_tab != active_tab:

        _set_active_tab(selected_tab)

        st.rerun()

    return selected_tab


# ==============================================================================
# MAIN INVENTORY PAGE
# ==============================================================================

def run_inventory_page():
    """
    Main ERP Inventory Control Center.

    All Inventory UI routing MUST remain inside this function.
    """

    # ==========================================================================
    # PAGE HEADER
    # ==========================================================================

    st.title(
        "🏭 Enterprise Product Master"
    )

    st.caption(
        "ERP Inventory Control Center | "
        "Mobile Ready | Maker Checker Enabled"
    )


    # ==========================================================================
    # SESSION INITIALIZATION
    # ==========================================================================

    if "inventory_barcode" not in st.session_state:

        st.session_state.inventory_barcode = ""

    _get_active_tab()


    # ==========================================================================
    # DATABASE CLIENT + SERVICES
    # ==========================================================================

    try:

        client = db()

        inventory_service = InventoryService(
            client
        )

        pricing_service = PricingService(
            client
        )

    except Exception as e:

        st.error(
            "ERP Service Connection Failed"
        )

        st.exception(e)

        st.stop()


    # ==========================================================================
    # WAREHOUSE
    # ==========================================================================

    try:

        warehouses = get_warehouses()

    except Exception as e:

        st.error(
            "Warehouse loading error"
        )

        st.exception(e)

        st.stop()


    if not warehouses:

        st.error(
            "No active warehouses found."
        )

        st.stop()


    # --------------------------------------------------------------------------
    # WAREHOUSE SELECTOR
    # --------------------------------------------------------------------------

    selected_wh_id, selected_wh_name = (
        render_warehouse_selector(
            warehouses,
            key="inventory_warehouse_selector",
        )
    )


    # --------------------------------------------------------------------------
    # STORE WAREHOUSE LIST
    # --------------------------------------------------------------------------

    st.session_state.warehouses = warehouses


    # ==========================================================================
    # BARCODE / SEARCH STATE
    # ==========================================================================

    barcode = st.session_state.get(
        "inventory_barcode",
        "",
    )

    barcode = (
        str(barcode).strip()
        if barcode
        else ""
    )


    # ==========================================================================
    # PRODUCT LOAD
    # ----------------------------------------------------------------------------
    # Product Master / Stock Adjustment / Dashboard
    # may use this product list.
    #
    # Product Import does NOT depend on this list.
    # ==========================================================================

    try:

        products = get_inventory_view(
            warehouse_id=selected_wh_id,
            search=barcode,
        )

    except Exception as e:

        st.error(
            "Product loading error"
        )

        st.exception(e)

        products = []


    # ==========================================================================
    # TAB NAVIGATION
    # ==========================================================================

    active_tab = _render_tab_navigation()

    st.markdown("---")


    # ==========================================================================
    # PRODUCT MASTER
    # ==========================================================================

    if active_tab == "Product Master":

        render_product_master(
            products
        )


    # ==========================================================================
    # ADD PRODUCT
    # ==========================================================================

    elif active_tab == "Add Product":

        render_product_create(
            db_client=client,
            pricing_service=pricing_service,
            warehouse_id=selected_wh_id,
        )


    # ==========================================================================
    # APPROVAL QUEUE
    # ==========================================================================

    elif active_tab == "Approval Queue":

        render_product_approval_queue()


    # ==========================================================================
    # EDIT PRODUCT
    # ==========================================================================

    elif active_tab == "Edit Product":

        render_product_edit(
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
        )


    # ==========================================================================
    # PRODUCT MASTER BULK IMPORT
    # ----------------------------------------------------------------------------
    # CSV / Excel
    #
    # IMPORTANT:
    # This must call product_import.py
    #
    # It creates:
    #
    # product_create_requests
    #
    # It does NOT directly insert products.
    # ==========================================================================

    elif active_tab == "Product Import":

    render_product_import(
        warehouse_id=selected_wh_id,
    )

    # ==========================================================================
    # INVENTORY IN
    # ----------------------------------------------------------------------------
    # Existing Product → Stock Entry
    #
    # IMPORTANT:
    # This is completely separate from Product Master Import.
    # ==========================================================================

    elif active_tab == "Inventory In":

        render_inventory_import()


    # ==========================================================================
    # STOCK ADJUSTMENT
    # ==========================================================================

    elif active_tab == "Stock Adjustment":

        render_stock_adjustment(
            products=products,
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
            inventory_service=inventory_service,
        )


    # ==========================================================================
    # DASHBOARD
    # ==========================================================================

    elif active_tab == "Dashboard":

        render_inventory_dashboard(
            warehouse_id=selected_wh_id,
        )


# ==============================================================================
# LEGACY ENTRY
# ------------------------------------------------------------------------------
# Compatible with:
#
# erp_pages/2_Inventory.py
#
# ==============================================================================

def run():

    return run_inventory_page()
