# ==============================================================================
# erp_pages/inventory/product_approval.py
# ERP ENTERPRISE PRODUCT APPROVAL QUEUE v2.1 CLEAN
# Part 1 / 2
# ==============================================================================

import time
import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager


# ==============================================================================
# USER NAME HELPER
# ==============================================================================

def _get_user_name(user_id, users_cache):
    """Convert UUID -> username."""

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
    """Load users once for username lookup."""

    try:
        response = (
            client
            .table("users")
            .select("id,username,is_active")
            .execute()
        )

        users = response.data or []
        result = {}

        for user in users:
            uid = user.get("id")
            if uid:
                result[str(uid)] = user

        return result

    except Exception as e:
        st.warning(f"⚠️ User lookup failed: {e}")
        return {}


# ==============================================================================
# MONEY FORMAT
# ==============================================================================

def _money(value):
    try:
        return f"{float(value or 0):,.2f} MMK"
    except Exception:
        return "0.00 MMK"


# ==============================================================================
# MAIN APPROVAL QUEUE
# ==============================================================================

def render_product_approval_queue():

    st.subheader("🟡 Product Approval Queue")

    # --------------------------------------------------------------------------
    # Current user
    # --------------------------------------------------------------------------

    current_user = st.session_state.get("user")

    if not current_user:
        st.warning("🔐 Login required.")
        return

    if not isinstance(current_user, dict):
        st.error("❌ Invalid login session.")
        return

    current_user_id = current_user.get("id")
    current_username = (
        current_user.get("username")
        or current_user.get("full_name")
        or "Unknown User"
    )

    if not current_user_id:
        st.error("❌ Current user ID is missing.")
        return

    # --------------------------------------------------------------------------
    # Role check
    # --------------------------------------------------------------------------

    role_name = str(current_user.get("role_name", "")).strip().lower()
    role_id = current_user.get("role_id")

    is_checker = (
        role_name in ("admin", "manager")
        or role_id in (1, 2)
    )

    if not is_checker:
        st.info("🔒 Approval Queue is available only to Admin / Manager.")
        return

    # --------------------------------------------------------------------------
    # Privileged DB
    # --------------------------------------------------------------------------

    try:
        client = privileged_db()
    except Exception as e:
        st.error("❌ Privileged database connection failed.")
        st.exception(e)
        return

    users_cache = _load_users(client)

    # --------------------------------------------------------------------------
    # Load pending requests
    # --------------------------------------------------------------------------

    try:
        response = (
            client
            .table("product_create_requests")
            .select("*")
            .eq("status", "PENDING")
            .order("id", desc=True)
            .execute()
        )

        requests = response.data or []

    except Exception as e:
        st.error("❌ Failed to load approval queue.")
        st.exception(e)
        return

    # --------------------------------------------------------------------------
    # Pending count
    # --------------------------------------------------------------------------

    pending_count = len(requests)

    if pending_count == 0:
        st.success("✅ No pending product requests.")
        return

    st.warning(f"🟡 Pending Product Requests: {pending_count}")
    st.markdown("---")

    # --------------------------------------------------------------------------
    # Request loop
    # --------------------------------------------------------------------------

    for req in requests:

        request_id = req.get("id")
        product = req.get("product_data") or {}

        requester_id = req.get("requested_by")
        requester_name = _get_user_name(requester_id, users_cache)

        with st.container(border=True):

            st.markdown(f"### 📝 Product Request #{request_id}")

            st.warning("🟡 STATUS: PENDING — Approval Required")

            c1, c2 = st.columns(2)

            with c1:
                st.write(f"**Product:** {product.get('name', '-')}")
                st.write(f"**SKU:** {product.get('sku', '-')}")
                st.write(f"**Barcode:** {product.get('barcode', '-')}")
                st.write(f"**Unit:** {product.get('unit', '-')}")

            with c2:
                st.write(f"**Opening Qty:** {req.get('initial_qty', 0)}")
                st.write(f"**Purchase Price:** {_money(product.get('purchase_price'))}")
                st.write(f"**Selling Price:** {_money(product.get('selling_price'))}")
                st.write(f"**Warehouse:** {req.get('warehouse_id', '-')}")

            st.markdown(f"👤 **Requested By:** `{requester_name}`")
            st.write(f"🕒 **Created At:** {req.get('created_at', '-')}")

            st.markdown("---")

            # ------------------------------------------------------------------
            # Self approval protection
            # ------------------------------------------------------------------

            is_own_request = str(requester_id) == str(current_user_id)

            if is_own_request:
                st.error("🚫 SELF-APPROVAL BLOCKED")
                st.info(
                    f"Maker '{requester_name}' cannot approve his own request."
                )
                st.caption(
                    "Another Admin / Manager must approve this request."
                )
            else:
                b1, b2 = st.columns(2)

