# ==============================================================================
# erp_pages/inventory/product_approval.py
# ERP ENTERPRISE PRODUCT APPROVAL QUEUE v2.0 CLEAN
#
# FEATURES
# ------------------------------------------------------------------------------
# 1. Pending Product Approval Queue
# 2. Admin / Manager Checker Only
# 3. Maker Cannot Approve Own Request
# 4. UUID -> Username Display
# 5. Clear SUCCESS / ERROR Notifications
# 6. Toast Notifications
# 7. 3-Second Success / Reject Display
# 8. Approved By / Rejected By History
# 9. Approval RPC uses p_checker_id
# 10. Privileged Server Client
# ==============================================================================

import time

import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager


# ==============================================================================
# HELPERS
# ==============================================================================

def _get_user_name(user_id, users_cache):
    """
    Convert user UUID -> username.

    Supports:
        username
        full_name
        name
    """

    if not user_id:
        return "Unknown User"

    user = users_cache.get(str(user_id))

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
    Load users once for this page.

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
# APPROVAL QUEUE
# ==============================================================================

def render_product_approval_queue():

    st.subheader(
        "🟡 Product Approval Queue"
    )

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================

    current_user = st.session_state.get("user")

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

    current_user_id = current_user.get("id")

    current_username = (
        current_user.get("username")
        or current_user.get("full_name")
        or current_user.get("name")
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
            ""
        )
    ).strip().lower()

    role_id = current_user.get(
        "role_id"
    )

    # --------------------------------------------------------------------------
    # Admin = 1
    # Manager = 2
    # --------------------------------------------------------------------------

    is_checker = (
        role_name in (
            "admin",
            "manager"
        )
        or role_id in (
            1,
            2
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
            f"❌ Privileged database connection failed: {e}"
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
            f"❌ Failed to load approval queue: {e}"
        )

        return

    # ==========================================================================
    # HEADER
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
                users_cache
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
                "🟡 STATUS: PENDING — Approval Required"
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

🕒 **Created At:** {req.get('created_at', '-')}
"""
            )

            st.markdown("---")

            # ==================================================================
            # SELF APPROVAL PROTECTION
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
                    f"Maker '{requester_name}' သည် "
                    f"မိမိတင်ထားသော Product Request ကို "
                    f"မိမိကိုယ်တိုင် Approve မလုပ်နိုင်ပါ။"
                )

                st.caption(
                    "အခြား Admin / Manager တစ်ဦးကသာ "
                    "Approve လုပ်ရပါမည်။"
                )

                continue

            # ==================================================================
            # APPROVE / REJECT BUTTONS
            # ==================================================================

            b1, b2 = st.columns(2)

            # ==================================================================
            # APPROVE
            # ==================================================================

            with b1:

                approve_key = (
                    f"approve_product_{request_id}"
                )

                if st.button(
                    "✅ APPROVE REQUEST",
                    key=approve_key,
                    use_container_width=True
                ):

                    try:

                        # ------------------------------------------------------
                        # CALL APPROVAL RPC
                        #
                        # IMPORTANT:
                        # RPC signature:
                        #
                        # approve_product_create_rpc(
                        #     p_request_id bigint,
                        #     p_checker_id uuid
                        # )
                        # ------------------------------------------------------

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
                                }
                            )
                            .execute()
                        )

                        result = response.data

                        # ------------------------------------------------------
                        # NORMALIZE RESPONSE
                        # ------------------------------------------------------

                        if isinstance(
                            result,
                            list
                        ):

                            result = (
                                result[0]
                                if result
                                else None
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

                            approved_request_id = (
                                result.get(
                                    "request_id",
                                    request_id
                                )
                            )

                            product_id = result.get(
                                "product_id"
                            )

                            batch_id = result.get(
                                "batch_id"
                            )

                            cost_layer_id = result.get(
                                "cost_layer_id"
                            )

                            approved_by_name = (
                                current_username
                            )

                            # --------------------------------------------------
                            # SAVE APPROVAL HISTORY
                            #
                            # RPC already performs the actual approval.
                            # This update records the checker identity.
                            # --------------------------------------------------

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
                                                "now()",
                                        }
                                    )
                                    .eq(
                                        "id",
                                        request_id
                                    )
                                    .execute()
                                )

                            except Exception as history_error:

                                # Do NOT turn a successful approval
                                # into a failed approval.
                                st.warning(
                                    "⚠️ Approval succeeded, "
                                    "but approval history could not "
                                    f"be saved: {history_error}"
                                )

                            # --------------------------------------------------
                            # MAIN SUCCESS NOTIFICATION
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

**Product:** {product.get('name', '-')}

**SKU:** {product.get('sku', '-')}

**Requested By:** {requester_name}

**Approved By:** {approved_by_name}

**Status:** APPROVED

**Product ID:** {product_id or '-'}

**Batch ID:** {batch_id or '-'}

**Cost Layer ID:** {cost_layer_id or '-'}

**Opening Qty:** {req.get('initial_qty', 0)}

✅ Product creation has been authorized.
"""
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
                            # 3 SECOND NOTIFICATION DISPLAY
                            # --------------------------------------------------

                            time.sleep(
                                3.0
                            )

                            st.rerun()

                        # ======================================================
                        # FAILURE
                        # ======================================================

                        else:

                            message = result.get(
                                "message",
                                "Approval failed."
                            )

                            status = result.get(
                                "status",
                                "ERROR"
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

                reject_key = (
                    f"reject_product_{request_id}"
                )

                if st.button(
                    "❌ REJECT REQUEST",
                    key=reject_key,
                    use_container_width=True
                ):

                    try:

                        # ------------------------------------------------------
                        # REJECT
                        # ------------------------------------------------------

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
                                        "now()",
                                }
                            )
                            .eq(
                                "id",
                                request_id
                            )
                            .execute()
                        )

                        # ------------------------------------------------------
                        # REJECT SUCCESS NOTIFICATION
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

**Product:** {product.get('name', '-')}

**SKU:** {product.get('sku', '-')}

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
