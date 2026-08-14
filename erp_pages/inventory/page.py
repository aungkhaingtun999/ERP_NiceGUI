# ==============================================================================
# erp_pages/inventory/page.py
# ERP ENTERPRISE INVENTORY PAGE CONTROLLER v2.0
#
# ------------------------------------------------------------------------------
# RESPONSIBILITIES
# ------------------------------------------------------------------------------
# Product Master
# Product 360°
# Add Product
# Product Approval Queue
# Edit Product
# Product Master Import
# Inventory In
# Stock Adjustment
# Inventory Dashboard
#
# ------------------------------------------------------------------------------
# MAKER-CHECKER
# ------------------------------------------------------------------------------
# Product Creation
#
# Maker
#   ↓
# request_product_create_rpc()
#   ↓
# product_create_requests
#   ↓
# PENDING
#   ↓
# Checker
#   ↓
# approve_product_create_rpc()
#   ↓
# products
# warehouse_stock
# inventory_batches
# inventory_cost_layers
#
# ------------------------------------------------------------------------------
# INVENTORY IN
# ------------------------------------------------------------------------------
# Existing Product
#   ↓
# Inventory Import / Stock Entry
#
# ------------------------------------------------------------------------------
# WAREHOUSE TRANSFER
# ------------------------------------------------------------------------------
# Warehouse Transfer is intentionally NOT handled here.
#
# Dedicated page:
#
#     erp_pages/8_Transfer.py
#
# Approval module:
#
#     erp_pages/inventory/warehouse_transfer_approval.py
#
# IMPORTANT:
# Do NOT import warehouse_transfer_approval here.
#
# ------------------------------------------------------------------------------
# PRODUCT 360°
# ------------------------------------------------------------------------------
# Product Master
# Warehouse Stock
# Batch / FEFO
# FIFO Cost Layers
# Pricing
# Sales
# Purchases
# Adjustments
# Transfers
# Refunds
# Movement History
# Audit History
# Integrity
#
# ------------------------------------------------------------------------------
# COMPATIBILITY
# ------------------------------------------------------------------------------
# erp_pages/2_Inventory.py
#
#     from erp_pages.inventory.page import run
#
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
from .inventory_import_approval import (
    render_inventory_import_approval,
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
# INVENTORY TABS
# ==============================================================================

INVENTORY_TABS = [
    "Product Master",
    "Product 360°",
    "Add Product",
    "Approval Queue",
    "Edit Product",
    "Product Import",
    "Inventory In",
    "Inventory In Approval",
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
    "✅",
    "🔧",
    "📊",
]

# ==============================================================================
# SESSION STATE
# ==============================================================================

def _initialize_session_state():
    """
    Initialize Inventory page session state.

    This function must remain safe across Streamlit reruns.
    """

    if "inventory_active_tab" not in st.session_state:
        st.session_state.inventory_active_tab = "Product Master"

    if "inventory_barcode" not in st.session_state:
        st.session_state.inventory_barcode = ""

    if "product_360_selected_id" not in st.session_state:
        st.session_state.product_360_selected_id = None


# ==============================================================================
# ACTIVE TAB
# ==============================================================================

def _get_active_tab() -> str:
    """
    Return currently selected Inventory tab.
    """

    active_tab = st.session_state.get(
        "inventory_active_tab",
        "Product Master",
    )

    if active_tab not in INVENTORY_TABS:

        active_tab = "Product Master"

        st.session_state.inventory_active_tab = active_tab

    return active_tab


# ==============================================================================
# SET ACTIVE TAB
# ==============================================================================

def _set_active_tab(tab_name: str):
    """
    Safely update Inventory active tab.
    """

    if tab_name in INVENTORY_TABS:
        st.session_state.inventory_active_tab = tab_name


# ==============================================================================
# TAB NAVIGATION
# ==============================================================================

def _render_tab_navigation() -> str:
    """
    Render Inventory navigation.

    Radio is intentionally used instead of st.tabs so that
    the active section survives Streamlit reruns.
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
# PRODUCT 360° SELECTOR
# ==============================================================================

def _render_product_360_selector(
    products,
):
    """
    Render Product 360° product selector.

    Product 360° is only rendered when the Product 360° tab
    is active.

    Returns:
        int | None
    """

    if not products:

        st.warning(
            "No products found for the selected warehouse."
        )

        st.session_state.product_360_selected_id = None

        return None

    # --------------------------------------------------------------------------
    # PRODUCT OPTIONS
    # --------------------------------------------------------------------------

    product_options = {}

    for product in products:

        product_id = (
            product.get("product_id")
            or product.get("id")
        )

        if product_id is None:
            continue

        try:

            product_id = int(product_id)

        except (
            TypeError,
            ValueError,
        ):

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

        # ----------------------------------------------------------------------
        # Prevent duplicate labels
        # ----------------------------------------------------------------------

        if label in product_options:

            label = (
                f"{name} ({sku}) "
                f"[ID: {product_id}]"
            )

        product_options[label] = product_id

    if not product_options:

        st.warning(
            "Products were loaded, "
            "but no valid Product ID was found."
        )

        st.session_state.product_360_selected_id = None

        return None

    labels = list(
        product_options.keys()
    )

    # --------------------------------------------------------------------------
    # CURRENT SELECTION
    # --------------------------------------------------------------------------

    current_product_id = (
        st.session_state.get(
            "product_360_selected_id"
        )
    )

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
    # SELECTOR
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

    selected_product_id = (
        product_options[selected_label]
    )

    st.session_state.product_360_selected_id = (
        selected_product_id
    )

    return selected_product_id


# ==============================================================================
# PRODUCT LOAD
# ==============================================================================

def _load_inventory_products(
    selected_wh_id,
):
    """
    Load Product Master inventory view for the selected warehouse.

    Product Import and Inventory In intentionally do not depend
    on this list.
    """

    barcode = st.session_state.get(
        "inventory_barcode",
        "",
    )

    barcode = (
        str(barcode).strip()
        if barcode
        else ""
    )

    try:

        products = get_inventory_view(
            warehouse_id=selected_wh_id,
            search=barcode,
        )

        return products or []

    except Exception as e:

        st.error(
            "Product loading error."
        )

        st.exception(e)

        return []


# ==============================================================================
# DATABASE + SERVICES
# ==============================================================================

def _initialize_services():
    """
    Create database client and Inventory/Pricing services.

    Returns:
        tuple(client, inventory_service, pricing_service)
        or
        (None, None, None)
    """

    try:

        client = db()

        inventory_service = InventoryService(
            client
        )

        pricing_service = PricingService(
            client
        )

        return (
            client,
            inventory_service,
            pricing_service,
        )

    except Exception as e:

        st.error(
            "ERP Service Connection Failed."
        )

        st.exception(e)

        return (
            None,
            None,
            None,
        )


# ==============================================================================
# WAREHOUSE
# ==============================================================================

def _load_warehouses():
    """
    Load active ERP warehouses.
    """

    try:

        warehouses = get_warehouses()

    except Exception as e:

        st.error(
            "Warehouse loading error."
        )

        st.exception(e)

        return []

    return warehouses or []


# ==============================================================================
# PRODUCT MASTER
# ==============================================================================

def _render_product_master_tab(
    products,
):

    render_product_master(
        products
    )


# ==============================================================================
# PRODUCT 360°
# ==============================================================================

def _render_product_360_tab(
    client,
    products,
):

    selected_product_id = (
        _render_product_360_selector(
            products
        )
    )

    st.markdown("---")

    if selected_product_id is None:

        st.info(
            "Select a product above "
            "to open Product 360°."
        )

        return

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


# ==============================================================================
# ADD PRODUCT
# ==============================================================================

def _render_add_product_tab(
    client,
    pricing_service,
    selected_wh_id,
):

    render_product_create(
        db_client=client,
        pricing_service=pricing_service,
        warehouse_id=selected_wh_id,
    )


# ==============================================================================
# APPROVAL QUEUE
# ==============================================================================

def _render_approval_tab():

    render_product_approval_queue()


# ==============================================================================
# EDIT PRODUCT
# ==============================================================================

def _render_edit_product_tab(
    selected_wh_id,
    selected_wh_name,
):

    render_product_edit(
        warehouse_id=selected_wh_id,
        warehouse_name=selected_wh_name,
    )


# ==============================================================================
# PRODUCT IMPORT
# ==============================================================================

def _render_product_import_tab(
    selected_wh_id,
):

    # --------------------------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------------------------
    # Product Import is Maker-Checker.
    #
    # It must NOT directly create:
    #     products
    #     warehouse_stock
    #     inventory_batches
    #     inventory_cost_layers
    #
    # The approval workflow handles actual creation.
    # --------------------------------------------------------------------------

    render_product_import(
        warehouse_id=selected_wh_id,
    )


# ==============================================================================
# INVENTORY IN
# ==============================================================================

def _render_inventory_in_tab():

    # --------------------------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------------------------
    # Inventory In is NOT Product Import.
    #
    # It is for stock entry against an EXISTING product.
    # --------------------------------------------------------------------------

    render_inventory_import()
# ==============================================================================
# INVENTORY IN APPROVAL
# ==============================================================================

def _render_inventory_in_approval_tab():

    # --------------------------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------------------------
    # Inventory In Approval is the Checker side of Inventory In.
    #
    # Maker:
    #     Excel / CSV
    #         ↓
    #     inventory_import_batches
    #         ↓
    #     PENDING
    #
    # Checker:
    #     Select All / Individual Select
    #         ↓
    #     Approve Selected
    #         ↓
    #     approve_inventory_import_batch()
    #
    # Actual stock posting is performed by the PostgreSQL approval RPC.
    # Python UI must NOT directly update:
    #
    #     warehouse_stock
    #     inventory_batches
    #     inventory_cost_layers
    #
    # --------------------------------------------------------------------------

    render_inventory_import_approval()

# ==============================================================================
# STOCK ADJUSTMENT
# ==============================================================================

def _render_stock_adjustment_tab(
    products,
    selected_wh_id,
    selected_wh_name,
    inventory_service,
):

    render_stock_adjustment(
        products=products,
        warehouse_id=selected_wh_id,
        warehouse_name=selected_wh_name,
        inventory_service=inventory_service,
    )


# ==============================================================================
# DASHBOARD
# ==============================================================================

def _render_dashboard_tab(
    selected_wh_id,
):

    render_inventory_dashboard(
        warehouse_id=selected_wh_id,
    )


# ==============================================================================
# MAIN INVENTORY PAGE
# ==============================================================================

def run_inventory_page():
    """
    Main ERP Inventory Control Center.

    This function is the only Inventory UI router.

    Warehouse Transfer is intentionally NOT routed here.
    Warehouse Transfer has its own dedicated page:
        erp_pages/8_Transfer.py
    """

    # ==========================================================================
    # SESSION STATE
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
    # DATABASE + SERVICES
    # ==========================================================================

    (
        client,
        inventory_service,
        pricing_service,
    ) = _initialize_services()

    if client is None:

        st.stop()

    # ==========================================================================
    # WAREHOUSES
    # ==========================================================================

    warehouses = _load_warehouses()

    if not warehouses:

        st.error(
            "No active warehouses found."
        )

        st.stop()

    # ==========================================================================
    # WAREHOUSE SELECTOR
    # ==========================================================================

    try:

        (
            selected_wh_id,
            selected_wh_name,
        ) = render_warehouse_selector(
            warehouses,
            key="inventory_warehouse_selector",
        )

    except Exception as e:

        st.error(
            "Warehouse selector failed."
        )

        st.exception(e)

        st.stop()

    # ==========================================================================
    # SESSION WAREHOUSE LIST
    # ==========================================================================

    st.session_state.warehouses = (
        warehouses
    )

    # ==========================================================================
    # LOAD INVENTORY PRODUCTS
    # ==========================================================================

    products = _load_inventory_products(
        selected_wh_id
    )

    # ==========================================================================
    # TAB NAVIGATION
    # ==========================================================================

    active_tab = _render_tab_navigation()

    st.markdown("---")

    # ==========================================================================
    # PRODUCT MASTER
    # ==========================================================================

    if active_tab == "Product Master":

        _render_product_master_tab(
            products
        )

    # ==========================================================================
    # PRODUCT 360°
    # ==========================================================================

    elif active_tab == "Product 360°":

        _render_product_360_tab(
            client=client,
            products=products,
        )

    # ==========================================================================
    # ADD PRODUCT
    # ==========================================================================

    elif active_tab == "Add Product":

        _render_add_product_tab(
            client=client,
            pricing_service=pricing_service,
            selected_wh_id=selected_wh_id,
        )

    # ==========================================================================
    # APPROVAL QUEUE
    # ==========================================================================

    elif active_tab == "Approval Queue":

        _render_approval_tab()

    # ==========================================================================
    # EDIT PRODUCT
    # ==========================================================================

    elif active_tab == "Edit Product":

        _render_edit_product_tab(
            selected_wh_id=selected_wh_id,
            selected_wh_name=selected_wh_name,
        )

    # ==========================================================================
    # PRODUCT MASTER IMPORT
    # ==========================================================================

    elif active_tab == "Product Import":

        _render_product_import_tab(
            selected_wh_id=selected_wh_id,
        )

    # ==========================================================================
    # INVENTORY IN
    # ==========================================================================

    elif active_tab == "Inventory In":

        _render_inventory_in_tab()
    elif active_tab == "Inventory In Approval":

        _render_inventory_in_approval_tab()

    # ==========================================================================
    # STOCK ADJUSTMENT
    # ==========================================================================

    elif active_tab == "Stock Adjustment":

        _render_stock_adjustment_tab(
            products=products,
            selected_wh_id=selected_wh_id,
            selected_wh_name=selected_wh_name,
            inventory_service=inventory_service,
        )

    # ==========================================================================
    # DASHBOARD
    # ==========================================================================

    elif active_tab == "Dashboard":

        _render_dashboard_tab(
            selected_wh_id=selected_wh_id,
        )


# ==============================================================================
# LEGACY / PAGE ENTRY
# ==============================================================================
#
# Compatible with:
#
#     erp_pages/2_Inventory.py
#
#     from erp_pages.inventory.page import run
#
# ==============================================================================

def run():
    """
    Public page entry point.
    """

    return run_inventory_page()


# ==============================================================================
# MODULE EXPORTS
# ==============================================================================

__all__ = [
    "run",
    "run_inventory_page",
]
