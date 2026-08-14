# ==============================================================================
# erp_pages/inventory/inventory_import_approval.py
#
# ERP ENTERPRISE INVENTORY IN APPROVAL v6.0
#
# STEP 5 - LINE APPROVAL / REJECTION / BATCH CANCELLATION
#
# ==============================================================================
#
# WORKFLOW
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
# ┌─────────────────────────────────────────────┐
# │                                             │
# │ Select / Individual Lines                   │
# │                                             │
# └─────────────────────────────────────────────┘
#          │
#          ├───────────────────────┐
#          │                       │
#          ▼                       ▼
#      APPROVE                   REJECT
#          │                       │
#          ▼                       ▼
#   approve_inventory_       reject_inventory_
#   import_batch()            import_lines()
#          │                       │
#          ▼                       ▼
#       POSTED                  REJECTED
#
#
# BATCH LEVEL
# ------------------------------------------------------------------------------
#
# PENDING
#    │
#    └── Cancel Batch
#            │
#            ▼
#        CANCELLED
#
# ==============================================================================
#
# VERIFIED RPCs
# ------------------------------------------------------------------------------
#
# APPROVE:
#
# approve_inventory_import_batch(
#     p_batch_no text,
#     p_checker_id uuid,
#     p_line_ids bigint[]
# )
#
#
# REJECT:
#
# reject_inventory_import_lines(
#     p_batch_no text,
#     p_checker_id uuid,
#     p_line_ids bigint[],
#     p_reason text
# )
#
#
# CANCEL:
#
# cancel_inventory_import_batch(
#     p_batch_no text,
#     p_checker_id uuid,
#     p_reason text
# )
#
# ==============================================================================
#
# FEATURES
# ------------------------------------------------------------------------------
#
# ✔ Batch selector
# ✔ Select All pending valid lines
# ✔ Clear All
# ✔ Individual line selection
# ✔ Already APPROVED lines disabled
# ✔ Already REJECTED lines disabled
# ✔ Invalid lines disabled
# ✔ Maker-Checker enforced by SQL
# ✔ Partial approval
# ✔ Partial rejection
# ✔ Approve selected lines
# ✔ Reject selected lines
# ✔ Rejection reason required
# ✔ Batch cancellation
# ✔ Cancellation reason required
# ✔ Cancel confirmation required
# ✔ Myanmar Standard Time display
# ✔ Approval metadata
# ✔ Rejection metadata
# ✔ Batch cancellation metadata
# ✔ Pending / Approved / Rejected counters
# ✔ Atomic approval posting
# ✔ SQL RPC owns business transaction
# ✔ UI NEVER directly modifies inventory stock
#
# IMPORTANT
# ------------------------------------------------------------------------------
#
# Batch cancellation is allowed ONLY by the SQL RPC.
#
# UI does NOT:
#
# - update inventory_import_batches directly
# - delete import lines
# - modify warehouse_stock
# - modify inventory_batches
# - modify inventory_cost_layers
#
# All business rules remain inside PostgreSQL RPCs.
#
# ==============================================================================

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from database import db


# ==============================================================================
# CONSTANTS
# ==============================================================================

STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_POSTED = "POSTED"
STATUS_CANCELLED = "CANCELLED"

MYANMAR_TIMEZONE = ZoneInfo("Asia/Yangon")


# ==============================================================================
# SESSION STATE
# ==============================================================================

