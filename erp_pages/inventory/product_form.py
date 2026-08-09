# ==============================================================================
# erp_pages/inventory/product_form.py
# ERP ENTERPRISE PRODUCT REQUEST FORM v15.0
#
# MAKER-CHECKER PRODUCT CREATION
# ------------------------------------------------------------------------------
# IMPORTANT
# ------------------------------------------------------------------------------
# create_product_full()
#     ❌ NOT USED
#
# request_product_create_rpc()
#     ✅ USED
#
# Flow:
#
# User
#   ↓
# Product Request
#   ↓
# product_create_requests
#   ↓
# PENDING
#   ↓
# Admin / Manager Approval
#   ↓
# Actual Product Creation
#
# ==============================================================================

import time
import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager


# ==============================================================================
# CONSTANTS
# ==============================================================================

REQUEST_RPC = "request_product_create_rpc"


# ==============================================================================
# HELPER
# ==============================================================================

def _get_current_user():

    user = st.session_state.get("user")

    if not user:
        return None

    if not isinstance(user, dict):
        return None

    return user


# ==============================================================================
# SAVED / REQUEST MESSAGE
# ==============================================================================

def show_saved_message():

    message = st.session_state.pop(
        "product_request_message",
        None
    )

    request_id = st.session_state.pop(
        "product_request_id",
        None
    )

    if message:

        st.success(
            f"🎉 {message}"
        )

        if request_id:

            st.info(
                f"""
### 📝 Product Request Submitted

**Request ID:** `{request_id}`

**Status:** 🟡 `PENDING`

The product has **NOT been created yet**.

Admin / Manager approval is required before:

- Product Master creation
- Warehouse Stock creation
- Inventory Batch creation
- FIFO Cost Layer creation
"""
            )


# ==============================================================================
# NEW PRODUCT REQUEST FORM
# ==============================================================================

