# ==============================================================================
# erp_pages/inventory/inventory_import_approval.py
# ERP ENTERPRISE INVENTORY IN APPROVAL v4.0
#
# STEP 4 - LINE LEVEL APPROVAL (RPC CONNECTED)
#
# Workflow
# ------------------------------------------------------------------------------
#
# inventory_import_batches
# ↓
# PENDING
# ↓
# Select Batch
# ↓
# Load Import Lines
# ↓
# Select All / Individual Lines
# ↓
# approve_inventory_import_batch(
#     p_batch_no,
#     p_checker_id,
#     p_line_ids
# )
# ↓
# Selected lines only
# ↓
# warehouse_stock
# inventory_batches
# inventory_cost_layers
#
# ------------------------------------------------------------------------------
# FEATURES
# ------------------------------------------------------------------------------
# ✔ Select All
# ✔ Clear All
# ✔ Individual line selection
# ✔ Already approved lines disabled
# ✔ Maker-Checker enforced in SQL
# ✔ Partial approval supported
# ✔ Atomic posting
# ==============================================================================

from __future__ import annotations
import streamlit as st
from database import db

STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"

# ==============================================================================
# SESSION STATE
# ==============================================================================
def _initialize_state():
    defaults = {
        "inventory_import_approval_batch_no": None,
        "inventory_import_approval_selected_lines": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ==============================================================================
# CURRENT USER
# ==============================================================================
def _get_current_user_id():
    possible_keys = [
        "user_id",
        "current_user_id",
        "logged_in_user_id",
    ]
    for key in possible_keys:
        value = st.session_state.get(key)
        if value:
            return value
    return None

# ==============================================================================
# LOAD PENDING BATCHES
# ==============================================================================
def _load_pending_batches(client):
    response = (
        client.table("inventory_import_batches")
        .select(
            """
            id,
            batch_no,
            transaction_type,
            status,
            warehouse_to,
            requested_by,
            remarks,
            total_lines,
            valid_lines,
            error_lines,
            created_at
            """
        )
        .eq("status", STATUS_PENDING)
        .order("created_at", desc=False)
        .execute()
    )
    return response.data or []

# ==============================================================================
# LOAD WAREHOUSE MAP
# ==============================================================================
def _load_warehouse_map(client):
    response = (
        client.table("warehouses")
        .select("id,name")
        .order("id")
        .execute()
    )
    rows = response.data or []
    return {
        int(row["id"]): row.get("name", "")
        for row in rows
        if row.get("id") is not None
    }

# ==============================================================================
# LOAD IMPORT LINES
# ==============================================================================
def _load_import_lines(client, batch_id):
    response = (
        client.table("inventory_import_lines")
        .select(
            """
            id,
            batch_id,
            line_no,
            warehouse_id,
            sku,
            product_id,
            qty,
            unit_cost,
            lot_no,
            mfg_date,
            expiry_date,
            reference_no,
            supplier_code,
            is_valid,
            error_message,
            approval_status,
            approved_by,
            approved_at
            """
        )
        .eq("batch_id", batch_id)
        .order("line_no")
        .execute()
    )
    return response.data or []

# ==============================================================================
# FORMAT HELPERS
# ==============================================================================
def _display(value):
    if value is None:
        return "-"
    text = str(value).strip()
    return text if text else "-"

def _format_number(value):
    if value is None:
        return "-"
    try:
        number = float(value)
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.2f}"
    except Exception:
        return str(value)

# ==============================================================================
# BATCH SUMMARY
# ==============================================================================
def _render_batch_summary(batch, warehouse_map):
    warehouse_id = batch.get("warehouse_to")
    try:
        warehouse_id = int(warehouse_id)
    except Exception:
        pass

    warehouse_name = warehouse_map.get(
        warehouse_id,
        f"Warehouse {_display(warehouse_id)}",
    )

    st.markdown(f"### 📦 {batch.get('batch_no', '-')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", _display(batch.get("status")))
    c2.metric("Total Lines", batch.get("total_lines", 0))
    c3.metric("Valid Lines", batch.get("valid_lines", 0))
    c4.metric("Error Lines", batch.get("error_lines", 0))

    st.caption(
        f"Warehouse: {warehouse_name} | "
        f"Maker: {_display(batch.get('requested_by'))}"
    )

    if batch.get("remarks"):
        st.caption(f"Remarks: {batch.get('remarks')}")

