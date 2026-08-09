# ==============================================================================
# erp_pages/inventory/product_approval.py
# ERP ENTERPRISE PRODUCT APPROVAL QUEUE v3.0 CLEAN
#
# MAKER-CHECKER
# ------------------------------------------------------------------------------
# Maker:
#   - Can submit product creation request
#   - Cannot approve own request
#
# Checker:
#   - Admin
#   - Manager
#   - Must have inventory.adjust permission
#
# Cashier:
#   - Cannot approve
#
# FEATURES
# ------------------------------------------------------------------------------
# 1. Pending Approval Queue
# 2. UUID -> Username
# 3. Admin / Manager validation
# 4. inventory.adjust permission validation
# 5. Self-approval protection
# 6. Correct approval RPC parameters
# 7. Clear success notification
# 8. Clear failure notification
# 9. Toast notification
# 10. Approved / Rejected history
# 11. Product / Batch / Cost Layer result
# 12. 3-second result display
# ==============================================================================

import time

import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager


# ==============================================================================
# CONSTANTS
# ==============================================================================

CHECKER_ROLE_IDS = {
    1,  # Admin
    2,  # Manager
}

CHECKER_ROLE_NAMES = {
    "admin",
    "manager",
}

INVENTORY_ADJUST_PERMISSION = "inventory.adjust"


# ==============================================================================
# USER NAME HELPER
# ==============================================================================

def _get_user_name(user_id, users_cache):
    """
    Convert UUID -> readable username.
    """

    if not user_id:
        return "Unknown User"

    user = users_cache.get(
        str(user_id)
    )

    if not user:
        return str(user_id)

    return (
        user.get("username")
        or user.get("full_name")
        or user.get("name")
        or str(user_id)
    )


# ==============================================================================
# LOAD USERS
# ==============================================================================

def _load_users(client):
    """
    Load users once.

    Returns:
        {
            "uuid": {
                "id": "...",
                "username": "...",
                ...
            }
        }
    """

    try:

        response = (
            client
            .table("users")
            .select(
                "id,username,full_name,name,is_active"
            )
            .execute()
        )

        users = response.data or []

        users_cache = {}

        for user in users:

            user_id = user.get("id")

            if user_id:

                users_cache[
                    str(user_id)
                ] = user

        return users_cache

    except Exception as e:

        st.warning(
            "⚠️ User lookup failed: "
            f"{e}"
        )

        return {}


# ==============================================================================
# CHECKER PERMISSION
# ==============================================================================

def _has_inventory_adjust_permission(
    client,
    role_id,
):
    """
    Check whether role has inventory.adjust permission.
    """

    if not role_id:
        return False

    try:

        response = (
            client
            .table("role_permissions")
            .select(
                "permission_id,permissions(permission_key)"
            )
            .eq(
                "role_id",
                int(role_id)
            )
            .execute()
        )

        rows = response.data or []

        for row in rows:

            permission = (
                row.get("permissions")
                or {}
            )

            permission_key = (
                permission.get(
                    "permission_key"
                )
            )

            if permission_key == (
                INVENTORY_ADJUST_PERMISSION
            ):

                return True

        return False

    except Exception:

        # Do not silently grant permission.
        return False


# ==============================================================================
# ROLE CHECK
# ==============================================================================

def _is_checker(
    current_user,
):
    """
    Admin / Manager only.
    """

    role_name = str(
        current_user.get(
            "role_name",
            ""
        )
    ).strip().lower()

    role_id = current_user.get(
        "role_id"
    )

    if role_name in CHECKER_ROLE_NAMES:

        return True

    try:

        if int(role_id) in CHECKER_ROLE_IDS:

            return True

    except Exception:

        pass

    return False


# ==============================================================================
# NORMALIZE RPC RESULT
# ==============================================================================

def _normalize_result(data):

    if isinstance(
        data,
        list
    ):

        return (
            data[0]
            if data
            else None
        )

    return data


# ==============================================================================
# APPROVAL QUEUE
# ==============================================================================

