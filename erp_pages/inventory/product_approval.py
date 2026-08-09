# ==============================================================================
# erp_pages/inventory/product_approval.py
# ERP ENTERPRISE PRODUCT APPROVAL QUEUE v3.0 CLEAN
#
# MAKER-CHECKER
# ------------------------------------------------------------------------------
# Maker:
#   Any authorized user can create a product request.
#
# Checker:
#   Admin   = role_id 1
#   Manager = role_id 2
#
# Cashier:
#   role_id 3 -> cannot approve
#
# Rules:
#   1. Maker cannot approve own request
#   2. Another Admin / Manager can approve
#   3. Approval is performed by approve_product_create_rpc
#   4. approved_by / approved_at are stored by RPC
#   5. Username is resolved from users.username
#   6. No users.name dependency
#   7. Clear success / failure notifications
#   8. Approval history displayed
# ==============================================================================

import time

import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager


# ==============================================================================
# USER CACHE
# ==============================================================================

def _load_users(client):

    try:
        response = (
            client
            .table("users")
            .select("id,username,full_name,is_active")
            .execute()
        )

        users = response.data or []

        result = {}

        for user in users:

            user_id = user.get("id")

            if user_id:
                result[str(user_id)] = user

        return result

    except Exception as e:

        st.warning(
            f"⚠️ User name lookup failed: {e}"
        )

        return {}

# ==============================================================================
# USERNAME
# ==============================================================================

def _get_user_name(user_id, users_cache):

    if not user_id:
        return "Unknown User"

    user = users_cache.get(str(user_id))

    if not user:
        return str(user_id)

    return (
        user.get("username")
        or user.get("full_name")
        or str(user_id)
    )


# ==============================================================================
# ROLE
# ==============================================================================

def _is_checker(user):

    if not isinstance(
        user,
        dict,
    ):

        return False

    role_id = user.get(
        "role_id"
    )

    role_name = str(
        user.get(
            "role_name",
            ""
        )
    ).strip().lower()

    return (
        role_id in (1, 2)
        or role_name in (
            "admin",
            "manager",
        )
    )


# ==============================================================================
# MONEY
# ==============================================================================

def _money(value):

    try:

        return f"{float(value or 0):,.2f} MMK"

    except Exception:

        return "0.00 MMK"


# ==============================================================================
# PRODUCT APPROVAL QUEUE
# ==============================================================================

