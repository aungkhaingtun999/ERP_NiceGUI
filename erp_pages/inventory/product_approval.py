"""
erp_pages/inventory/product_approval.py

ERP ENTERPRISE PRODUCT APPROVAL QUEUE v5.0
------------------------------------------------------------
LIST VIEW
SELECT MULTIPLE
SELECT ALL
BATCH APPROVAL
DETAIL VIEW
REJECT
MAKER-CHECKER
SELF-APPROVAL PROTECTION
COMPLETE DATA VALIDATION
MOBILE READY

IMPORTANT DATABASE NOTE
------------------------------------------------------------
product_create_requests DOES NOT HAVE requested_at.

Use:
    created_at

NOT:
    requested_at

BATCH APPROVAL RPC:
    approve_product_create_batch_rpc(
        p_request_ids bigint[],
        p_checker_id uuid
    )
"""

import time
import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager


# ==============================================================================
# REQUIRED FIELD VALIDATION
# ==============================================================================

def _validate_product_request(req):
    """
    Validate product creation request before Checker approval.

    Required:
        Product Name
        SKU
        Barcode
        Unit
        Opening Qty >= 0
        Purchase Price > 0
        Selling Price / Owner Price > 0
        Warehouse
    """

    product = req.get("product_data") or {}
    missing = []

    # --------------------------------------------------------------------------
    # PRODUCT NAME
    # --------------------------------------------------------------------------

    product_name = str(
        product.get("name") or ""
    ).strip()

    if not product_name:
        missing.append("Product Name")

    # --------------------------------------------------------------------------
    # SKU
    # --------------------------------------------------------------------------

    sku = str(
        product.get("sku") or ""
    ).strip()

    if not sku:
        missing.append("SKU")

    # --------------------------------------------------------------------------
    # BARCODE
    # --------------------------------------------------------------------------

    barcode = str(
        product.get("barcode") or ""
    ).strip()

    if (
        not barcode
        or barcode.lower() in ("none", "null", "nan")
    ):
        missing.append("Barcode")

    # --------------------------------------------------------------------------
    # UNIT
    # --------------------------------------------------------------------------

    unit = str(
        product.get("unit") or ""
    ).strip()

    if not unit:
        missing.append("Unit")

    # --------------------------------------------------------------------------
    # OPENING QTY
    #
    # IMPORTANT:
    # 0 IS VALID.
    #
    # create_product_full() supports initial_qty = 0.
    # Therefore approval must NOT require > 0.
    # --------------------------------------------------------------------------

    try:
        opening_qty = float(
            req.get("initial_qty")
            if req.get("initial_qty") is not None
            else 0
        )
    except (TypeError, ValueError):
        opening_qty = -1

    if opening_qty < 0:
        missing.append("Opening Qty (>= 0)")

    # --------------------------------------------------------------------------
    # PURCHASE PRICE
    # --------------------------------------------------------------------------

    try:
        purchase_price = float(
            product.get("purchase_price") or 0
        )
    except (TypeError, ValueError):
        purchase_price = 0

    if purchase_price <= 0:
        missing.append("Purchase Price (> 0)")

    # --------------------------------------------------------------------------
    # SELLING PRICE
    #
    # CSV / IMPORT may provide:
    #     selling_price
    #
    # New pricing architecture also supports:
    #     owner_selling_price
    #
    # Owner price has priority for validation.
    # --------------------------------------------------------------------------

    owner_price = product.get("owner_selling_price")

    selling_price = product.get("selling_price")

    try:
        if owner_price not in (None, "", 0, "0"):
            effective_selling_price = float(owner_price)
        else:
            effective_selling_price = float(
                selling_price or 0
            )
    except (TypeError, ValueError):
        effective_selling_price = 0

    if effective_selling_price <= 0:
        missing.append(
            "Selling Price / Owner Price (> 0)"
        )

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    warehouse_id = req.get("warehouse_id")

    if warehouse_id in (
        None,
        "",
        0,
        "0",
    ):
        missing.append("Warehouse")

    return missing


# ==============================================================================
# USER LOOKUP
# ==============================================================================