def render_product_approval_queue():

    st.subheader(
        "🟡 Product Approval Queue"
    )

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================

    current_user = st.session_state.get(
        "user"
    )

    if not current_user:

        st.warning(
            "🔐 Login required."
        )

        return

    if not isinstance(
        current_user,
        dict
    ):

        st.error(
            "❌ Invalid login session."
        )

        return

    current_user_id = current_user.get(
        "id"
    )

    current_username = (
        current_user.get("username")
        or current_user.get("full_name")
        or current_user.get("name")
        or "Unknown User"
    )

    current_role_name = str(
        current_user.get(
            "role_name",
            ""
        )
    ).strip()

    current_role_id = current_user.get(
        "role_id"
    )

    if not current_user_id:

        st.error(
            "❌ Current user ID is missing."
        )

        return

    # ==========================================================================
    # CHECKER ROLE
    # ==========================================================================

    if not _is_checker(
        current_user
    ):

        st.info(
            "🔒 Approval Queue is available "
            "only to Admin / Manager."
        )

        st.caption(
            f"Current User: {current_username}"
        )

        st.caption(
            f"Current Role: "
            f"{current_role_name or 'Unknown'}"
        )

        return

    # ==========================================================================
    # PRIVILEGED CLIENT
    # ==========================================================================

    try:

        client = privileged_db()

    except Exception as e:

        st.error(
            "❌ Privileged database connection failed."
        )

        st.error(
            str(e)
        )

        return

    # ==========================================================================
    # CHECK INVENTORY.ADJUST
    # ==========================================================================

    has_permission = (
        _has_inventory_adjust_permission(
            client,
            current_role_id
        )
    )

    if not has_permission:

        st.error(
            "🚫 APPROVAL ACCESS DENIED"
        )

        st.warning(
            "Your role does not have "
            "`inventory.adjust` permission."
        )

        st.info(
            f"""
**User:** {current_username}

**Role:** {current_role_name}

**Role ID:** {current_role_id}

**Required Permission:** inventory.adjust
"""
        )

        return

    # ==========================================================================
    # LOAD USERS
    # ==========================================================================

    users_cache = _load_users(
        client
    )

    # ==========================================================================
    # LOAD PENDING REQUESTS
    # ==========================================================================

    try:

        response = (
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

        requests = (
            response.data
            or []
        )

    except Exception as e:

        st.error(
            "❌ Failed to load approval queue."
        )

        st.error(
            str(e)
        )

        return

    # ==========================================================================
    # HEADER
    # ==========================================================================

    pending_count = len(
        requests
    )

    st.markdown(
        f"""
### 👤 Checker

**User:** {current_username}

**Role:** {current_role_name}

**Permission:** ✅ inventory.adjust

**Pending Requests:** 🟡 {pending_count}
"""
    )

    st.markdown("---")

    # ==========================================================================
    # NO REQUEST
    # ==========================================================================

    if pending_count == 0:

        st.success(
            "✅ No pending product requests."
        )

        return

    st.warning(
        f"🟡 PENDING PRODUCT REQUESTS: "
        f"{pending_count}"
    )

    # ==========================================================================
    # REQUEST LOOP
    # ==========================================================================

    for req in requests:

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

        requester_name = (
            _get_user_name(
                requester_id,
                users_cache
            )
        )

        product_name = (
            product.get(
                "name",
                "-"
            )
        )

        sku = (
            product.get(
                "sku",
                "-"
            )
        )

        # ======================================================================
        # REQUEST CARD
        # ======================================================================

        with st.container(
            border=True
        ):

            st.markdown(
                f"## 📝 Request #{request_id}"
            )

            st.warning(
                "🟡 STATUS: PENDING — Approval Required"
            )

            # ------------------------------------------------------------------
            # PRODUCT DETAILS
            # ------------------------------------------------------------------

            c1, c2 = st.columns(2)

            with c1:

                st.write(
                    f"**Product:** "
                    f"{product_name}"
                )

                st.write(
                    f"**SKU:** "
                    f"{sku}"
                )

                st.write(
                    f"**Barcode:** "
                    f"{product.get('barcode', '-')}"
                )

                st.write(
                    f"**Unit:** "
                    f"{product.get('unit', '-')}"
                )

            with c2:

                st.write(
                    f"**Opening Qty:** "
                    f"{req.get('initial_qty', 0)}"
                )

                try:

                    purchase_price = float(
                        product.get(
                            "purchase_price",
                            0
                        )
                        or 0
                    )

                except Exception:

                    purchase_price = 0.0

                try:

                    selling_price = float(
                        product.get(
                            "selling_price",
                            0
                        )
                        or 0
                    )

                except Exception:

                    selling_price = 0.0

                st.write(
                    f"**Purchase Price:** "
                    f"{purchase_price:,.2f} MMK"
                )

                st.write(
                    f"**Selling Price:** "
                    f"{selling_price:,.2f} MMK"
                )

                st.write(
                    f"**Warehouse:** "
                    f"{req.get('warehouse_id', '-')}"
                )

            # ------------------------------------------------------------------
            # REQUESTER
            # ------------------------------------------------------------------

            st.markdown(
                f"""
👤 **Requested By:** {requester_name}

🆔 **Requester ID:** {requester_id or '-'}

🕒 **Created At:** {req.get('created_at', '-')}
"""
            )

            st.markdown("---")

            # ==================================================================
            # SELF APPROVAL BLOCK
            # ==================================================================

            is_own_request = (
                str(
                    requester_id
                )
                ==
                str(
                    current_user_id
                )
            )

            if is_own_request:

                st.error(
                    "🚫 SELF-APPROVAL BLOCKED"
                )

                st.info(
                    f"""
Maker: **{requester_name}**

Checker: **{current_username}**

Maker နှင့် Checker တစ်ယောက်တည်းဖြစ်နေသောကြောင့်
ဤ Request ကို Approve မလုပ်နိုင်ပါ။
"""
                )

                st.caption(
                    "အခြား Admin / Manager တစ်ဦးကသာ "
                    "Approve လုပ်နိုင်ပါသည်။"
                )

                st.markdown("---")

                continue

            # ==================================================================
            # BUTTONS
            # ==================================================================

            b1, b2 = st.columns(2)

            # ==================================================================
            # APPROVE
            # ==================================================================

            with b1:

                if st.button(
                    "✅ APPROVE REQUEST",
                    key=(
                        f"approve_product_"
                        f"{request_id}"
                    ),
                    use_container_width=True
                ):

                    try:

                        # ------------------------------------------------------
                        # RPC
                        # ------------------------------------------------------

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
                                }
                            )
                            .execute()
                        )

                        result = _normalize_result(
                            response.data
                        )

                        # ------------------------------------------------------
                        # INVALID RESPONSE
                        # ------------------------------------------------------

                        if not isinstance(
                            result,
                            dict
                        ):

                            st.error(
                                "❌ APPROVAL FAILED"
                            )

                            st.code(
                                str(result)
                            )

                            continue

                        # ======================================================
                        # SUCCESS
                        # ======================================================

                        if result.get(
                            "success"
                        ):

                            # --------------------------------------------------
                            # APPROVAL HISTORY
                            # --------------------------------------------------

                            history_saved = True

                            try:

                                (
                                    client
                                    .table(
                                        "product_create_requests"
                                    )
                                    .update(
                                        {
                                            "approved_by":
                                                str(
                                                    current_user_id
                                                ),

                                            "approved_at":
                                                None
                                        }
                                    )
                                    .eq(
                                        "id",
                                        request_id
                                    )
                                    .execute()
                                )

                            except Exception:

                                history_saved = False

                            # --------------------------------------------------
                            # RESULT DATA
                            # --------------------------------------------------

                            approved_request_id = (
                                result.get(
                                    "request_id",
                                    request_id
                                )
                            )

                            product_id = (
                                result.get(
                                    "product_id"
                                )
                            )

                            batch_id = (
                                result.get(
                                    "batch_id"
                                )
                            )

                            cost_layer_id = (
                                result.get(
                                    "cost_layer_id"
                                )
                            )

                            # --------------------------------------------------
                            # SUCCESS NOTIFICATION
                            # --------------------------------------------------

                            st.success(
                                "🎉 PRODUCT REQUEST "
                                "APPROVED SUCCESSFULLY!"
                            )

                            st.toast(
                                "✅ Product approval successful!",
                                icon="✅"
                            )

                            st.info(
                                f"""
🎉 **APPROVAL COMPLETED**

**Request ID:** #{approved_request_id}

**Product:** {product_name}

**SKU:** {sku}

**Requested By:** {requester_name}

**Approved By:** {current_username}

**Status:** APPROVED

**Product ID:** {product_id or '-'}

**Batch ID:** {batch_id or '-'}

**Cost Layer ID:** {cost_layer_id or '-'}

**Opening Qty:** {req.get('initial_qty', 0)}

**Checker Role:** {current_role_name}

**Maker-Checker:** {'✅ YES' if result.get('maker_checker') else '—'}

**Stock Changed:** {'✅ YES' if result.get('stock_changed') else '—'}

✅ Product creation has been authorized.
"""
                            )

                            if not history_saved:

                                st.warning(
                                    "⚠️ Approval succeeded, "
                                    "but approval history could not "
                                    "be saved."
                                )

                            # --------------------------------------------------
                            # CACHE
                            # --------------------------------------------------

                            CacheManager.bump(
                                "product_version"
                            )

                            CacheManager.bump(
                                "inventory_version"
                            )

                            st.cache_data.clear()

                            # --------------------------------------------------
                            # 3 SECOND NOTIFICATION
                            # --------------------------------------------------

                            time.sleep(
                                3.0
                            )

                            st.rerun()

                        # ======================================================
                        # FAILURE
                        # ======================================================

                        else:

                            message = (
                                result.get(
                                    "message",
                                    "Approval failed."
                                )
                            )

                            status = (
                                result.get(
                                    "status",
                                    "ERROR"
                                )
                            )

                            st.error(
                                "❌ APPROVAL FAILED"
                            )

                            st.warning(
                                f"Status: **{status}**"
                            )

                            st.error(
                                message
                            )

                            with st.expander(
                                "🔎 Approval Response Details"
                            ):

                                st.json(
                                    result
                                )

                    except Exception as e:

                        st.error(
                            "❌ APPROVAL FAILED — "
                            "Database / RPC Error"
                        )

                        st.error(
                            str(e)
                        )

                        with st.expander(
                            "🔎 Technical Error Details"
                        ):

                            st.code(
                                repr(e)
                            )

            # ==================================================================
            # REJECT
            # ==================================================================

            with b2:

                if st.button(
                    "❌ REJECT REQUEST",
                    key=(
                        f"reject_product_"
                        f"{request_id}"
                    ),
                    use_container_width=True
                ):

                    try:

                        (
                            client
                            .table(
                                "product_create_requests"
                            )
                            .update(
                                {
                                    "status":
                                        "REJECTED",

                                    "rejected_by":
                                        str(
                                            current_user_id
                                        ),

                                    "rejected_at":
                                        None,
                                }
                            )
                            .eq(
                                "id",
                                request_id
                            )
                            .execute()
                        )

                        # ------------------------------------------------------
                        # SUCCESS NOTIFICATION
                        # ------------------------------------------------------

                        st.success(
                            f"❌ Request #{request_id} "
                            "REJECTED successfully."
                        )

                        st.toast(
                            "Request rejected.",
                            icon="❌"
                        )

                        st.info(
                            f"""
❌ **PRODUCT REQUEST REJECTED**

**Request ID:** #{request_id}

**Product:** {product_name}

**SKU:** {sku}

**Requested By:** {requester_name}

**Rejected By:** {current_username}

**Status:** REJECTED

⚠️ Product, stock, batch and cost layer
were NOT created.
"""
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
                        # 3 SECOND DISPLAY
                        # ------------------------------------------------------

                        time.sleep(
                            3.0
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            "❌ REJECT FAILED"
                        )

                        st.error(
                            str(e)
                        )

        st.markdown("---")
