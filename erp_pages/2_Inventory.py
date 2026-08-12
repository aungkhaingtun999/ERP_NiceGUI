# ==============================================================================
# erp_pages/2_Inventory.py
# ERP ENTERPRISE INVENTORY ENTRY
# ==============================================================================

from erp_pages.inventory.page import run
from erp_pages.inventory.warehouse_transfer_approval import (
    render_warehouse_transfer_approval_queue,
)
tab_transfer_approval = st.tabs([
    ...,
    '🚚 Transfer Approval',
])[N]
with tab_transfer_approval:
    render_warehouse_transfer_approval_queue()