def _get_user_name(user_id, users_cache):
    """Convert UUID -> username."""

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
        or str(user_id)
    )


def _load_users(client):
    """Load users once for UUID -> username lookup."""

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

            uid = user.get("id")

            if uid:
                result[str(uid)] = user

        return result

    except Exception as e:

        st.warning(
            f"⚠️ User lookup failed: {e}"
        )

        return {}


# ==============================================================================
# MONEY FORMAT
# ==============================================================================

def _money(value):

    try:
        return (
            f"{float(value or 0):,.2f} MMK"
        )

    except Exception:

        return "0.00 MMK"


# ==============================================================================
# CACHE REFRESH
# ==============================================================================

def _refresh_inventory_cache():

    CacheManager.bump(
        "product_version"
    )

    CacheManager.bump(
        "inventory_version"
    )

    st.cache_data.clear()


# ==============================================================================
# NOTIFICATIONS
# ==============================================================================

def _notify_error(message):

    st.error(
        f"❌ {message}"
    )

    try:
        st.toast(
            f"❌ {message}",
            icon="❌",
        )
    except Exception:
        pass


def _notify_warning(message):

    st.warning(
        f"⚠️ {message}"
    )

    try:
        st.toast(
            f"⚠️ {message}",
            icon="⚠️",
        )
    except Exception:
        pass


def _notify_success(message):

    st.success(
        f"✅ {message}"
    )

    try:
        st.toast(
            f"✅ {message}",
            icon="✅",
        )
    except Exception:
        pass


# ==============================================================================
# REQUEST STATUS
# ==============================================================================

def _request_status_label(request_valid):

    if request_valid:
        return "🟢 READY"

    return "🔴 INCOMPLETE"


# ==============================================================================
# MAIN APPROVAL QUEUE
# ==============================================================================

