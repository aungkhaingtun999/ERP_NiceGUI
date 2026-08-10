# ==============================================================================
# erp_pages/inventory/product_create.py
#
# ERP ENTERPRISE INVENTORY PRODUCT CREATE v2.3
#
# Maker Checker Request Only
# Direct Product Creation DISABLED
#
# UI STATE FIX:
# Submit
#  ↓
# Validation Failure
#  ↓
# WARNING / ERROR
#  ↓
# Form Data PRESERVED
#
# Clear Form
#  ↓
# Explicitly Clear Fields
#
# IMPORTANT:
# This module NEVER calls create_product_full().
# Actual product / stock / batch / cost layer creation happens
# only after Maker-Checker approval.
# ==============================================================================

import streamlit as st
from erp_core.context import CacheManager
from erp_core import privileged_db

# ==============================================================================
# SESSION STATE HELPERS
# ==============================================================================

_FORM_KEYS = [
    "product_create_name",
    "product_create_sku",
    "product_create_barcode",
    "product_create_purchase_price",
    "product_create_minimum_stock",
    "product_create_unit",
    "product_create_initial_qty",
    "product_create_owner_price",
]

def _clear_product_create_form():
    """
    Explicitly clear Add Product form state.

    IMPORTANT:
    This function is called ONLY when the user presses the Clear Form button.
    Validation failure and Submit do NOT call this.
    """
    for key in _FORM_KEYS:
        st.session_state.pop(key, None)

