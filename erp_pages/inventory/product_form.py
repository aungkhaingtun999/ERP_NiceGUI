# ==============================================================================
# ERP ENTERPRISE PRODUCT FORM v14
#
# Compatible:
# - create_product_full RPC
# - Owner First Pricing
# - Warehouse Stock
# - Batch / Expiry Tracking
# ==============================================================================

import streamlit as st
from erp_core.context import CacheManager


# ------------------------------------------------------------------------------
# SAVE MESSAGE
# ------------------------------------------------------------------------------

def show_saved_message():

    if "product_saved_message" in st.session_state:

        st.success(
            st.session_state.product_saved_message
        )

        del st.session_state.product_saved_message


# ------------------------------------------------------------------------------
# NEW PRODUCT FORM
# ------------------------------------------------------------------------------

def render_new_product_form(
    db_client,
    pricing_service,
    warehouse_id,
    barcode=None
):

    show_saved_message()

    st.subheader(
        "🆕 New Product Registration"
    )

    name = st.text_input(
        "Product Name"
    )

    barcode_value = st.text_input(
        "Barcode",
        value=barcode or ""
    )

    sku = st.text_input(
        "SKU"
    )

    purchase_price = st.number_input(
        "Purchase Price",
        min_value=0.0,
        step=100.0
    )

    owner_price = st.number_input(
        "👑 Owner Selling Price",
        min_value=0.0,
        step=100.0
    )

    opening_stock = st.number_input(
        "Opening Stock",
        min_value=0,
        step=1
    )

    unit = st.selectbox(
        "Unit",
        [
            "pcs",
            "kg",
            "box"
        ]
    )

    # ------------------------------------------------------------------
    # Batch / Expiry Tracking
    # ------------------------------------------------------------------

    st.markdown("---")

    st.subheader("📦 Batch & Expiry Settings")

    track_batches = st.checkbox(
        "Track Batch Number",
        value=False,
        help="Enable batch/lot tracking for this product"
    )

    track_expiry = st.checkbox(
        "Track Expiry Date",
        value=False,
        help="Enable manufacturing and expiry date tracking"
    )

    shelf_life_days = st.number_input(
        "Default Shelf Life (Days)",
        min_value=0,
        value=0,
        step=1,
        help="Optional default shelf life in days"
    )

    if st.button(
        "💾 Save Product",
        use_container_width=True
    ):

        if not name:

            st.warning(
                "Please enter product name"
            )

            return

        try:

            # --------------------------------------------------
            # PRICE ENGINE
            # --------------------------------------------------

            if owner_price > 0:

                final_price = owner_price
                price_source = "OWNER_PRICE"

            else:

                preview = (
                    pricing_service
                    .calculate_selling_price(
                        cost=purchase_price,
                        product_id=None
                    )
                )

                # Support both dict and numeric return types
                if isinstance(preview, dict):

                    final_price = preview.get(
                        "selling_price",
                        purchase_price
                    )

                    price_source = preview.get(
                        "markup_source",
                        "DEFAULT"
                    )

                else:

                    final_price = float(preview)
                    price_source = "DEFAULT"

            payload = {

                "name":
                name,

                "barcode":
                barcode_value,

                "sku":
                sku,

                "purchase_price":
                purchase_price,

                "selling_price":
                final_price,

                "owner_selling_price":
                owner_price if owner_price > 0 else None,

                "final_selling_price":
                final_price,

                "price_source":
                price_source,

                "unit":
                unit,

                "category_id":
                1,

                # --------------------------------------------------
                # Batch / Expiry Fields
                # --------------------------------------------------

                "track_batches":
                bool(track_batches),

                "track_expiry":
                bool(track_expiry),

                "shelf_life_days":
                int(shelf_life_days) if shelf_life_days else None
            }

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
                        int(opening_stock)
                    }
                )
                .execute()
            )

            result = response.data

            if isinstance(result, list):

                result = result[0]

            if result.get("success"):

                st.session_state.product_saved_message = (
                    "✅ Product saved successfully!"
                )

                CacheManager.bump(
                    "inventory_version"
                )

                CacheManager.bump(
                    "product_version"
                )

                st.cache_data.clear()

                st.rerun()

            else:

                st.error(
                    result.get(
                        "message",
                        "Save failed"
                    )
                )

        except Exception as e:

            st.error(
                f"❌ Error: {e}"
            )
