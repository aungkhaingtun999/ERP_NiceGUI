# ==============================================================================
# erp_pages/inventory/inventory_import_approval.py
#
# ERP ENTERPRISE INVENTORY IN APPROVAL
# STEP 3 - LINE LEVEL SELECTION
#
# Workflow
# ------------------------------------------------------------------------------
#
# inventory_import_batches
#          ↓
#        PENDING
#          ↓
#      Select Batch
#          ↓
#   Load Import Lines
#          ↓
# Select All / Individual Lines
#
# IMPORTANT
# ------------------------------------------------------------------------------
# STEP 3 ONLY
#
# This module prepares LINE-LEVEL selection.
#
# It DOES NOT post stock.
#
# It DOES NOT call:
#
#     approve_inventory_import_batch()
#
# because the current RPC approves the ENTIRE batch.
#
# Line-level approval RPC will be implemented in the next step.
# ==============================================================================

from __future__ import annotations

import streamlit as st

from database import db


# ==============================================================================
# CONSTANTS
# ==============================================================================

STATUS_PENDING = "PENDING"


# ==============================================================================
# SESSION STATE
# ==============================================================================

def _initialize_state():

    defaults = {

        # Currently opened PENDING batch
        "inventory_import_approval_batch_no": None,

        # Selected line IDs
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
        client
        .table("inventory_import_batches")
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
        .eq(
            "status",
            STATUS_PENDING,
        )
        .order(
            "created_at",
            desc=False,
        )
        .execute()
    )

    return response.data or []


# ==============================================================================
# LOAD WAREHOUSES
# ==============================================================================

def _load_warehouse_map(client):

    response = (
        client
        .table("warehouses")
        .select(
            "id,name"
        )
        .order(
            "id"
        )
        .execute()
    )

    rows = response.data or []

    return {
        int(row["id"]): row.get(
            "name",
            "",
        )
        for row in rows
        if row.get("id") is not None
    }


# ==============================================================================
# LOAD IMPORT LINES
# ==============================================================================

