# ==============================================================================
# erp_pages/inventory/product_create.py
# ERP ENTERPRISE INVENTORY PRODUCT CREATE v1.3
#
# Owner First Pricing
# RPC Driven Product Creation
# FEFO Opening Batch Compatible
# ==============================================================================

import time
import streamlit as st

from erp_core.context import CacheManager


# ==============================================================================
# PRODUCT CREATE
# ==============================================================================

def render_product_create(
    db_client,
    pricing_service,
    warehouse_id,
):

    st.subheader(
        "➕ Add New Product"
    )

    with st.form(
        "add_product_form",
        clear_on_submit=True
    ):

        c1, c2 = st.columns(2)

        # ----------------------------------------------------------------------
        # LEFT
        # ----------------------------------------------------------------------

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
                step=0.01
            )

            minimum_stock = st.number_input(
                "Minimum Stock",
                min_value=0,
                value=5,
                step=1
            )

        # ----------------------------------------------------------------------
        # RIGHT
        # ----------------------------------------------------------------------

        with c2:

            barcode = st.text_input(
                "Barcode"
            )

            unit = st.selectbox(
                "Unit",
                [
                    "pcs",
                    "kg",
                    "box"
                ]
            )

            initial_qty = st.number_input(
                "Initial Stock Qty",
                min_value=0,
                value=0,
                step=1
            )

            owner_price = st.number_input(
                "Owner Selling Price (Main)",
                min_value=0.0,
                value=0.0,
                step=0.01
            )

        # ======================================================================
        # PRICING ENGINE
        # ======================================================================

        preview = {
            "selling_price": purchase_price,
            "final_markup_percent": 0,
            "markup_source": "PURCHASE_COST",
        }

        if purchase_price > 0:

            try:

                # ==============================================================
                # OWNER FIRST
                # ==============================================================

                if owner_price > 0:

                    preview = {
                        "selling_price": float(owner_price),
                        "final_markup_percent": 0,
                        "markup_source": "OWNER_PRICE",
                    }

                else:

                    # ==========================================================
                    # PRICING SERVICE
                    # ==========================================================

                    result = (
                        pricing_service
                        .calculate_selling_price(
                            cost=purchase_price,
                            product_id=None
                        )
                    )

                    # ==========================================================
                    # PRICING SERVICE RESPONSE NORMALIZATION
                    #
                    # Supported:
                    #
                    # 1. dict
                    # 2. int / float
                    #
                    # ==========================================================

                    if isinstance(result, dict):

                        preview = {
                            "selling_price": float(
                                result.get(
                                    "selling_price",
                                    purchase_price
                                )
                                or purchase_price
                            ),

                            "final_markup_percent": float(
                                result.get(
                                    "final_markup_percent",
                                    0
                                )
                                or 0
                            ),

                            "markup_source": result.get(
                                "markup_source",
                                "PRICING_SERVICE"
                            ),
                        }

                    elif isinstance(
                        result,
                        (int, float)
                    ):

                        calculated_price = float(
                            result
                        )

                        markup_percent = (
                            (
                                (
                                    calculated_price
                                    - purchase_price
                                )
                                / purchase_price
                            )
                            * 100
                            if purchase_price > 0
                            else 0
                        )

                        preview = {
                            "selling_price":
                                calculated_price,

                            "final_markup_percent":
                                markup_percent,

                            "markup_source":
                                "PRICING_SERVICE",
                        }

                    else:

                        raise ValueError(
                            "Invalid pricing service response."
                        )

                # ==============================================================
                # PRICING PREVIEW
                # ==============================================================

                st.info(
                    f"""
💰 Pricing Preview

Cost:
{purchase_price:,.2f} MMK

Markup:
{preview.get('final_markup_percent', 0):,.2f} %

Selling Price:
{preview.get('selling_price', 0):,.2f} MMK

Source:
{preview.get('markup_source', 'DEFAULT')}
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
            "💾 Create Product",
            use_container_width=True
        )

        if submit:

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
                # FINAL SELLING PRICE
                # ==================================================================

                final_price = float(
                    preview.get(
                        "selling_price",
                        purchase_price
                    )
                    or purchase_price
                )

                # ==================================================================
                # PRODUCT PAYLOAD
                # ==================================================================

                payload = {

                    "name":
                        name.strip(),

                    "sku":
                        sku.strip(),

                    "barcode":
                        barcode.strip()
                        if barcode
                        else None,

                    "purchase_price":
                        float(purchase_price),

                    "selling_price":
                        final_price,

                    "owner_selling_price":
                        float(owner_price)
                        if owner_price > 0
                        else None,

                    "final_selling_price":
                        final_price,

                    "price_source":
                        preview.get(
                            "markup_source",
                            "DEFAULT"
                        ),

                    "unit":
                        unit,

                    "minimum_stock":
                        int(minimum_stock),

                    "category_id":
                        1,
                }

                # ==================================================================
                # CREATE PRODUCT RPC
                #
                # create_product_full()
                #
                # RPC is responsible for:
                #
                #   products
                #   warehouse_stock
                #   inventory_batches
                #
                # Therefore initial stock becomes a FEFO batch.
                # ==================================================================

                response = (
                    db_client
                    .rpc(
                        "create_product_full",
                        {
                            "p_data":
                                payload,

                            "p_warehouse_id":
                                int(warehouse_id),

                            "p_initial_qty":
                                int(initial_qty),
                        }
                    )
                    .execute()
                )

                result = response.data

                # ==================================================================
                # NORMALIZE RPC RESPONSE
                # ==================================================================

                if isinstance(
                    result,
                    list
                ):

                    result = (
                        result[0]
                        if result
                        else None
                    )

                if not isinstance(
                    result,
                    dict
                ):

                    st.error(
                        "❌ Invalid response from create_product_full RPC."
                    )

                    st.stop()

                # ==================================================================
                # SUCCESS
                # ==================================================================

                if result.get("success"):

                    product_id = result.get(
                        "product_id"
                    )

                    batch_no = result.get(
                        "batch_no"
                    )

                    fefo_batch_created = result.get(
                        "fefo_batch_created",
                        False
                    )

                    st.success(
                        "✅ Product Created Successfully"
                    )

                    # ------------------------------------------------------------------
                    # Show useful creation details before rerun
                    # ------------------------------------------------------------------

                    details = []

                    if product_id is not None:

                        details.append(
                            f"Product ID: {product_id}"
                        )

                    details.append(
                        f"Initial Stock: {initial_qty}"
                    )

                    details.append(
                        f"Selling Price: {final_price:,.2f} MMK"
                    )

                    if fefo_batch_created:

                        details.append(
                            "FEFO Opening Batch: CREATED"
                        )

                        if batch_no:

                            details.append(
                                f"Batch: {batch_no}"
                            )

                    else:

                        details.append(
                            "FEFO Opening Batch: NOT CREATED "
                            "(Initial stock is zero)"
                        )

                    st.info(
                        "\n\n".join(details)
                    )

                    # ==================================================================
                    # CACHE INVALIDATION
                    # ==================================================================

                    CacheManager.bump(
                        "inventory_version"
                    )

                    CacheManager.bump(
                        "product_version"
                    )

                    st.cache_data.clear()

                    time.sleep(1)

                    st.rerun()

                # ==================================================================
                # RPC FAILURE
                # ==================================================================

                else:

                    st.error(
                        result.get(
                            "message",
                            "Create Product Failed"
                        )
                    )

            except Exception as e:

                st.error(
                    f"Create Product Error : {e}"
                )


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "render_product_create"
]