def _initialize_state():

    defaults = {

        # Currently selected batch
        "inventory_import_approval_batch_no": None,

        # Selected line IDs
        "inventory_import_approval_selected_lines": set(),

        # Line rejection reason
        "inventory_import_approval_reject_reason": "",

        # Batch cancellation reason
        "inventory_import_approval_cancel_reason": "",

        # Batch cancellation confirmation
        "inventory_import_approval_cancel_confirm": False,

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
# SAFE RPC RESULT
# ==============================================================================

def _normalize_rpc_result(data):

    """
    Supabase RPC may return:

        dict

    or occasionally:

        [dict]

    Normalize to dict.
    """

    if isinstance(data, dict):

        return data

    if isinstance(data, list) and data:

        first = data[0]

        if isinstance(first, dict):

            return first

    return {
        "success": False,
        "message": "Unexpected RPC response.",
        "raw": data,
    }


# ==============================================================================
# MYSQL / POSTGRES TIMESTAMP → MYANMAR TIME
# ==============================================================================

def _format_myanmar_datetime(value):

    """
    Convert PostgreSQL timestamp-with-time-zone value
    to Myanmar Standard Time.

    Display only.

    Database storage remains timezone-aware.
    """

    if value is None:

        return "-"

    try:

        if isinstance(value, datetime):

            dt = value

        else:

            text = str(value).strip()

            if not text:

                return "-"

            # PostgreSQL ISO format may contain +00:00
            # or trailing Z.
            if text.endswith("Z"):

                text = text[:-1] + "+00:00"

            dt = datetime.fromisoformat(
                text
            )

        # If timestamp has no timezone,
        # treat it as UTC rather than guessing.
        if dt.tzinfo is None:

            from datetime import timezone

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        dt = dt.astimezone(
            MYANMAR_TIMEZONE
        )

        return dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        ) + " MMT"

    except Exception:

        return str(value)


# ==============================================================================
# DISPLAY
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
            warehouse_from,
            warehouse_to,
            requested_by,
            approved_by,
            total_lines,
            valid_lines,
            error_lines,
            remarks,
            created_at,
            approved_at,
            posted_at,
            cancelled_by,
            cancelled_at,
            cancellation_reason
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
# LOAD WAREHOUSE MAP
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
            error_message,
            approval_status,
            approved_by,
            approved_at,
            rejected_by,
            rejected_at,
            rejection_reason
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
# BATCH SUMMARY
# ==============================================================================

