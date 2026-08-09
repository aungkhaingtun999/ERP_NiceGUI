
# ==============================================================================
# erp_pages/inventory/product_create.py
# ERP ENTERPRISE INVENTORY PRODUCT CREATE v2.2 CLEAN
#
# Maker Checker Request Only
# Direct Product Creation DISABLED
#
# Workflow:
#
#   User
#     ↓
#   request_product_create_rpc()
#     ↓
#   product_create_requests
#     ↓
#   PENDING
#     ↓
#   Admin / Manager Approval
#     ↓
#   approve_product_create_rpc()
#     ↓
#   Real Product / Stock / Batch / Cost Layer
# ==============================================================================

import time

import streamlit as st

from erp_core.context import CacheManager
from erp_core import privileged_db


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

    It only calls:

        request_product_create_rpc()

    using the server-side privileged Supabase client.

    Actual product creation happens only after approval.
    """

    st.subheader(
        "➕ Add New Product"
    )

    # ==========================================================================
    # CURRENT ERP USER
    # ==========================================================================

    current_user = st.session_state.get(
        "user"
    )

    if not current_user:

        st.error(
            "❌ Login session not found."
        )

        st.stop()

    # --------------------------------------------------------------------------
    # Validate session object
    # --------------------------------------------------------------------------

    if not isinstance(
        current_user,
        dict
    ):

        st.error(
            "❌ Invalid login session."
        )

        st.stop()

    # --------------------------------------------------------------------------
    # Normalize current user
    # --------------------------------------------------------------------------

    current_user_id = current_user.get(
        "id"
    )

    current_username = current_user.get(
        "username",
        "Unknown User"
    )

    if not current_user_id:

        st.error(
            "❌ Current user ID is missing."
        )

        st.stop()

    # ==========================================================================
    # PRODUCT REQUEST FORM
    # ==========================================================================

    with st.form(
        "add_product_form",
        clear_on_submit=True
    ):

        c1, c2 = st.columns(
            2
        )

        # ======================================================================
        # LEFT COLUMN
        # ======================================================================

        with c1:

            name = st.text_input(
                "Product Name *"
            )

            sku = st.text_input(
                "SKU *"
            )

            purchase_price = st.number_input(
                "Purchase Cost",
                min_value=0.0,
                value=0.0,
                step=0.01,
            )

            minimum_stock = st.number_input(
                "Minimum Stock",
                min_value=0,
                value=5,
                step=1,
            )

        # ======================================================================
        # RIGHT COLUMN
        # ======================================================================

        with c2:

            barcode = st.text_input(
                "Barcode"
            )

            unit = st.selectbox(
                "Unit",
                [
                    "pcs",
                    "kg",
                    "box",
                ],
            )

            initial_qty = st.number_input(
                "Initial Stock Qty",
                min_value=0,
                value=0,
                step=1,
            )

            owner_price = st.number_input(
                "Owner Selling Price (Main)",
                min_value=0.0,
                value=0.0,
                step=0.01,
            )

        # ======================================================================
        # PRICING PREVIEW
        # ======================================================================

        final_price = (
            float(owner_price)
            if owner_price > 0
            else float(purchase_price)
        )

        markup = 0.0

        if purchase_price > 0:

            try:

                # ------------------------------------------------------------------
                # OWNER PRICE HAS PRIORITY
                # ------------------------------------------------------------------

                if owner_price > 0:

                    final_price = float(
                        owner_price
                    )

                # ------------------------------------------------------------------
                # PRICING SERVICE
                # ------------------------------------------------------------------

                else:

                    result = (
                        pricing_service
                        .calculate_selling_price(
                            cost=purchase_price,
                            product_id=None,
                        )
                    )

                    # --------------------------------------------------------------
                    # Pricing Service → dict
                    # --------------------------------------------------------------

                    if isinstance(
                        result,
                        dict
                    ):

                        final_price = float(
                            result.get(
                                "selling_price",
                                purchase_price,
                            )
                            or purchase_price
                        )

                    # --------------------------------------------------------------
                    # Pricing Service → number
                    # --------------------------------------------------------------

                    elif isinstance(
                        result,
                        (int, float)
                    ):

                        final_price = float(
                            result
                        )

                # ------------------------------------------------------------------
                # MARKUP
                # ------------------------------------------------------------------

                if purchase_price > 0:

                    markup = (
                        (
                            final_price
                            - purchase_price
                        )
                        / purchase_price
                    ) * 100

                # ------------------------------------------------------------------
                # PRICING PREVIEW
                # ------------------------------------------------------------------

                st.info(
                    f"""
💰 Pricing Preview

Cost:
{purchase_price:,.2f} MMK

Markup:
{markup:,.2f} %