# ==============================================================================
# SELECTION HELPERS
# ==============================================================================
def _select_all_lines(lines):
    selected = {
        int(line["id"])
        for line in lines
        if line.get("is_valid") is True
        and line.get("approval_status", STATUS_PENDING) == STATUS_PENDING
        and line.get("id") is not None
    }
    st.session_state["inventory_import_approval_selected_lines"] = selected

def _clear_all_lines():
    st.session_state["inventory_import_approval_selected_lines"] = set()

# ==============================================================================
# LINE SELECTION UI
# ==============================================================================
def _render_line_selection(lines):
    st.markdown("### 📋 Import Lines")

    selectable_line_ids = {
        int(line["id"])
        for line in lines
        if line.get("is_valid") is True
        and line.get("approval_status", STATUS_PENDING) == STATUS_PENDING
        and line.get("id") is not None
    }

    current_selection = st.session_state.get(
        "inventory_import_approval_selected_lines",
        set(),
    )
    if not isinstance(current_selection, set):
        current_selection = set()

    current_selection = current_selection & selectable_line_ids
    st.session_state["inventory_import_approval_selected_lines"] = current_selection

    select_col, clear_col, info_col = st.columns([1.3, 1.3, 4])

    with select_col:
        if st.button(
            "☑️ Select All Lines",
            key="inventory_import_select_all_lines",
            use_container_width=True,
        ):
            _select_all_lines(lines)
            st.rerun()

    with clear_col:
        if st.button(
            "⬜ Clear All",
            key="inventory_import_clear_all_lines",
            use_container_width=True,
        ):
            _clear_all_lines()
            st.rerun()

    with info_col:
        st.caption(
            f"Selected: {len(current_selection)} / {len(selectable_line_ids)} selectable lines"
        )

    st.markdown("---")

    for line in lines:
        line_id = line.get("id")
        if line_id is None:
            continue
        line_id = int(line_id)

        is_valid = line.get("is_valid") is True
        approval_status = line.get("approval_status", STATUS_PENDING)
        is_approved = approval_status == STATUS_APPROVED
        is_selectable = is_valid and not is_approved
        is_selected = line_id in current_selection

        with st.container(border=True):
            select_col, data_col = st.columns([1.3, 6])

            with select_col:
                selected = st.checkbox(
                    f"Line {line.get('line_no', '-')}",
                    value=is_selected,
                    disabled=not is_selectable,
                    key=f"inventory_import_line_select_{line_id}",
                )

                current = st.session_state.get(
                    "inventory_import_approval_selected_lines",
                    set(),
                )
                if not isinstance(current, set):
                    current = set()

                if is_selectable and selected:
                    current.add(line_id)
                else:
                    current.discard(line_id)

                st.session_state["inventory_import_approval_selected_lines"] = current

            with data_col:
                st.write(
                    f"**SKU**: {_display(line.get('sku'))} | "
                    f"**Qty**: {_format_number(line.get('qty'))} | "
                    f"**Unit Cost**: {_format_number(line.get('unit_cost'))}"
                )
                st.write(
                    f"**Lot**: {_display(line.get('lot_no'))} | "
                    f"**MFG**: {_display(line.get('mfg_date'))} | "
                    f"**EXP**: {_display(line.get('expiry_date'))}"
                )
                st.write(
                    f"**Reference**: {_display(line.get('reference_no'))} | "
                    f"**Supplier**: {_display(line.get('supplier_code'))}"
                )

                if is_approved:
                    st.success(f"APPROVED by {_display(line.get('approved_by'))}")
                elif is_valid:
                    st.info("PENDING")
                else:
                    st.error("INVALID")

                if line.get("error_message"):
                    st.caption("Error: " + str(line.get("error_message")))

