# ==============================================================================
# erp_pages/inventory/page.py
#
# ERP ENTERPRISE INVENTORY PAGE CONTROLLER v1.7
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
from .product_master import render_product_master
from .product_create import render_product_create
from .product_approval import render_product_approval_queue
from .product_edit import render_product_edit
from .product_import import render_product_import
from .inventory_import import render_inventory_import
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
    "Product 360°",  # <-- ပေါင်းထည့်လိုက်သော Tab အသစ်
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
    "🔍",  # <-- Product 360° အတွက် Icon အသစ်
    "📊",
]


# ==============================================================================
# SESSION STATE MANAGEMENT
# ==============================================================================
def _get_active_tab():
    """Return currently selected Inventory tab with fallback safety."""
    if "inventory_active_tab" not in st.session_state:
        st.session_state.inventory_active_tab = "Product Master"

    current_tab = st.session_state.inventory_active_tab
    if current_tab not in INVENTORY_TABS:
        current_tab = "Product Master"
        st.session_state.inventory_active_tab = current_tab

    return current_tab


def _set_active_tab(tab_name):
    """Safely update active Inventory tab."""
    if tab_name in INVENTORY_TABS:
        st.session_state.inventory_active_tab = tab_name


# ==============================================================================
# TAB NAVIGATION RENDERER
# ==============================================================================
def _render_tab_navigation():
    """
    Render Inventory navigation using radio layout
    to persist states across Streamlit reruns.
    """
    active_tab = _get_active_tab()
    labels = [
        f"{icon} {name}"
        for icon, name in zip(INVENTORY_TAB_ICONS, INVENTORY_TABS)
    ]

    try:
        current_index = INVENTORY_TABS.index(active_tab)
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

    selected_tab = INVENTORY_TABS[labels.index(selected_label)]

    if selected_tab != active_tab:
        _set_active_tab(selected_tab)
        st.rerun()

    return selected_tab


# ==============================================================================
# MAIN INVENTORY PAGE CONTROLLER
# ==============================================================================
def run_inventory_page():
    """
    Main ERP Inventory Control Center Controller.
    All Inventory UI routing and state injection occur here.
    """
    st.title("🏭 Enterprise Product Master")
    st.caption(
        "ERP Inventory Control Center | Mobile Ready | Maker Checker Enabled"
    )

    # Initialize barcode session state if missing
    if "inventory_barcode" not in st.session_state:
        st.session_state.inventory_barcode = ""

    _get_active_tab()

    # Database client & Core Services initialization
    try:
        client = db()
        inventory_service = InventoryService(client)
        pricing_service = PricingService(client)
    except Exception as e:
        st.error("ERP Service Connection Failed")
        st.exception(e)
        st.stop()

    # Load Warehouses
    try:
        warehouses = get_warehouses()
    except Exception as e:
        st.error("Warehouse loading error")
        st.exception(e)
        st.stop()

    if not warehouses:
        st.error("No active warehouses found in the system.")
        st.stop()

    # Render Warehouse Selector
    selected_wh_id, selected_wh_name = render_warehouse_selector(
        warehouses,
        key="inventory_warehouse_selector",
    )

    st.session_state.warehouses = warehouses

    # Fetch Barcode / Search Query State
    barcode = st.session_state.get("inventory_barcode", "")
    barcode = str(barcode).strip() if barcode else ""

    # Load Products View based on Warehouse & Search Context
    try:
        products = get_inventory_view(
            warehouse_id=selected_wh_id,
            search=barcode,
        )
    except Exception as e:
        st.error("Product inventory data loading error")
        st.exception(e)
        products = []

    # Render Navigation Tabs
    active_tab = _render_tab_navigation()
    st.markdown("---")

    # ==========================================================================
    # ROUTING TO RESPECTIVE MODULES
    # ==========================================================================
    if active_tab == "Product Master":
        render_product_master(products)

    elif active_tab == "Add Product":
        render_product_create(
            db_client=client,
            pricing_service=pricing_service,
            warehouse_id=selected_wh_id,
        )

    elif active_tab == "Approval Queue":
        render_product_approval_queue()

    elif active_tab == "Edit Product":
        render_product_edit(
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
        )

    elif active_tab == "Product Import":
        render_product_import(
            warehouse_id=selected_wh_id,
        )

    elif active_tab == "Inventory In":
        render_inventory_import()

    elif active_tab == "Stock Adjustment":
        render_stock_adjustment(
            products=products,
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
            inventory_service=inventory_service,
        )

    elif active_tab == "Dashboard":
        render_inventory_dashboard(
            warehouse_id=selected_wh_id,
        )

# ==============================================================================
# PRODUCT 360° ROUTING
# ==============================================================================

    elif active_tab == "Product 360°":

        from .product_360 import render_page as render_product_360_page

        # ရွေးချယ်ထားသော Product များထဲမှ ပထမဆုံး (သို့) Session ထဲက Product ID ကို ယူသုံးရန်
        default_prod_id = products[0]["id"] if products and "id" in products[0] else 1
        
        render_product_360_page(
            client=client,
            product_id=default_prod_id,
        )
        
# ==============================================================================
# LEGACY ENTRY POINT
# ==============================================================================
def run():
    return run_inventory_page()
            