def _load_import_lines(
    client,
    batch_id,
):
    """
    Load all lines belonging to one Inventory In batch.
    """

    response = (
        client
        .table("inventory_import_lines")
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
            error_message
            """
        )
        .eq(
            "batch_id",
            batch_id,
        )
        .order(
            "line_no",
        )
        .execute()
    )

    return response.data or []


# ==============================================================================
# FORMAT VALUE
# ==============================================================================

def _display(value):

    if value is None:

        return "-"

    text = str(value).strip()

    return text if text else "-"


# ==============================================================================
# FORMAT NUMBER
# ==============================================================================

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

def _render_batch_summary(
    batch,
    warehouse_map,
):

    warehouse_id = batch.get(
        "warehouse_to"
    )

    try:

        warehouse_id = int(
            warehouse_id
        )

    except (
        TypeError,
        ValueError,
    ):

        pass

    warehouse_name = warehouse_map.get(
        warehouse_id,
        f"Warehouse {_display(warehouse_id)}",
    )

    st.markdown(
        f"### 📦 {batch.get('batch_no', '-')}"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Status",
        _display(
            batch.get("status")
        ),
    )

    c2.metric(
        "Total Lines",
        batch.get(
            "total_lines",
            0,
        ),
    )

    c3.metric(
        "Valid Lines",
        batch.get(
            "valid_lines",
            0,
        ),
    )

    c4.metric(
        "Error Lines",
        batch.get(
            "error_lines",
            0,
        ),
    )

    st.caption(
        f"Warehouse: {warehouse_name} | "
        f"Maker: {_display(batch.get('requested_by'))}"
    )

    if batch.get("remarks"):

        st.caption(
            f"Remarks: {batch.get('remarks')}"
        )


# ==============================================================================
# SELECT ALL LINES
# ==============================================================================

def _select_all_lines(
    lines,
):
    """
    Select all VALID lines.

    Invalid lines are never selectable for posting.
    """

    selected = {
        int(line["id"])
        for line in lines
        if line.get("is_valid") is True
        and line.get("id") is not None
    }

    st.session_state[
        "inventory_import_approval_selected_lines"
    ] = selected


# ==============================================================================
# CLEAR ALL LINES
# ==============================================================================

def _clear_all_lines():

    st.session_state[
        "inventory_import_approval_selected_lines"
    ] = set()


# ==============================================================================
# LINE SELECTION
# ==============================================================================

def _render_line_selection(
    lines,
):

    st.markdown(
        "### 📋 Import Lines"
    )

    valid_line_ids = {
        int(line["id"])
        for line in lines
        if line.get("is_valid") is True
        and line.get("id") is not None
    }

    current_selection = st.session_state.get(
        "inventory_import_approval_selected_lines",
        set(),
    )

    if not isinstance(
        current_selection,
        set,
    ):

        current_selection = set()

    # --------------------------------------------------------------------------
    # Remove stale selections
    # --------------------------------------------------------------------------

    current_selection = (
        current_selection
        & valid_line_ids
    )

    st.session_state[
        "inventory_import_approval_selected_lines"
    ] = current_selection

    # --------------------------------------------------------------------------
    # Selection controls
    # --------------------------------------------------------------------------

    select_col, clear_col, info_col = st.columns(
        [1.3, 1.3, 4]
    )

    with select_col:

        if st.button(
            "☑️ Select All Lines",
            key="inventory_import_select_all_lines",
            use_container_width=True,
        ):

            _select_all_lines(
                lines
            )

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
            f"Selected: {len(current_selection)} "
            f"/ {len(valid_line_ids)} valid lines"
        )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # Line-by-line selection
    # --------------------------------------------------------------------------

    for line in lines:

        line_id = line.get(
            "id"
        )

        if line_id is None:

            continue

        try:

            line_id = int(
                line_id
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        is_valid = (
            line.get("is_valid")
            is True
        )

        is_selected = (
            line_id
            in current_selection
        )

        # ----------------------------------------------------------------------
        # LINE CARD
        # ----------------------------------------------------------------------

        with st.container(
            border=True
        ):

            select_col, data_col = st.columns(
                [1.3, 6]
            )

            with select_col:

                if is_valid:

                    selected = st.checkbox(
                        f"Line {line.get('line_no', '-')}",
                        value=is_selected,
                        key=(
                            "inventory_import_line_select_"
                            f"{line_id}"
                        ),
                    )

                    current = st.session_state.get(
                        "inventory_import_approval_selected_lines",
                        set(),
                    )

                    if not isinstance(
                        current,
                        set,
                    ):

                        current = set()

                    if selected:

                        current.add(
                            line_id
                        )

                    else:

                        current.discard(
                            line_id
                        )

                    st.session_state[
                        "inventory_import_approval_selected_lines"
                    ] = current

                else:

                    st.checkbox(
                        f"Line {line.get('line_no', '-')}",
                        value=False,
                        disabled=True,
                        key=(
                            "inventory_import_line_invalid_"
                            f"{line_id}"
                        ),
                    )

            with data_col:

                sku = _display(
                    line.get("sku")
                )

                qty = _format_number(
                    line.get("qty")
                )

                unit_cost = _format_number(
                    line.get("unit_cost")
                )

                lot_no = _display(
                    line.get("lot_no")
                )

                mfg_date = _display(
                    line.get("mfg_date")
                )

                expiry_date = _display(
                    line.get("expiry_date")
                )

                reference_no = _display(
                    line.get("reference_no")
                )

                supplier_code = _display(
                    line.get("supplier_code")
                )

                c1, c2, c3 = st.columns(3)

                c1.write(
                    f"**SKU**  \n{sku}"
                )

                c2.write(
                    f"**Quantity**  \n{qty}"
                )

                c3.write(
                    f"**Unit Cost**  \n{unit_cost}"
                )

                c4, c5, c6 = st.columns(3)

                c4.write(
                    f"**Lot No**  \n{lot_no}"
                )

                c5.write(
                    f"**MFG Date**  \n{mfg_date}"
                )

                c6.write(
                    f"**Expiry Date**  \n{expiry_date}"
                )

                c7, c8 = st.columns(2)

                c7.write(
                    f"**Reference No**  \n"
                    f"{reference_no}"
                )

                c8.write(
                    f"**Supplier Code**  \n"
                    f"{supplier_code}"
                )

                if is_valid:

                    st.success(
                        "VALID"
                    )

                else:

                    st.error(
                        "INVALID"
                    )

                    if line.get(
                        "error_message"
                    ):

                        st.caption(
                            "Error: "
                            + str(
                                line.get(
                                    "error_message"
                                )
                            )
                        )


# ==============================================================================
# MAIN
# ==============================================================================

def render_inventory_import_approval():

    # ==========================================================================
    # SESSION
    # ==========================================================================

    _initialize_state()

    # ==========================================================================
    # HEADER
    # ==========================================================================

    st.subheader(
        "✅ Inventory In Approval"
    )

    st.caption(
        "Checker | Select individual import lines or Select All Lines"
    )

    st.info(
        "ဒီအဆင့်မှာ Batch တစ်ခုအတွင်းရှိတဲ့ "
        "Import Line တွေကို ရွေးချယ်ခြင်းပဲ ပြုလုပ်ထားပါတယ်။ "
        "Approve လုပ်တဲ့ Database RPC ကို နောက်အဆင့်မှာ "
        "Selected Line ID များအတိုင်း ပြောင်းလဲပါမယ်။"
    )

    # ==========================================================================
    # DATABASE
    # ==========================================================================

    try:

        client = db()

    except Exception as e:

        st.error(
            f"Database connection failed: {e}"
        )

        return

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================

    checker_id = _get_current_user_id()

    if not checker_id:

        st.warning(
            "Current user session ID was not found."
        )

        return

    # ==========================================================================
    # LOAD BATCHES
    # ==========================================================================

    try:

        batches = _load_pending_batches(
            client
        )

        warehouse_map = _load_warehouse_map(
            client
        )

    except Exception as e:

        st.error(
            "Approval queue loading failed."
        )

        st.exception(e)

        return

    # ==========================================================================
    # NO PENDING
    # ==========================================================================

    if not batches:

        st.success(
            "🎉 No PENDING Inventory In batches."
        )

        st.session_state[
            "inventory_import_approval_batch_no"
        ] = None

        _clear_all_lines()

        return

    # ==========================================================================
    # SELECT BATCH
    # ==========================================================================

    batch_options = {
        str(
            batch["batch_no"]
        ): batch
        for batch in batches
        if batch.get("batch_no")
    }

    batch_nos = list(
        batch_options.keys()
    )

    current_batch_no = st.session_state.get(
        "inventory_import_approval_batch_no"
    )

    if (
        current_batch_no not in batch_options
    ):

        current_batch_no = batch_nos[0]

        st.session_state[
            "inventory_import_approval_batch_no"
        ] = current_batch_no

        _clear_all_lines()

    selected_batch_no = st.selectbox(
        "Select PENDING Inventory In Batch",
        batch_nos,
        index=batch_nos.index(
            current_batch_no
        ),
        key="inventory_import_approval_batch_selector",
    )

    if selected_batch_no != current_batch_no:

        st.session_state[
            "inventory_import_approval_batch_no"
        ] = selected_batch_no

        _clear_all_lines()

        st.rerun()

    # ==========================================================================
    # SELECTED BATCH
    # ==========================================================================

    selected_batch = batch_options[
        selected_batch_no
    ]

    _render_batch_summary(
        selected_batch,
        warehouse_map,
    )

    st.markdown("---")

    # ==========================================================================
    # LOAD LINES
    # ==========================================================================

    try:

        lines = _load_import_lines(
            client,
            selected_batch["id"],
        )

    except Exception as e:

        st.error(
            "Import line loading failed."
        )

        st.exception(e)

        return

    # ==========================================================================
    # NO LINES
    # ==========================================================================

    if not lines:

        st.warning(
            "No import lines found in this batch."
        )

        return

    # ==========================================================================
    # LINE SELECTION
    # ==========================================================================

    _render_line_selection(
        lines
    )

    # ==========================================================================
    # SELECTED SUMMARY
    # ==========================================================================

    selected_line_ids = st.session_state.get(
        "inventory_import_approval_selected_lines",
        set(),
    )

    if not isinstance(
        selected_line_ids,
        set,
    ):

        selected_line_ids = set()

    valid_lines = [
        line
        for line in lines
        if line.get("is_valid") is True
    ]

    selected_lines = [
        line
        for line in valid_lines
        if int(line["id"])
        in selected_line_ids
    ]

    st.markdown("---")

    st.markdown(
        "### 📊 Selection Summary"
    )

    total_selected_qty = sum(
        float(
            line.get(
                "qty",
                0,
            )
            or 0
        )
        for line in selected_lines
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Valid Lines",
        len(valid_lines),
    )

    c2.metric(
        "Selected Lines",
        len(selected_lines),
    )

    c3.metric(
        "Selected Quantity",
        _format_number(
            total_selected_qty
        ),
    )

    if selected_lines:

        st.success(
            f"{len(selected_lines)} line(s) selected."
        )

        for line in selected_lines:

            st.write(
                f"• Line {line.get('line_no')} | "
                f"{line.get('sku')} | "
                f"Qty {_format_number(line.get('qty'))}"
            )

    else:

        st.info(
            "Approve လုပ်မည့် Line များကို အပေါ်မှ ရွေးချယ်ပါ။"
        )

    # ==========================================================================
    # APPROVE BUTTON
    # ==========================================================================

    st.markdown("---")

    st.warning(
        "⚠️ Approve button ကို နောက်အဆင့်မှာ "
        "Selected Lines အတိုင်း Database RPC နှင့် ချိတ်ဆက်ပါမယ်။"
    )

    st.button(
        "✅ Approve Selected Lines",
        disabled=True,
        use_container_width=True,
        key="inventory_import_approve_selected_lines",
    )
