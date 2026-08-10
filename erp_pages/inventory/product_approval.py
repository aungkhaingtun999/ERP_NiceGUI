==============================================================================

erp_pages/inventory/product_approval.py

ERP ENTERPRISE PRODUCT APPROVAL QUEUE v4.0

LIST VIEW + SELECT → DETAIL → ACTION

COMPLETE DATA VALIDATION

MAKER-CHECKER

SELF-APPROVAL PROTECTION

MOBILE READY

==============================================================================

import time
import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager

==============================================================================

REQUIRED FIELD VALIDATION

==============================================================================

def _validate_product_request(req):
    """
    Validate product creation request before Checker approval.

    Required:
      Product Name
      SKU
      Barcode
      Unit
      Opening Qty > 0
      Purchase Price > 0
      Selling Price > 0
      Warehouse
    """
    product = req.get("product_data") or {}
    missing = []

    # --------------------------------------------------------------------------
    # PRODUCT NAME
    # --------------------------------------------------------------------------
    product_name = str(product.get("name") or "").strip()
    if not product_name:
        missing.append("Product Name")

    # --------------------------------------------------------------------------
    # SKU
    # --------------------------------------------------------------------------
    sku = str(product.get("sku") or "").strip()
    if not sku:
        missing.append("SKU")

    # --------------------------------------------------------------------------
    # BARCODE
    # --------------------------------------------------------------------------
    barcode = str(product.get("barcode") or "").strip()
    if not barcode or barcode.lower() in ("none", "null", "nan"):
        missing.append("Barcode")

    # --------------------------------------------------------------------------
    # UNIT
    # --------------------------------------------------------------------------
    unit = str(product.get("unit") or "").strip()
    if not unit:
        missing.append("Unit")

    # --------------------------------------------------------------------------
    # OPENING QTY
    # --------------------------------------------------------------------------
    try:
        opening_qty = float(req.get("initial_qty") or 0)
    except (TypeError, ValueError):
        opening_qty = 0

    if opening_qty <= 0:
        missing.append("Opening Qty (> 0)")

    # --------------------------------------------------------------------------
    # PURCHASE PRICE
    # --------------------------------------------------------------------------
    try:
        purchase_price = float(product.get("purchase_price") or 0)
    except (TypeError, ValueError):
        purchase_price = 0

    if purchase_price <= 0:
        missing.append("Purchase Price (> 0)")

    # --------------------------------------------------------------------------
    # SELLING PRICE
    # --------------------------------------------------------------------------
    try:
        selling_price = float(product.get("selling_price") or 0)
    except (TypeError, ValueError):
        selling_price = 0

    if selling_price <= 0:
        missing.append("Selling Price (> 0)")

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------
    warehouse_id = req.get("warehouse_id")
    if warehouse_id in (None, "", 0, "0"):
        missing.append("Warehouse")

    return missing


==============================================================================

USER LOOKUP

==============================================================================

def _get_user_name(user_id, users_cache):
    """Convert UUID -> username."""
    if not user_id:
        return "Unknown User"
    user = users_cache.get(str(user_id))
    if not user:
        return str(user_id)
    return user.get("username") or user.get("full_name") or str(user_id)