# ------------------------------------------------------------------
                # APPROVE
                # ------------------------------------------------------------------

                with b1:

                    if st.button(
                        "✅ APPROVE REQUEST",
                        key=f"approve_product_{request_id}",
                        use_container_width=True,
                    ):

                        try:

                            response = (
                                client
                                .rpc(
                                    "approve_product_create_rpc",
                                    {
                                        "p_request_id": int(request_id),
                                        "p_checker_id": str(current_user_id),
                                    },
                                )
                                .execute()
                            )

                            result = response.data

                            if isinstance(result, list):
                                result = result[0] if result else None

                            if not isinstance(result, dict):

                                st.error("❌ APPROVAL FAILED")
                                st.code(str(result))

                            elif not result.get("success", False):

                                st.error("❌ APPROVAL FAILED")

                                st.warning(
                                    f"Status: {result.get('status', 'ERROR')}"
                                )

                                st.error(
                                    result.get(
                                        "message",
                                        "Unknown approval error.",
                                    )
                                )

                                with st.expander("🔎 RPC Response"):
                                    st.json(result)

                            else:

                                approved_request_id = result.get(
                                    "request_id",
                                    request_id,
                                )

                                product_id = result.get("product_id")

                                st.success(
                                    "🎉 PRODUCT REQUEST APPROVED SUCCESSFULLY!"
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
Approved By  : {current_username}
Product ID   : {product_id or '-'}
Status       : APPROVED

✅ Product creation has been authorized.
"""
                                )

                                CacheManager.bump("product_version")
                                CacheManager.bump("inventory_version")
                                st.cache_data.clear()

                                time.sleep(2)
                                st.rerun()

                        except Exception as e:

                            st.error(
                                "❌ APPROVAL FAILED — Database / RPC Error"
                            )

                            st.exception(e)

                # ------------------------------------------------------------------
                # REJECT
                # ------------------------------------------------------------------

                with b2:

                    if st.button(
                        "❌ REJECT REQUEST",
                        key=f"reject_product_{request_id}",
                        use_container_width=True,
                    ):

                        try:

                            (
                                client
                                .table("product_create_requests")
                                .update({"status": "REJECTED"})
                                .eq("id", request_id)
                                .execute()
                            )

                            st.success(
                                f"❌ Request #{request_id} rejected successfully."
                            )

                            st.toast(
                                "❌ Product request rejected.",
                                icon="❌",
                            )

                            CacheManager.bump("product_version")
                            st.cache_data.clear()

                            time.sleep(2)
                            st.rerun()

                        except Exception as e:

                            st.error("❌ REJECT FAILED")
                            st.exception(e)

                st.markdown("---")

    # ==========================================================================
    # APPROVAL HISTORY
    # ==========================================================================

    st.markdown("---")
    st.subheader("📜 Recent Approval History")

    try:

        history_response = (
            client
            .table("product_create_requests")
            .select(
                "id,status,approved_by,rejected_by,approved_at,rejected_at,product_data"
            )
            .neq("status", "PENDING")
            .order("id", desc=True)
            .limit(10)
            .execute()
        )

        history = history_response.data or []

        if not history:
            st.info("No approval history found.")
        else:
            for item in history:

                product_name = (
                    item.get("product_data", {})
                    .get("name", "-")
                )

                approved_by_name = _get_user_name(
                    item.get("approved_by"),
                    users_cache,
                )

                rejected_by_name = _get_user_name(
                    item.get("rejected_by"),
                    users_cache,
                )

                with st.container(border=True):

                    st.write(f"**Request ID:** {item.get('id')}")
                    st.write(f"**Product:** {product_name}")
                    st.write(f"**Status:** {item.get('status')}")

                    if item.get("status") == "APPROVED":
                        st.write(f"**Approved By:** {approved_by_name}")
                        st.write(f"**Approved At:** {item.get('approved_at')}")

                    elif item.get("status") == "REJECTED":
                        st.write(f"**Rejected By:** {rejected_by_name}")
                        st.write(f"**Rejected At:** {item.get('rejected_at')}")

    except Exception as e:
        st.warning(f"⚠️ Approval history load failed: {e}")