def render_product_approval_queue():

    st.subheader(
        "🟡 Product Approval Center"
    )

    st.caption(
        "Maker → Checker → Product Creation"
    )

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================

    current_user = (
        st.session_state.get(
            "user"
        )
    )

    if not current_user:

        st.warning(
            "🔐 Login required."
        )

        return

    if not isinstance(
        current_user,
        dict,
    ):

        st.error(
            "❌ Invalid login session."
        )

        return

    current_user_id = (
        current_user.get("id")
    )

    current_username = (
        current_user.get(
            "username"
        )
        or "Unknown"
    )

    current_role_id = (
        current_user.get(
            "role_id"
        )
    )

    current_role_name = (
        current_user.get(
            "role_name"
        )
        or (
            "Admin"
            if current_role_id == 1
            else "Manager"
            if current_role_id == 2
            else "Cashier"
            if current_role_id == 3
            else "Unknown"
        )
    )

    if not current_user_id:

        st.error(
            "❌ Current user ID is missing."
        )

        return

    # ==========================================================================
    # CHECKER ACCESS
    # ==========================================================================

    if not _is_checker(
        current_user
    ):

        st.info(
            "🔒 Approval Center is available "
            "only to Admin / Manager."
        )

        st.caption(
            f"Current User: {current_username} "
            f"| Role: {current_role_name}"
        )

        return

    # ==========================================================================
    # SERVER CLIENT
    # ==========================================================================

    try:

        client = privileged_db()

    except Exception as e:

        st.error(
            "❌ Privileged database connection failed."
        )

        st.code(
            repr(e)
        )

        return

    # ==========================================================================
    # USERS
    # ==========================================================================

    users_cache = _load_users(
        client
    )

    # ==========================================================================
    # CURRENT USER HEADER
    # ==========================================================================

    st.info(
        f"👤 Checker: **{current_username}**  "
        f"| Role: **{current_role_name}**"
    )

    # ==========================================================================
    # PENDING REQUESTS
    # ==========================================================================

    try:

        pending_response = (
            client
            .table(
                "product_create_requests"
            )
            .select("*")
            .eq(
                "status",
                "PENDING"
            )
            .order(
                "id",
                desc=True
            )
            .execute()
        )

        pending_requests = (
            pending_response.data
            or []
        )

    except Exception as e:

        st.error(
            "❌ Failed to load pending requests."
        )

        st.code(
            repr(e)
        )

        return

    pending_count = len(
        pending_requests
    )

    # ==========================================================================
    # PENDING HEADER
    # ==========================================================================

    st.markdown(
        f"""
### 🟡 Pending Product Requests: **{pending_count}**
"""
    )

    if pending_count == 0:

        st.success(
            "✅ No pending product requests."
        )

    # ==========================================================================
    # PENDING REQUEST CARDS
    # ==========================================================================

    for req in pending_requests:

        request_id = req.get(
            "id"
        )

        product = (
            req.get(
                "product_data"
            )
            or {}
        )

        requester_id = req.get(
            "requested_by"
        )

        requester_name = _username(
            requester_id,
            users_cache,
        )

        product_name = product.get(
            "name",
            "-"
        )

        sku = product.get(
            "sku",
            "-"
        )

        barcode = product.get(
            "barcode",
            "-"
        )

        unit = product.get(
            "unit",
            "-"
        )

        initial_qty = req.get(
            "initial_qty",
            0
        )

        warehouse_id = req.get(
            "warehouse_id",
            "-"
        )

        purchase_price = product.get(
            "purchase_price",
            0
        )

        selling_price = product.get(
            "selling_price",
            0
        )

        created_at = req.get(
            "created_at",
            "-"
        )

        # ======================================================================
        # SELF APPROVAL
        # ======================================================================

        is_own_request = (
            str(requester_id)
            ==
            str(current_user_id)
        )

        # ======================================================================
        # CARD
        # ======================================================================

        with st.container(
            border=True
        ):

            st.markdown(
                f"""
## 📝 Request #{request_id}
"""
            )

            st.warning(
                "🟡 PENDING — Approval Required"
            )

            # ------------------------------------------------------------------
            # PRODUCT
            # ------------------------------------------------------------------

            c1, c2 = st.columns(
                2
            )

            with c1:

                st.write(
                    f"**Product:** {product_name}"
                )

                st.write(
                    f"**SKU:** {sku}"
                )

                st.write(
                    f"**Barcode:** {barcode}"
                )

                st.write(
                    f"**Unit:** {unit}"
                )

            with c2:

                st.write(
                    f"**Opening Qty:** {initial_qty}"
                )

                st.write(
                    f"**Purchase Price:** "
                    f"{_money(purchase_price)}"
                )

                st.write(
                    f"**Selling Price:** "
                    f"{_money(selling_price)}"
                )

                st.write(
                    f"**Warehouse:** {warehouse_id}"
                )

            # ------------------------------------------------------------------
            # MAKER
            # ------------------------------------------------------------------

            st.markdown(
                f"""
### 👤 Maker Information

**Requested By:** `{requester_name}`  
**Created At:** `{created_at}`
"""
            )

            st.markdown("---")

            # ==================================================================
            # SELF APPROVAL BLOCK
            # ==================================================================

            if is_own_request:

                st.error(
                    "🚫 SELF-APPROVAL BLOCKED"
                )

                st.warning(
                    f"Maker **{requester_name}** သည် "
                    "မိမိတင်ထားသော Request ကို "
                    "Approve မလုပ်နိုင်ပါ။"
                )

                st.caption(
                    "➡️ အခြား Admin / Manager တစ်ဦးက "
                    "Approve လုပ်ရပါမည်။"
                )

                continue

            # ==================================================================
            # APPROVE / REJECT
            # ==================================================================

            b1, b2 = st.columns(
                2
            )

            # ------------------------------------------------------------------
            # APPROVE
            # ------------------------------------------------------------------

            with b1:

                if st.button(
                    "✅ APPROVE",
                    key=f"approve_{request_id}",
                    use_container_width=True,
                ):

                    try:

                        st.info(
                            f"⏳ Approving Request #{request_id}..."
                        )

                        response = (
                            client
                            .rpc(
                                "approve_product_create_rpc",
                                {
                                    "p_request_id":
                                        int(
                                            request_id
                                        ),

                                    "p_checker_id":
                                        str(
                                            current_user_id
                                        ),
                                },
                            )
                            .execute()
                        )

                        result = response.data

                        if isinstance(
                            result,
                            list,
                        ):

                            result = (
                                result[0]
                                if result
                                else None
                            )