def _render_batch_summary(
    batch,
    warehouse_map,
    lines,
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

    # --------------------------------------------------------------------------
    # MAIN BATCH METRICS
    # --------------------------------------------------------------------------

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

    # --------------------------------------------------------------------------
    # LINE STATUS COUNTERS
    # --------------------------------------------------------------------------

    pending_count = 0
    approved_count = 0
    rejected_count = 0
    invalid_count = 0

    for line in lines:

        if line.get("is_valid") is not True:

            invalid_count += 1

            continue

        status = str(
            line.get(
                "approval_status",
                STATUS_PENDING,
            )
        ).upper()

        if status == STATUS_APPROVED:

            approved_count += 1

        elif status == STATUS_REJECTED:

            rejected_count += 1

        else:

            pending_count += 1

    st.markdown(
        "#### 📊 Line Status"
    )

    s1, s2, s3, s4 = st.columns(4)

    s1.metric(
        "Pending",
        pending_count,
    )

    s2.metric(
        "Approved",
        approved_count,
    )

    s3.metric(
        "Rejected",
        rejected_count,
    )

    s4.metric(
        "Invalid",
        invalid_count,
    )

    # --------------------------------------------------------------------------
    # BATCH INFO
    # --------------------------------------------------------------------------

    st.caption(
        f"Warehouse: {warehouse_name} | "
        f"Maker: {_display(batch.get('requested_by'))}"
    )

    if batch.get("transaction_type"):

        st.caption(
            f"Transaction Type: "
            f"{_display(batch.get('transaction_type'))}"
        )

    if batch.get("remarks"):

        st.caption(
            f"Remarks: {_display(batch.get('remarks'))}"
        )

    # --------------------------------------------------------------------------
    # CREATED TIME
    # --------------------------------------------------------------------------

    st.caption(
        f"Created: "
        f"{_format_myanmar_datetime(batch.get('created_at'))}"
    )


# ==============================================================================
# SELECTION HELPERS
# ==============================================================================

def _get_selectable_line_ids(lines):

    return {
        int(line["id"])

        for line in lines

        if line.get("id") is not None

        and line.get("is_valid") is True

        and str(
            line.get(
                "approval_status",
                STATUS_PENDING,
            )
        ).upper() == STATUS_PENDING
    }


# ==============================================================================
# SELECT ALL
# ==============================================================================

def _select_all_lines(lines):

    selected = _get_selectable_line_ids(
        lines
    )

    st.session_state[
        "inventory_import_approval_selected_lines"
    ] = selected


# ==============================================================================
# CLEAR ALL
# ==============================================================================

def _clear_all_lines():

    st.session_state[
        "inventory_import_approval_selected_lines"
    ] = set()


# ==============================================================================
# CLEAR REJECT REASON
# ==============================================================================

def _clear_reject_reason():

    st.session_state[
        "inventory_import_approval_reject_reason"
    ] = ""


# ==============================================================================
# CLEAR CANCEL REASON
# ==============================================================================

def _clear_cancel_reason():

    st.session_state[
        "inventory_import_approval_cancel_reason"
    ] = ""

    st.session_state[
        "inventory_import_approval_cancel_confirm"
    ] = False


# ==============================================================================
# LINE SELECTION UI
# ==============================================================================

def _render_line_selection(
    lines,
):

    st.markdown(
        "### 📋 Import Lines"
    )

    selectable_line_ids = _get_selectable_line_ids(
        lines
    )

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
        & selectable_line_ids
    )

    st.session_state[
        "inventory_import_approval_selected_lines"
    ] = current_selection

    # --------------------------------------------------------------------------
    # Selection controls
    # --------------------------------------------------------------------------

    select_col, clear_col, info_col = st.columns(
        [1.4, 1.3, 4]
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
            f"/ {len(selectable_line_ids)} selectable lines"
        )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # Lines
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

        approval_status = str(
            line.get(
                "approval_status",
                STATUS_PENDING,
            )
        ).upper()

        is_approved = (
            approval_status
            == STATUS_APPROVED
        )

        is_rejected = (
            approval_status
            == STATUS_REJECTED
        )

        is_selectable = (
            is_valid
            and not is_approved
            and not is_rejected
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
                [1.4, 6]
            )

            # ------------------------------------------------------------------
            # CHECKBOX
            # ------------------------------------------------------------------

            with select_col:

                selected = st.checkbox(
                    f"Line {line.get('line_no', '-')}",
                    value=is_selected,
                    disabled=not is_selectable,
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

                if (
                    is_selectable
                    and selected
                ):

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

            # ------------------------------------------------------------------
            # DATA
            # ------------------------------------------------------------------

            with data_col:

                c1, c2, c3 = st.columns(3)

                c1.write(
                    f"**SKU**  \n"
                    f"{_display(line.get('sku'))}"
                )

                c2.write(
                    f"**Quantity**  \n"
                    f"{_format_number(line.get('qty'))}"
                )

                c3.write(
                    f"**Unit Cost**  \n"
                    f"{_format_number(line.get('unit_cost'))}"
                )

                c4, c5, c6 = st.columns(3)

                c4.write(
                    f"**Lot No**  \n"
                    f"{_display(line.get('lot_no'))}"
                )

                c5.write(
                    f"**MFG Date**  \n"
                    f"{_display(line.get('mfg_date'))}"
                )

                c6.write(
                    f"**Expiry Date**  \n"
                    f"{_display(line.get('expiry_date'))}"
                )

                c7, c8 = st.columns(2)

                c7.write(
                    f"**Reference No**  \n"
                    f"{_display(line.get('reference_no'))}"
                )

                c8.write(
                    f"**Supplier Code**  \n"
                    f"{_display(line.get('supplier_code'))}"
                )

                # --------------------------------------------------------------
                # APPROVED
                # --------------------------------------------------------------

                if is_approved:

                    st.success(
                        "✅ APPROVED"
                    )

                    st.caption(
                        f"Approved By: "
                        f"{_display(line.get('approved_by'))}"
                    )

                    st.caption(
                        f"Approved At: "
                        f"{_format_myanmar_datetime(line.get('approved_at'))}"
                    )

                # --------------------------------------------------------------
                # REJECTED
                # --------------------------------------------------------------

                elif is_rejected:

                    st.error(
                        "❌ REJECTED"
                    )

                    st.caption(
                        f"Rejected By: "
                        f"{_display(line.get('rejected_by'))}"
                    )

                    st.caption(
                        f"Rejected At: "
                        f"{_format_myanmar_datetime(line.get('rejected_at'))}"
                    )

                    st.caption(
                        f"Reason: "
                        f"{_display(line.get('rejection_reason'))}"
                    )

                # --------------------------------------------------------------
                # PENDING
                # --------------------------------------------------------------

                elif is_valid:

                    st.info(
                        "⏳ PENDING"
                    )

                # --------------------------------------------------------------
                # INVALID
                # --------------------------------------------------------------

                else:

                    st.error(
                        "⚠️ INVALID"
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
# APPROVE RPC
# ==============================================================================

def _approve_selected_lines(
    client,
    batch_no,
    checker_id,
    line_ids,
):

    response = (
        client
        .rpc(
            "approve_inventory_import_batch",
            {
                "p_batch_no": str(
                    batch_no
                ),

                "p_checker_id": str(
                    checker_id
                ),

                "p_line_ids": [
                    int(x)
                    for x in line_ids
                ],
            },
        )
        .execute()
    )

    return _normalize_rpc_result(
        response.data
    )


# ==============================================================================
# REJECT RPC
# ==============================================================================

def _reject_selected_lines(
    client,
    batch_no,
    checker_id,
    line_ids,
    reason,
):

    response = (
        client
        .rpc(
            "reject_inventory_import_lines",
            {
                "p_batch_no": str(
                    batch_no
                ),

                "p_checker_id": str(
                    checker_id
                ),

                "p_line_ids": [
                    int(x)
                    for x in line_ids
                ],

                "p_reason": str(
                    reason
                ).strip(),
            },
        )
        .execute()
    )

    return _normalize_rpc_result(
        response.data
    )


# ==============================================================================
# CANCEL BATCH RPC
# ==============================================================================

def _cancel_inventory_batch(
    client,
    batch_no,
    checker_id,
    reason,
):

    response = (
        client
        .rpc(
            "cancel_inventory_import_batch",
            {
                "p_batch_no": str(
                    batch_no
                ),

                "p_checker_id": str(
                    checker_id
                ),

                "p_reason": str(
                    reason
                ).strip(),
            },
        )
        .execute()
    )

    return _normalize_rpc_result(
        response.data
    )


# ==============================================================================
# SELECTION SUMMARY
# ==============================================================================

def _render_selection_summary(
    lines,
    checker_id,
):

    selected_line_ids = st.session_state.get(
        "inventory_import_approval_selected_lines",
        set(),
    )

    if not isinstance(
        selected_line_ids,
        set,
    ):

        selected_line_ids = set()

    selected_lines = []

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

        if line_id in selected_line_ids:

            selected_lines.append(
                line
            )

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
        "Selected Lines",
        len(selected_lines),
    )

    c2.metric(
        "Selected Quantity",
        _format_number(
            total_selected_qty
        ),
    )

    c3.metric(
        "Checker",
        str(
            checker_id
        )[:8]
        + "...",
    )

    if selected_lines:

        st.success(
            f"{len(selected_lines)} line(s) selected."
        )

        for line in selected_lines:

            st.write(
                f"• Line "
                f"{line.get('line_no')} | "
                f"{line.get('sku')} | "
                f"Qty "
                f"{_format_number(line.get('qty'))}"
            )

    else:

        st.info(
            "Approve / Reject လုပ်မည့် "
            "Line များကို အပေါ်မှ ရွေးချယ်ပါ။"
        )

    return (
        selected_line_ids,
        selected_lines,
    )


# ==============================================================================
# LINE APPROVAL / REJECTION ACTION PANEL
# ==============================================================================

def _render_action_panel(
    client,
    selected_batch_no,
    checker_id,
    selected_line_ids,
):

    st.markdown("---")

    st.markdown(
        "### ⚙️ Line Approval Actions"
    )

    if not selected_line_ids:

        st.info(
            "Line တစ်ခုခုကို ရွေးပြီးမှ "
            "Approve / Reject ပြုလုပ်နိုင်ပါမည်။"
        )

        return

    # ==========================================================================
    # REJECTION REASON
    # ==========================================================================

    st.markdown(
        "#### ❌ Rejection Reason"
    )

    reject_reason = st.text_area(
        "Reject Reason",
        value=st.session_state.get(
            "inventory_import_approval_reject_reason",
            "",
        ),
        placeholder=(
            "ဥပမာ - Quantity မမှန်ပါ၊ "
            "Lot No မမှန်ပါ၊ Unit Cost ပြန်စစ်ရန်..."
        ),
        key="inventory_import_reject_reason_input",
        height=100,
    )

    st.session_state[
        "inventory_import_approval_reject_reason"
    ] = reject_reason

    st.caption(
        "Reject လုပ်ရာတွင် Reason မဖြစ်မနေထည့်ရပါမည်။"
    )

    st.markdown("---")

    approve_col, reject_col, clear_col = st.columns(
        [2.2, 2.2, 1.4]
    )

    # ==========================================================================
    # APPROVE
    # ==========================================================================

    with approve_col:

        approve_clicked = st.button(
            "✅ Approve Selected Lines",
            use_container_width=True,
            key=(
                "inventory_import_"
                "approve_selected_lines"
            ),
        )

    # ==========================================================================
    # REJECT
    # ==========================================================================

    with reject_col:

        reject_clicked = st.button(
            "❌ Reject Selected Lines",
            use_container_width=True,
            key=(
                "inventory_import_"
                "reject_selected_lines"
            ),
        )

    # ==========================================================================
    # CLEAR
    # ==========================================================================

    with clear_col:

        clear_clicked = st.button(
            "↩️ Clear",
            use_container_width=True,
            key=(
                "inventory_import_"
                "clear_action_selection"
            ),
        )

    # ==========================================================================
    # CLEAR UI
    # ==========================================================================

    if clear_clicked:

        _clear_all_lines()

        _clear_reject_reason()

        st.rerun()

    # ==========================================================================
    # APPROVE
    # ==========================================================================

    if approve_clicked:

        try:

            with st.spinner(
                "Approving selected inventory lines..."
            ):

                result = _approve_selected_lines(
                    client=client,
                    batch_no=selected_batch_no,
                    checker_id=checker_id,
                    line_ids=sorted(
                        selected_line_ids
                    ),
                )

            if result.get(
                "success"
            ):

                st.success(
                    result.get(
                        "message",
                        "Inventory lines approved successfully.",
                    )
                )

                st.json(
                    result
                )

                _clear_all_lines()

                _clear_reject_reason()

                st.rerun()

            else:

                st.error(
                    result.get(
                        "message",
                        "Inventory approval failed.",
                    )
                )

                st.json(
                    result
                )

        except Exception as e:

            st.error(
                f"Inventory approval failed: {e}"
            )

            st.exception(
                e
            )

    # ==========================================================================
    # REJECT
    # ==========================================================================

    if reject_clicked:

        reason = str(
            reject_reason
            or ""
        ).strip()

        if not reason:

            st.error(
                "❌ Reject Reason မဖြစ်မနေထည့်ပေးပါ။"
            )

            return

        if len(reason) < 3:

            st.error(
                "❌ Reject Reason အနည်းဆုံး "
                "3 characters ရှိရပါမည်။"
            )

            return

        try:

            with st.spinner(
                "Rejecting selected inventory lines..."
            ):

                result = _reject_selected_lines(
                    client=client,
                    batch_no=selected_batch_no,
                    checker_id=checker_id,
                    line_ids=sorted(
                        selected_line_ids
                    ),
                    reason=reason,
                )

            if result.get(
                "success"
            ):

                st.success(
                    result.get(
                        "message",
                        "Selected inventory lines rejected successfully.",
                    )
                )

                st.json(
                    result
                )

                _clear_all_lines()

                _clear_reject_reason()

                st.rerun()

            else:

                st.error(
                    result.get(
                        "message",
                        "Inventory rejection failed.",
                    )
                )

                st.json(
                    result
                )

        except Exception as e:

            st.error(
                f"Inventory rejection failed: {e}"
            )

            st.exception(
                e
            )


# ==============================================================================
# BATCH CANCELLATION PANEL
# ==============================================================================

def _render_batch_cancel_panel(
    client,
    selected_batch,
    checker_id,
):

    """
    Batch-level cancellation.

    IMPORTANT:
    Only PENDING batches are shown in this page because
    the queue itself is PENDING-only.

    Actual authorization and state validation remain
    inside cancel_inventory_import_batch RPC.
    """

    st.markdown("---")

    st.markdown(
        "### 🚫 Batch Cancellation"
    )

    batch_no = _display(
        selected_batch.get(
            "batch_no"
        )
    )

    status = str(
        selected_batch.get(
            "status",
            "",
        )
    ).upper()

    if status != STATUS_PENDING:

        st.info(
            f"Batch {batch_no} is not PENDING. "
            f"Cancellation is unavailable."
        )

        return

    st.warning(
        f"⚠️ ဒီလုပ်ဆောင်ချက်က Batch တစ်ခုလုံးကို "
        f"`CANCELLED` အဖြစ် ပြောင်းပါမယ်။\n\n"
        f"Batch: **{batch_no}**"
    )

    # ==========================================================================
    # CANCEL REASON
    # ==========================================================================

    cancel_reason = st.text_area(
        "Cancellation Reason",
        value=st.session_state.get(
            "inventory_import_approval_cancel_reason",
            "",
        ),
        placeholder=(
            "ဥပမာ - Import file မှားယွင်းနေပါသည်၊ "
            "Warehouse မှားနေပါသည်၊ Duplicate import ဖြစ်နေပါသည်..."
        ),
        key="inventory_import_cancel_reason_input",
        height=100,
    )

    st.session_state[
        "inventory_import_approval_cancel_reason"
    ] = cancel_reason

    # ==========================================================================
    # CONFIRMATION
    # ==========================================================================

    confirm_cancel = st.checkbox(
        "⚠️ ဒီ Batch တစ်ခုလုံးကို CANCEL လုပ်မည်ကို အတည်ပြုပါသည်။",
        value=st.session_state.get(
            "inventory_import_approval_cancel_confirm",
            False,
        ),
        key="inventory_import_cancel_confirm_input",
    )

    st.session_state[
        "inventory_import_approval_cancel_confirm"
    ] = confirm_cancel

    st.markdown("---")

    cancel_col, clear_col = st.columns(
        [2.5, 1.5]
    )

    # ==========================================================================
    # CANCEL BATCH
    # ==========================================================================

    with cancel_col:

        cancel_clicked = st.button(
            "🚫 Cancel Entire Batch",
            disabled=not confirm_cancel,
            use_container_width=True,
            key="inventory_import_cancel_entire_batch",
        )

    # ==========================================================================
    # CLEAR CANCEL FORM
    # ==========================================================================

    with clear_col:

        clear_clicked = st.button(
            "Clear",
            use_container_width=True,
            key="inventory_import_clear_cancel_form",
        )

    if clear_clicked:

        _clear_cancel_reason()

        st.rerun()

    # ==========================================================================
    # CANCEL RPC
    # ==========================================================================

    if cancel_clicked:

        reason = str(
            cancel_reason
            or ""
        ).strip()

        # ----------------------------------------------------------------------
        # REASON REQUIRED
        # ----------------------------------------------------------------------

        if not reason:

            st.error(
                "❌ Cancellation Reason မဖြစ်မနေထည့်ပေးပါ။"
            )

            return

        # ----------------------------------------------------------------------
        # MINIMUM REASON
        # ----------------------------------------------------------------------

        if len(reason) < 3:

            st.error(
                "❌ Cancellation Reason အနည်းဆုံး "
                "3 characters ရှိရပါမည်။"
            )

            return

        # ----------------------------------------------------------------------
        # RPC
        # ----------------------------------------------------------------------

        try:

            with st.spinner(
                "Cancelling inventory import batch..."
            ):

                result = _cancel_inventory_batch(
                    client=client,
                    batch_no=batch_no,
                    checker_id=checker_id,
                    reason=reason,
                )

            if result.get(
                "success"
            ):

                st.success(
                    result.get(
                        "message",
                        "Inventory import batch cancelled successfully.",
                    )
                )

                st.json(
                    result
                )

                # Clear all UI state
                _clear_all_lines()

                _clear_reject_reason()

                _clear_cancel_reason()

                # Remove current batch from selector
                st.session_state[
                    "inventory_import_approval_batch_no"
                ] = None

                st.rerun()

            else:

                st.error(
                    result.get(
                        "message",
                        "Inventory batch cancellation failed.",
                    )
                )

                st.json(
                    result
                )

        except Exception as e:

            st.error(
                f"Inventory batch cancellation failed: {e}"
            )

            st.exception(
                e
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
        "Checker | Line Approval / Rejection | Batch Cancellation | Maker-Checker"
    )

    st.info(
        "Inventory Import Batch တစ်ခုအတွင်းမှ "
        "လိုအပ်သော Line များကို ရွေးချယ်ပြီး "
        "Approve / Reject ပြုလုပ်နိုင်ပါသည်။ "
        "လိုအပ်ပါက Batch တစ်ခုလုံးကိုလည်း Cancel ပြုလုပ်နိုင်ပါသည်။"
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

        st.exception(
            e
        )

        return

    # ==========================================================================
    # NO PENDING BATCH
    # ==========================================================================

    if not batches:

        st.success(
            "🎉 No PENDING Inventory In batches."
        )

        st.session_state[
            "inventory_import_approval_batch_no"
        ] = None

        _clear_all_lines()

        _clear_reject_reason()

        _clear_cancel_reason()

        return

    # ==========================================================================
    # BATCH OPTIONS
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

    # ==========================================================================
    # CURRENT BATCH
    # ==========================================================================

    current_batch_no = st.session_state.get(
        "inventory_import_approval_batch_no"
    )

    if (
        current_batch_no
        not in batch_options
    ):

        current_batch_no = batch_nos[0]

        st.session_state[
            "inventory_import_approval_batch_no"
        ] = current_batch_no

        _clear_all_lines()

        _clear_reject_reason()

        _clear_cancel_reason()

    # ==========================================================================
    # BATCH SELECTOR
    # ==========================================================================

    selected_batch_no = st.selectbox(
        "Select PENDING Inventory In Batch",
        batch_nos,
        index=batch_nos.index(
            current_batch_no
        ),
        key=(
            "inventory_import_approval_"
            "batch_selector"
        ),
    )

    # ==========================================================================
    # BATCH CHANGED
    # ==========================================================================

    if selected_batch_no != current_batch_no:

        st.session_state[
            "inventory_import_approval_batch_no"
        ] = selected_batch_no

        _clear_all_lines()

        _clear_reject_reason()

        _clear_cancel_reason()

        st.rerun()

    # ==========================================================================
    # SELECTED BATCH
    # ==========================================================================

    selected_batch = batch_options[
        selected_batch_no
    ]

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

        st.exception(
            e
        )

        return

    # ==========================================================================
    # BATCH SUMMARY
    # ==========================================================================

    _render_batch_summary(
        selected_batch,
        warehouse_map,
        lines,
    )

    st.markdown("---")

    # ==========================================================================
    # NO LINES
    # ==========================================================================

    if not lines:

        st.warning(
            "No import lines found in this batch."
        )

        # Even if lines are missing,
        # batch cancellation remains SQL-controlled.
        _render_batch_cancel_panel(
            client=client,
            selected_batch=selected_batch,
            checker_id=checker_id,
        )

        return

    # ==========================================================================
    # LINE SELECTION
    # ==========================================================================

    _render_line_selection(
        lines
    )

    # ==========================================================================
    # SELECTION SUMMARY
    # ==========================================================================

    (
        selected_line_ids,
        selected_lines,
    ) = _render_selection_summary(
        lines,
        checker_id,
    )

    # ==========================================================================
    # LINE ACTION PANEL
    # ==========================================================================

    _render_action_panel(
        client=client,
        selected_batch_no=selected_batch_no,
        checker_id=checker_id,
        selected_line_ids=selected_line_ids,
    )

    # ==========================================================================
    # BATCH CANCEL PANEL
    # ==========================================================================

    _render_batch_cancel_panel(
        client=client,
        selected_batch=selected_batch,
        checker_id=checker_id,
    )


# ==============================================================================
# END OF FILE
# ==============================================================================
