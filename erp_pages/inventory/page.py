# ==============================================================================
# erp_pages/inventory/page.py
# ERP ENTERPRISE INVENTORY PAGE CONTROLLER v1.1 FINAL
# ==============================================================================

import streamlit as st


# ==============================================================================
# DATABASE
# ==============================================================================

from database import (
    db,
    get_inventory_view,
    get_warehouses
)


# ==============================================================================
# CORE SERVICES
# ==============================================================================

from erp_core.services.inventory_service import InventoryService
from erp_core.services.pricing_service import PricingService


# ==============================================================================
# MODULES
# ==============================================================================

from .warehouse import render_warehouse_selector
from .product_master import render_product_master
from .product_create import render_product_create
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

    selected_wh_id, selected_wh_name = render_warehouse_selector(warehouses)

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

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            '📋 Product Master',
            '➕ Add Product',
            '✏️ Edit Product',
            '🔧 Stock Adjustment',
            '📊 Dashboard'
        ]
    )

    # --------------------------------------------------------------------------
    # TAB 1 : PRODUCT MASTER
    # --------------------------------------------------------------------------

    with tab1:

        render_product_master(products)

    # --------------------------------------------------------------------------
    # TAB 2 : CREATE PRODUCT
    # --------------------------------------------------------------------------

    with tab2:

        render_product_create(
            db_client=client,
            pricing_service=pricing_service,
            warehouse_id=selected_wh_id
        )

    # --------------------------------------------------------------------------
    # TAB 3 : EDIT PRODUCT
    # --------------------------------------------------------------------------

    with tab3:

        render_product_edit(
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name
        )

    # --------------------------------------------------------------------------
    # TAB 4 : STOCK ADJUSTMENT
    # --------------------------------------------------------------------------

    with tab4:

        render_stock_adjustment(
            products=products,
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
            inventory_service=inventory_service
        )

    # --------------------------------------------------------------------------
    # TAB 5 : DASHBOARD
    # --------------------------------------------------------------------------

    with tab5:

        render_inventory_dashboard(
            warehouse_id=selected_wh_id
        )
