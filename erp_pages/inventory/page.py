# ==============================================================================
# erp_pages/8_Transfer.py
# ERP ENTERPRISE WAREHOUSE TRANSFER v32
#
# MAKER-CHECKER ENABLED
#
# FLOW
# ------------------------------------------------------------------------------
# Maker
#   ↓
# create_warehouse_transfer_request_rpc()
#   ↓
# warehouse_transfer_requests
#   ↓
# PENDING
#   ↓
# Checker
#   ↓
# approve_warehouse_transfer_rpc()
#   ↓
# warehouse_stock movement
#
# IMPORTANT
# ------------------------------------------------------------------------------
# This page MUST NOT directly update warehouse_stock.
# All stock movement is controlled by Supabase RPC.
# ==============================================================================

import time
import streamlit as st

from erp_core.base_repo import db, log_error
from erp_core.loaders.warehouse_loader import get_warehouses

from .inventory.warehouse_transfer_approval import (
    render_warehouse_transfer_approval_queue,
)


# ==============================================================================
# USER
# ==============================================================================

def _get_current_user():

    user = st.session_state.get("user")

    if not isinstance(user, dict):
        return None

    return user


# ==============================================================================
# REQUEST TRANSFER
# ==============================================================================

def _create_transfer_request(
    client,
    current_user_id,
    source_warehouse_id,
    destination_warehouse_id,
    product_id,
    quantity,
):

    try:

        response = (
            client.rpc(
                "create_warehouse_transfer_request_rpc",
                {
                    "p_source_warehouse_id":
                        int(source_warehouse_id),

                    "p_destination_warehouse_id":
                        int(destination_warehouse_id),

                    "p_product_id":
                        int(product_id),

                    "p_quantity":
                        float(quantity),

                    "p_maker_id":
                        str(current_user_id),
                },
            )
            .execute()
        )

        result = response.data

        if isinstance(result, list):
            result = result[0] if result else None

        if not isinstance(result, dict):

            st.error(
                "❌ Invalid transfer RPC response."
            )

            st.json(result)

            return False

        if not result.get("success"):

            st.error(
                result.get(
                    "message",
                    "Transfer request failed."
                )
            )

            return False

        request_id = result.get(
            "request_id",
            "-"
        )

        status = result.get(
            "status",
            "PENDING"
        )

        # ----------------------------------------------------------------------
        # DO NOT show only a short-lived toast.
        # Keep the result visible.
        # ----------------------------------------------------------------------

        st.session_state[
            "warehouse_transfer_last_result"
        ] = {
            "success": True,
            "request_id": request_id,
            "status": status,
            "quantity": result.get(
                "quantity",
                quantity
            ),
            "source_warehouse_id":
                result.get(
                    "source_warehouse_id",
                    source_warehouse_id
                ),
            "destination_warehouse_id":
                result.get(
                    "destination_warehouse_id",
                    destination_warehouse_id
                ),
            "product_id":
                result.get(
                    "product_id",
                    product_id
                ),
            "message":
                result.get(
                    "message",
                    "Transfer request created."
                ),
        }

        return True

    except Exception as e:

        log_error(
            message="Warehouse transfer request failed.",
            exception=e
        )

        st.error(
            "❌ Failed to create warehouse transfer request."
        )

        st.exception(e)

        return False


# ==============================================================================
# SHOW LAST RESULT
# ==============================================================================

def _render_last_result():

    result = st.session_state.get(
        "warehouse_transfer_last_result"
    )

    if not result:
        return

    st.markdown("---")
    st.subheader("📌 Latest Transfer Request")

    if result.get("success"):

        st.success(
            "✅ Transfer request created successfully."
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Request ID",
                f"#{result.get('request_id')}"
            )

        with c2:

            st.metric(
                "Status",
                result.get("status", "PENDING")
            )

        with c3:

            st.metric(
                "Quantity",
                result.get("quantity", 0)
            )

        st.info(
            """
🟡 STATUS: PENDING

Stock has NOT been moved yet.

This transfer is waiting for Checker approval.
"""
        )

        st.write(
            f"**Source Warehouse:** "
            f"{result.get('source_warehouse_id')}"
        )

        st.write(
            f"**Destination Warehouse:** "
            f"{result.get('destination_warehouse_id')}"
        )

        st.write(
            f"**Product ID:** "
            f"{result.get('product_id')}"
        )

        st.caption(
            "Maker → Pending → Checker Approval → Stock Movement"
        )


# ==============================================================================
# TRANSFER REQUEST FORM
# ==============================================================================

