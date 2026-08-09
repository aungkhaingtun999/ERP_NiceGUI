# ==============================================================================
# erp_pages/inventory/page.py
# ERP ENTERPRISE INVENTORY PAGE CONTROLLER v1.2 CLEAN
# Approval Queue Enabled
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
from .stock_adjustment import render_stock_adjustment
from .dashboard import render_inventory_dashboard


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run_inventory_page():

    st.title('🏭 Enterprise Product Master')

    st.caption(
        'ERP Inventory Control Center | Mobile Ready | Maker Checker Enabled'
    )

    # --------------------------------------------------------------------------
    # SESSION
    # --------------------------------------------------------------------------

    if 'inventory_barcode' not in st.session_state:

        st.session_state.inventory_barcode = ''

    # --------------------------------------------------------------------------
    # SERVICES
    # --------------------------------------------------------------------------

    try:

        client = db()

        inventory_service = InventoryService(client)

        pricing_service = PricingService(client)

    except Exception as e:

        st.error(f'ERP Service Connection Failed : {e}')

        st.stop()

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    warehouses = get_warehouses()

    if not warehouses:

        st.error('No active warehouses found')

        st.stop()

    selected_wh_id, selected_wh_name = render_warehouse_selector(
        warehouses,
        key='inventory_warehouse_selector'
    )

    # --------------------------------------------------------------------------
    # PRODUCT LOAD
    # --------------------------------------------------------------------------

    barcode = st.session_state.get('inventory_barcode', '')

    try:

        products = get_inventory_view(
            warehouse_id=selected_wh_id,
            search=barcode.strip()
        )

    except Exception as e:

        st.error(f'Product loading error : {e}')

        products = []

    # --------------------------------------------------------------------------
    # TABS
    # --------------------------------------------------------------------------

    (
        tab_master,
        tab_add,
        tab_approval,
        tab_edit,
        tab_adjust,
        tab_dashboard
    ) = st.tabs(
        [
            '📋 Product Master',
            '➕ Add Product',
            '🟡 Approval Queue',
            '✏️ Edit Product',
            '🔧 Stock Adjustment',
            '📊 Dashboard',
        ]
    )

    # --------------------------------------------------------------------------
    # PRODUCT MASTER
    # --------------------------------------------------------------------------

    with tab_master:

        render_product_master(products)

    # --------------------------------------------------------------------------
    # ADD PRODUCT REQUEST
    # --------------------------------------------------------------------------

    with tab_add:

        render_product_create(
            db_client=client,
            pricing_service=pricing_service,
            warehouse_id=selected_wh_id,
        )

    # --------------------------------------------------------------------------
    # APPROVAL QUEUE
    # --------------------------------------------------------------------------

    with tab_approval:

        render_product_approval_queue()

    # --------------------------------------------------------------------------
    # EDIT PRODUCT
    # --------------------------------------------------------------------------

    with tab_edit:

        render_product_edit(
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
        )

    # --------------------------------------------------------------------------
    # STOCK ADJUSTMENT
    # --------------------------------------------------------------------------

    with tab_adjust:

        render_stock_adjustment(
            products=products,
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
            inventory_service=inventory_service,
        )

    # --------------------------------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------------------------------

    with tab_dashboard:

        render_inventory_dashboard(
            warehouse_id=selected_wh_id
        )


# ==============================================================================
# LEGACY ENTRY
# Compatible with erp_pages/2_Inventory.py
# ==============================================================================

def run():

    return run_inventory_page()