# ------------------------------------------------------
# INVALID RESPONSE
# ------------------------------------------------------

if not isinstance(result, dict):

    st.error(
        "❌ APPROVAL FAILED — Invalid RPC Response"
    )

    st.warning(
        "Database returned an unexpected response."
    )

    with st.expander("🔎 Technical Response"):

        st.code(
            repr(result)
        )

    continue


# ------------------------------------------------------
# RPC FAILURE
# ------------------------------------------------------

if not result.get("success", False):

    error_message = result.get(
        "message",
        "Unknown approval error."
    )

    error_status = result.get(
        "status",
        "ERROR"
    )

    st.error(
        "❌ APPROVAL FAILED"
    )

    st.warning(
        f"Status: {error_status}"
    )

    st.error(
        f"Reason: {error_message}"
    )

    with st.expander(
        "🔎 RPC Response Details"
    ):

        st.json(result)

    continue

                        # ======================================================
                        # SUCCESS
                        # ======================================================

                        approved_request_id = (
                            result.get(
                                "request_id",
                                request_id,
                            )
                        )

                        product_id = result.get(
                            "product_id",
                            "-"
                        )

                        batch_id = result.get(
                            "batch_id",
                            "-"
                        )

                        cost_layer_id = result.get(
                            "cost_layer_id",
                            "-"
                        )

                        # ------------------------------------------------------
                        # SUCCESS NOTIFICATION
                        # ------------------------------------------------------

                        st.success(
                            "🎉🎉 APPROVAL SUCCESSFUL!"
                        )

                        st.toast(
                            "✅ Product approved successfully!",
                            icon="✅"
                        )

                        st.markdown(
                            f"""
# 🎉 Product Request Approved

| Field | Value |
|---|---|
| Request ID | **#{approved_request_id}** |
| Product | **{product_name}** |
| SKU | **{sku}** |
| Requested By | **{requester_name}** |
| Approved By | **{current_username}** |
| Checker Role | **{current_role_name}** |
| Status | **APPROVED** |
| Product ID | **{product_id}** |
| Batch ID | **{batch_id}** |
| Cost Layer ID | **{cost_layer_id}** |
| Opening Stock | **{initial_qty}** |
"""
                        )

                        st.info(
                            "✅ Product + Warehouse Stock + "
                            "Batch + Cost Layer were created."
                        )

                        # ------------------------------------------------------
                        # CACHE
                        # ------------------------------------------------------

                        CacheManager.bump(
                            "product_version"
                        )

                        CacheManager.bump(
                            "inventory_version"
                        )

                        st.cache_data.clear()

                        # ------------------------------------------------------
                        # KEEP SUCCESS MESSAGE
                        # ------------------------------------------------------

                        st.session_state[
                            "approval_success_message"
                        ] = (
                            f"✅ Request #{approved_request_id} "
                            f"approved by {current_username}."
                        )

                        time.sleep(
                            2
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ APPROVAL FAILED — "
                            "DATABASE / RPC ERROR"
                        )

                        st.error(
                            str(e)
                        )

                        with st.expander(
                            "🔎 Technical Details"
                        ):

                            st.code(
                                repr(e)
                            )

            # ------------------------------------------------------------------
            # REJECT
            # ------------------------------------------------------------------

            with b2:

                if st.button(
                    "❌ REJECT",
                    key=f"reject_{request_id}",
                    use_container_width=True,
                ):

                    try:

                        response = (
                            client
                            .table(
                                "product_create_requests"
                            )
                            .update(
                                {
                                    "status":
                                        "REJECTED"
                                }
                            )
                            .eq(
                                "id",
                                request_id
                            )
                            .execute()
                        )

                        rows = (
                            response.data
                            or []
                        )

                        if not rows:

                            st.error(
                                "❌ REJECT FAILED"
                            )

                            st.warning(
                                "No database row was updated."
                            )

                            continue

                        # ------------------------------------------------------
                        # SUCCESS
                        # ------------------------------------------------------

                        st.success(
                            f"❌ Request #{request_id} "
                            "REJECTED SUCCESSFULLY!"
                        )

                        st.toast(
                            "❌ Product request rejected.",
                            icon="❌"
                        )

                        st.session_state[
                            "approval_reject_message"
                        ] = (
                            f"❌ Request #{request_id} "
                            f"rejected by {current_username}."
                        )

                        CacheManager.bump(
                            "product_version"
                        )

                        CacheManager.bump(
                            "inventory_version"
                        )

                        st.cache_data.clear()

                        time.sleep(
                            2
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ REJECT FAILED"
                        )

                        st.error(
                            str(e)
                        )

                        with st.expander(
                            "🔎 Reject Technical Details"
                        ):

                            st.code(
                                repr(e)
                            )

    # ==========================================================================
    # PERSISTENT NOTIFICATIONS AFTER RERUN
    # ==========================================================================

    success_message = st.session_state.pop(
        "approval_success_message",
        None
    )

    if success_message:

        st.success(
            f"🎉 {success_message}"
        )

        st.toast(
            success_message,
            icon="✅"
        )

    reject_message = st.session_state.pop(
        "approval_reject_message",
        None
    )

    if reject_message:

        st.error(
            reject_message
        )

        st.toast(
            reject_message,
            icon="❌"
        )

    # ==========================================================================
    # APPROVAL HISTORY
    # ==========================================================================

    st.markdown("---")

    st.subheader(
        "📜 Recent Product Approval History"
    )

    try:

        history_response = (
            client
            .table(
                "product_create_requests"
            )
            .select("*")
            .in_(
                "status",
                [
                    "APPROVED",
                    "REJECTED",
                ]
            )
            .order(
                "id",
                desc=True
            )
            .limit(
                10
            )
            .execute()
        )

        history = (
            history_response.data
            or []
        )

    except Exception as e:

        st.error(
            "❌ Failed to load approval history."
        )

        st.code(
            repr(e)
        )

        return

    if not history:

        st.info(
            "No approval history yet."
        )

        return

    # ==========================================================================
    # HISTORY TABLE
    # ==========================================================================

    for row in history:

        request_id = row.get(
            "id"
        )

        product = (
            row.get(
                "product_data"
            )
            or {}
        )

        product_name = product.get(
            "name",
            "-"
        )

        sku = product.get(
            "sku",
            "-"
        )

        status = row.get(
            "status",
            "-"
        )

        requester_name = _username(
            row.get(
                "requested_by"
            ),
            users_cache,
        )

        approved_by = row.get(
            "approved_by"
        )

        approved_name = _username(
            approved_by,
            users_cache,
        )

        approved_at = row.get(
            "approved_at"
        )

        rejected_by = row.get(
            "rejected_by"
        )

        rejected_name = _username(
            rejected_by,
            users_cache,
        )

        rejected_at = row.get(
            "rejected_at"
        )

        st.markdown(
            f"""
### #{request_id} — {product_name}

| Field | Value |
|---|---|
| SKU | **{sku}** |
| Status | **{status}** |
| Requested By | **{requester_name}** |
| Approved By | **{approved_name if status == "APPROVED" else "—"}** |
| Approved At | **{approved_at if status == "APPROVED" else "—"}** |
| Rejected By | **{rejected_name if status == "REJECTED" else "—"}** |
| Rejected At | **{rejected_at if status == "REJECTED" else "—"}** |
"""
        )

        st.markdown("---")


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "render_product_approval_queue"
]
