# ==============================================================================
# erp_pages/inventory/page.py
#
# ERP ENTERPRISE INVENTORY PAGE CONTROLLER v1.8
# ------------------------------------------------------------------------------
# PRODUCT MASTER
# PRODUCT 360°
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
# Product Import and Inventory In are DIFFERENT workflows.
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
# Product 360°
#     ↓
# Product Master
# Current Stock
# Warehouse
# FIFO / Cost Layers
# Batch / FEFO
# Pricing
# Sales
# Purchases
# Adjustments
# Transfers
# Refunds
# Movement History
# Audit History
# Integrity
# ==============================================================================

from __future__ import annotations

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

from erp_core.services.inventory_service import (
    InventoryService,
)

from erp_core.services.pricing_service import (
    PricingService,
)


# ==============================================================================
# INVENTORY UI MODULES
# ==============================================================================

from .warehouse import (
    render_warehouse_selector,
)

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

from .product_import import (
    render_product_import,
)

from .inventory_import import (
    render_inventory_import,
)

from .stock_adjustment import (
    render_stock_adjustment,
)

from .dashboard import (
    render_inventory_dashboard,
)


# ==============================================================================
# PRODUCT 360°
# ==============================================================================

from .product_360 import (
    render_product_360_page,
)


# ==============================================================================
# TAB DEFINITIONS
# ==============================================================================

INVENTORY_TABS = [
    "Product Master",
    "Product 360°",
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
    "🧭",
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

def _initialize_session_state():
    """
    Initialize Inventory page session state.
    """

    if "inventory_active_tab" not in st.session_state:

        st.session_state.inventory_active_tab = (
            "Product Master"
        )

    if "inventory_barcode" not in st.session_state:

        st.session_state.inventory_barcode = ""

    if "product_360_selected_id" not in st.session_state:

        st.session_state.product_360_selected_id = None


# ==============================================================================
# GET ACTIVE TAB
# ==============================================================================

def _get_active_tab():
    """
    Return currently selected Inventory tab.

    Default:
        Product Master
    """

    active_tab = st.session_state.get(
        "inventory_active_tab",
        "Product Master",
    )

    if active_tab not in INVENTORY_TABS:

        active_tab = "Product Master"

        st.session_state.inventory_active_tab = (
            active_tab
        )

    return active_tab


# ==============================================================================
# SET ACTIVE TAB
# ==============================================================================

def _set_active_tab(
    tab_name: str,
):
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

    Uses radio instead of st.tabs so selected
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

        _set_active_tab(
            active_tab
        )

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

        _set_active_tab(
            selected_tab
        )

        st.rerun()

    return selected_tab


# ==============================================================================
# PRODUCT 360° PRODUCT SELECTOR
# ==============================================================================

def _render_product_360_selector(
    products,
):
    """
    Render Product 360° product selector.

    IMPORTANT
    ----------
    This selector is rendered ONLY inside Product 360° tab.

    Returns:
        product_id or None
    """

    if not products:

        st.warning(
            "No products found for the selected warehouse."
        )

        st.session_state.product_360_selected_id = (
            None
        )

        return None

    # --------------------------------------------------------------------------
    # Build safe product options
    # --------------------------------------------------------------------------

    product_options = {}

    for product in products:

        product_id = (
            product.get("product_id")
            or product.get("id")
        )

        if product_id is None:

            continue

        name = (
            product.get("name")
            or product.get("product_name")
            or "Unnamed Product"
        )

        sku = (
            product.get("sku")
            or "-"
        )

        label = (
            f"{name} ({sku})"
        )

        # Prevent duplicate labels
        if label in product_options:

            label = (
                f"{name} ({sku}) "
                f"[ID: {product_id}]"
            )

        product_options[label] = int(
            product_id
        )

    if not product_options:

        st.warning(
            "Products were loaded, but no valid Product ID was found."
        )

        st.session_state.product_360_selected_id = (
            None
        )

        return None

    labels = list(
        product_options.keys()
    )

    current_product_id = (
        st.session_state.get(
            "product_360_selected_id"
        )
    )

    # --------------------------------------------------------------------------
    # Determine default selection
    # --------------------------------------------------------------------------

    default_index = 0

    if current_product_id is not None:

        try:

            current_product_id = int(
                current_product_id
            )

            for index, label in enumerate(labels):

                if (
                    product_options[label]
                    == current_product_id
                ):

                    default_index = index
                    break

        except (
            TypeError,
            ValueError,
        ):

            default_index = 0

    # --------------------------------------------------------------------------
    # Selector
    # --------------------------------------------------------------------------

    st.subheader(
        "🧭 Product 360°"
    )

    selected_label = st.selectbox(
        "Select Product",
        labels,
        index=default_index,
        key="product_360_selector",
    )

    selected_product_id = product_options[
        selected_label
    ]

    st.session_state.product_360_selected_id = (
        selected_product_id
    )

    return selected_product_id


# ==============================================================================
# MAIN INVENTORY PAGE
# ==============================================================================

def run_inventory_page():
    """
    Main ERP Inventory Control Center.

    All Inventory UI routing MUST remain inside
    this function.
    """

    # ==========================================================================
    # SESSION INITIALIZATION
    # ==========================================================================

    _initialize_session_state()

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
    # Warehouse selector
    # --------------------------------------------------------------------------

    selected_wh_id, selected_wh_name = (
        render_warehouse_selector(
            warehouses,
            key="inventory_warehouse_selector",
        )
    )

    # --------------------------------------------------------------------------
    # Store warehouse list
    # --------------------------------------------------------------------------

    st.session_state.warehouses = (
        warehouses
    )

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
    # Product Master
    # Product 360°
    # Stock Adjustment
    #
    # Product Import does NOT depend on this list.
    # Inventory In does NOT depend on this list.
    # ==========================================================================

    try:

        products = get_inventory_view(
            warehouse_id=selected_wh_id,
            search=barcode,
        )

        if not products:

            products = []

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
    # PRODUCT 360°
    # ==========================================================================

    elif active_tab == "Product 360°":

        selected_product_id = (
            _render_product_360_selector(
                products
            )
        )

        st.markdown("---")

        if selected_product_id is None:

            st.info(
                "Select a product above to open Product 360°."
            )

        else:

            try:

                render_product_360_page(
                    client,
                    int(selected_product_id),
                )

            except Exception as e:

                st.error(
                    "Product 360° failed to load."
                )

                st.exception(e)

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
    # This workflow must create
    # product_create_requests only.
    #
    # It must NOT directly insert:
    #     products
    #     warehouse_stock
    #     inventory_batches
    #     inventory_cost_layers
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