Selling Price:
{final_price:,.2f} MMK
"""
                )

            except Exception as e:

                st.warning(
                    f"Pricing Preview Error : {e}"
                )

        # ======================================================================
        # SUBMIT
        # ======================================================================

        submit = st.form_submit_button(
            "📝 Submit Product Request",
            use_container_width=True,
        )

        if not submit:

            return

        # ======================================================================
        # SUBMIT PROCESS
        # ======================================================================

        try:

            # ==================================================================
            # VALIDATION
            # ==================================================================

            if not name.strip():

                st.error(
                    "❌ Product Name is required."
                )

                st.stop()

            if not sku.strip():

                st.error(
                    "❌ SKU is required."
                )

                st.stop()

            if purchase_price < 0:

                st.error(
                    "❌ Purchase Cost cannot be negative."
                )

                st.stop()

            if initial_qty < 0:

                st.error(
                    "❌ Initial Stock cannot be negative."
                )

                st.stop()

            if warehouse_id is None:

                st.error(
                    "❌ Warehouse is required."
                )

                st.stop()

            # ==================================================================
            # PRODUCT PAYLOAD
            # ==================================================================

            payload = {

                "name":
                    name.strip(),

                "sku":
                    sku.strip(),

                "barcode":
                    (
                        barcode.strip()
                        if barcode
                        else None
                    ),

                "purchase_price":
                    float(
                        purchase_price
                    ),

                "selling_price":
                    float(
                        final_price
                    ),

                "owner_selling_price":
                    (
                        float(
                            owner_price
                        )
                        if owner_price > 0
                        else None
                    ),

                "final_selling_price":
                    float(
                        final_price
                    ),

                "price_source":
                    (
                        "OWNER_PRICE"
                        if owner_price > 0
                        else "PRICING_SERVICE"
                    ),

                "unit":
                    unit,

                "minimum_stock":
                    int(
                        minimum_stock
                    ),

                "category_id":
                    1,
            }

            # ==================================================================
            # MAKER-CHECKER RPC
            #
            # IMPORTANT:
            #
            # DO NOT call:
            #
            #     create_product_full()
            #
            # This request RPC ONLY creates:
            #
            #     product_create_requests
            #
            # Actual:
            #
            #     products
            #     warehouse_stock
            #     inventory_batches
            #     inventory_cost_layers
            #
            # are created only after approval.
            # ==================================================================

            server_db = privileged_db()

            response = (
                server_db
                .rpc(
                    "request_product_create_rpc",
                    {
                        "p_product_data":
                            payload,

                        "p_warehouse_id":
                            int(
                                warehouse_id
                            ),

                        "p_initial_qty":
                            int(
                                initial_qty
                            ),

                        "p_reason":
                            (
                                "Product creation request "
                                "from Inventory UI"
                            ),

                        "p_requested_by":
                            current_user_id,
                    },
                )
                .execute()
            )

            # ==================================================================
            # RPC RESPONSE
            # ==================================================================

            result = response.data

            # ------------------------------------------------------------------
            # Supabase RPC may return a list
            # ------------------------------------------------------------------

            if isinstance(
                result,
                list
            ):

                result = (
                    result[0]
                    if result
                    else None
                )

            # ------------------------------------------------------------------
            # Validate response
            # ------------------------------------------------------------------

            if not isinstance(
                result,
                dict
            ):

                st.error(
                    "❌ Invalid response from "
                    "request_product_create_rpc."
                )

                st.stop()

            # ==================================================================
            # SUCCESS
            # ==================================================================

            if result.get(
                "success"
            ):

                request_id = result.get(
                    "request_id"
                )

                status = result.get(
                    "status",
                    "PENDING"
                )

                requester_role = result.get(
                    "requester_role",
                    "Unknown"
                )

                st.success(
                    "📝 Product Request "
                    "Submitted Successfully"
                )

                st.info(
                    f"""
Request ID:
{request_id}

Status:
{status}

Requested By:
{current_username}

Requester Role:
{requester_role}

Initial Stock:
{initial_qty}

Selling Price:
{final_price:,.2f} MMK

Warehouse ID:
{warehouse_id}

⚠️ Product, stock, batch and cost layer
are NOT created yet.

Admin or Manager approval is required.
"""
                )

                # ==============================================================
                # CACHE INVALIDATION
                # ==============================================================

                CacheManager.bump(
                    "inventory_version"
                )

                CacheManager.bump(
                    "product_version"
                )

                st.cache_data.clear()

                # ==============================================================
                # SHORT DELAY
                # ==============================================================

                time.sleep(
                    1
                )

                st.rerun()

            # ==================================================================
            # RPC BUSINESS FAILURE
            # ==================================================================

            else:

                error_status = result.get(
                    "status",
                    "ERROR"
                )

                error_message = result.get(
                    "message",
                    "Product request failed."
                )

                st.error(
                    f"❌ [{error_status}] {error_message}"
                )

                # ------------------------------------------------------------------
                # Optional debug information
                # ------------------------------------------------------------------

                if result.get(
                    "requested_by"
                ):

                    st.caption(
                        "Requested By: "
                        + str(
                            result.get(
                                "requested_by"
                            )
                        )
                    )

                if result.get(
                    "role_id"
                ):

                    st.caption(
                        "Role ID: "
                        + str(
                            result.get(
                                "role_id"
                            )
                        )
                    )

        # ======================================================================
        # PYTHON / DATABASE EXCEPTION
        # ======================================================================

        except Exception as e:

            st.error(
                f"❌ Product Request Error : {e}"
            )


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "render_product_create"
]