def render_product_approval_queue():

    st.subheader(
        "🟡 Product Approval Queue"
    )

    st.caption(
        "Select one or multiple product requests and approve them as a batch."
    )

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================

    current_user = (
        st.session_state.get("user")
    )

    if not current_user:

        _notify_warning(
            "Login required."
        )

        return

    if not isinstance(
        current_user,
        dict,
    ):

        _notify_error(
            "Invalid login session."
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

        _notify_error(
            "Current user ID is missing."
        )

        return

    # ==========================================================================
    # ROLE CHECK
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

    is_checker = (
        role_name in (
            "admin",
            "manager",
        )
        or role_id in (1, 2)
    )

    if not is_checker:

        st.info(
            "🔒 Approval Queue is available only to Admin / Manager."
        )

        return

    # ==========================================================================
    # DATABASE
    # ==========================================================================

    try:

        client = privileged_db()

    except Exception as e:

        _notify_error(
            "Privileged database connection failed."
        )

        st.exception(e)

        return

    # ==========================================================================
    # USERS
    # ==========================================================================

    users_cache = _load_users(
        client
    )

    # ==========================================================================
    # LOAD PENDING REQUESTS
    #
    # IMPORTANT:
    # created_at is the request timestamp.
    #
    # DO NOT USE requested_at.
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

        _notify_error(
            "Failed to load approval queue."
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

        _render_approval_history(
            client=client,
            users_cache=users_cache,
        )

        return

    else:

        st.warning(
            f"🟡 Pending Product Requests: {pending_count}"
        )

    st.markdown("---")

    # ==========================================================================
    # BUILD REQUEST MAP
    # ==========================================================================

    request_map = {}

    for req in requests:

        request_id = req.get(
            "id"
        )

        if request_id is not None:

            request_map[
                int(request_id)
            ] = req

    # ==========================================================================
    # BATCH APPROVAL SECTION
    # ==========================================================================

    st.markdown(
        "### 📦 Batch Approval"
    )

    st.caption(
        "Select multiple READY requests. "
        "The system will approve them through the database batch RPC."
    )

    # ==========================================================================
    # SELECT ALL
    # ==========================================================================

    select_all_key = (
        "product_approval_select_all"
    )

    select_all = st.checkbox(
        "☑️ SELECT ALL READY REQUESTS",
        key=select_all_key,
    )

    selected_ids = []

    # ==========================================================================
    # REQUEST TABLE / CHECKBOXES
    # ==========================================================================

    st.markdown(
        "#### 📋 Pending Requests"
    )

    for req in requests:

        request_id = req.get(
            "id"
        )

        if request_id is None:
            continue

        product = (
            req.get("product_data")
            or {}
        )

        product_name = str(
            product.get("name")
            or "-"
        )

        sku = str(
            product.get("sku")
            or "-"
        )

        requester_id = (
            req.get("requested_by")
        )

        requester_name = (
            _get_user_name(
                requester_id,
                users_cache,
            )
        )

        missing_fields = (
            _validate_product_request(
                req
            )
        )

        request_valid = (
            len(missing_fields) == 0
        )

        is_own_request = (
            str(requester_id)
            == str(current_user_id)
        )

        # ----------------------------------------------------------------------
        # SELF APPROVAL
        # ----------------------------------------------------------------------

        if is_own_request:

            st.warning(
                f"🚫 #{request_id} | "
                f"{product_name} | "
                f"SKU: {sku} | "
                f"Maker: {requester_name} | "
                f"SELF-APPROVAL BLOCKED"
            )

            continue

        # ----------------------------------------------------------------------
        # INVALID REQUEST
        # ----------------------------------------------------------------------

        if not request_valid:

            with st.expander(
                f"🔴 #{request_id} | {product_name} | SKU: {sku}"
            ):

                st.write(
                    "Approval blocked."
                )

                st.write(
                    "Missing / Invalid:"
                )

                for field in missing_fields:

                    st.write(
                        f"❌ {field}"
                    )

            continue

        # ----------------------------------------------------------------------
        # READY CHECKBOX
        # ----------------------------------------------------------------------

        checkbox_key = (
            f"product_approval_select_{request_id}"
        )

        checked = st.checkbox(
            f"#{request_id} | "
            f"{product_name} | "
            f"SKU: {sku} | "
            f"Maker: {requester_name} | "
            f"🟢 READY",
            value=select_all,
            key=checkbox_key,
        )

        if checked:

            selected_ids.append(
                int(request_id)
            )

    # ==========================================================================
    # SELECTED COUNT
    # ==========================================================================

    st.markdown("---")

    st.info(
        f"📌 Selected Requests: "
        f"**{len(selected_ids)}** / {pending_count}"
    )

    # ==========================================================================
    # BATCH APPROVE BUTTON
    # ==========================================================================

    batch_col1, batch_col2 = st.columns(
        2
    )

    with batch_col1:

        approve_batch = st.button(
            "✅ APPROVE SELECTED BATCH",
            type="primary",
            use_container_width=True,
            disabled=(
                len(selected_ids) == 0
            ),
            key="approve_selected_product_batch",
        )

    with batch_col2:

        clear_selection = st.button(
            "🔄 CLEAR SELECTION",
            use_container_width=True,
            key="clear_product_batch_selection",
        )

    if clear_selection:

        for req in requests:

            request_id = req.get(
                "id"
            )

            if request_id is not None:

                key = (
                    f"product_approval_select_{request_id}"
                )

                if key in st.session_state:

                    st.session_state[key] = False

        st.session_state[
            select_all_key
        ] = False

        st.rerun()

    # ==========================================================================
    # EXECUTE BATCH APPROVAL
    # ==========================================================================

    if approve_batch:

        _approve_batch(
            client=client,
            request_ids=selected_ids,
            current_user_id=current_user_id,
            current_username=current_username,
            request_map=request_map,
            users_cache=users_cache,
        )

    # ==========================================================================
    # SINGLE REQUEST DETAIL
    # ==========================================================================

    st.markdown("---")

    st.markdown(
        "### 🔎 Request Detail"
    )

    option_labels = []

    detail_map = {}

    for req in requests:

        request_id = req.get(
            "id"
        )

        product = (
            req.get("product_data")
            or {}
        )

        product_name = str(
            product.get("name")
            or "-"
        )

        sku = str(
            product.get("sku")
            or "-"
        )

        missing_fields = (
            _validate_product_request(
                req
            )
        )

        status_label = (
            _request_status_label(
                len(missing_fields) == 0
            )
        )

        requester_name = (
            _get_user_name(
                req.get("requested_by"),
                users_cache,
            )
        )

        label = (
            f"#{request_id} | "
            f"{product_name} | "
            f"SKU: {sku} | "
            f"{status_label} | "
            f"Maker: {requester_name}"
        )

        option_labels.append(
            label
        )

        detail_map[
            label
        ] = req

    if option_labels:

        selected_label = st.selectbox(
            "Select Product Request",
            option_labels,
            key="product_approval_selected_request",
        )

        selected_request = (
            detail_map.get(
                selected_label
            )
        )

        if selected_request:

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

    _render_approval_history(
        client=client,
        users_cache=users_cache,
    )


# ==============================================================================
# BATCH APPROVAL
# ==============================================================================

def _approve_batch(
    client,
    request_ids,
    current_user_id,
    current_username,
    request_map,
    users_cache,
):
    """
    Approve multiple product creation requests.

    RPC:
        approve_product_create_batch_rpc(
            p_request_ids bigint[],
            p_checker_id uuid
        )
    """

    if not request_ids:

        _notify_warning(
            "No product requests selected."
        )

        return

    # ==========================================================================
    # FINAL SECURITY VALIDATION
    # ==========================================================================

    clean_ids = []

    blocked_self = []

    invalid_ids = []

    for request_id in request_ids:

        req = request_map.get(
            int(request_id)
        )

        if not req:

            invalid_ids.append(
                int(request_id)
            )

            continue

        requester_id = req.get(
            "requested_by"
        )

        # ----------------------------------------------------------------------
        # SELF APPROVAL
        # ----------------------------------------------------------------------

        if (
            str(requester_id)
            == str(current_user_id)
        ):

            blocked_self.append(
                int(request_id)
            )

            continue

        # ----------------------------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------------------------

        missing_fields = (
            _validate_product_request(
                req
            )
        )

        if missing_fields:

            invalid_ids.append(
                int(request_id)
            )

            continue

        clean_ids.append(
            int(request_id)
        )

    # ==========================================================================
    # NOTHING APPROVABLE
    # ==========================================================================

    if not clean_ids:

        _notify_error(
            "No selected requests are eligible for approval."
        )

        if blocked_self:

            st.warning(
                "🚫 Self-approval blocked for Request IDs: "
                + ", ".join(
                    str(x)
                    for x in blocked_self
                )
            )

        if invalid_ids:

            st.warning(
                "🔴 Invalid / incomplete Request IDs: "
                + ", ".join(
                    str(x)
                    for x in invalid_ids
                )
            )

        return

    # ==========================================================================
    # SHOW BATCH CONFIRMATION
    # ==========================================================================

    st.markdown("---")

    st.markdown(
        f"### 🚀 Approving {len(clean_ids)} Request(s)"
    )

    with st.expander(
        "🔎 Selected Request IDs"
    ):

        st.write(
            clean_ids
        )

    # ==========================================================================
    # CALL BATCH RPC
    # ==========================================================================

    try:

        response = (
            client
            .rpc(
                "approve_product_create_batch_rpc",
                {
                    "p_request_ids": clean_ids,
                    "p_checker_id": str(
                        current_user_id
                    ),
                },
            )
            .execute()
        )

        result = response.data

        # ----------------------------------------------------------------------
        # NORMALIZE RESPONSE
        # ----------------------------------------------------------------------

        if isinstance(
            result,
            list,
        ):

            result = (
                result[0]
                if result
                else None
            )

        if not isinstance(
            result,
            dict,
        ):

            _notify_error(
                "BATCH APPROVAL FAILED — Invalid RPC response."
            )

            st.code(
                str(result)
            )

            return

        # ==========================================================================
        # RPC RESULT
        # ==========================================================================

        status = result.get(
            "status"
        )

        success = result.get(
            "success",
            False,
        )

        approved = result.get(
            "approved",
            0,
        )

        failed = result.get(
            "failed",
            0,
        )

        total = result.get(
            "total",
            len(clean_ids),
        )

        message = result.get(
            "message",
            "",
        )

        # ==========================================================================
        # SUCCESS
        # ==========================================================================

        if (
            success
            and str(status).upper()
            == "APPROVED"
        ):

            _notify_success(
                f"Batch approval completed: "
                f"{approved}/{total} approved."
            )

            st.success(
                f"""
🎉 BATCH APPROVAL COMPLETED

Checker       : {current_username}
Total         : {total}
Approved      : {approved}
Failed        : {failed}
Status        : APPROVED

✅ Product creation requests have been processed.
"""
            )

            # ------------------------------------------------------------------
            # RPC DETAIL
            # ------------------------------------------------------------------

            results = result.get(
                "results"
            )

            if results:

                with st.expander(
                    "📋 Approval Results"
                ):

                    for item in results:

                        request_id = (
                            item.get(
                                "request_id",
                                "-",
                            )
                        )

                        product_id = (
                            item.get(
                                "product_id",
                                "-",
                            )
                        )

                        item_status = (
                            item.get(
                                "status",
                                "-",
                            )
                        )

                        product_name = "-"

                        req = request_map.get(
                            int(request_id)
                        )

                        if req:

                            product_data = (
                                req.get(
                                    "product_data"
                                )
                                or {}
                            )

                            product_name = (
                                product_data.get(
                                    "name"
                                )
                                or "-"
                            )

                        if (
                            str(item_status).upper()
                            == "APPROVED"
                        ):

                            st.write(
                                f"✅ Request #{request_id} "
                                f"| {product_name} "
                                f"| Product ID: {product_id}"
                            )

                        else:

                            st.error(
                                f"❌ Request #{request_id} "
                                f"| {item.get('message', '-')}"
                            )

            # ------------------------------------------------------------------
            # CACHE
            # ------------------------------------------------------------------

            _refresh_inventory_cache()

            # ------------------------------------------------------------------
            # RERUN
            # ------------------------------------------------------------------

            time.sleep(
                0.8
            )

            st.rerun()

            return

        # ==========================================================================
        # PARTIAL / FAILURE
        # ==========================================================================

        if success:

            _notify_warning(
                f"Batch completed with status: {status}"
            )

        else:

            _notify_error(
                "BATCH APPROVAL FAILED"
            )

        st.warning(
            message
            or "Unknown batch approval result."
        )

        with st.expander(
            "🔎 Batch RPC Response"
        ):

            st.json(
                result
            )

    except Exception as e:

        _notify_error(
            "BATCH APPROVAL FAILED — Database / RPC Error"
        )

        st.exception(e)


# ==============================================================================
# SELECTED REQUEST DETAIL
# ==============================================================================

def _render_selected_request(
    client,
    request,
    users_cache,
    current_user_id,
    current_username,
):

    request_id = request.get(
        "id"
    )

    product = (
        request.get(
            "product_data"
        )
        or {}
    )

    requester_id = (
        request.get(
            "requested_by"
        )
    )

    requester_name = (
        _get_user_name(
            requester_id,
            users_cache,
        )
    )

    # ==========================================================================
    # VALIDATION
    # ==========================================================================

    missing_fields = (
        _validate_product_request(
            request
        )
    )

    request_valid = (
        len(missing_fields) == 0
    )

    # ==========================================================================
    # DETAIL PANEL
    # ==========================================================================

    st.markdown("---")

    st.markdown(
        f"### 📝 Request #{request_id}"
    )

    # ==========================================================================
    # STATUS
    # ==========================================================================

    if request_valid:

        st.success(
            "🟢 STATUS: READY FOR CHECKER APPROVAL"
        )

    else:

        st.error(
            "🔴 STATUS: INCOMPLETE DATA — APPROVAL BLOCKED"
        )

        st.warning(
            "⚠️ Required product information is incomplete."
        )

        st.markdown(
            "**❗ Missing / Invalid Required Fields:**"
        )

        for field in missing_fields:

            st.write(
                f"• ❌ {field}"
            )

    # ==========================================================================
    # PRODUCT DETAILS
    # ==========================================================================

    with st.container(
        border=True
    ):

        st.markdown(
            "#### 📦 Product Information"
        )

        c1, c2 = st.columns(
            2
        )

        with c1:

            st.write(
                f"**Product:** "
                f"{product.get('name') or '-'}"
            )

            st.write(
                f"**SKU:** "
                f"{product.get('sku') or '-'}"
            )

            barcode = (
                product.get(
                    "barcode"
                )
            )

            st.write(
                f"**Barcode:** "
                f"{barcode or '❌ NOT PROVIDED'}"
            )

            st.write(
                f"**Unit:** "
                f"{product.get('unit') or '-'}"
            )

        with c2:

            opening_qty = (
                request.get(
                    "initial_qty"
                )
            )

            if opening_qty is None:

                opening_qty_display = "0"

            else:

                opening_qty_display = str(
                    opening_qty
                )

            st.write(
                f"**Opening Qty:** "
                f"{opening_qty_display}"
            )

            st.write(
                f"**Purchase Price:** "
                f"{_money(product.get('purchase_price'))}"
            )

            owner_price = (
                product.get(
                    "owner_selling_price"
                )
            )

            selling_price = (
                product.get(
                    "selling_price"
                )
            )

            if owner_price not in (
                None,
                "",
                0,
                "0",
            ):

                display_selling_price = (
                    owner_price
                )

            else:

                display_selling_price = (
                    selling_price
                )

            st.write(
                f"**Selling / Owner Price:** "
                f"{_money(display_selling_price)}"
            )

            st.write(
                f"**Warehouse:** "
                f"{request.get('warehouse_id') or '❌ NOT PROVIDED'}"
            )

    # ==========================================================================
    # REQUEST INFORMATION
    # ==========================================================================

    with st.container(
        border=True
    ):

        st.markdown(
            "#### 👤 Request Information"
        )

        st.write(
            f"**Requested By:** `{requester_name}`"
        )

        st.caption(
            f"Requested User ID: {requester_id}"
        )

        # IMPORTANT:
        # created_at is the correct timestamp.
        # requested_at DOES NOT EXIST.

        st.write(
            f"**Created At:** "
            f"{request.get('created_at', '-')}"
        )

    # ==========================================================================
    # SELF APPROVAL PROTECTION
    # ==========================================================================

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
            "cannot approve his own request."
        )

        st.caption(
            "Another Admin / Manager must approve this request."
        )

        st.markdown("---")

        st.info(
            "ℹ️ Approval is disabled because this request belongs to you."
        )

        _render_reject_button(
            client=client,
            request=request,
        )

        return

    # ==========================================================================
    # INVALID DATA
    # ==========================================================================

    if not request_valid:

        st.error(
            "🚫 APPROVAL DISABLED"
        )

        st.info(
            "This request cannot be approved until all required product data is complete."
        )

        st.caption(
            "The Maker must submit a complete product request."
        )

        st.markdown("---")

        _render_reject_button(
            client=client,
            request=request,
        )

        return

    # ==========================================================================
    # INDIVIDUAL APPROVAL
    #
    # Uses the SAME batch RPC with one ID.
    # Therefore there is only ONE approval path.
    # ==========================================================================

    st.markdown("---")

    st.markdown(
        "#### ⚙️ Approval Action"
    )

    b1, b2 = st.columns(
        2
    )

    with b1:

        if st.button(
            "✅ APPROVE REQUEST",
            key=f"approve_product_{request_id}",
            use_container_width=True,
        ):

            _approve_batch(
                client=client,
                request_ids=[
                    int(request_id)
                ],
                current_user_id=current_user_id,
                current_username=current_username,
                request_map={
                    int(request_id): request
                },
                users_cache=users_cache,
            )

    with b2:

        if st.button(
            "❌ REJECT REQUEST",
            key=f"reject_product_{request_id}",
            use_container_width=True,
        ):

            _reject_request(
                client=client,
                request=request,
            )


# ==============================================================================
# REJECT BUTTON
# ==============================================================================

def _render_reject_button(
    client,
    request,
):

    request_id = request.get(
        "id"
    )

    if st.button(
        "❌ REJECT REQUEST",
        key=f"reject_product_detail_{request_id}",
        use_container_width=True,
    ):

        _reject_request(
            client=client,
            request=request,
        )


# ==============================================================================
# REJECT REQUEST
# ==============================================================================

def _reject_request(
    client,
    request,
):

    request_id = request.get(
        "id"
    )

    try:

        user_info = (
            st.session_state.get(
                "user",
                {}
            )
        )

        user_id_val = (
            user_info.get(
                "id"
            )
        )

        (
            client
            .table(
                "product_create_requests"
            )
            .update(
                {
                    "status": "REJECTED",
                    "rejected_by": (
                        str(user_id_val)
                        if user_id_val
                        else None
                    ),
                    "rejected_at": (
                        "now()"
                    ),
                }
            )
            .eq(
                "id",
                request_id,
            )
            .execute()
        )

        _notify_success(
            f"Request #{request_id} rejected successfully."
        )

        _refresh_inventory_cache()

        time.sleep(
            0.7
        )

        st.rerun()

    except Exception as e:

        _notify_error(
            "REJECT FAILED"
        )

        st.exception(e)


# ==============================================================================
# APPROVAL HISTORY
# ==============================================================================

def _render_approval_history(
    client,
    users_cache,
):

    st.markdown("---")

    st.subheader(
        "📜 Recent Approval History"
    )

    try:

        history_response = (
            client
            .table(
                "product_create_requests"
            )
            .select(
                "id,"
                "status,"
                "approved_by,"
                "rejected_by,"
                "approved_at,"
                "rejected_at,"
                "created_at,"
                "product_data"
            )
            .neq(
                "status",
                "PENDING",
            )
            .order(
                "id",
                desc=True,
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

        if not history:

            st.info(
                "No approval history found."
            )

            return

        history_labels = []

        history_map = {}

        for item in history:

            request_id = item.get(
                "id"
            )

            status = item.get(
                "status"
            )

            product_data = (
                item.get(
                    "product_data"
                )
                or {}
            )

            product_name = (
                product_data.get(
                    "name"
                )
                or "-"
            )

            icon = (
                "✅"
                if status == "APPROVED"
                else "❌"
            )

            label = (
                f"{icon} Request #{request_id} "
                f"| {product_name} "
                f"| {status}"
            )

            history_labels.append(
                label
            )

            history_map[
                label
            ] = item

        selected_history_label = (
            st.selectbox(
                "Select History Record",
                history_labels,
                key="product_approval_history_selected",
            )
        )

        selected_history = (
            history_map.get(
                selected_history_label
            )
        )

        if not selected_history:
            return

        product_data = (
            selected_history.get(
                "product_data"
            )
            or {}
        )

        product_name = (
            product_data.get(
                "name"
            )
            or "-"
        )

        status = (
            selected_history.get(
                "status"
            )
        )

        approved_by_name = (
            _get_user_name(
                selected_history.get(
                    "approved_by"
                ),
                users_cache,
            )
        )

        rejected_by_name = (
            _get_user_name(
                selected_history.get(
                    "rejected_by"
                ),
                users_cache,
            )
        )

        with st.container(
            border=True
        ):

            if status == "APPROVED":

                st.success(
                    f"✅ APPROVED — "
                    f"Request #{selected_history.get('id')}"
                )

                st.write(
                    f"**Product:** "
                    f"{product_name}"
                )

                st.write(
                    f"**Approved By:** "
                    f"{approved_by_name}"
                )

                st.write(
                    f"**Approved At:** "
                    f"{selected_history.get('approved_at')}"
                )

                st.caption(
                    f"Created At: "
                    f"{selected_history.get('created_at', '-')}"
                )

            else:

                st.error(
                    f"❌ REJECTED — "
                    f"Request #{selected_history.get('id')}"
                )

                st.write(
                    f"**Product:** "
                    f"{product_name}"
                )

                st.write(
                    f"**Rejected By:** "
                    f"{rejected_by_name}"
                )

                st.write(
                    f"**Rejected At:** "
                    f"{selected_history.get('rejected_at')}"
                )

                st.caption(
                    f"Created At: "
                    f"{selected_history.get('created_at', '-')}"
                )

    except Exception as e:

        st.warning(
            f"⚠️ Approval history load failed: {e}"
        )


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "render_product_approval_queue"
]