def render_new_product_form(
    db_client=None,
    pricing_service=None,
    warehouse_id=None,
    barcode=None,
):
    """
    Render Maker product creation request form.

    IMPORTANT:
        This function does NOT directly create products.

    It creates only:
        product_create_requests

    Actual product creation happens after approval.
    """

    # --------------------------------------------------------------------------
    # Show previous success message
    # --------------------------------------------------------------------------

    show_saved_message()

    # --------------------------------------------------------------------------
    # Current ERP user
    # --------------------------------------------------------------------------

    current_user = _get_current_user()

    if not current_user:

        st.error(
            "❌ Login session not found. Please login again."
        )

        return

    current_user_id = current_user.get("id")

    current_username = current_user.get(
        "username",
        "Unknown User"
    )

    if not current_user_id:

        st.error(
            "❌ Current user ID is missing."
        )

        return

    # --------------------------------------------------------------------------
    # Warehouse validation
    # --------------------------------------------------------------------------

    if warehouse_id is None:

        st.error(
            "❌ Warehouse is required before creating a product request."
        )

        return

    # ==============================================================================
    # HEADER
    # ==============================================================================

    st.subheader(
        "🆕 New Product Registration"
    )

    st.caption(
        "Maker-Checker Mode — Product will remain PENDING until Admin / Manager approval."
    )

    # ==============================================================================
    # REQUEST FORM
    # ==============================================================================

    with st.form(
        "product_request_form_v15",
        clear_on_submit=False,
    ):

        # ----------------------------------------------------------------------
        # PRODUCT BASIC INFORMATION
        # ----------------------------------------------------------------------

        st.markdown("### 📦 Product Information")

        c1, c2 = st.columns(2)

        with c1:

            name = st.text_input(
                "Product Name *",
                placeholder="e.g. Rice / Meat",
            )

            sku = st.text_input(
                "SKU *",
                placeholder="e.g. R1122",
            )

            purchase_price = st.number_input(
                "Purchase Price",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

            minimum_stock = st.number_input(
                "Minimum Stock",
                min_value=0,
                value=5,
                step=1,
            )

        with c2:

            barcode_value = st.text_input(
                "Barcode",
                value=barcode or "",
            )

            unit = st.selectbox(
                "Unit",
                [
                    "pcs",
                    "kg",
                    "box",
                ],
            )

            opening_stock = st.number_input(
                "Opening Stock",
                min_value=0,
                value=0,
                step=1,
            )

            owner_price = st.number_input(
                "👑 Owner Selling Price",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )

        # ----------------------------------------------------------------------
        # BATCH / EXPIRY
        # ----------------------------------------------------------------------

        st.markdown("---")

        st.markdown(
            "### 📦 Batch & Expiry Settings"
        )

        b1, b2 = st.columns(2)

        with b1:

            track_batches = st.checkbox(
                "Track Batch Number",
                value=False,
            )

        with b2:

            track_expiry = st.checkbox(
                "Track Expiry Date",
                value=False,
            )

        shelf_life_days = st.number_input(
            "Default Shelf Life (Days)",
            min_value=0,
            value=0,
            step=1,
        )

        # ----------------------------------------------------------------------
        # PRICING PREVIEW
        # ----------------------------------------------------------------------

        st.markdown("---")

        st.markdown(
            "### 💰 Pricing Preview"
        )

        final_price = float(
            owner_price
            if owner_price > 0
            else purchase_price
        )

        price_source = "PURCHASE_COST"

        markup = 0.0

        if purchase_price > 0:

            try:

                if owner_price > 0:

                    final_price = float(
                        owner_price
                    )

                    price_source = "OWNER_PRICE"

                elif pricing_service is not None:

                    preview = (
                        pricing_service
                        .calculate_selling_price(
                            cost=purchase_price,
                            product_id=None,
                        )
                    )

                    if isinstance(
                        preview,
                        dict,
                    ):

                        final_price = float(
                            preview.get(
                                "selling_price",
                                purchase_price,
                            )
                            or purchase_price
                        )

                        price_source = str(
                            preview.get(
                                "markup_source",
                                "PRICING_SERVICE",
                            )
                            or "PRICING_SERVICE"
                        )

                    elif isinstance(
                        preview,
                        (int, float),
                    ):

                        final_price = float(
                            preview
                        )

                        price_source = "PRICING_SERVICE"

                if purchase_price > 0:

                    markup = (
                        (
                            final_price
                            - purchase_price
                        )
                        / purchase_price
                    ) * 100

            except Exception as e:

                st.warning(
                    f"⚠️ Pricing preview unavailable: {e}"
                )

        p1, p2, p3 = st.columns(3)

        with p1:

            st.metric(
                "Purchase Cost",
                f"{purchase_price:,.2f} MMK",
            )

        with p2:

            st.metric(
                "Markup",
                f"{markup:,.2f} %",
            )

        with p3:

            st.metric(
                "Selling Price",
                f"{final_price:,.2f} MMK",
            )

        # ----------------------------------------------------------------------
        # SUBMIT
        # ----------------------------------------------------------------------

        st.markdown("---")

        submit = st.form_submit_button(
            "📝 Submit Product Request",
            use_container_width=True,
        )

    # ==============================================================================
    # SUBMIT PROCESS
    # ==============================================================================

    if not submit:

        return

    # ==============================================================================
    # VALIDATION
    # ==============================================================================

    if not name.strip():

        st.error(
            "❌ Product Name is required."
        )

        return

    if not sku.strip():

        st.error(
            "❌ SKU is required."
        )

        return

    if purchase_price < 0:

        st.error(
            "❌ Purchase Price cannot be negative."
        )

        return

    if opening_stock < 0:

        st.error(
            "❌ Opening Stock cannot be negative."
        )

        return

    if warehouse_id is None:

        st.error(
            "❌ Warehouse is required."
        )

        return

    # ==============================================================================
    # PAYLOAD
    # ==============================================================================

    payload = {

        "name":
            name.strip(),

        "sku":
            sku.strip(),

        "barcode":
            (
                barcode_value.strip()
                if barcode_value.strip()
                else None
            ),

        "unit":
            unit,

        "purchase_price":
            float(purchase_price),

        "selling_price":
            float(final_price),

        "final_selling_price":
            float(final_price),

        "owner_selling_price":
            (
                float(owner_price)
                if owner_price > 0
                else None
            ),

        "minimum_stock":
            int(minimum_stock),

        "category_id":
            1,

        "price_source":
            price_source,

        "track_batches":
            bool(track_batches),

        "track_expiry":
            bool(track_expiry),

        "shelf_life_days":
            (
                int(shelf_life_days)
                if shelf_life_days > 0
                else None
            ),
    }

    # ==============================================================================
    # VISIBLE PROCESS MESSAGE
    # ==============================================================================

    progress_box = st.empty()

    try:

        progress_box.info(
            "⏳ Submitting Product Request..."
        )

        # ==========================================================================
        # IMPORTANT
        # --------------------------------------------------------------------------
        # ALWAYS use privileged server-side client.
        #
        # NEVER call create_product_full().
        # ==========================================================================

        client = privileged_db()

        # ==========================================================================
        # RPC
        # ==========================================================================

        response = (
            client
            .rpc(
                REQUEST_RPC,
                {
                    "p_product_data":
                        payload,

                    "p_warehouse_id":
                        int(warehouse_id),

                    "p_initial_qty":
                        int(opening_stock),

                    "p_reason":
                        "Product creation request from Inventory UI",

                    "p_requested_by":
                        current_user_id,
                },
            )
            .execute()
        )

        result = response.data

        # ==========================================================================
        # NORMALIZE RESPONSE
        # ==========================================================================

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

            progress_box.empty()

            st.error(
                "❌ Invalid response from Product Request RPC."
            )

            st.code(
                str(result)
            )

            return

        # ==========================================================================
        # SUCCESS
        # ==========================================================================

        if result.get("success"):

            request_id = result.get(
                "request_id"
            )

            progress_box.empty()

            # ----------------------------------------------------------------------
            # VERY VISIBLE SUCCESS MESSAGE
            # ----------------------------------------------------------------------

            st.success(
                "🎉🎉 PRODUCT REQUEST SUBMITTED SUCCESSFULLY 🎉🎉"
            )

            st.markdown(
                f"""
## 🟡 PENDING APPROVAL

### Request ID: `{request_id}`

| Information | Value |
|---|---|
| Product | **{name.strip()}** |
| SKU | **{sku.strip()}** |
| Barcode | **{barcode_value.strip() or "-"}** |
| Opening Stock | **{int(opening_stock)}** |
| Selling Price | **{final_price:,.2f} MMK** |
| Requested By | **{current_username}** |
| Status | 🟡 **PENDING** |

### ⚠️ IMPORTANT

**Product has NOT been created yet.**

The following will be created **ONLY after Admin / Manager approval**:

- ✅ Product Master
- ✅ Warehouse Stock
- ✅ Inventory Batch
- ✅ FIFO Cost Layer

**Request has been safely recorded in the Maker-Checker queue.**
"""
            )

            # ----------------------------------------------------------------------
            # SESSION MESSAGE
            # ----------------------------------------------------------------------

            st.session_state.product_request_message = (
                f"Product request for '{name.strip()}' is now PENDING."
            )

            st.session_state.product_request_id = (
                request_id
            )

            # ----------------------------------------------------------------------
            # CACHE INVALIDATION
            # ----------------------------------------------------------------------

            try:

                CacheManager.bump(
                    "inventory_version"
                )

                CacheManager.bump(
                    "product_version"
                )

            except Exception:

                pass

            try:

                st.cache_data.clear()

            except Exception:

                pass

            # ----------------------------------------------------------------------
            # DO NOT IMMEDIATELY RERUN
            #
            # User must be able to SEE the PENDING notification.
            # ----------------------------------------------------------------------

            st.toast(
                f"🟡 Request #{request_id} is PENDING approval.",
                icon="📝",
            )

            time.sleep(0.5)

            return

        # ==============================================================================
        # RPC BUSINESS FAILURE
        # ==============================================================================

        progress_box.empty()

        status = result.get(
            "status",
            "ERROR",
        )

        message = result.get(
            "message",
            "Product request failed.",
        )

        if status == "DUPLICATE":

            st.error(
                "🚫 DUPLICATE PRODUCT"
            )

            st.warning(
                message
            )

        elif status == "DENIED":

            st.error(
                "🚫 PRODUCT REQUEST DENIED"
            )

            st.warning(
                message
            )

        else:

            st.error(
                "❌ PRODUCT REQUEST FAILED"
            )

            st.warning(
                message
            )

        st.json(
            result
        )

    # ==============================================================================
    # EXCEPTION
    # ==============================================================================

    except Exception as e:

        progress_box.empty()

        st.error(
            "❌ PRODUCT REQUEST ERROR"
        )

        st.exception(e)

        st.warning(
            """
If this error says:

permission denied for function request_product_create_rpc

then check that the Streamlit server is using
SUPABASE_SERVICE_ROLE_KEY and not SUPABASE_KEY.
"""
        )


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "render_new_product_form",
]