def _render_transfer_request():

    st.subheader("🚚 Create Warehouse Transfer")

    current_user = _get_current_user()

    if not current_user:

        st.error("🔒 Login required.")

        return

    current_user_id = current_user.get("id")

    if not current_user_id:

        st.error(
            "Current user ID is missing."
        )

        return

    # --------------------------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------------------------

    try:

        client = db()

    except Exception as e:

        st.error(
            "ERP database connection failed."
        )

        st.exception(e)

        return

    # --------------------------------------------------------------------------
    # WAREHOUSES
    # --------------------------------------------------------------------------

    try:

        warehouses = get_warehouses()

    except Exception as e:

        st.error(
            "Warehouse loading failed."
        )

        st.exception(e)

        return

    if not warehouses:

        st.warning(
            "No warehouses found."
        )

        return

    warehouse_options = {}

    for warehouse in warehouses:

        try:

            warehouse_id = int(
                warehouse.get("id")
            )

        except Exception:

            continue

        code = (
            warehouse.get("code")
            or "N/A"
        )

        name = (
            warehouse.get("name")
            or "Unknown"
        )

        warehouse_options[
            warehouse_id
        ] = (
            f"[{warehouse_id}] "
            f"{code} - {name}"
        )

    if len(warehouse_options) < 2:

        st.warning(
            "At least two warehouses are required."
        )

        return

    # --------------------------------------------------------------------------
    # SOURCE / DESTINATION
    # --------------------------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        source_warehouse_id = st.selectbox(
            "Source Warehouse",
            list(
                warehouse_options.keys()
            ),
            format_func=lambda x:
                warehouse_options[x],
            key="transfer_source_warehouse",
        )

    destination_list = [
        x
        for x in warehouse_options.keys()
        if x != source_warehouse_id
    ]

    with col2:

        destination_warehouse_id = st.selectbox(
            "Destination Warehouse",
            destination_list,
            format_func=lambda x:
                warehouse_options[x],
            key="transfer_destination_warehouse",
        )

    # --------------------------------------------------------------------------
    # SOURCE STOCK
    # --------------------------------------------------------------------------

    try:

        stock_rows = (
            client
            .table("warehouse_stock")
            .select(
                """
                product_id,
                qty,
                available_qty
                """
            )
            .eq(
                "warehouse_id",
                int(source_warehouse_id)
            )
            .gt(
                "available_qty",
                0
            )
            .execute()
            .data
            or []
        )

    except Exception as e:

        st.error(
            "Source stock loading failed."
        )

        st.exception(e)

        return

    if not stock_rows:

        st.warning(
            "Source warehouse has no available stock."
        )

        return

    # --------------------------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------------------------

    product_ids = []

    for row in stock_rows:

        try:

            product_ids.append(
                int(row["product_id"])
            )

        except Exception:

            pass

    if not product_ids:

        st.warning(
            "No valid products found."
        )

        return

    try:

        products = (
            client
            .table("products")
            .select(
                "id,name,sku"
            )
            .in_(
                "id",
                product_ids
            )
            .execute()
            .data
            or []
        )

    except Exception as e:

        st.error(
            "Product loading failed."
        )

        st.exception(e)

        return

    product_options = {}

    for product in products:

        try:

            product_id = int(
                product["id"]
            )

        except Exception:

            continue

        name = (
            product.get("name")
            or "Unnamed Product"
        )

        sku = (
            product.get("sku")
            or "-"
        )

        product_options[
            product_id
        ] = (
            f"{name} "
            f"(SKU: {sku})"
        )

    if not product_options:

        st.warning(
            "No products available for transfer."
        )

        return

    # --------------------------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------------------------

    selected_product_id = st.selectbox(
        "Select Product",
        list(
            product_options.keys()
        ),
        format_func=lambda x:
            product_options[x],
        key="transfer_product",
    )

    # --------------------------------------------------------------------------
    # SOURCE STOCK
    # --------------------------------------------------------------------------

    source_stock = next(
        (
            row
            for row in stock_rows
            if int(row["product_id"])
            == int(selected_product_id)
        ),
        None
    )

    if not source_stock:

        st.error(
            "Source stock record not found."
        )

        return

    try:

        source_qty = float(
            source_stock.get(
                "qty",
                0
            ) or 0
        )

        source_available = float(
            source_stock.get(
                "available_qty",
                0
            ) or 0
        )

    except Exception:

        source_qty = 0
        source_available = 0

    # --------------------------------------------------------------------------
    # DESTINATION STOCK
    # --------------------------------------------------------------------------

    try:

        dest_rows = (
            client
            .table("warehouse_stock")
            .select(
                "qty,available_qty"
            )
            .eq(
                "warehouse_id",
                int(destination_warehouse_id)
            )
            .eq(
                "product_id",
                int(selected_product_id)
            )
            .limit(1)
            .execute()
            .data
            or []
        )

    except Exception as e:

        st.error(
            "Destination stock loading failed."
        )

        st.exception(e)

        return

    if dest_rows:

        dest_qty = float(
            dest_rows[0].get(
                "qty",
                0
            ) or 0
        )

        dest_available = float(
            dest_rows[0].get(
                "available_qty",
                0
            ) or 0
        )

    else:

        dest_qty = 0
        dest_available = 0

    # --------------------------------------------------------------------------
    # STOCK DISPLAY
    # --------------------------------------------------------------------------

    c1, c2 = st.columns(2)

    with c1:

        st.info(
            f"""
📤 SOURCE STOCK

Warehouse:
{warehouse_options[source_warehouse_id]}

Product:
{product_options[selected_product_id]}

Current Qty:
{source_qty:g}

Available Qty:
{source_available:g}
"""
        )

    with c2:

        st.success(
            f"""
📥 DESTINATION STOCK

Warehouse:
{warehouse_options[destination_warehouse_id]}

Product:
{product_options[selected_product_id]}

Current Qty:
{dest_qty:g}

Available Qty:
{dest_available:g}
"""
        )

    if source_available <= 0:

        st.error(
            "No available stock."
        )

        return

    # --------------------------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------------------------

    transfer_qty = st.number_input(
        "Transfer Quantity",
        min_value=1.0,
        max_value=float(source_available),
        value=1.0,
        step=1.0,
        key="warehouse_transfer_quantity",
    )

    # --------------------------------------------------------------------------
    # PREVIEW
    # --------------------------------------------------------------------------

    st.subheader(
        "📊 Transfer Preview"
    )

    p1, p2 = st.columns(2)

    with p1:

        st.metric(
            "After Approval - Source Stock",
            f"{source_qty - transfer_qty:g}",
            delta=f"-{transfer_qty:g}",
        )

    with p2:

        st.metric(
            "After Approval - Destination Stock",
            f"{dest_qty + transfer_qty:g}",
            delta=f"+{transfer_qty:g}",
        )

    # --------------------------------------------------------------------------
    # IMPORTANT NOTICE
    # --------------------------------------------------------------------------

    st.warning(
        """
⚠️ Maker-Checker Control

This action creates a PENDING transfer request only.

Stock will NOT move now.

Stock will move only after a different Checker
approves the request.
"""
    )

    # --------------------------------------------------------------------------
    # SUBMIT
    # --------------------------------------------------------------------------

    if st.button(
        "📤 Submit Transfer Request",
        type="primary",
        use_container_width=True,
        key="submit_warehouse_transfer_request",
    ):

        if int(source_warehouse_id) == int(
            destination_warehouse_id
        ):

            st.error(
                "Source and destination warehouses must be different."
            )

            return

        if transfer_qty <= 0:

            st.error(
                "Transfer quantity must be greater than zero."
            )

            return

        if transfer_qty > source_available:

            st.error(
                "Transfer quantity exceeds available stock."
            )

            return

        success = _create_transfer_request(
            client=client,
            current_user_id=current_user_id,
            source_warehouse_id=
                source_warehouse_id,
            destination_warehouse_id=
                destination_warehouse_id,
            product_id=
                selected_product_id,
            quantity=
                transfer_qty,
        )

        if success:

            # Do NOT immediately rerun.
            # User must see the PENDING result.
            st.session_state[
                "warehouse_transfer_form_submitted"
            ] = True


# ==============================================================================
# MAIN
# ==============================================================================

def run():

    st.title(
        "🔁 Enterprise Warehouse Transfer"
    )

    st.caption(
        "Maker-Checker Controlled Warehouse Transfer"
    )

    current_user = _get_current_user()

    if not current_user:

        st.error(
            "🔒 Login required."
        )

        return

    # --------------------------------------------------------------------------
    # TABS
    # --------------------------------------------------------------------------

    request_tab, approval_tab = st.tabs(
        [
            "📤 Transfer Request",
            "🟡 Transfer Approval",
        ]
    )

    # --------------------------------------------------------------------------
    # MAKER
    # --------------------------------------------------------------------------

    with request_tab:

        _render_transfer_request()

        _render_last_result()

    # --------------------------------------------------------------------------
    # CHECKER
    # --------------------------------------------------------------------------

    with approval_tab:

        render_warehouse_transfer_approval_queue()


if __name__ == "__main__":

    run()