# ==============================================================================
# APPROVE RPC
# ==============================================================================
def _approve_selected_lines(
    client,
    batch_no,
    checker_id,
    line_ids,
):
    response = (
        client.rpc(
            "approve_inventory_import_batch",
            {
                "p_batch_no": batch_no,
                "p_checker_id": str(checker_id),
                "p_line_ids": list(line_ids),
            },
        )
        .execute()
    )
    return response.data

# ==============================================================================
# MAIN
# ==============================================================================
def render_inventory_import_approval():
    _initialize_state()

    st.subheader("✅ Inventory In Approval")
    st.caption("Checker | Line-Level Approval | Maker-Checker Enabled")

    try:
        client = db()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return

    checker_id = _get_current_user_id()
    if not checker_id:
        st.warning("Current user session ID was not found.")
        return

    try:
        batches = _load_pending_batches(client)
        warehouse_map = _load_warehouse_map(client)
    except Exception as e:
        st.error("Approval queue loading failed.")
        st.exception(e)
        return

    if not batches:
        st.success("🎉 No PENDING Inventory In batches.")
        st.session_state["inventory_import_approval_batch_no"] = None
        _clear_all_lines()
        return

    batch_options = {
        str(batch["batch_no"]): batch
        for batch in batches
        if batch.get("batch_no")
    }
    batch_nos = list(batch_options.keys())

    current_batch_no = st.session_state.get(
        "inventory_import_approval_batch_no"
    )
    if current_batch_no not in batch_options:
        current_batch_no = batch_nos[0]
        st.session_state["inventory_import_approval_batch_no"] = current_batch_no
        _clear_all_lines()

    selected_batch_no = st.selectbox(
        "Select PENDING Inventory In Batch",
        batch_nos,
        index=batch_nos.index(current_batch_no),
        key="inventory_import_approval_batch_selector",
    )

    if selected_batch_no != current_batch_no:
        st.session_state["inventory_import_approval_batch_no"] = selected_batch_no
        _clear_all_lines()
        st.rerun()

    selected_batch = batch_options[selected_batch_no]

    _render_batch_summary(selected_batch, warehouse_map)
    st.markdown("---")

    try:
        lines = _load_import_lines(
            client,
            selected_batch["id"],
        )
    except Exception as e:
        st.error("Import line loading failed.")
        st.exception(e)
        return

    if not lines:
        st.warning("No import lines found in this batch.")
        return

    _render_line_selection(lines)

    selected_line_ids = st.session_state.get(
        "inventory_import_approval_selected_lines",
        set(),
    )
    if not isinstance(selected_line_ids, set):
        selected_line_ids = set()

    selected_lines = [
        line
        for line in lines
        if line.get("id") is not None and int(line["id"]) in selected_line_ids
    ]

    st.markdown("---")
    st.markdown("### 📊 Selection Summary")

    total_selected_qty = sum(
        float(line.get("qty", 0) or 0) for line in selected_lines
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Selected Lines",
        len(selected_lines),
    )
    c2.metric(
        "Selected Quantity",
        _format_number(total_selected_qty),
    )
    c3.metric(
        "Checker",
        str(checker_id)[:8] + "...",
    )

    if selected_lines:
        st.success(f"{len(selected_lines)} line(s) selected for approval.")
    else:
        st.info("Please select the lines above to approve.")

    st.markdown("---")

    approve_clicked = st.button(
        "✅ Approve Selected Lines",
        disabled=len(selected_line_ids) == 0,
        use_container_width=True,
        key="inventory_import_approve_selected_lines",
    )

    if approve_clicked:
        try:
            result = _approve_selected_lines(
                client=client,
                batch_no=selected_batch_no,
                checker_id=checker_id,
                line_ids=sorted(selected_line_ids),
            )
            if result.get("success"):
                st.success(
                    result.get(
                        "message",
                        "Inventory lines approved successfully.",
                    )
                )
                st.json(result)
                _clear_all_lines()
                st.rerun()
            else:
                st.error(
                    result.get(
                        "message",
                        "Inventory approval failed.",
                    )
                )
                st.json(result)
        except Exception as e:
            st.error(f"Inventory approval failed: {e}")
            st.exception(e)
