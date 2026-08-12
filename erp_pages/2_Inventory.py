# ==============================================================================
# erp_pages/2_Inventory.py
# ERP ENTERPRISE INVENTORY ENTRY
# ==============================================================================

import streamlit as st
from erp_pages.inventory.page import run
from erp_pages.inventory.warehouse_transfer_approval import (
    render_warehouse_transfer_approval_queue,
)

# Define all your tabs in order
tabs = st.tabs([
    "📊 Overview",
    "📦 Stock Levels",
    "🚚 Transfer Approval",
])

# Unpack the tabs or reference them by index
# Assuming '🚚 Transfer Approval' is the 3rd tab (index 2)
tab_overview, tab_stock, tab_transfer_approval = tabs

with tab_transfer_approval:
    render_warehouse_transfer_approval_queue()
