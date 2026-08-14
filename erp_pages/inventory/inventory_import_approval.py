# ==============================================================================
# erp_pages/inventory/inventory_import_approval.py
#
# ERP ENTERPRISE INVENTORY IN APPROVAL
# VERSION 7.0
#
# STEP 5
# ------------------------------------------------------------------------------
# LINE APPROVAL
# LINE REJECTION
# BATCH CANCELLATION
#
# ARCHITECTURE
# ------------------------------------------------------------------------------
#
# Streamlit UI
#      ↓
# Supabase RPC
#      ↓
# PostgreSQL Business Transaction
#
# UI NEVER directly modifies:
#
# - inventory_import_batches
# - inventory_import_lines
# - warehouse_stock
# - inventory_batches
# - inventory_cost_layers
#
# ALL business rules remain inside PostgreSQL RPCs.
#
# VERIFIED RPCs
# ------------------------------------------------------------------------------
#
# APPROVE
#
# approve_inventory_import_batch(
#     p_batch_no text,
#     p_checker_id uuid,
#     p_line_ids bigint[]
# )
#
#
# REJECT
#
# reject_inventory_import_lines(
#     p_batch_no text,
#     p_checker_id uuid,
#     p_line_ids bigint[],
#     p_reason text
# )
#
#
# CANCEL
#
# cancel_inventory_import_batch(
#     p_batch_no text,
#     p_checker_id uuid,
#     p_reason text
# )
#
# IMPORTANT DATABASE NOTE
# ------------------------------------------------------------------------------
#
# inventory_import_lines DOES NOT have batch_no.
#
# Relationship:
#
# inventory_import_batches.id
#          ↓
# inventory_import_lines.batch_id
#
# Therefore this UI NEVER selects/inserts/updates inventory_import_lines.batch_no.
#
# ==============================================================================

from __future__ import annotations

from datetime import datetime, timezone
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
# SESSION STATE KEYS
# ==============================================================================

KEY_BATCH_NO = "inventory_import_approval_batch_no"
KEY_SELECTED_LINES = "inventory_import_approval_selected_lines"
KEY_REJECT_REASON = "inventory_import_approval_reject_reason"
KEY_CANCEL_REASON = "inventory_import_approval_cancel_reason"
KEY_CANCEL_CONFIRM = "inventory_import_approval_cancel_confirm"


# ==============================================================================
# SESSION INITIALIZATION
# ==============================================================================