def _load_users(client):
    """Load users once for UUID -> username lookup."""
    try:
        response = (
            client.table("users")
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


==============================================================================

MONEY FORMAT

==============================================================================

def _money(value):
    try:
        return f"{float(value or 0):,.2f} MMK"
    except Exception:
        return "0.00 MMK"


==============================================================================

CACHE REFRESH

==============================================================================

def _refresh_inventory_cache():
    CacheManager.bump("product_version")
    CacheManager.bump("inventory_version")
    st.cache_data.clear()


==============================================================================

NOTIFICATIONS

==============================================================================

def _notify_error(message):
    st.error(f"❌ {message}")
    try:
        st.toast(f"❌ {message}", icon="❌")
    except Exception:
        pass


def _notify_warning(message):
    st.warning(f"⚠️ {message}")
    try:
        st.toast(f"⚠️ {message}", icon="⚠️")
    except Exception:
        pass


def _notify_success(message):
    st.success(f"✅ {message}")
    try:
        st.toast(f"✅ {message}", icon="✅")
    except Exception:
        pass


==============================================================================

REQUEST SUMMARY

==============================================================================

def _request_status_label(request_valid):
    """Return compact status for list view."""
    if request_valid:
        return "🟢 READY"
    return "🔴 INCOMPLETE"


==============================================================================

MAIN APPROVAL QUEUE

==============================================================================

def render_product_approval_queue():
    st.subheader("🟡 Product Approval Queue")
    st.caption("Select a request to view details and perform approval actions.")

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================
    current_user = st.session_state.get("user")
    if not current_user:
        _notify_warning("Login required.")
        return
    if not isinstance(current_user, dict):
        _notify_error("Invalid login session.")
        return

    current_user_id = current_user.get("id")
    current_username = (
        current_user.get("username")
        or current_user.get("full_name")
        or "Unknown User"
    )
    if not current_user_id:
        _notify_error("Current user ID is missing.")
        return

    # ==========================================================================
    # ROLE CHECK
    # ==========================================================================
    role_name = str(current_user.get("role_name", "")).strip().lower()
    role_id = current_user.get("role_id")
    is_checker = role_name in ("admin", "manager") or role_id in (1, 2)

    if not is_checker:
        st.info("🔒 Approval Queue is available only to Admin / Manager.")
        return

    # ==========================================================================
    # DATABASE
    # ==========================================================================
    try:
        client = privileged_db()
    except Exception as e:
        _notify_error("Privileged database connection failed.")
        st.exception(e)
        return

    # ==========================================================================
    # USERS
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
        _notify_error("Failed to load approval queue.")
        st.exception(e)
        return

    # ==========================================================================
    # PENDING COUNT
    # ==========================================================================
    pending_count = len(requests)
    if pending_count == 0:
        st.success("✅ No pending product requests.")
    else:
        st.warning(f"🟡 Pending Product Requests: {pending_count}")

    st.markdown("---")

    # ======================================================================
    # BUILD SELECT OPTIONS
    # ======================================================================
    request_map = {}
    option_labels = []
    for req in requests:
        request_id = req.get("id")
        product = req.get("product_data") or {}
        product_name = str(product.get("name") or "-")
        sku = str(product.get("sku") or "-")
        missing_fields = _validate_product_request(req)
        request_valid = len(missing_fields) == 0
        requester_id = req.get("requested_by")
        requester_name = _get_user_name(requester_id, users_cache)
        status_label = _request_status_label(request_valid)

        label = (
            f"#{request_id} | "
            f"{product_name} | "
            f"SKU: {sku} | "
            f"{status_label} | "
            f"Maker: {requester_name}"
        )
        request_map[label] = req
        option_labels.append(label)

    # ======================================================================
    # REQUEST SELECTOR
    # ======================================================================
    st.markdown("### 📋 Pending Requests")
    if not option_labels:
        st.info("No requests available to select.")
        _render_approval_history(client=client, users_cache=users_cache)
        return

    selected_label = st.selectbox(
        "Select Product Request",
        option_labels,
        key="product_approval_selected_request",
    )
    selected_request = request_map.get(selected_label)

    if not selected_request:
        st.info("Select a product request.")
    else:
        _render_selected_request(
            client=client,
            request=selected_request,
            users_cache=users_cache,
            current_user_id=current_user_id,
            current_username=current_username,
        )

    # ==========================================================================
    # APPROVAL HISTORY
    # ==========================================================================
    _render_approval_history(client=client, users_cache=users_cache)


==============================================================================

SELECTED REQUEST DETAIL

==============================================================================

def _render_selected_request(
    client,
    request,
    users_cache,
    current_user_id,
    current_username,
):
    request_id = request.get("id")
    product = request.get("product_data") or {}
    requester_id = request.get("requested_by")
    requester_name = _get_user_name(requester_id, users_cache)

    # ==========================================================================
    # VALIDATION
    # ==========================================================================
    missing_fields = _validate_product_request(request)
    request_valid = len(missing_fields) == 0

    # ==========================================================================
    # DETAIL PANEL
    # ==========================================================================
    st.markdown("---")
    st.markdown(f"### 📝 Request #{request_id}")

    # ==========================================================================
    # STATUS
    # ==========================================================================
    if request_valid:
        st.success("🟢 STATUS: READY FOR CHECKER APPROVAL")
    else:
        st.error("🔴 STATUS: INCOMPLETE DATA — APPROVAL BLOCKED")
        st.warning("⚠️ Required product information is incomplete.")
        st.markdown("**❗ Missing / Invalid Required Fields:**")
        for field in missing_fields:
            st.write(f"• ❌ {field}")

    # ==========================================================================
    # PRODUCT DETAILS
    # ==========================================================================
    with st.container(border=True):
        st.markdown("#### 📦 Product Information")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Product:** {product.get('name') or '-'}")
            st.write(f"**SKU:** {product.get('sku') or '-'}")
            barcode = product.get("barcode")
            st.write(f"**Barcode:** {barcode or '❌ NOT PROVIDED'}")
            st.write(f"**Unit:** {product.get('unit') or '-'}")
        with c2:
            opening_qty = request.get("initial_qty")
            if opening_qty in (None, "", 0, "0"):
                opening_qty_display = "❌ NOT PROVIDED / INVALID"
            else:
                opening_qty_display = str(opening_qty)
            st.write(f"**Opening Qty:** {opening_qty_display}")
            st.write(f"**Purchase Price:** {_money(product.get('purchase_price'))}")
            st.write(f"**Selling Price:** {_money(product.get('selling_price'))}")
            warehouse_id = request.get("warehouse_id")
            st.write(f"**Warehouse:** {warehouse_id or '❌ NOT PROVIDED'}")

    # ==========================================================================
    # REQUESTER
    # ==========================================================================
    with st.container(border=True):
        st.markdown("#### 👤 Request Information")
        st.write(f"**Requested By:** `{requester_name}`")
        st.caption(f"Requested User ID: {requester_id}")
        st.write(f"**Created At:** {request.get('created_at', '-')}")

    # ==========================================================================
    # SELF APPROVAL PROTECTION
    # ==========================================================================
    is_own_request = str(requester_id) == str(current_user_id)
    if is_own_request:
        st.error("🚫 SELF-APPROVAL BLOCKED")
        st.info(f"Maker '{requester_name}' cannot approve his own request.")
        st.caption("Another Admin / Manager must approve this request.")
        st.markdown("---")
        st.info("ℹ️ Approval is disabled because this request belongs to you.")
        _render_reject_button(client=client, request=request)
        return

    # ==========================================================================
    # INVALID DATA
    # ==========================================================================
    if not request_valid:
        st.error("🚫 APPROVAL DISABLED")
        st.info("This request cannot be approved until all required product data is complete.")
        st.caption("The Maker must submit a complete product request.")
        st.markdown("---")
        _render_reject_button(client=client, request=request)
        return

    # ==========================================================================
    # APPROVE / REJECT
    # ==========================================================================
    st.markdown("---")
    st.markdown("#### ⚙️ Approval Action")
    b1, b2 = st.columns(2)

    # ==========================================================================
    # APPROVE
    # ==========================================================================
    with b1:
        if st.button(
            "✅ APPROVE REQUEST",
            key=f"approve_product_{request_id}",
            use_container_width=True,
        ):
            _approve_request(
                client=client,
                request=request,
                current_user_id=current_user_id,
                current_username=current_username,
                requester_name=requester_name,
            )

    # ==========================================================================
    # REJECT
    # ==========================================================================
    with b2:
        if st.button(
            "❌ REJECT REQUEST",
            key=f"reject_product_{request_id}",
            use_container_width=True,
        ):
            _reject_request(client=client, request=request)


==============================================================================

APPROVE REQUEST

==============================================================================

def _approve_request(
    client,
    request,
    current_user_id,
    current_username,
    requester_name,
):
    request_id = request.get("id")
    product = request.get("product_data") or {}

    # ==========================================================================
    # FINAL VALIDATION
    # ==========================================================================
    latest_missing = _validate_product_request(request)
    if latest_missing:
        _notify_error("Approval blocked. Required product data is incomplete.")
        with st.expander("🔎 Missing Required Fields"):
            for field in latest_missing:
                st.write(f"❌ {field}")
        return

    # ==========================================================================
    # RPC
    # ==========================================================================
    try:
        response = (
            client.rpc(
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

        # ======================================================================
        # INVALID RESPONSE
        # ======================================================================
        if not isinstance(result, dict):
            _notify_error("APPROVAL FAILED")
            st.code(str(result))
            return

        # ======================================================================
        # RPC FAILURE
        # ======================================================================
        if not result.get("success", False):
            _notify_error("APPROVAL FAILED")
            st.warning(f"Status: {result.get('status', 'ERROR')}")
            st.error(result.get("message", "Unknown approval error."))
            with st.expander("🔎 RPC Response"):
                st.json(result)
            return

        # ======================================================================
        # SUCCESS
        # ======================================================================
        approved_request_id = result.get("request_id", request_id)
        product_id = result.get("product_id")
        _notify_success("Product request approved successfully!")
        st.info(
            f"""
🎉 APPROVAL COMPLETED

Request ID : #{approved_request_id}
Product : {product.get('name', '-')}
SKU : {product.get('sku', '-')}
Requested By : {requester_name}
Approved By : {current_username}
Product ID : {product_id or '-'}
Status : APPROVED

✅ Product creation has been authorized.
"""
        )

        _refresh_inventory_cache()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        _notify_error("APPROVAL FAILED — Database / RPC Error")
        st.exception(e)


==============================================================================

REJECT BUTTON

==============================================================================

def _render_reject_button(client, request):
    request_id = request.get("id")
    if st.button(
        "❌ REJECT REQUEST",
        key=f"reject_product_detail_{request_id}",
        use_container_width=True,
    ):
        _reject_request(client=client, request=request)


==============================================================================

REJECT REQUEST

==============================================================================

def _reject_request(client, request):
    request_id = request.get("id")
    try:
        user_info = st.session_state.get("user", {})
        user_id_val = user_info.get("id")
        
        client.table("product_create_requests").update(
            {
                "status": "REJECTED",
                "rejected_by": str(user_id_val) if user_id_val else None,
            }
        ).eq("id", request_id).execute()

        _notify_success(f"Request #{request_id} rejected successfully.")
        CacheManager.bump("product_version")
        CacheManager.bump("inventory_version")
        st.cache_data.clear()
        time.sleep(0.7)
        st.rerun()
    except Exception as e:
        _notify_error("REJECT FAILED")
        st.exception(e)


==============================================================================

APPROVAL HISTORY

==============================================================================

def _render_approval_history(client, users_cache):
    st.markdown("---")
    st.subheader("📜 Recent Approval History")
    try:
        history_response = (
            client.table("product_create_requests")
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
            return

        # ======================================================================
        # HISTORY AS COMPACT LIST
        # ======================================================================
        history_labels = []
        history_map = {}
        for item in history:
            request_id = item.get("id")
            status = item.get("status")
            product_data = item.get("product_data") or {}
            product_name = product_data.get("name") or "-"
            icon = "✅" if status == "APPROVED" else "❌"

            label = f"{icon} Request #{request_id} | {product_name} | {status}"
            history_labels.append(label)
            history_map[label] = item

        # ======================================================================
        # HISTORY SELECT
        # ======================================================================
        selected_history_label = st.selectbox(
            "Select History Record",
            history_labels,
            key="product_approval_history_selected",
        )
        selected_history = history_map.get(selected_history_label)

        if not selected_history:
            return

        # ======================================================================
        # HISTORY DETAIL
        # ======================================================================
        product_data = selected_history.get("product_data") or {}
        product_name = product_data.get("name") or "-"
        status = selected_history.get("status")
        approved_by_name = _get_user_name(
            selected_history.get("approved_by"), users_cache
        )
        rejected_by_name = _get_user_name(
            selected_history.get("rejected_by"), users_cache
        )

        with st.container(border=True):
            if status == "APPROVED":
                st.success(f"✅ APPROVED — Request #{selected_history.get('id')}")
                st.write(f"**Product:** {product_name}")
                st.write(f"**Approved By:** {approved_by_name}")
                st.write(f"**Approved At:** {selected_history.get('approved_at')}")
            else:
                st.error(f"❌ REJECTED — Request #{selected_history.get('id')}")
                st.write(f"**Product:** {product_name}")
                st.write(f"**Rejected By:** {rejected_by_name}")
                st.write(f"**Rejected At:** {selected_history.get('rejected_at')}")
    except Exception as e:
        st.warning(f"⚠️ Approval history load failed: {e}")


==============================================================================

EXPORT

==============================================================================

__all__ = ["render_product_approval_queue"]
