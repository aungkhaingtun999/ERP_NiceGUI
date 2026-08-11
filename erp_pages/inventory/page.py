ERP ENTERPRISE INVENTORY PAGE CONTROLLER v1.7

PRODUCT MASTER

PRODUCT 360°

ADD PRODUCT

APPROVAL QUEUE

EDIT PRODUCT

PRODUCT MASTER BULK IMPORT

INVENTORY IN

STOCK ADJUSTMENT

DASHBOARD

MAKER-CHECKER ENABLED

MOBILE READY

import streamlit as st

==============================================================================

DATABASE

==============================================================================

from database import ( db, get_inventory_view, get_warehouses, )

==============================================================================

SERVICES

==============================================================================

from erp_core.services.inventory_service import InventoryService
from erp_core.services.pricing_service import PricingService

==============================================================================

INVENTORY UI MODULES

==============================================================================

from .warehouse import render_warehouse_selector
from .product_master import render_product_master
from .product_create import render_product_create
from .product_approval import render_product_approval_queue
from .product_edit import render_product_edit
from .product_import import render_product_import
from .inventory_import import render_inventory_import
from .stock_adjustment import render_stock_adjustment
from .dashboard import render_inventory_dashboard

==============================================================================

PRODUCT 360°

==============================================================================

from .product_360 import render_product_360_page

==============================================================================

TAB DEFINITIONS

==============================================================================

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

==============================================================================

TAB ICONS

==============================================================================

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

==============================================================================

SESSION STATE

==============================================================================

def _get_active_tab():
    if "inventory_active_tab" not in st.session_state:
        st.session_state.inventory_active_tab = "Product Master"
    current_tab = st.session_state.inventory_active_tab
    if current_tab not in INVENTORY_TABS:
        current_tab = "Product Master"
        st.session_state.inventory_active_tab = current_tab
    return current_tab 

def _set_active_tab(tab_name):
    if tab_name in INVENTORY_TABS:
        st.session_state.inventory_active_tab = tab_name 

==============================================================================

TAB NAVIGATION

==============================================================================

def _render_tab_navigation():
    active_tab = _get_active_tab()
    labels = [
        f"{icon} {name}" for icon, name in zip(INVENTORY_TAB_ICONS, INVENTORY_TABS)
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

==============================================================================

MAIN INVENTORY PAGE

==============================================================================

def run_inventory_page():
    st.title("🏭 Enterprise Product Master")
    st.caption(
        "ERP Inventory Control Center | Mobile Ready | Maker Checker Enabled"
    )
    
    # --------------------------------------------------------------------------
    # Session Init
    # --------------------------------------------------------------------------
    if "inventory_barcode" not in st.session_state:
        st.session_state.inventory_barcode = ""
    if "product_360_selected_id" not in st.session_state:
        st.session_state.product_360_selected_id = None
    _get_active_tab()
    
    # --------------------------------------------------------------------------
    # Database
    # --------------------------------------------------------------------------
    try:
        client = db()
        inventory_service = InventoryService(client)
        pricing_service = PricingService(client)
    except Exception as e:
        st.error("ERP Service Connection Failed")
        st.exception(e)
        st.stop()
        
    # --------------------------------------------------------------------------
    # Warehouses
    # --------------------------------------------------------------------------
    try:
        warehouses = get_warehouses()
    except Exception as e:
        st.error("Warehouse loading error")
        st.exception(e)
        st.stop()
        
    if not warehouses:
        st.error("No active warehouses found.")
        st.stop()
        
    selected_wh_id, selected_wh_name = render_warehouse_selector(
        warehouses,
        key="inventory_warehouse_selector",
    )
    st.session_state.warehouses = warehouses
    
    # --------------------------------------------------------------------------
    # Product Load
    # --------------------------------------------------------------------------
    barcode = st.session_state.get("inventory_barcode", "")
    barcode = str(barcode).strip() if barcode else ""
    try:
        products = get_inventory_view(
            warehouse_id=selected_wh_id,
            search=barcode,
        )
    except Exception as e:
        st.error("Product loading error")
        st.exception(e)
        products = []
        
    # --------------------------------------------------------------------------
    # Product 360 Selector
    # --------------------------------------------------------------------------
    product_options = {
        f"{p.get('name')} ({p.get('sku')})": p.get("product_id") for p in products
    }
    selected_product_id = st.session_state.get("product_360_selected_id")
    if product_options:
        labels = list(product_options.keys())
        default_index = 0
        for i, label in enumerate(labels):
            if product_options[label] == selected_product_id:
                default_index = i
                break
        selected_label = st.selectbox(
            "🔎 Product 360° Product",
            labels,
            index=default_index,
            key="product_360_selector",
        )
        selected_product_id = product_options[selected_label]
        st.session_state.product_360_selected_id = selected_product_id
        
    # --------------------------------------------------------------------------
    # Navigation
    # --------------------------------------------------------------------------
    active_tab = _render_tab_navigation()
    st.markdown("---")
    
    # --------------------------------------------------------------------------
    # Product Master
    # --------------------------------------------------------------------------
    if active_tab == "Product Master":
        render_product_master(products)
        
    # --------------------------------------------------------------------------
    # Product 360°
    # --------------------------------------------------------------------------
    elif active_tab == "Product 360°":
        if not selected_product_id:
            st.info("Select a product above to open Product 360°.")
        else:
            render_product_360_page(
                client,
                int(selected_product_id),
            )
            
    # --------------------------------------------------------------------------
    # Add Product
    # --------------------------------------------------------------------------
    elif active_tab == "Add Product":
        render_product_create(
            db_client=client,
            pricing_service=pricing_service,
            warehouse_id=selected_wh_id,
        )
        
    # --------------------------------------------------------------------------
    # Approval Queue
    # --------------------------------------------------------------------------
    elif active_tab == "Approval Queue":
        render_product_approval_queue()
        
    # --------------------------------------------------------------------------
    # Edit Product
    # --------------------------------------------------------------------------
    elif active_tab == "Edit Product":
        render_product_edit(
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
        )
        
    # --------------------------------------------------------------------------
    # Product Import
    # --------------------------------------------------------------------------
    elif active_tab == "Product Import":
        render_product_import(
            warehouse_id=selected_wh_id,
        )
        
    # --------------------------------------------------------------------------
    # Inventory In
    # --------------------------------------------------------------------------
    elif active_tab == "Inventory In":
        render_inventory_import()
        
    # --------------------------------------------------------------------------
    # Stock Adjustment
    # --------------------------------------------------------------------------
    elif active_tab == "Stock Adjustment":
        render_stock_adjustment(
            products=products,
            warehouse_id=selected_wh_id,
            warehouse_name=selected_wh_name,
            inventory_service=inventory_service,
        )
        
    # --------------------------------------------------------------------------
    # Dashboard
    # --------------------------------------------------------------------------
    elif active_tab == "Dashboard":
        render_inventory_dashboard(
            warehouse_id=selected_wh_id,
        ) 

==============================================================================

LEGACY ENTRY

==============================================================================

def run():
    return run_inventory_page()