def _initialize_state():

    defaults = {

        KEY_BATCH_NO: None,

        KEY_SELECTED_LINES: set(),

        KEY_REJECT_REASON: "",

        KEY_CANCEL_REASON: "",

        KEY_CANCEL_CONFIRM: False,

    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


# ==============================================================================
# CURRENT USER
# ==============================================================================

def _get_current_user_id():

    """
    Try the common ERP session keys.

    SQL RPC remains the final authority for:
        - user existence
        - active status
        - role
        - permission
        - maker/checker segregation
    """

    possible_keys = (
        "user_id",
        "current_user_id",
        "logged_in_user_id",
    )

    for key in possible_keys:

        value = st.session_state.get(key)

        if value:

            return value

    return None


# ==============================================================================
# RPC RESULT NORMALIZER
# ==============================================================================

def _normalize_rpc_result(data):

    """
    Supabase RPC can return:

        dict

    or:

        [dict]

    Normalize both to one dict.
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
# DISPLAY HELPERS
# ==============================================================================

def _display(value):

    if value is None:

        return "-"

    text = str(value).strip()

    if not text:

        return "-"

    return text


# ==============================================================================
# NUMBER FORMAT
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
# BOOLEAN NORMALIZATION
# ==============================================================================

def _is_true(value):

    if value is True:

        return True

    if isinstance(value, str):

        return value.strip().lower() in {
            "true",
            "t",
            "1",
            "yes",
        }

    if isinstance(value, int):

        return value == 1

    return False


# ==============================================================================
# STATUS NORMALIZATION
# ==============================================================================

def _normalize_status(value):

    return str(
        value or STATUS_PENDING
    ).strip().upper()


# ==============================================================================
# DATETIME → MYANMAR STANDARD TIME
# ==============================================================================

def _format_myanmar_datetime(value):

    """
    PostgreSQL timestamp display helper.

    Database storage remains unchanged.

    Display timezone:
        Asia/Yangon
        UTC +06:30
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

            if text.endswith("Z"):

                text = text[:-1] + "+00:00"

            dt = datetime.fromisoformat(
                text
            )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        dt = dt.astimezone(
            MYANMAR_TIMEZONE
        )

        return (
            dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            + " MMT"
        )

    except Exception:

        return str(value)


# ==============================================================================
# CLEAR SELECTION
# ==============================================================================

def _clear_selected_lines():

    st.session_state[
        KEY_SELECTED_LINES
    ] = set()


# ==============================================================================
# CLEAR REJECTION FORM
# ==============================================================================

def _clear_reject_reason():

    st.session_state[
        KEY_REJECT_REASON
    ] = ""

    # Do not directly mutate the text_area widget key.
    # It will be reset on rerun because the application state is cleared.


# ==============================================================================
# CLEAR CANCELLATION FORM
# ==============================================================================

def _clear_cancel_form():

    st.session_state[
        KEY_CANCEL_REASON
    ] = ""

    st.session_state[
        KEY_CANCEL_CONFIRM
    ] = False


# ==============================================================================
# LOAD PENDING BATCHES
# ==============================================================================

def _load_pending_batches(client):

    response = (
        client
        .table(
            "inventory_import_batches"
        )
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
# LOAD WAREHOUSES
# ==============================================================================

def _load_warehouse_map(client):

    response = (
        client
        .table(
            "warehouses"
        )
        .select(
            "id,name"
        )
        .order(
            "id"
        )
        .execute()
    )

    rows = response.data or []

    result = {}

    for row in rows:

        warehouse_id = row.get(
            "id"
        )

        if warehouse_id is None:

            continue

        try:

            warehouse_id = int(
                warehouse_id
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        result[
            warehouse_id
        ] = _display(
            row.get("name")
        )

    return result


# ==============================================================================
# LOAD IMPORT LINES
# ==============================================================================

def _load_import_lines(
    client,
    batch_id,
):

    """
    IMPORTANT:

    inventory_import_lines has batch_id,
    NOT batch_no.

    Therefore only batch_id is used here.
    """

    response = (
        client
        .table(
            "inventory_import_lines"
        )
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
            desc=False,
        )
        .execute()
    )

    return response.data or []


# ==============================================================================
# SELECTABLE LINE IDS
# ==============================================================================

def _get_selectable_line_ids(lines):

    selectable = set()

    for line in lines:

        line_id = line.get(
            "id"
        )

        if line_id is None:

            continue

        if not _is_true(
            line.get("is_valid")
        ):

            continue

        status = _normalize_status(
            line.get(
                "approval_status"
            )
        )

        if status != STATUS_PENDING:

            continue

        try:

            selectable.add(
                int(line_id)
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

    return selectable


# ==============================================================================
# CLEAN STALE SELECTION
# ==============================================================================

def _sync_selection_with_lines(lines):

    selectable_ids = (
        _get_selectable_line_ids(
            lines
        )
    )

    current = st.session_state.get(
        KEY_SELECTED_LINES,
        set(),
    )

    if not isinstance(
        current,
        set,
    ):

        current = set()

    cleaned = (
        current
        & selectable_ids
    )

    st.session_state[
        KEY_SELECTED_LINES
    ] = cleaned

    return cleaned


# ==============================================================================
# BATCH SUMMARY
# ==============================================================================

def _render_batch_summary(
    batch,
    warehouse_map,
    lines,
):

    batch_no = _display(
        batch.get("batch_no")
    )

    st.markdown(
        f"### 📦 {batch_no}"
    )

    # --------------------------------------------------------------------------
    # BATCH METRICS
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
    # ACTUAL LINE COUNTERS
    # --------------------------------------------------------------------------

    pending_count = 0
    approved_count = 0
    rejected_count = 0
    invalid_count = 0

    for line in lines:

        if not _is_true(
            line.get("is_valid")
        ):

            invalid_count += 1

            continue

        status = _normalize_status(
            line.get(
                "approval_status"
            )
        )

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
        "⏳ Pending",
        pending_count,
    )

    s2.metric(
        "✅ Approved",
        approved_count,
    )

    s3.metric(
        "❌ Rejected",
        rejected_count,
    )

    s4.metric(
        "⚠️ Invalid",
        invalid_count,
    )

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    warehouse_id = batch.get(
        "warehouse_to"
    )

    try:

        warehouse_id_int = int(
            warehouse_id
        )

    except (
        TypeError,
        ValueError,
    ):

        warehouse_id_int = warehouse_id

    warehouse_name = warehouse_map.get(
        warehouse_id_int,
        f"Warehouse {_display(warehouse_id)}",
    )

    st.caption(
        f"🏭 Warehouse: {warehouse_name}"
    )

    # --------------------------------------------------------------------------
    # MAKER
    # --------------------------------------------------------------------------

    st.caption(
        f"👤 Maker: "
        f"{_display(batch.get('requested_by'))}"
    )

    # --------------------------------------------------------------------------
    # TRANSACTION TYPE
    # --------------------------------------------------------------------------

    transaction_type = batch.get(
        "transaction_type"
    )

    if transaction_type:

        st.caption(
            f"Transaction Type: "
            f"{_display(transaction_type)}"
        )

    # --------------------------------------------------------------------------
    # REMARKS
    # --------------------------------------------------------------------------

    remarks = batch.get(
        "remarks"
    )

    if remarks:

        st.caption(
            f"Remarks: {_display(remarks)}"
        )

    # --------------------------------------------------------------------------
    # CREATED
    # --------------------------------------------------------------------------

    st.caption(
        "Created: "
        + _format_myanmar_datetime(
            batch.get("created_at")
        )
    )


# ==============================================================================
# SELECT ALL
# ==============================================================================

def _select_all_lines(lines):

    selectable = (
        _get_selectable_line_ids(
            lines
        )
    )

    st.session_state[
        KEY_SELECTED_LINES
    ] = set(selectable)


# ==============================================================================
# LINE SELECTION UI
# ==============================================================================

def _render_line_selection(
    lines,
):

    st.markdown(
        "### 📋 Import Lines"
    )

    selectable_ids = (
        _get_selectable_line_ids(
            lines
        )
    )

    current = _sync_selection_with_lines(
        lines
    )

    # --------------------------------------------------------------------------
    # TOP CONTROLS
    # --------------------------------------------------------------------------

    select_col, clear_col, info_col = st.columns(
        [1.5, 1.3, 4]
    )

    with select_col:

        if st.button(
            "☑️ Select All Lines",
            key=(
                "inventory_import_select_all_lines_v7"
            ),
            use_container_width=True,
            disabled=not selectable_ids,
        ):

            _select_all_lines(
                lines
            )

            st.rerun()

    with clear_col:

        if st.button(
            "⬜ Clear All",
            key=(
                "inventory_import_clear_all_lines_v7"
            ),
            use_container_width=True,
        ):

            _clear_selected_lines()

            st.rerun()

    with info_col:

        st.caption(
            f"Selected: {len(current)} "
            f"/ {len(selectable_ids)} selectable lines"
        )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # RENDER EACH LINE
    # --------------------------------------------------------------------------

    for line in lines:

        line_id_raw = line.get(
            "id"
        )

        if line_id_raw is None:

            continue

        try:

            line_id = int(
                line_id_raw
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        is_valid = _is_true(
            line.get("is_valid")
        )

        status = _normalize_status(
            line.get(
                "approval_status"
            )
        )

        is_pending = (
            status == STATUS_PENDING
        )

        is_approved = (
            status == STATUS_APPROVED
        )

        is_rejected = (
            status == STATUS_REJECTED
        )

        is_selectable = (
            is_valid
            and is_pending
        )

        is_selected = (
            line_id in current
        )

        # ======================================================================
        # LINE CARD
        # ======================================================================

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

                checkbox_key = (
                    "inventory_import_line_"
                    f"select_v7_{line_id}"
                )

                selected = st.checkbox(
                    f"Line {line.get('line_no', '-')}",
                    value=is_selected,
                    disabled=not is_selectable,
                    key=checkbox_key,
                )

                current_selection = st.session_state.get(
                    KEY_SELECTED_LINES,
                    set(),
                )

                if not isinstance(
                    current_selection,
                    set,
                ):

                    current_selection = set()

                if (
                    is_selectable
                    and selected
                ):

                    current_selection.add(
                        line_id
                    )

                else:

                    current_selection.discard(
                        line_id
                    )

                st.session_state[
                    KEY_SELECTED_LINES
                ] = current_selection

            # ------------------------------------------------------------------
            # DATA
            # ------------------------------------------------------------------

            with data_col:

                c1, c2, c3 = st.columns(3)

                c1.write(
                    "**SKU**\n\n"
                    + _display(
                        line.get("sku")
                    )
                )

                c2.write(
                    "**Quantity**\n\n"
                    + _format_number(
                        line.get("qty")
                    )
                )

                c3.write(
                    "**Unit Cost**\n\n"
                    + _format_number(
                        line.get("unit_cost")
                    )
                )

                c4, c5, c6 = st.columns(3)

                c4.write(
                    "**Lot No**\n\n"
                    + _display(
                        line.get("lot_no")
                    )
                )

                c5.write(
                    "**MFG Date**\n\n"
                    + _display(
                        line.get("mfg_date")
                    )
                )

                c6.write(
                    "**Expiry Date**\n\n"
                    + _display(
                        line.get("expiry_date")
                    )
                )

                c7, c8 = st.columns(2)

                c7.write(
                    "**Reference No**\n\n"
                    + _display(
                        line.get(
                            "reference_no"
                        )
                    )
                )

                c8.write(
                    "**Supplier Code**\n\n"
                    + _display(
                        line.get(
                            "supplier_code"
                        )
                    )
                )

                # ==============================================================
                # APPROVED
                # ==============================================================

                if is_approved:

                    st.success(
                        "✅ APPROVED"
                    )

                    st.caption(
                        "Approved By: "
                        + _display(
                            line.get(
                                "approved_by"
                            )
                        )
                    )

                    st.caption(
                        "Approved At: "
                        + _format_myanmar_datetime(
                            line.get(
                                "approved_at"
                            )
                        )
                    )

                # ==============================================================
                # REJECTED
                # ==============================================================

                elif is_rejected:

                    st.error(
                        "❌ REJECTED"
                    )

                    st.caption(
                        "Rejected By: "
                        + _display(
                            line.get(
                                "rejected_by"
                            )
                        )
                    )

                    st.caption(
                        "Rejected At: "
                        + _format_myanmar_datetime(
                            line.get(
                                "rejected_at"
                            )
                        )
                    )

                    st.caption(
                        "Reason: "
                        + _display(
                            line.get(
                                "rejection_reason"
                            )
                        )
                    )

                # ==============================================================
                # VALID + PENDING
                # ==============================================================

                elif is_valid and is_pending:

                    st.info(
                        "⏳ PENDING"
                    )

                # ==============================================================
                # INVALID
                # ==============================================================

                else:

                    st.error(
                        "⚠️ INVALID"
                    )

                    error_message = line.get(
                        "error_message"
                    )

                    if error_message:

                        st.caption(
                            "Error: "
                            + str(
                                error_message
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

    selected_ids = st.session_state.get(
        KEY_SELECTED_LINES,
        set(),
    )

    if not isinstance(
        selected_ids,
        set,
    ):

        selected_ids = set()

    selected_lines = []

    for line in lines:

        try:

            line_id = int(
                line.get("id")
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        if line_id in selected_ids:

            selected_lines.append(
                line
            )

    st.markdown("---")

    st.markdown(
        "### 📊 Selection Summary"
    )

    total_qty = 0.0

    for line in selected_lines:

        try:

            total_qty += float(
                line.get(
                    "qty",
                    0,
                )
                or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            pass

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Selected Lines",
        len(selected_lines),
    )

    c2.metric(
        "Selected Quantity",
        _format_number(
            total_qty
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
                f"{_display(line.get('line_no'))} | "
                f"{_display(line.get('sku'))} | "
                f"Qty "
                f"{_format_number(line.get('qty'))}"
            )

    else:

        st.info(
            "Approve / Reject ပြုလုပ်ရန် "
            "အပေါ်မှ Pending line များကို ရွေးချယ်ပါ။"
        )

    return (
        selected_ids,
        selected_lines,
    )


# ==============================================================================
# LINE ACTION PANEL
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

    reject_reason_input = st.text_area(
        "Reject Reason",
        value=st.session_state.get(
            KEY_REJECT_REASON,
            "",
        ),
        placeholder=(
            "ဥပမာ - Quantity မမှန်ပါ၊ "
            "Lot No မမှန်ပါ၊ Unit Cost ပြန်စစ်ရန်..."
        ),
        key=(
            "inventory_import_reject_reason_input_v7"
        ),
        height=100,
    )

    st.session_state[
        KEY_REJECT_REASON
    ] = reject_reason_input

    st.caption(
        "Reject လုပ်ရာတွင် Reason မဖြစ်မနေထည့်ရပါမည်။"
    )

    st.markdown("---")

    approve_col, reject_col, clear_col = st.columns(
        [2.2, 2.2, 1.3]
    )

    # ==========================================================================
    # APPROVE BUTTON
    # ==========================================================================

    with approve_col:

        approve_clicked = st.button(
            "✅ Approve Selected Lines",
            use_container_width=True,
            key=(
                "inventory_import_"
                "approve_selected_lines_v7"
            ),
        )

    # ==========================================================================
    # REJECT BUTTON
    # ==========================================================================

    with reject_col:

        reject_clicked = st.button(
            "❌ Reject Selected Lines",
            use_container_width=True,
            key=(
                "inventory_import_"
                "reject_selected_lines_v7"
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
                "clear_action_selection_v7"
            ),
        )

    # ==========================================================================
    # CLEAR
    # ==========================================================================

    if clear_clicked:

        _clear_selected_lines()

        _clear_reject_reason()

        st.rerun()

    # ==========================================================================
    # APPROVE
    # ==========================================================================

    if approve_clicked:

        selected_ids = sorted(
            int(x)
            for x in selected_line_ids
        )

        if not selected_ids:

            st.warning(
                "Approve လုပ်ရန် line မရှိပါ။"
            )

            return

        try:

            with st.spinner(
                "Approving inventory import lines..."
            ):

                result = (
                    _approve_selected_lines(
                        client=client,
                        batch_no=selected_batch_no,
                        checker_id=checker_id,
                        line_ids=selected_ids,
                    )
                )

            if result.get("success"):

                st.success(
                    result.get(
                        "message",
                        "Inventory lines approved successfully.",
                    )
                )

                # --------------------------------------------------------------
                # RPC RESULT
                # --------------------------------------------------------------

                st.json(
                    result
                )

                # --------------------------------------------------------------
                # CLEAR UI
                # --------------------------------------------------------------

                _clear_selected_lines()

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

        except Exception as exc:

            st.error(
                "Inventory approval failed."
            )

            st.exception(
                exc
            )

    # ==========================================================================
    # REJECT
    # ==========================================================================

    if reject_clicked:

        reason = str(
            reject_reason_input or ""
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

        selected_ids = sorted(
            int(x)
            for x in selected_line_ids
        )

        if not selected_ids:

            st.warning(
                "Reject လုပ်ရန် line မရှိပါ။"
            )

            return

        try:

            with st.spinner(
                "Rejecting inventory import lines..."
            ):

                result = (
                    _reject_selected_lines(
                        client=client,
                        batch_no=selected_batch_no,
                        checker_id=checker_id,
                        line_ids=selected_ids,
                        reason=reason,
                    )
                )

            if result.get("success"):

                st.success(
                    result.get(
                        "message",
                        "Selected inventory lines rejected successfully.",
                    )
                )

                st.json(
                    result
                )

                _clear_selected_lines()

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

        except Exception as exc:

            st.error(
                "Inventory rejection failed."
            )

            st.exception(
                exc
            )


# ==============================================================================
# BATCH CANCELLATION PANEL
# ==============================================================================

def _render_batch_cancel_panel(
    client,
    selected_batch,
    checker_id,
):

    st.markdown("---")

    st.markdown(
        "### 🚫 Batch Cancellation"
    )

    batch_no = _display(
        selected_batch.get(
            "batch_no"
        )
    )

    status = _normalize_status(
        selected_batch.get(
            "status"
        )
    )

    # --------------------------------------------------------------------------
    # ONLY PENDING
    # --------------------------------------------------------------------------

    if status != STATUS_PENDING:

        st.info(
            f"Batch {batch_no} is "
            f"`{status}`. "
            f"Cancellation is unavailable."
        )

        return

    st.warning(
        f"⚠️ Batch တစ်ခုလုံးကို "
        f"`CANCELLED` အဖြစ် ပြောင်းလဲပါမည်။\n\n"
        f"Batch: **{batch_no}**"
    )

    # ==========================================================================
    # REASON
    # ==========================================================================

    cancel_reason_input = st.text_area(
        "Cancellation Reason",
        value=st.session_state.get(
            KEY_CANCEL_REASON,
            "",
        ),
        placeholder=(
            "ဥပမာ - Import file မှားနေပါသည်၊ "
            "Warehouse မှားနေပါသည်၊ "
            "Duplicate import ဖြစ်နေပါသည်..."
        ),
        key=(
            "inventory_import_cancel_reason_input_v7"
        ),
        height=100,
    )

    st.session_state[
        KEY_CANCEL_REASON
    ] = cancel_reason_input

    # ==========================================================================
    # CONFIRMATION
    # ==========================================================================

    confirm_cancel = st.checkbox(
        "⚠️ ဒီ Batch တစ်ခုလုံးကို CANCEL လုပ်မည်ကို အတည်ပြုပါသည်။",
        value=st.session_state.get(
            KEY_CANCEL_CONFIRM,
            False,
        ),
        key=(
            "inventory_import_cancel_confirm_input_v7"
        ),
    )

    st.session_state[
        KEY_CANCEL_CONFIRM
    ] = confirm_cancel

    st.markdown("---")

    cancel_col, clear_col = st.columns(
        [2.5, 1.5]
    )

    # ==========================================================================
    # CANCEL
    # ==========================================================================

    with cancel_col:

        cancel_clicked = st.button(
            "🚫 Cancel Entire Batch",
            disabled=not confirm_cancel,
            use_container_width=True,
            key=(
                "inventory_import_cancel_entire_batch_v7"
            ),
        )

    # ==========================================================================
    # CLEAR
    # ==========================================================================

    with clear_col:

        clear_clicked = st.button(
            "Clear",
            use_container_width=True,
            key=(
                "inventory_import_clear_cancel_form_v7"
            ),
        )

    if clear_clicked:

        _clear_cancel_form()

        st.rerun()

    # ==========================================================================
    # CANCEL RPC
    # ==========================================================================

    if cancel_clicked:

        reason = str(
            cancel_reason_input or ""
        ).strip()

        if not reason:

            st.error(
                "❌ Cancellation Reason "
                "မဖြစ်မနေထည့်ပေးပါ။"
            )

            return

        if len(reason) < 3:

            st.error(
                "❌ Cancellation Reason "
                "အနည်းဆုံး 3 characters "
                "ရှိရပါမည်။"
            )

            return

        try:

            with st.spinner(
                "Cancelling inventory import batch..."
            ):

                result = (
                    _cancel_inventory_batch(
                        client=client,
                        batch_no=batch_no,
                        checker_id=checker_id,
                        reason=reason,
                    )
                )

            if result.get("success"):

                st.success(
                    result.get(
                        "message",
                        "Inventory import batch cancelled successfully.",
                    )
                )

                st.json(
                    result
                )

                # --------------------------------------------------------------
                # RESET UI
                # --------------------------------------------------------------

                _clear_selected_lines()

                _clear_reject_reason()

                _clear_cancel_form()

                st.session_state[
                    KEY_BATCH_NO
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

        except Exception as exc:

            st.error(
                "Inventory batch cancellation failed."
            )

            st.exception(
                exc
            )


# ==============================================================================
# EMPTY QUEUE
# ==============================================================================

def _render_empty_queue():

    st.success(
        "🎉 No PENDING Inventory In batches."
    )

    st.caption(
        "All submitted inventory import batches "
        "have already been processed."
    )


# ==============================================================================
# MAIN RENDER
# ==============================================================================

def render_inventory_import_approval():

    # ==========================================================================
    # INITIALIZE
    # ==========================================================================

    _initialize_state()

    # ==========================================================================
    # HEADER
    # ==========================================================================

    st.subheader(
        "✅ Inventory In Approval"
    )

    st.caption(
        "Checker | Line Approval / Rejection | "
        "Batch Cancellation | Maker-Checker"
    )

    st.info(
        "Inventory Import Batch အတွင်းရှိ "
        "Valid Pending Lines များကို ရွေးချယ်ပြီး "
        "Approve / Reject ပြုလုပ်နိုင်ပါသည်။ "
        "လိုအပ်ပါက Batch တစ်ခုလုံးကို Cancel ပြုလုပ်နိုင်ပါသည်။"
    )

    # ==========================================================================
    # DATABASE
    # ==========================================================================

    try:

        client = db()

    except Exception as exc:

        st.error(
            "Database connection failed."
        )

        st.exception(
            exc
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

        st.info(
            "Login session ကို ပြန်စစ်ပေးပါ။"
        )

        return

    # ==========================================================================
    # LOAD PENDING BATCHES
    # ==========================================================================

    try:

        batches = _load_pending_batches(
            client
        )

        warehouse_map = _load_warehouse_map(
            client
        )

    except Exception as exc:

        st.error(
            "Approval queue loading failed."
        )

        st.exception(
            exc
        )

        return

    # ==========================================================================
    # NO PENDING BATCH
    # ==========================================================================

    if not batches:

        _render_empty_queue()

        st.session_state[
            KEY_BATCH_NO
        ] = None

        _clear_selected_lines()

        return

    # ==========================================================================
    # BUILD BATCH MAP
    # ==========================================================================

    batch_options = {}

    for batch in batches:

        batch_no = batch.get(
            "batch_no"
        )

        if not batch_no:

            continue

        batch_options[
            str(batch_no)
        ] = batch

    if not batch_options:

        st.warning(
            "PENDING batches were found, "
            "but no valid batch number was returned."
        )

        return

    batch_nos = list(
        batch_options.keys()
    )

    # ==========================================================================
    # RESTORE CURRENT BATCH
    # ==========================================================================

    current_batch_no = st.session_state.get(
        KEY_BATCH_NO
    )

    if current_batch_no not in batch_options:

        current_batch_no = batch_nos[0]

        st.session_state[
            KEY_BATCH_NO
        ] = current_batch_no

        _clear_selected_lines()

        _clear_reject_reason()

        _clear_cancel_form()

    # ==========================================================================
    # BATCH SELECTOR
    # ==========================================================================

    selected_batch_no = st.selectbox(
        "Select PENDING Inventory In Batch",
        options=batch_nos,
        index=batch_nos.index(
            current_batch_no
        ),
        key=(
            "inventory_import_approval_"
            "batch_selector_v7"
        ),
    )

    # ==========================================================================
    # BATCH CHANGED
    # ==========================================================================

    if selected_batch_no != current_batch_no:

        st.session_state[
            KEY_BATCH_NO
        ] = selected_batch_no

        _clear_selected_lines()

        _clear_reject_reason()

        _clear_cancel_form()

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
            client=client,
            batch_id=selected_batch[
                "id"
            ],
        )

    except Exception as exc:

        st.error(
            "Import line loading failed."
        )

        st.exception(
            exc
        )

        return

    # ==========================================================================
    # BATCH SUMMARY
    # ==========================================================================

    _render_batch_summary(
        batch=selected_batch,
        warehouse_map=warehouse_map,
        lines=lines,
    )

    st.markdown("---")

    # ==========================================================================
    # NO LINES
    # ==========================================================================

    if not lines:

        st.warning(
            "No import lines found in this batch."
        )

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
        lines=lines
    )

    # ==========================================================================
    # SELECTION SUMMARY
    # ==========================================================================

    (
        selected_line_ids,
        selected_lines,
    ) = _render_selection_summary(
        lines=lines,
        checker_id=checker_id,
    )

    # ==========================================================================
    # LINE ACTIONS
    # ==========================================================================

    _render_action_panel(
        client=client,
        selected_batch_no=selected_batch_no,
        checker_id=checker_id,
        selected_line_ids=selected_line_ids,
    )

    # ==========================================================================
    # BATCH CANCELLATION
    # ==========================================================================

    _render_batch_cancel_panel(
        client=client,
        selected_batch=selected_batch,
        checker_id=checker_id,
    )


# ==============================================================================
# END OF FILE
# ==============================================================================
