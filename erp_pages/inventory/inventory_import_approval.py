# ==============================================================================
# erp_pages/inventory/inventory_import_approval.py
#
# ERP ENTERPRISE INVENTORY IN APPROVAL
#
# Maker-Checker Workflow
#
# inventory_import_batches
#       ↓
#     PENDING
#       ↓
# Checker selects:
#       - Select All
#       - Individual batches
#       ↓
# Approve Selected
#       ↓
# approve_inventory_import_batch()
#       ↓
# POSTED
#
# IMPORTANT
# ------------------------------------------------------------------------------
# Python NEVER directly updates:
#
#     warehouse_stock
#     inventory_batches
#     inventory_cost_layers
#
# Actual posting is owned by PostgreSQL RPC:
#
#     approve_inventory_import_batch()
#
# ==============================================================================

from __future__ import annotations

import streamlit as st

from database import db


# ==============================================================================
# CONSTANTS
# ==============================================================================

PAGE_TITLE = "Inventory In Approval"

STATUS_PENDING = "PENDING"


# ==============================================================================
# SESSION STATE
# ==============================================================================

def _initialize_state():
    """
    Initialize approval-page session state.

    IMPORTANT
    ----------
    Selection state belongs only to this approval page.
    """

    if "inventory_import_approval_selected" not in st.session_state:

        st.session_state[
            "inventory_import_approval_selected"
        ] = set()


# ==============================================================================
# CURRENT USER
# ==============================================================================

