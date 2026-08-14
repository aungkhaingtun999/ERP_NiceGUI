# ==============================================================================
# erp_pages/inventory/inventory_import_approval.py
#
# ERP ENTERPRISE INVENTORY IN
# CHECKER APPROVAL QUEUE
#
# STEP 1
# ------------------------------------------------------------------------------
# Purpose:
#   - Load PENDING Inventory In batches
#   - Display batch summary
#   - Individual batch selection
#   - Select All
#
# IMPORTANT
# ------------------------------------------------------------------------------
# This STEP does NOT approve or post anything.
#
# Workflow:
#
# Maker
#   ↓
# inventory_import.py
#   ↓
# DRAFT
#   ↓
# submit_inventory_import_batch()
#   ↓
# PENDING
#   ↓
# THIS PAGE
#   ↓
# Checker Queue
#
# Approval RPC will be connected in a later step.
# ==============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional

import streamlit as st

from database import db


# ==============================================================================
# CONSTANTS
# ==============================================================================

PAGE_TITLE = "📥 Inventory In Approval"

STATUS_PENDING = "PENDING"


# ==============================================================================
# SESSION STATE
# ==============================================================================

def _init_state():
    """
    Initialize only UI state.

    We deliberately keep selected batch IDs in session state.
    """

    defaults = {
        "inventory_in_approval_selected": [],
        "inventory_in_approval_refresh": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


# ==============================================================================
# CURRENT USER
# ==============================================================================

def _get_current_user_id():
    """
    Get current logged-in user ID from the existing ERP session.
    """

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
# SAFE HELPERS
# ==============================================================================

def _safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:

        return int(value)

    except Exception:

        return default


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:

        return float(value)

    except Exception:

        return default


def _safe_text(
    value: Any,
    default: str = "",
) -> str:

    if value is None:

        return default

    return str(value)


# ==============================================================================
# LOAD PENDING BATCHES
# ==============================================================================

def _load_pending_batches(
    client,
) -> List[Dict[str, Any]]:
    """
    Load Inventory In batches waiting for Checker approval.

    IMPORTANT
    ----------
    This function only READS data.

    It does NOT:
        - approve
        - reject
        - post stock
        - modify inventory
    """

    try:

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

    except Exception as e:

        st.error(
            f"Pending Inventory In loading failed: {e}"
        )

        return []


# ==============================================================================
# LOAD WAREHOUSES
# ==============================================================================

def _load_warehouses(
    client,
) -> Dict[int, str]:
    """
    Load warehouse names once.

    Returns:
        {
            warehouse_id: warehouse_name
        }
    """

    try:

        response = (
            client
            .table("warehouses")
            .select(
                "id,name"
            )
            .execute()
        )

        rows = response.data or []

        return {
            _safe_int(row.get("id")):
                _safe_text(
                    row.get("name"),
                    "Unknown Warehouse",
                )
            for row in rows
        }

    except Exception as e:

        st.error(
            f"Warehouse loading failed: {e}"
        )

        return {}


# ==============================================================================
# LOAD USERS
# ==============================================================================

def _load_users(
    client,
) -> Dict[str, str]:
    """
    Load maker usernames.

    We only need the display name for the queue.
    """

    try:

        response = (
            client
            .table("users")
            .select(
                "id,username"
            )
            .execute()
        )

        rows = response.data or []

        return {
            str(row.get("id")):
                _safe_text(
                    row.get("username"),
                    "Unknown User",
                )
            for row in rows
            if row.get("id") is not None
        }

    except Exception as e:

        st.error(
            f"User loading failed: {e}"
        )

        return {}


# ==============================================================================
# FORMAT BATCH ROW
# ==============================================================================

def _format_batch_row(
    batch: Dict[str, Any],
    warehouse_map: Dict[int, str],
    user_map: Dict[str, str],
) -> Dict[str, Any]:
    """
    Convert database batch row into a clean UI row.
    """

    batch_id = batch.get("id")

    warehouse_id = _safe_int(
        batch.get("warehouse_to")
    )

    requested_by = batch.get(
        "requested_by"
    )

    maker_name = user_map.get(
        str(requested_by),
        "Unknown",
    )

    return {
        "id": batch_id,

        "Batch No":
            _safe_text(
                batch.get("batch_no")
            ),

        "Warehouse":
            warehouse_map.get(
                warehouse_id,
                f"Warehouse {warehouse_id}",
            ),

        "Maker":
            maker_name,

        "Lines":
            _safe_int(
                batch.get("total_lines")
            ),

        "Valid":
            _safe_int(
                batch.get("valid_lines")
            ),

        "Errors":
            _safe_int(
                batch.get("error_lines")
            ),

        "Status":
            _safe_text(
                batch.get("status")
            ),

        "Created":
            _safe_text(
                batch.get("created_at")
            ),

        "Remarks":
            _safe_text(
                batch.get("remarks")
            ),
    }


# ==============================================================================
# SELECT ALL / CLEAR ALL
# ==============================================================================

def _select_all(
    rows: List[Dict[str, Any]],
):
    """
    Select all currently displayed pending batches.
    """

    st.session_state[
        "inventory_in_approval_selected"
    ] = [
        row["id"]
        for row in rows
        if row.get("id") is not None
    ]


def _clear_all():
    """
    Clear all selected batches.
    """

    st.session_state[
        "inventory_in_approval_selected"
    ] = []


# ==============================================================================
# SELECTION CHECKBOX
# ==============================================================================

def _render_selection(
    row: Dict[str, Any],
) -> bool:
    """
    Render one batch checkbox.

    Checkbox state is synchronized with the selected ID list.
    """

    batch_id = row["id"]

    selected_ids = set(
        st.session_state.get(
            "inventory_in_approval_selected",
            [],
        )
    )

    current_value = (
        batch_id in selected_ids
    )

    widget_key = (
        "inventory_in_approval_select_"
        + str(batch_id)
    )

    checked = st.checkbox(
        "Select",
        value=current_value,
        key=widget_key,
    )

    if checked:

        if batch_id not in selected_ids:

            selected_ids.add(
                batch_id
            )

    else:

        selected_ids.discard(
            batch_id
        )

    st.session_state[
        "inventory_in_approval_selected"
    ] = list(
        selected_ids
    )

    return checked


# ==============================================================================
# BATCH CARD
# ==============================================================================

def _render_batch_card(
    row: Dict[str, Any],
):
    """
    Render one pending Inventory In batch.
    """

    batch_id = row["id"]

    st.markdown("---")

    col_select, col_main, col_status = st.columns(
        [0.8, 5.5, 1.5]
    )

    # --------------------------------------------------------------------------
    # SELECT
    # --------------------------------------------------------------------------

    with col_select:

        _render_selection(
            row
        )

    # --------------------------------------------------------------------------
    # MAIN
    # --------------------------------------------------------------------------

    with col_main:

        st.markdown(
            f"### 📦 {row['Batch No']}"
        )

        st.caption(
            f"Maker: **{row['Maker']}**  |  "
            f"Warehouse: **{row['Warehouse']}**"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Lines",
            row["Lines"],
        )

        c2.metric(
            "Valid",
            row["Valid"],
        )

        c3.metric(
            "Errors",
            row["Errors"],
        )

        if row["Remarks"]:

            st.caption(
                f"Remarks: {row['Remarks']}"
            )

        st.caption(
            f"Created: {row['Created']}"
        )

    # --------------------------------------------------------------------------
    # STATUS
    # --------------------------------------------------------------------------

    with col_status:

        st.success(
            row["Status"]
        )


# ==============================================================================
# SUMMARY
# ==============================================================================

def _render_summary(
    rows: List[Dict[str, Any]],
):
    """
    Render queue summary.
    """

    selected_ids = set(
        st.session_state.get(
            "inventory_in_approval_selected",
            [],
        )
    )

    selected_count = len(
        selected_ids
    )

    total_batches = len(
        rows
    )

    total_lines = sum(
        _safe_int(
            row.get("Lines")
        )
        for row in rows
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Pending Batches",
        total_batches,
    )

    c2.metric(
        "Total Lines",
        total_lines,
    )

    c3.metric(
        "Selected",
        selected_count,
    )


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def render_inventory_import_approval():
    """
    Inventory In Checker Queue — STEP 1.

    Only queue + selection are implemented in this step.
    """

    _init_state()

    # ==========================================================================
    # HEADER
    # ==========================================================================

    st.subheader(
        PAGE_TITLE
    )

    st.caption(
        "ERP Enterprise | "
        "Maker-Checker | "
        "Inventory In Pending Queue"
    )

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================

    current_user_id = (
        _get_current_user_id()
    )

    if not current_user_id:

        st.warning(
            "Current user session ID was not found."
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
    # LOAD DATA
    # ==========================================================================

    warehouse_map = _load_warehouses(
        client
    )

    user_map = _load_users(
        client
    )

    pending_batches = (
        _load_pending_batches(
            client
        )
    )

    # ==========================================================================
    # NORMALIZE
    # ==========================================================================

    rows = [
        _format_batch_row(
            batch,
            warehouse_map,
            user_map,
        )
        for batch in pending_batches
    ]

    # ==========================================================================
    # SUMMARY
    # ==========================================================================

    _render_summary(
        rows
    )

    # ==========================================================================
    # EMPTY QUEUE
    # ==========================================================================

    if not rows:

        st.success(
            "✅ No pending Inventory In batches."
        )

        # Clear stale selection
        _clear_all()

        return

    # ==========================================================================
    # SELECT ALL CONTROLS
    # ==========================================================================

    st.markdown(
        "### Pending Inventory In"
    )

    control_col1, control_col2, control_col3 = (
        st.columns([2, 2, 6])
    )

    with control_col1:

        if st.button(
            "☑ Select All",
            use_container_width=True,
            key="inventory_in_approval_select_all",
        ):

            _select_all(
                rows
            )

            st.rerun()

    with control_col2:

        if st.button(
            "☐ Clear Selection",
            use_container_width=True,
            key="inventory_in_approval_clear_all",
        ):

            _clear_all()

            st.rerun()

    with control_col3:

        selected_count = len(
            st.session_state.get(
                "inventory_in_approval_selected",
                [],
            )
        )

        if selected_count:

            st.info(
                f"{selected_count} batch(es) selected."
            )

        else:

            st.caption(
                "Select one or more batches."
            )

    # ==========================================================================
    # BATCH LIST
    # ==========================================================================

    for row in rows:

        _render_batch_card(
            row
        )

    # ==========================================================================
    # STEP 1 ACTION AREA
    # ==========================================================================

    st.markdown("---")

    selected_ids = (
        st.session_state.get(
            "inventory_in_approval_selected",
            [],
        )
    )

    if selected_ids:

        st.info(
            f"✅ {len(selected_ids)} "
            "Inventory In batch(es) selected."
        )

        st.caption(
            "Approval action will be connected in the next step."
        )

    else:

        st.caption(
            "No Inventory In batch selected."
        )

    # ==========================================================================
    # IMPORTANT
    # ==========================================================================

    st.markdown("---")

    st.caption(
        "Step 1: Pending Queue + Select All + Individual Selection"
    )

    st.caption(
        "⚠️ No stock posting or approval is performed on this page yet."
    )


# ==============================================================================
# PUBLIC EXPORT
# ==============================================================================

__all__ = [
    "render_inventory_import_approval",
]


# ==============================================================================
# END
# ==============================================================================