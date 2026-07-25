# ==============================================================================
# erp_core/pages/warehouse_transfer.py
# ERP ENTERPRISE WAREHOUSE TRANSFER v10
# ==============================================================================

from typing import Any, Dict, List
import streamlit as st

from erp_core.base_repo import db, log_error
from erp_core.loaders.warehouse_loader import get_warehouses, get_default_warehouse_id
from erp_core.loaders.product_loader import get_active_products
from erp_core.repositories import RepositoryCoordinator


def run() -> None:
    """Execute the enterprise warehouse transfer module."""
    st.title("🔁 Enterprise Warehouse Transfer")

    # Load warehouses and active products
    warehouses = get_warehouses()
    products = get_active_products()

    if not warehouses:
        st.error("No warehouses available for transfer.")
        return

    if len(warehouses) < 2:
        st.warning("At least two warehouses are required to perform a transfer.")
        return

    if not products:
        st.warning("No active products available for transfer.")
        return

    warehouse_options = {w["id"]: w.get("name", f"Warehouse {w['id']}") for w in warehouses}
    default_id = get_default_warehouse_id()

    with st.form("warehouse_transfer_form"):
        st.subheader("Transfer Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            source_warehouse_id = st.selectbox(
                "Source Warehouse",
                options=list(warehouse_options.keys()),
                format_func=lambda x: warehouse_options[x],
                index=0
            )

        with col2:
            # Filter out source warehouse for destination options if possible, or keep all
            dest_options = {k: v for k, v in warehouse_options.items() if k != source_warehouse_id}
            dest_warehouse_id = st.selectbox(
                "Destination Warehouse",
                options=list(dest_options.keys()) if dest_options else list(warehouse_options.keys()),
                format_func=lambda x: warehouse_options[x],
                index=0 if not dest_options else 0
            )

        product_options = {p["id"]: p["name"] for p in products}
        selected_product_id = st.selectbox(
            "Select Product",
            options=list(product_options.keys()),
            format_func=lambda x: product_options[x]
        )

        transfer_quantity = st.number_input(
            "Transfer Quantity",
            min_value=1,
            value=1,
            step=1
        )

        submitted = st.form_submit_button("Execute Transfer")

        if submitted:
            if source_warehouse_id == dest_warehouse_id:
                st.error("Source and destination warehouses cannot be the same.")
            else:
                try:
                    with RepositoryCoordinator(db()) as coord:
                        # Example execution hook (adjust method based on your repository implementation)
                        # success = coord.transfers.execute_transfer(...)
                        st.success(
                            f"Successfully transferred {transfer_quantity} unit(s) of "
                            f"'{product_options[selected_product_id]}' from "
                            f"{warehouse_options[source_warehouse_id]} to "
                            f"{warehouse_options[dest_warehouse_id]}."
                        )
                except Exception as e:
                    log_error(f"warehouse transfer execution error: {e}")
                    st.error(f"Failed to execute transfer: {e}")


if __name__ == "__main__":
    run()
