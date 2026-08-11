# ==============================================================================
# erp_pages/inventory/page.py
#
# ERP ENTERPRISE INVENTORY PAGE CONTROLLER v1.5
#
# PRODUCT MASTER BULK IMPORT ENABLED
# INVENTORY IN ENABLED
# ACTIVE TAB PERSISTENCE
# MAKER CHECKER ENABLED
# ==============================================================================

import streamlit as st

from database import (
    db,
    get_inventory_view,
    get_warehouses,
)

from erp_core.services.inventory_service import InventoryService
from erp_core.services.pricing_service import PricingService

from .warehouse import render_warehouse_selector
from .product_master import render_product_master
from .product_create import render_product_create
from .product_approval import render_product_approval_queue
from .product_edit import render_product_edit

# Inventory In
from .inventory_import import render_inventory_import

# Product Master CSV / Excel Bulk Import
from .product_import import render_product_import

from .stock_adjustment import render_stock_adjustment
from .dashboard import render_inventory_dashboard


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
# TAB STATE
# ==============================================================================

def _get_active_tab():

    if "inventory_active_tab" not in st.session_state:

        st.session_state.inventory_active_tab = "Product Master"

    return st.session_state.inventory_active_tab


def _set_active_tab(tab_name):

    if tab_name in INVENTORY_TABS:

        st.session_state.inventory_active_tab = tab_name


# ==============================================================================
# TAB NAVIGATION
# ==============================================================================

def _render_tab_navigation():

    active_tab = _get_active_tab()

    labels = [
        f"{icon} {name}"
        for icon, name in zip(
            INVENTORY_TAB_ICONS,
            INVENTORY_TABS,
        )
    ]

    current_index = INVENTORY_TABS.index(active_tab)

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
# MAIN PAGE
# ==============================================================================

def run_inventory_page():

    st.title("🏭 Enterprise Product Master")

    st.caption(
        "ERP Inventory Control Center | "
        "Mobile Ready | Maker Checker Enabled"
    )


    # ==========================================================================
    # SESSION
    # ==========================================================================

    if "inventory_barcode" not in st.session_state:

        st.session_state.inventory_barcode = ""

    _get_active_tab()


    # ==========================================================================
    # SERVICES
    # ==========================================================================

    try:

        client = db()

        inventory_service = InventoryService(client)

        pricing_service = PricingService(client)

    except Exception as e:

        st.error(
            f"ERP Service Connection Failed : {e}"
        )

        st.stop()


    # ==========================================================================
    # WAREHOUSE
    # ==========================================================================

    warehouses = get_warehouses()

    if not warehouses:

        st.error(
            "No active warehouses found"
        )

        st.stop()


    selected_wh_id, selected_wh_name = (
        render_warehouse_selector(
            warehouses,
            key="inventory_warehouse_selector",
        )
    )


    # Keep warehouses available to Inventory modules

    st.session_state.warehouses = warehouses


    # ==========================================================================
    # PRODUCT LOAD
    # ==========================================================================

    barcode = st.session_state.get(
        "inventory_barcode",
        "",
    )


    try:

        products = get_inventory_view(
            warehouse_id=selected_wh_id,
            search=barcode.strip(),
        )

    except Exception as e:

        st.error(
            f"Product loading error : {e}"
        )

        products = []


    # ==========================================================================
    # NAVIGATION
    # ==========================================================================

    active_tab = _render_tab_navigation()

    st.markdown("---")


    # ==========================================================================
    # PRODUCT MASTER
    # ==========================================================================

    if active_tab == "Product Master":

        render_product_master(products)


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
    # PRODUCT APPROVAL QUEUE
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
    #
    # CSV / Excel
    #
    # IMPORTANT:
    #   This does NOT directly insert into products.
    #
    #   Next stage:
    #
    #   CSV / Excel
    #        ↓
    #   Validation
    #        ↓
    #   Preview
    #        ↓
    #   Maker Request
    #        ↓
    #   Checker Approval
    #        ↓
    #   products
    # ==========================================================================

    elif active_tab == "Product Import":

        render_product_import()


    # ==========================================================================
    # INVENTORY IN
    #
    # Existing Stock-In workflow
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
            warehouse_id=selected_wh_id
        )


# ==============================================================================
# LEGACY ENTRY
# Compatible with erp_pages/2_Inventory.py
# ==============================================================================

def run():

    return run_inventory_page()