def _get_current_user_id():
    """
    Get current logged-in user ID.

    Supports the same session keys used elsewhere
    in the ERP application.
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
# LOAD PENDING BATCHES
# ==============================================================================

def _load_pending_batches(client):
    """
    Load all PENDING Inventory In batches.

    Only batch/header information is loaded here.

    Actual posting is performed by the approval RPC.
    """

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
# LOAD WAREHOUSE NAMES
# ==============================================================================

def _load_warehouse_map(client):
    """
    Load warehouse names for display.
    """

    response = (
        client
        .table("warehouses")
        .select("id,name")
        .order("id")
        .execute()
    )

    warehouses = response.data or []

    return {
        int(row["id"]): row.get(
            "name",
            "",
        )
        for row in warehouses
        if row.get("id") is not None
    }


# ==============================================================================
# FORMAT DATE
# ==============================================================================

def _format_datetime(value):
    """
    Safe display formatter.
    """

    if not value:

        return "-"

    text = str(value)

    if "T" in text:

        text = text.replace(
            "T",
            " ",
            1,
        )

    if "+" in text:

        text = text.split(
            "+",
            1,
        )[0]

    return text[:19]


# ==============================================================================
# APPROVE ONE BATCH
# ==============================================================================

def _approve_batch(
    client,
    batch_no,
    checker_id,
):
    """
    Approve one Inventory In batch through PostgreSQL RPC.

    IMPORTANT
    ----------
    This function does NOT perform stock updates directly.
    """

    response = client.rpc(
        "approve_inventory_import_batch",
        {
            "p_batch_no": batch_no,
            "p_checker_id": checker_id,
        },
    ).execute()

    result = response.data

    if isinstance(result, list):

        if result:

            return result[0]

        return {}

    return result or {}


# ==============================================================================
# SELECTION HELPERS
# ==============================================================================

def _get_selected_batch_nos():
    """
    Return selected batch numbers.
    """

    selected = st.session_state.get(
        "inventory_import_approval_selected",
        set(),
    )

    if not isinstance(
        selected,
        set,
    ):

        selected = set()

    return selected


def _set_selected_batch_nos(values):
    """
    Replace selected batch numbers.
    """

    st.session_state[
        "inventory_import_approval_selected"
    ] = set(values)


def _select_all(batch_nos):
    """
    Select all currently displayed PENDING batches.
    """

    _set_selected_batch_nos(
        batch_nos
    )


def _clear_all():
    """
    Clear all selections.
    """

    _set_selected_batch_nos(
        set()
    )


# ==============================================================================
# MAIN UI
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
        "ERP Enterprise Inventory In | "
        "Checker Approval | "
        "Maker-Checker Enabled"
    )

    st.info(
        "ဒီနေရာမှာ PENDING Inventory In batch များကို "
        "တစ်ခုချင်း သို့မဟုတ် Select All ဖြင့် ရွေးချယ်ပြီး "
        "Checker အဖြစ် Approve လုပ်နိုင်ပါတယ်။"
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
    # CHECKER
    # ==========================================================================

    checker_id = _get_current_user_id()

    if not checker_id:

        st.warning(
            "Current checker user ID was not found. "
            "Please log in again."
        )

        return

    # ==========================================================================
    # LOAD DATA
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
            "Inventory In approval queue loading failed."
        )

        st.exception(e)

        return

    # ==========================================================================
    # EMPTY QUEUE
    # ==========================================================================

    if not batches:

        _clear_all()

        st.success(
            "🎉 No PENDING Inventory In batches."
        )

        st.caption(
            "All Inventory In requests have been processed."
        )

        return

    # ==========================================================================
    # CLEAN OLD SELECTIONS
    # ==========================================================================

    available_batch_nos = {
        str(
            batch.get("batch_no")
        ).strip()
        for batch in batches
        if batch.get("batch_no")
    }

    current_selection = _get_selected_batch_nos()

    cleaned_selection = (
        current_selection
        & available_batch_nos
    )

    if cleaned_selection != current_selection:

        _set_selected_batch_nos(
            cleaned_selection
        )

    # ==========================================================================
    # KPI
    # ==========================================================================

    selected_count = len(
        cleaned_selection
    )

    total_pending = len(
        batches
    )

    total_lines = sum(
        int(
            batch.get(
                "total_lines",
                0,
            )
            or 0
        )
        for batch in batches
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Pending Batches",
        total_pending,
    )

    c2.metric(
        "Selected",
        selected_count,
    )

    c3.metric(
        "Pending Lines",
        total_lines,
    )

    st.markdown("---")

    # ==========================================================================
    # SELECT ALL / CLEAR ALL
    # ==========================================================================

    col1, col2, col3 = st.columns(
        [1, 1, 4]
    )

    batch_nos = [
        str(
            batch.get("batch_no")
        ).strip()
        for batch in batches
        if batch.get("batch_no")
    ]

    with col1:

        if st.button(
            "☑️ Select All",
            key="inventory_import_select_all",
            use_container_width=True,
        ):

            _select_all(
                batch_nos
            )

            st.rerun()

    with col2:

        if st.button(
            "⬜ Clear All",
            key="inventory_import_clear_all",
            use_container_width=True,
        ):

            _clear_all()

            st.rerun()

    with col3:

        if selected_count:

            st.caption(
                f"{selected_count} batch(es) selected."
            )

        else:

            st.caption(
                "Select one or more batches to approve."
            )

    # ==========================================================================
    # APPROVAL QUEUE
    # ==========================================================================

    st.markdown(
        "### 📋 Pending Inventory In Batches"
    )

    # ==========================================================================
    # INDIVIDUAL SELECTION
    # ==========================================================================

    for batch in batches:

        batch_no = str(
            batch.get(
                "batch_no",
                "",
            )
        ).strip()

        if not batch_no:

            continue

        is_selected = (
            batch_no
            in cleaned_selection
        )

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

            warehouse_id_int = None

        warehouse_name = (
            warehouse_map.get(
                warehouse_id_int,
                f"Warehouse {warehouse_id}",
            )
        )

        requested_by = batch.get(
            "requested_by"
        )

        total = int(
            batch.get(
                "total_lines",
                0,
            )
            or 0
        )

        valid = int(
            batch.get(
                "valid_lines",
                0,
            )
            or 0
        )

        errors = int(
            batch.get(
                "error_lines",
                0,
            )
            or 0
        )

        created_at = _format_datetime(
            batch.get(
                "created_at"
            )
        )

        # ----------------------------------------------------------------------
        # BATCH CARD
        # ----------------------------------------------------------------------

        with st.container(
            border=True
        ):

            col_select, col_info = st.columns(
                [0.5, 5]
            )

            with col_select:

                selected = st.checkbox(
                    "Select",
                    value=is_selected,
                    key=(
                        "inventory_import_select_"
                        + batch_no
                    ),
                    label_visibility="collapsed",
                )

            with col_info:

                st.markdown(
                    f"**📦 {batch_no}**"
                )

                i1, i2, i3, i4 = st.columns(4)

                i1.write(
                    f"**Warehouse**  \n"
                    f"{warehouse_name}"
                )

                i2.write(
                    f"**Lines**  \n"
                    f"{total}"
                )

                i3.write(
                    f"**Valid**  \n"
                    f"{valid}"
                )

                i4.write(
                    f"**Status**  \n"
                    f"`PENDING`"
                )

                st.caption(
                    f"Maker: {requested_by or '-'} | "
                    f"Created: {created_at}"
                )

                if batch.get("remarks"):

                    st.caption(
                        f"Remarks: {batch.get('remarks')}"
                    )

                if errors:

                    st.warning(
                        f"Validation errors: {errors}"
                    )

            # ------------------------------------------------------------------
            # UPDATE SELECTION
            # ------------------------------------------------------------------

            current = _get_selected_batch_nos()

            if selected:

                current.add(
                    batch_no
                )

            else:

                current.discard(
                    batch_no
                )

            _set_selected_batch_nos(
                current
            )

    # ==========================================================================
    # APPROVAL ACTION
    # ==========================================================================

    st.markdown("---")

    selected_batches = sorted(
        _get_selected_batch_nos()
    )

    st.markdown(
        "### 🚀 Approval Action"
    )

    if not selected_batches:

        st.info(
            "Approve လုပ်ရန် Batch တစ်ခုခုကို ရွေးပါ။"
        )

        return

    st.warning(
        f"⚠️ {len(selected_batches)} batch(es) "
        "ကို approve လုပ်မည်။ "
        "Approval ပြီးပါက stock posting ကို "
        "database RPC မှ atomic transaction ဖြင့် လုပ်ဆောင်ပါမည်။"
    )

    with st.expander(
        "Selected Batches",
        expanded=False,
    ):

        for batch_no in selected_batches:

            st.write(
                f"• {batch_no}"
            )

    # ==========================================================================
    # APPROVE SELECTED
    # ==========================================================================

    if st.button(
        "✅ Approve Selected",
        type="primary",
        use_container_width=True,
        key="inventory_import_approve_selected",
    ):

        success_count = 0
        failed_count = 0

        successful_batches = []
        failed_batches = []

        # ----------------------------------------------------------------------
        # PROCESS EACH SELECTED BATCH
        # ----------------------------------------------------------------------

        progress = st.progress(
            0,
            text="Starting approval...",
        )

        total_selected = len(
            selected_batches
        )

        for index, batch_no in enumerate(
            selected_batches,
            start=1,
        ):

            progress.progress(
                int(
                    ((index - 1)
                    / total_selected)
                    * 100
                ),
                text=(
                    f"Approving {batch_no} "
                    f"({index}/{total_selected})..."
                ),
            )

            try:

                result = _approve_batch(
                    client=client,
                    batch_no=batch_no,
                    checker_id=checker_id,
                )

                if result.get(
                    "success"
                ):

                    success_count += 1

                    successful_batches.append(
                        batch_no
                    )

                else:

                    failed_count += 1

                    failed_batches.append(
                        {
                            "batch_no": batch_no,
                            "message": result.get(
                                "message",
                                "Approval failed.",
                            ),
                        }
                    )

            except Exception as e:

                failed_count += 1

                failed_batches.append(
                    {
                        "batch_no": batch_no,
                        "message": str(e),
                    }
                )

        progress.progress(
            100,
            text="Approval processing completed.",
        )

        # ----------------------------------------------------------------------
        # REMOVE SUCCESSFUL SELECTIONS
        # ----------------------------------------------------------------------

        current = _get_selected_batch_nos()

        for batch_no in successful_batches:

            current.discard(
                batch_no
            )

        _set_selected_batch_nos(
            current
        )

        # ----------------------------------------------------------------------
        # RESULT
        # ----------------------------------------------------------------------

        if success_count:

            st.success(
                f"✅ {success_count} batch(es) "
                "approved and posted successfully."
            )

        if failed_count:

            st.error(
                f"❌ {failed_count} batch(es) "
                "failed to approve."
            )

            for failed in failed_batches:

                st.error(
                    f"{failed['batch_no']}: "
                    f"{failed['message']}"
                )

        if success_count:

            st.rerun()
