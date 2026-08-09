import streamlit as st
from erp_core import privileged_db
from erp_core.context import CacheManager

# ==============================================================================
# HELPERS
# ==============================================================================

def _get_user_name(user_id, users_cache):
    """
    Convert user UUID -> username.
    Supports common users table fields: username, full_name, name
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
    Load active users once for this page.
    Returns: { "uuid": { "username": "...", ... } }
    """
    try:
        response = (
            client.table("users")
            .select("id,username,full_name,name,is_active")
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
        st.warning(f"⚠️ User name lookup failed: {e}")
        return {}

# ==============================================================================
# APPROVAL QUEUE
# ==============================================================================

def render_product_approval_queue():
    st.subheader("🟡 Product Approval Queue")

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================
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
        or current_user.get("name")
        or "Unknown User"
    )

    if not current_user_id:
        st.error("❌ Current user ID is missing.")
        return

    # ==========================================================================
    # ROLE
    # ==========================================================================
    role_name = str(current_user.get("role_name", "")).strip().lower()
    role_id = current_user.get("role_id")

    # --------------------------------------------------------------------------
    # Support both role_name and role_id
    # Admin = 1
    # Manager = 2
    # --------------------------------------------------------------------------
    is_checker = role_name in ("admin", "manager") or role_id in (1, 2)
    if not is_checker:
        st.info("🔒 Approval Queue is available only to Admin / Manager.")
        return

    # ==========================================================================
    # PRIVILEGED SERVER CLIENT
    # ==========================================================================
    try:
        client = privileged_db()
    except Exception as e:
        st.error(f"❌ Privileged database connection failed: {e}")
        return

    # ==========================================================================
    # LOAD USERS
    # ==========================================================================
    users_cache = _load_users(client)

    # ==========================================================================
    # LOAD PENDING REQUESTS
    # ==========================================================================
    try:
        response = (
            client.table("product_create_requests")
            .select("*")
            .eq("status", "PENDING")
            .order("id", desc=True)
            .execute()
        )
        requests = response.data or []
    except Exception as e:
        st.error(f"❌ Failed to load approval queue: {e}")
        return

    # ==========================================================================
    # HEADER / PENDING COUNT
    # ==========================================================================
    pending_count = len(requests)
    if pending_count == 0:
        st.success("✅ No pending product requests.")
        return

    st.warning(f"🟡 PENDING PRODUCT REQUESTS: {pending_count}")
    st.markdown("---")

    # ==========================================================================
    # REQUEST LOOP
    # ==========================================================================
    for req in requests:
        request_id = req.get("id")
        product = req.get("product_data") or {}
        requester_id = req.get("requested_by")
        requester_name = _get_user_name(requester_id, users_cache)

        # ======================================================================
        # REQUEST CARD
        # ======================================================================
        with st.container(border=True):
            st.markdown(f"### 📝 Product Request #{request_id}")

            # ------------------------------------------------------------------
            # STATUS
            # ------------------------------------------------------------------
            st.warning("🟡 STATUS: PENDING — Approval Required")

            # ------------------------------------------------------------------
            # PRODUCT INFORMATION
            # ------------------------------------------------------------------
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Product:** {product.get('name', '-')}")
                st.write(f"**SKU:** {product.get('sku', '-')}")
                st.write(f"**Barcode:** {product.get('barcode', '-')}")
                st.write(f"**Unit:** {product.get('unit', '-')}")
            with c2:
                st.write(f"**Opening Qty:** {req.get('initial_qty', 0)}")
                st.write(f"**Purchase Price:** {float(product.get('purchase_price', 0) or 0):,.2f} MMK")
                st.write(f"**Selling Price:** {float(product.get('selling_price', 0) or 0):,.2f} MMK")
                st.write(f"**Warehouse:** {req.get('warehouse_id', '-')}")

            # ------------------------------------------------------------------
            # REQUESTER
            # ------------------------------------------------------------------
            st.markdown(f"""
👤 Requested By: {requester_name}
🕒 Created At: {req.get('created_at', '-')}
            """)

            st.markdown("---")

            # ==================================================================
            # SELF-APPROVAL PROTECTION
            # ==================================================================
            is_own_request = str(requester_id) == str(current_user_id)
            if is_own_request:
                st.error("🚫 SELF-APPROVAL BLOCKED")
                st.info(f"Maker '{requester_name}' သည် မိမိတင်ထားသော Product Request ကို မိမိကိုယ်တိုင် Approve မလုပ်နိုင်ပါ။")
                st.caption("အခြား Admin / Manager တစ်ဦးကသာ Approve လုပ်ရပါမည်။")
                continue

            # ==================================================================
            # APPROVE / REJECT
            # ==================================================================
            b1, b2 = st.columns(2)

            # ------------------------------------------------------------------
            # APPROVE
            # ------------------------------------------------------------------
            with b1:
                approve_key = f"approve_product_{request_id}"
                if st.button("✅ APPROVE REQUEST", key=approve_key, use_container_width=True):
                    try:
                        response = (
                            client.rpc(
                                "approve_product_create_rpc",
                                {
                                    "p_request_id": int(request_id),
                                    "p_checker_id": str(current_user_id),
                                }
                            )
                            .execute()
                        )
                        result = response.data

                        if isinstance(result, list):
                            result = result[0] if result else None

                        if not isinstance(result, dict):
                            st.error("❌ APPROVAL FAILED")
                            st.code(str(result))
                            continue

                        if result.get("success"):
                            approved_request_id = result.get("request_id", request_id)
                            st.success("🎉 PRODUCT REQUEST APPROVED SUCCESSFULLY!")
                            st.toast("✅ Product approval successful!", icon="✅")
                            st.info(f"""
🎉 APPROVAL COMPLETED
Request ID: #{approved_request_id}
Product: {product.get('name', '-')}
SKU: {product.get('sku', '-')}
Requested By: {requester_name}
Approved By: {current_username}
Status: APPROVED
✅ Product creation has been authorized.
                            """)

                            CacheManager.bump("product_version")
                            CacheManager.bump("inventory_version")
                            st.cache_data.clear()

                            import time
                            time.sleep(3.0)  # ၃ စက္ကန့်ကြာအောင် ပြသပေးရန် ပြင်ဆင်ထားသည်
                            st.rerun()
                        else:
                            message = result.get("message", "Approval failed.")
                            status = result.get("status", "ERROR")
                            st.error("❌ APPROVAL FAILED")
                            st.warning(f"Status: **{status}**")
                            st.error(message)
                            with st.expander("🔎 Approval Response Details"):
                                st.json(result)

                    except Exception as e:
                        st.error("❌ APPROVAL FAILED — Database / RPC Error")
                        st.error(str(e))
                        with st.expander("🔎 Technical Error Details"):
                            st.code(repr(e))

            # ------------------------------------------------------------------
            # REJECT
            # ------------------------------------------------------------------
            with b2:
                reject_key = f"reject_product_{request_id}"
                if st.button("❌ REJECT REQUEST", key=reject_key, use_container_width=True):
                    try:
                        (
                            client.table("product_create_requests")
                            .update({"status": "REJECTED"})
                            .eq("id", request_id)
                            .execute()
                        )
                        st.success(f"❌ Request #{request_id} REJECTED successfully.")
                        st.toast("Request rejected.", icon="❌")
                        CacheManager.bump("product_version")
                        st.cache_data.clear()

                        import time
                        time.sleep(3.0)  # Reject အတွက်ပါ ၃ စက္ကန့် စောင့်စေလိုပါက ဤနေရာတွင်လည်း ပြင်နိုင်သည်
                        st.rerun()
                    except Exception as e:
                        st.error("❌ REJECT FAILED")
                        st.error(str(e))

        st.markdown("---")
