# ==============================================================================
# erp_pages/inventory/product_approval.py
# ERP ENTERPRISE PRODUCT APPROVAL QUEUE v2.0 CLEAN
#
# FEATURES
# ------------------------------------------------------------------------------
# 1. Admin / Manager approval
# 2. Maker-Checker segregation
# 3. Self-approval blocked
# 4. Correct RPC parameters
# 5. User UUID -> username
# 6. Clear success / failure notifications
# 7. No invalid users.name column
# 8. No unsafe continue inside try/except
# 9. Cache refresh after approval
# ==============================================================================

import time

import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager


# ==============================================================================
# USER NAME HELPER
# ==============================================================================

def _get_user_name(user_id, users_cache):
    """
    Convert user UUID to username.

    Current users table:
        id
        username
        is_active

    IMPORTANT:
        Do NOT query users.name because that column does not exist.
    """

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
# LOAD USERS
# ==============================================================================

def _load_users(client):
    """
    Load users for UUID -> username display.

    Only fields known to exist are requested.
    """

    try:

        response = (
            client
            .table("users")
            .select(
                "id,username,is_active"
            )
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
            f"⚠️ User lookup failed: {e}"
        )

        return {}


# ==============================================================================
# FORMAT MONEY
# ==============================================================================

def _money(value):

    try:

        return f"{float(value or 0):,.2f} MMK"

    except Exception:

        return "0.00 MMK"


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

    current_user = (
        st.session_state.get("user")
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
        current_user.get("username")
        or current_user.get("full_name")
        or "Unknown User"
    )

    if not current_user_id:

        st.error(
            "❌ Current user ID is missing."
        )

        return

    # ==========================================================================
    # ROLE
    # ==========================================================================

    role_name = str(
        current_user.get(
            "role_name",
            "",
        )
    ).strip().lower()

    role_id = current_user.get(
        "role_id"
    )

    # --------------------------------------------------------------------------
    # ADMIN = 1
    # MANAGER = 2
    # CASHIER = 3
    # --------------------------------------------------------------------------

    is_checker = (
        role_name in (
            "admin",
            "manager",
        )
        or role_id in (
            1,
            2,
        )
    )

    if not is_checker:

        st.info(
            "🔒 Approval Queue is available "
            "only to Admin / Manager."
        )

        return

    # ==========================================================================
    # PRIVILEGED DATABASE
    # ==========================================================================

    try:

        client = privileged_db()

    except Exception as e:

        st.error(
            "❌ Privileged database connection failed."
        )

        st.exception(e)

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
                "PENDING",
            )
            .order(
                "id",
                desc=True,
            )
            .execute()
        )

        requests = (
            response.data or []
        )

    except Exception as e:

        st.error(
            "❌ Failed to load approval queue."
        )

        st.exception(e)

        return

    # ==========================================================================
    # PENDING COUNT
    # ==========================================================================

    pending_count = len(
        requests
    )

    if pending_count == 0:

        st.success(
            "✅ No pending product requests."
        )

        return

    st.warning(
        f"🟡 PENDING PRODUCT REQUESTS: "
        f"{pending_count}"
    )

    st.markdown("---")

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
                users_cache,
            )
        )

        # ======================================================================
        # REQUEST CARD
        # ======================================================================

        with st.container(
            border=True
        ):

            st.markdown(
                f"### 📝 Product Request #{request_id}"
            )

            # ------------------------------------------------------------------
            # STATUS
            # ------------------------------------------------------------------

            st.warning(
                "🟡 STATUS: PENDING — "
                "Approval Required"
            )

            # ------------------------------------------------------------------
            # PRODUCT INFORMATION
            # ------------------------------------------------------------------

            c1, c2 = st.columns(2)

            with c1:

                st.write(
                    f"**Product:** "
                    f"{product.get('name', '-')}"
                )

                st.write(
                    f"**SKU:** "
                    f"{product.get('sku', '-')}"
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

                st.write(
                    f"**Purchase Price:** "
                    f"{_money(product.get('purchase_price'))}"
                )

                st.write(
                    f"**Selling Price:** "
                    f"{_money(product.get('selling_price'))}"
                )

                st.write(
                    f"**Warehouse:** "
                    f"{req.get('warehouse_id', '-')}"
                )

            # ------------------------------------------------------------------
            # REQUESTER
            # ------------------------------------------------------------------

            st.markdown(
                f"👤 **Requested By:** "
                f"`{requester_name}`"
            )

            st.caption(
                f"Requested User ID: {requester_id}"
            )

            st.write(
                f"🕒 **Created At:** "
                f"{req.get('created_at', '-')}"
            )

            st.markdown("---")

            # ==================================================================
            # SELF APPROVAL CHECK
            # ==================================================================

            is_own_request = (
                str(requester_id)
                == str(current_user_id)
            )

            if is_own_request:

                st.error(
                    "🚫 SELF-APPROVAL BLOCKED"
                )

                st.info(
                    f"Maker '{requester_name}' "
                    "သည် မိမိတင်ထားသော Product Request "
                    "ကို မိမိကိုယ်တိုင် Approve မလုပ်နိုင်ပါ။"
                )

                st.caption(
                    "အခြား Admin / Manager တစ်ဦးကသာ "
                    "Approve လုပ်ရပါမည်။"
                )

            else:

                # ==============================================================
                # APPROVE / REJECT BUTTONS
                # ==============================================================

                b1, b2 = st.columns(2)

                # ==============================================================
                # APPROVE
                # ==============================================================

                with b1:

                    if st.button(
                        "✅ APPROVE REQUEST",
                        key=f"approve_product_{request_id}",
                        use_container_width=True,
                    ):

                        # ------------------------------------------------------
                        # RPC CALL
                        # ------------------------------------------------------

                        try:

                            response = (
                                client
                                .rpc(
                                    "approve_product_create_rpc",
                                    {
                                        "p_request_id":
                                            int(request_id),

                                        "p_checker_id":
                                            str(
                                                current_user_id
                                            ),
                                    },
                                )
                                .execute()
                            )

                            result = (
                                response.data
                            )

                            if isinstance(
                                result,
                                list,
                            ):

                                result = (
                                    result[0]
                                    if result
                                    else None
                                )

                            # --------------------------------------------------
                            # INVALID RESPONSE
                            # --------------------------------------------------

                            if not isinstance(
                                result,
                                dict,
                            ):

                                st.error(
                                    "❌ APPROVAL FAILED"
                                )

                                st.error(
                                    "RPC returned "
                                    "an invalid response."
                                )

                                st.code(
                                    str(result)
                                )

                            # --------------------------------------------------
                            # RPC RESPONSE
                            # --------------------------------------------------

                            elif not result.get(
                                "success",
                                False,
                            ):

                                error_message = (
                                    result.get(
                                        "message",
                                        "Unknown approval error.",
                                    )
                                )

                                error_status = (
                                    result.get(
                                        "status",
                                        "ERROR",
                                    )
                                )

                                st.error(
                                    "❌ APPROVAL FAILED"
                                )

                                st.warning(
                                    f"Status: **{error_status}**"
                                )

                                st.error(
                                    f"Reason: {error_message}"
                                )

                                with st.expander(
                                    "🔎 Approval Response Details"
                                ):

                                    st.json(
                                        result
                                    )

                            # --------------------------------------------------
                            # SUCCESS
                            # --------------------------------------------------

                            else:

                                approved_request_id = (
                                    result.get(
                                        "request_id",
                                        request_id,
                                    )
                                )

                                product_id = (
                                    result.get(
                                        "product_id"
                                    )
                                )

                                checker_name = (
                                    current_username
                                )

                                st.success(
                                    "🎉 PRODUCT REQUEST "
                                    "APPROVED SUCCESSFULLY!"
                                )

                                st.toast(
                                    "✅ Product approval successful!",
                                    icon="✅",
                                )

                                st.info(
                                    f"""
🎉 APPROVAL COMPLETED

Request ID   : #{approved_request_id}
Product      : {product.get('name', '-')}
SKU          : {product.get('sku', '-')}
Requested By : {requester_name}
Approved By  : {checker_name}
Product ID   : {product_id or '-'}
Status       : APPROVED

✅ Product creation has been authorized.
"""
                                )

                                # --------------------------------------------------
                                # CACHE REFRESH
                                # --------------------------------------------------

                                CacheManager.bump(
                                    "product_version"
                                )

                                CacheManager.bump(
                                    "inventory_version"
                                )

                                st.cache_data.clear()

                                # --------------------------------------------------
                                # SHORT DISPLAY DELAY
                                # --------------------------------------------------

                                time.sleep(
                                    2
                                )

                                st.rerun()

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

                                st.exception(
                                    e
                                )

                # ==============================================================
                # REJECT
                # ==============================================================

                with b2:

                    if st.button(
                        "❌ REJECT REQUEST",
                        key=f"reject_product_{request_id}",
                        use_container_width=True,
                    ):

                        try:

                            reject_response = (
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
                                    request_id,
                                )
                                .execute()
                            )

                            rejected_rows = (
                                reject_response.data
                                or []
                            )

                            st.success(
                                f"❌ Request #{request_id} "
                                "REJECTED successfully."
                            )

                            st.toast(
                                "❌ Product request rejected.",
                                icon="❌",
                            )

                            CacheManager.bump(
                                "product_version"
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
                                "🔎 Technical Error Details"
                            ):

                                st.exception(
                                    e
                                )

            st.markdown("---")