def _init_product_create_state():
    """
    Initialize stable session-state defaults.

    Using explicit widget keys prevents Streamlit reruns from
    unexpectedly losing user-entered values.
    """
    defaults = {
        "product_create_name": "",
        "product_create_sku": "",
        "product_create_barcode": "",
        "product_create_purchase_price": 0.0,
        "product_create_minimum_stock": 5,
        "product_create_unit": "pcs",
        "product_create_initial_qty": 0,
        "product_create_owner_price": 0.0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ==============================================================================
# PRODUCT CREATE
# ==============================================================================

def render_product_create(
    db_client,
    pricing_service,
    warehouse_id,
):
    """
    Render Maker-Checker Product Creation Request UI.

    IMPORTANT:
    This page NEVER calls create_product_full().
    It only calls: request_product_create_rpc()
    Actual product creation happens only after approval.
    """
    st.subheader("➕ Add New Product")

    # ==========================================================================
    # CURRENT ERP USER
    # ==========================================================================
    current_user = st.session_state.get("user")
    if not current_user:
        st.error("❌ Login session not found.")
        st.stop()

    if not isinstance(current_user, dict):
        st.error("❌ Invalid login session.")
        st.stop()

    current_user_id = current_user.get("id")
    current_username = current_user.get("username", "Unknown User")

    if not current_user_id:
        st.error("❌ Current user ID is missing.")
        st.stop()

    # ==========================================================================
    # INITIALIZE FORM STATE
    # ==========================================================================
    _init_product_create_state()

    # ==========================================================================
    # CLEAR BUTTON
    #
    # IMPORTANT:
    # Only this button clears the form.
    # ==========================================================================
    clear_col, info_col = st.columns([1, 3])

    with clear_col:
        clear_form = st.button(
            "🧹 Clear Form",
            key="product_create_clear_button",
            use_container_width=True,
        )

    with info_col:
        st.caption("⚠️ Form data will remain until you explicitly press 'Clear Form'.")

    if clear_form:
        _clear_product_create_form()
        st.success("🧹 Product form cleared.")
        st.rerun()

    # ==========================================================================
    # PRODUCT REQUEST FORM
    #
    # IMPORTANT:
    # clear_on_submit MUST be False.
    # Otherwise Streamlit automatically clears all widgets immediately
    # after the Submit button is pressed, including validation failures.
    # ==========================================================================
    with st.form("add_product_form", clear_on_submit=False):
        c1, c2 = st.columns(2)

        # ======================================================================
        # LEFT COLUMN
        # ======================================================================
        with c1:
            name = st.text_input(
                "Product Name *",
                key="product_create_name",
            )
            sku = st.text_input(
                "SKU *",
                key="product_create_sku",
            )
            purchase_price = st.number_input(
                "Purchase Cost",
                min_value=0.0,
                value=0.0,
                step=0.01,
                key="product_create_purchase_price",
            )
            minimum_stock = st.number_input(
                "Minimum Stock",
                min_value=0,
                value=5,
                step=1,
                key="product_create_minimum_stock",
            )

        # ======================================================================
        # RIGHT COLUMN
        # ======================================================================
        with c2:
            barcode = st.text_input(
                "Barcode",
                key="product_create_barcode",
            )
            unit = st.selectbox(
                "Unit",
                [
                    "pcs",
                    "kg",
                    "box",
                ],
                key="product_create_unit",
            )
            initial_qty = st.number_input(
                "Initial Stock Qty",
                min_value=0,
                value=0,
                step=1,
                key="product_create_initial_qty",
            )
            owner_price = st.number_input(
                "Owner Selling Price (Main)",
                min_value=0.0,
                value=0.0,
                step=0.01,
                key="product_create_owner_price",
            )

        # ======================================================================
        # PRICING PREVIEW
        # ======================================================================
        final_price = float(owner_price) if owner_price > 0 else float(purchase_price)
        markup = 0.0

        if purchase_price > 0:
            try:
                # ------------------------------------------------------------------
                # OWNER PRICE HAS PRIORITY
                # ------------------------------------------------------------------
                if owner_price > 0:
                    final_price = float(owner_price)
                # ------------------------------------------------------------------
                # PRICING SERVICE
                # ------------------------------------------------------------------
                else:
                    result = pricing_service.calculate_selling_price(
                        cost=purchase_price,
                        product_id=None,
                    )
                    if isinstance(result, dict):
                        final_price = float(
                            result.get("selling_price", purchase_price) or purchase_price
                        )
                    elif isinstance(result, (int, float)):
                        final_price = float(result)

                # ------------------------------------------------------------------
                # MARKUP
                # ------------------------------------------------------------------
                if purchase_price > 0:
                    markup = ((final_price - purchase_price) / purchase_price) * 100

                # ------------------------------------------------------------------
                # PRICING PREVIEW
                # ------------------------------------------------------------------
                st.info(
                    f"""
💰 **Pricing Preview**
* Cost: {purchase_price:,.2f} MMK
* Markup: {markup:,.2f} %
* Selling Price: {final_price:,.2f} MMK
"""
                )

            except Exception as e:
                st.warning(f"Pricing Preview Error : {e}")

        # ======================================================================
        # SUBMIT
        # ======================================================================
        submit = st.form_submit_button(
            "📝 Submit Product Request",
            use_container_width=True,
        )

    # ==========================================================================
    # NO SUBMIT
    #
    # IMPORTANT:
    # Do NOT clear anything here.
    # ==========================================================================
    if not submit:
        return

    # ==========================================================================
    # VALIDATION
    #
    # IMPORTANT:
    # Do NOT call st.rerun().
    # Do NOT clear session state.
    # Returning from this function preserves the entered values.
    # ==========================================================================
    if not name.strip():
        st.warning("⚠️ Product Name is required.")
        return

    if not sku.strip():
        st.warning("⚠️ SKU is required.")
        return

    if purchase_price < 0:
        st.warning("⚠️ Purchase Cost cannot be negative.")
        return

    if initial_qty < 0:
        st.warning("⚠️ Initial Stock cannot be negative.")
        return

    if warehouse_id is None:
        st.warning("⚠️ Warehouse is required.")
        return

    # ==========================================================================
    # PRODUCT PAYLOAD
    # ==========================================================================
    payload = {
        "name": name.strip(),
        "sku": sku.strip(),
        "barcode": barcode.strip() if barcode else None,
        "purchase_price": float(purchase_price),
        "selling_price": float(final_price),
        "owner_selling_price": float(owner_price) if owner_price > 0 else None,
        "final_selling_price": float(final_price),
        "price_source": "OWNER_PRICE" if owner_price > 0 else "PRICING_SERVICE",
        "unit": unit,
        "minimum_stock": int(minimum_stock),
        "category_id": 1,
    }

    # ==========================================================================
    # MAKER-CHECKER RPC
    #
    # IMPORTANT:
    # DO NOT call:
    # create_product_full()
    #
    # This RPC ONLY creates:
    # product_create_requests
    #
    # Actual:
    # products
    # warehouse_stock
    # inventory_batches
    # inventory_cost_layers
    # are created only after approval.
    # ==========================================================================
    try:
        server_db = privileged_db()
        response = (
            server_db.rpc(
                "request_product_create_rpc",
                {
                    "p_product_data": payload,
                    "p_warehouse_id": int(warehouse_id),
                    "p_initial_qty": int(initial_qty),
                    "p_reason": "Product creation request from Inventory UI",
                    "p_requested_by": current_user_id,
                },
            )
            .execute()
        )

        # ======================================================================
        # RPC RESPONSE
        # ======================================================================
        result = response.data

        # ----------------------------------------------------------------------
        # Supabase RPC may return a list
        # ----------------------------------------------------------------------
        if isinstance(result, list):
            result = result[0] if result else None

        # ----------------------------------------------------------------------
        # Validate response
        # ----------------------------------------------------------------------
        if not isinstance(result, dict):
            st.error("❌ Invalid response from request_product_create_rpc.")
            return

        # ==========================================================================
        # SUCCESS
        # ==========================================================================
        if result.get("success"):
            request_id = result.get("request_id")
            status = result.get("status", "PENDING")
            requester_role = result.get("requester_role", "Unknown")

            st.success("📝 Product Request Submitted Successfully")
            st.info(
                f"""
* **Request ID**: {request_id}
* **Status**: {status}
* **Requested By**: {current_username}
* **Requester Role**: {requester_role}
* **Initial Stock**: {initial_qty}
* **Selling Price**: {final_price:,.2f} MMK
* **Warehouse ID**: {warehouse_id}

⚠️ **Product, stock, batch and cost layer are NOT created yet.**
Admin or Manager approval is required.

💡 Form data has been preserved. Press 🧹 Clear Form when you want to enter another product.
"""
            )

            # ==================================================================
            # CACHE INVALIDATION
            #
            # IMPORTANT:
            # Do NOT st.rerun().
            # The current form must remain visible.
            # ==================================================================
            CacheManager.bump("inventory_version")
            CacheManager.bump("product_version")

            # ------------------------------------------------------------------
            # Do NOT call:
            # st.cache_data.clear()
            # here unless the entire application specifically requires it.
            # Cache version bumps are sufficient for the inventory workflow.
            # ------------------------------------------------------------------
            return

        # ==========================================================================
        # RPC BUSINESS FAILURE
        # ==========================================================================
        error_status = result.get("status", "ERROR")
        error_message = result.get("message", "Product request failed.")

        st.error(f"❌ [{error_status}] {error_message}")

        # ----------------------------------------------------------------------
        # Optional debug information
        # ----------------------------------------------------------------------
        if result.get("requested_by"):
            st.caption("Requested By: " + str(result.get("requested_by")))
        if result.get("role_id"):
            st.caption("Role ID: " + str(result.get("role_id")))

        # IMPORTANT:
        # Business failure also preserves the form.
        return

    # ==========================================================================
    # PYTHON / DATABASE EXCEPTION
    # ==========================================================================
    except Exception as e:
        st.error(f"❌ Product Request Error : {e}")
        # IMPORTANT:
        # Exception does NOT clear the form.
        return

# ==============================================================================
# EXPORT
# ==============================================================================
__all__ = ["render_product_create"]
