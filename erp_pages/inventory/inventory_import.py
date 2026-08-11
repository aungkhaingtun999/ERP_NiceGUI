# ==============================================================================
# erp_pages/inventory/inventory_import.py
#
# ERP ENTERPRISE INVENTORY IN
# Maker-Checker Inventory Import
#
# STEP 1
# - Batch creation
# - Inventory import line entry
# - Submit to Maker-Checker
# - No direct stock posting from UI
#
# Database workflow:
#
# DRAFT
#   ↓
# inventory_import_lines
#   ↓
# submit_inventory_import_batch
#   ↓
# PENDING
#   ↓
# approve_inventory_import_batch
#   ↓
# POSTED
#
# ==============================================================================

import time
import streamlit as st

from database import db


# ==============================================================================
# SESSION STATE
# ==============================================================================

def _init_state():

    defaults = {
        "inventory_import_batch_no": "",
        "inventory_import_remarks": "",
        "inventory_import_warehouse": None,
        "inventory_import_lines": [],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==============================================================================
# BATCH NUMBER
# ==============================================================================

def _generate_batch_no():

    ts = time.strftime("%Y%m%d-%H%M%S")

    return f"INV-IN-{ts}"


# ==============================================================================
# LOAD WAREHOUSES
# ==============================================================================

def _get_warehouses(client):

    response = (
        client
        .table("warehouses")
        .select("id,name")
        .order("id")
        .execute()
    )

    return response.data or []


# ==============================================================================
# FIND PRODUCT
# ==============================================================================

def _find_product(client, sku):

    sku = (sku or "").strip()

    if not sku:
        return None

    response = (
        client
        .table("products")
        .select("id,sku,name")
        .eq("sku", sku)
        .maybe_single()
        .execute()
    )

    return response.data


# ==============================================================================
# CREATE BATCH
# ==============================================================================

def _create_batch(
    client,
    batch_no,
    warehouse_id,
    remarks,
    user_id=None,
):

    payload = {
        "batch_no": batch_no,
        "transaction_type": "STOCK_IN",
        "status": "DRAFT",
        "warehouse_to": warehouse_id,
        "requested_by": user_id,
        "remarks": remarks,
        "total_lines": 0,
        "valid_lines": 0,
        "error_lines": 0,
    }

    response = (
        client
        .table("inventory_import_batches")
        .insert(payload)
        .execute()
    )

    data = response.data or []

    if not data:
        raise RuntimeError(
            "Inventory import batch creation failed."
        )

    return data[0]


# ==============================================================================
# ADD LINE
# ==============================================================================

def _add_line(
    client,
    batch_id,
    line_no,
    warehouse_id,
    sku,
    product_id,
    qty,
    unit_cost,
    lot_no,
):

    payload = {
        "batch_id": batch_id,
        "line_no": line_no,
        "warehouse_id": warehouse_id,
        "sku": sku,
        "product_id": product_id,
        "qty": qty,
        "unit_cost": unit_cost,
        "lot_no": lot_no,
        "is_valid": False,
        "error_message": None,
    }

    response = (
        client
        .table("inventory_import_lines")
        .insert(payload)
        .execute()
    )

    data = response.data or []

    if not data:
        raise RuntimeError(
            "Inventory import line creation failed."
        )

    return data[0]


# ==============================================================================
# SUBMIT BATCH
# ==============================================================================

def _submit_batch(client, batch_no):

    response = client.rpc(
        "submit_inventory_import_batch",
        {
            "p_batch_no": batch_no,
        },
    ).execute()

    return response.data


# ==============================================================================
# MAIN UI
# ==============================================================================

def render_inventory_import():

    _init_state()

    st.subheader("📥 Inventory In")
    st.caption(
        "ERP Enterprise Inventory In | Maker-Checker Enabled"
    )

    # --------------------------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------------------------

    try:
        client = db()
    except Exception as e:
        st.error(
            f"Database connection failed: {e}"
        )
        return

    # --------------------------------------------------------------------------
    # CURRENT USER
    # --------------------------------------------------------------------------

    current_user = (
        st.session_state.get("user_id")
        or st.session_state.get("current_user_id")
    )

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    try:
        warehouses = _get_warehouses(client)
    except Exception as e:
        st.error(
            f"Warehouse loading failed: {e}"
        )
        return

    if not warehouses:
        st.warning(
            "No warehouses found."
        )
        return

    warehouse_options = {
        f"{w['id']} - {w.get('name', '')}": w["id"]
        for w in warehouses
    }

    selected_warehouse_label = st.selectbox(
        "Destination Warehouse",
        list(warehouse_options.keys()),
        key="inventory_import_warehouse_select",
    )

    selected_warehouse_id = warehouse_options[
        selected_warehouse_label
    ]

    # --------------------------------------------------------------------------
    # BATCH INFORMATION
    # --------------------------------------------------------------------------

    st.markdown("### 1️⃣ Import Batch")

    col1, col2 = st.columns(2)

    with col1:

        batch_no = st.text_input(
            "Batch No",
            value=st.session_state.inventory_import_batch_no,
            key="inventory_import_batch_no_input",
        )

        if not batch_no.strip():

            if st.button(
                "Generate Batch No",
                key="inventory_import_generate_batch",
            ):

                st.session_state.inventory_import_batch_no = (
                    _generate_batch_no()
                )

                st.rerun()

    with col2:

        remarks = st.text_input(
            "Remarks",
            value=st.session_state.inventory_import_remarks,
            key="inventory_import_remarks_input",
        )

    # --------------------------------------------------------------------------
    # LINE
    # --------------------------------------------------------------------------

    st.markdown("### 2️⃣ Stock In Line")

    col1, col2 = st.columns(2)

    with col1:

        sku = st.text_input(
            "Product SKU",
            key="inventory_import_sku",
        )

        qty = st.number_input(
            "Quantity",
            min_value=0.0,
            step=1.0,
            key="inventory_import_qty",
        )

    with col2:

        unit_cost = st.number_input(
            "Unit Cost",
            min_value=0.0,
            step=100.0,
            key="inventory_import_unit_cost",
        )

        lot_no = st.text_input(
            "Lot No",
            key="inventory_import_lot_no",
        )

    # --------------------------------------------------------------------------
    # ADD LINE
    # --------------------------------------------------------------------------

    if st.button(
        "➕ Add Stock In Line",
        type="primary",
        key="inventory_import_add_line",
    ):

        if not sku.strip():

            st.error("SKU is required.")
            return

        if qty <= 0:

            st.error("Quantity must be greater than zero.")
            return

        if unit_cost < 0:

            st.error("Unit cost cannot be negative.")
            return

        try:

            product = _find_product(
                client,
                sku,
            )

            if not product:

                st.error(
                    f"Product not found for SKU: {sku}"
                )
                return

            st.session_state.inventory_import_lines.append(
                {
                    "sku": sku.strip(),
                    "product_id": product["id"],
                    "product_name": product.get("name", ""),
                    "qty": qty,
                    "unit_cost": unit_cost,
                    "lot_no": lot_no.strip() or None,
                }
            )

            st.success(
                f"Added: {product.get('name', sku)}"
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to add line: {e}"
            )

    # --------------------------------------------------------------------------
    # SHOW LINES
    # --------------------------------------------------------------------------

    lines = st.session_state.inventory_import_lines

    if lines:

        st.markdown("### 3️⃣ Import Lines")

        for index, line in enumerate(lines, start=1):

            c1, c2, c3, c4, c5 = st.columns(
                [1, 2, 1, 1, 1]
            )

            c1.write(index)
            c2.write(
                f"{line['sku']} - {line['product_name']}"
            )
            c3.write(
                f"Qty: {line['qty']}"
            )
            c4.write(
                f"Cost: {line['unit_cost']}"
            )
            c5.write(
                f"Lot: {line['lot_no'] or '-'}"
            )

    else:

        st.info(
            "No inventory lines added yet."
        )

    # --------------------------------------------------------------------------
    # CREATE + SUBMIT
    # --------------------------------------------------------------------------

    st.markdown("### 4️⃣ Submit for Approval")

    if st.button(
        "📤 Submit Inventory In",
        type="primary",
        disabled=not bool(lines),
        key="inventory_import_submit",
    ):

        if not batch_no.strip():

            st.error(
                "Batch No is required."
            )
            return

        try:

            # --------------------------------------------------------------
            # CREATE DRAFT BATCH
            # --------------------------------------------------------------

            batch = _create_batch(
                client=client,
                batch_no=batch_no.strip(),
                warehouse_id=selected_warehouse_id,
                remarks=remarks.strip() or None,
                user_id=current_user,
            )

            batch_id = batch["id"]

            # --------------------------------------------------------------
            # INSERT LINES
            # --------------------------------------------------------------

            for index, line in enumerate(
                lines,
                start=1,
            ):

                _add_line(
                    client=client,
                    batch_id=batch_id,
                    line_no=index,
                    warehouse_id=selected_warehouse_id,
                    sku=line["sku"],
                    product_id=line["product_id"],
                    qty=line["qty"],
                    unit_cost=line["unit_cost"],
                    lot_no=line["lot_no"],
                )

            # --------------------------------------------------------------
            # SUBMIT THROUGH VERIFIED RPC
            # --------------------------------------------------------------

            result = _submit_batch(
                client,
                batch_no.strip(),
            )

            if isinstance(result, list):

                result = (
                    result[0]
                    if result
                    else {}
                )

            if not isinstance(result, dict):

                st.error(
                    f"Unexpected RPC response: {result}"
                )
                return

            if result.get("success"):

                st.success(
                    "Inventory In submitted successfully."
                )

                st.json(result)

                st.session_state.inventory_import_lines = []
                st.session_state.inventory_import_batch_no = ""
                st.session_state.inventory_import_remarks = ""

                st.info(
                    "Batch is now waiting for Checker approval."
                )

            else:

                st.error(
                    result.get(
                        "message",
                        "Inventory import submission failed.",
                    )
                )

                st.json(result)

        except Exception as e:

            st.error(
                f"Inventory In submission failed: {e}"
            )

    # --------------------------------------------------------------------------
    # WORKFLOW INFO
    # --------------------------------------------------------------------------

    st.markdown("---")

    st.caption(
        "Maker → DRAFT → Submit → PENDING → "
        "Checker Approval → POSTED → FIFO / Stock Movement"
    )
