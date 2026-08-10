# ==============================================================================
# erp_pages/inventory/product_create.py
# ==============================================================================

"""
ERP ENTERPRISE INVENTORY PRODUCT CREATE v3.0

MAKER-CHECKER PRODUCT REQUEST

IMPORTANT:
- Submit -> product_create_requests ONLY
- Approve -> Actual product / stock / batch / FIFO layer creation

Features:
- Complete Product Master fields
- Opening Batch / Expiry information
- Strong validation
- Duplicate SKU / Barcode pre-check
- Form state preserved on validation failure
- Form state preserved after successful request
- Explicit Clear Form only
"""

from datetime import date

import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager

# ==============================================================================
# SESSION STATE KEYS
# ==============================================================================

_FORM_KEYS = [
    "product_create_name",
    "product_create_sku",
    "product_create_barcode",
    "product_create_category",
    "product_create_brand",
    "product_create_unit",
    "product_create_purchase_price",
    "product_create_selling_price",
    "product_create_owner_price",
    "product_create_initial_qty",
    "product_create_batch_no",
    "product_create_mfg_date",
    "product_create_expiry_date",
    "product_create_supplier_code",
    "product_create_minimum_stock",
    "product_create_max_stock",
    "product_create_reorder_level",
    "product_create_tax_rate",
    "product_create_expiry_controlled",
    "product_create_batch_controlled",
    "product_create_country",
    "product_create_description",
]

# ==============================================================================
# CLEAR FORM
# ==============================================================================


def _clear_product_create_form():
    """Clear Add Product form ONLY when user explicitly requests it."""
    for key in _FORM_KEYS:
        st.session_state.pop(key, None)


# ==============================================================================
# INITIALIZE FORM STATE
# ==============================================================================


def _init_product_create_state():
    defaults = {
        "product_create_name": "",
        "product_create_sku": "",
        "product_create_barcode": "",
        "product_create_category": "",
        "product_create_brand": "",
        "product_create_unit": "pcs",
        "product_create_purchase_price": 0.0,
        "product_create_selling_price": 0.0,
        "product_create_owner_price": 0.0,
        "product_create_initial_qty": 0,
        "product_create_batch_no": "",
        "product_create_mfg_date": date.today(),
        "product_create_expiry_date": date.today(),
        "product_create_supplier_code": "",
        "product_create_minimum_stock": 5,
        "product_create_max_stock": 0,
        "product_create_reorder_level": 0,
        "product_create_tax_rate": 0.0,
        "product_create_expiry_controlled": False,
        "product_create_batch_controlled": False,
        "product_create_country": "",
        "product_create_description": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==============================================================================
# DUPLICATE CHECK
# ==============================================================================


def _check_duplicate_product(
    db_client,
    sku,
    barcode,
):
    """Check existing products before submitting request.

    Returns: None OR error message string
    """
    try:
        if sku:
            result = (
                db_client.table("products")
                .select("id,name,sku")
                .eq("sku", sku)
                .limit(1)
                .execute()
            )
            if result.data:
                existing = result.data[0]
                return f"SKU already exists: {existing.get('sku')}"
        if barcode:
            result = (
                db_client.table("products")
                .select("id,name,barcode")
                .eq("barcode", barcode)
                .limit(1)
                .execute()
            )
            if result.data:
                existing = result.data[0]
                return f"Barcode already exists: {existing.get('barcode')}"
        return None
    except Exception as e:
        return f"Duplicate check failed: {e}"


# ==============================================================================
# PRODUCT CREATE
# ==============================================================================


def render_product_create(
    db_client,
    pricing_service,
    warehouse_id,
):
    st.subheader("➕ Add New Product")
    st.caption(
        "Maker-Checker enabled. "
        "Submit creates a request only. "
        "Actual inventory is created after approval."
    )

    # ==========================================================================
    # CURRENT USER
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
    # FORM STATE
    # ==========================================================================
    _init_product_create_state()

    # ==========================================================================
    # CLEAR FORM
    # ==========================================================================
    clear_col, info_col = st.columns([1, 3])
    with clear_col:
        clear_form = st.button(
            "🧹 Clear Form",
            key="product_create_clear_button",
            use_container_width=True,
        )
    with info_col:
        st.caption("⚠️ Submit / validation failure will NOT clear the form.")

    if clear_form:
        _clear_product_create_form()
        st.success("🧹 Product form cleared.")
        st.rerun()

    # ==========================================================================
    # FORM
    # ==========================================================================
    with st.form("add_product_form", clear_on_submit=False):
        # ======================================================================
        # BASIC INFORMATION
        # ======================================================================
        st.markdown("### 📦 Basic Product Information")
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input(
                "Product Name *",
                key="product_create_name",
            )
            sku = st.text_input(
                "SKU *",
                key="product_create_sku",
            )
            barcode = st.text_input(
                "Barcode",
                key="product_create_barcode",
            )
        with c2:
            category = st.text_input(
                "Category",
                key="product_create_category",
            )
            brand = st.text_input(
                "Brand",
                key="product_create_brand",
            )
            unit = st.selectbox(
                "Unit",
                [
                    "pcs",
                    "kg",
                    "g",
                    "liter",
                    "ml",
                    "bottle",
                    "box",
                    "pack",
                    "carton",
                ],
                key="product_create_unit",
            )
        with c3:
            supplier_code = st.text_input(
                "Supplier Code",
                key="product_create_supplier_code",
            )
            country = st.text_input(
                "Country of Origin",
                key="product_create_country",
            )
            tax_rate = st.number_input(
                "Tax Rate %",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                key="product_create_tax_rate",
            )

        # ======================================================================
        # PRICING
        # ======================================================================
        st.markdown("### 💰 Pricing")
        p1, p2, p3 = st.columns(3)
        with p1:
            purchase_price = st.number_input(
                "Purchase Cost *",
                min_value=0.0,
                step=0.01,
                key="product_create_purchase_price",
            )
        with p2:
            selling_price_input = st.number_input(
                "Selling Price",
                min_value=0.0,
                step=0.01,
                key="product_create_selling_price",
            )
        with p3:
            owner_price = st.number_input(
                "Owner Selling Price",
                min_value=0.0,
                step=0.01,
                key="product_create_owner_price",
            )

        # ======================================================================
        # STOCK CONTROL
        # ======================================================================
        st.markdown("### 📊 Stock Control")
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            initial_qty = st.number_input(
                "Opening Qty",
                min_value=0,
                step=1,
                key="product_create_initial_qty",
            )
        with s2:
            minimum_stock = st.number_input(
                "Min Stock",
                min_value=0,
                step=1,
                key="product_create_minimum_stock",
            )
        with s3:
            max_stock = st.number_input(
                "Max Stock",
                min_value=0,
                step=1,
                key="product_create_max_stock",
            )
        with s4:
            reorder_level = st.number_input(
                "Reorder Level",
                min_value=0,
                step=1,
                key="product_create_reorder_level",
            )

        # ======================================================================
        # BATCH / EXPIRY CONTROL
        # ======================================================================
        st.markdown("### 🧾 Batch / Expiry Control")
        b1, b2 = st.columns(2)
        with b1:
            batch_controlled = st.checkbox(
                "Enable Batch Control",
                key="product_create_batch_controlled",
            )
            expiry_controlled = st.checkbox(
                "Enable Expiry Control",
                key="product_create_expiry_controlled",
            )
        with b2:
            batch_no = st.text_input(
                "Opening Batch No",
                key="product_create_batch_no",
            )
            supplier_code_batch = supplier_code

        d1, d2 = st.columns(2)
        with d1:
            mfg_date = st.date_input(
                "Manufacturing Date",
                key="product_create_mfg_date",
            )
        with d2:
            expiry_date = st.date_input(
                "Expiry Date",
                key="product_create_expiry_date",
            )

        # ======================================================================
        # DESCRIPTION
        # ======================================================================
        st.markdown("### 📝 Description")
        description = st.text_area(
            "Product Description",
            key="product_create_description",
        )

        # ======================================================================
        # PRICING PREVIEW
        # ======================================================================
        st.markdown("### 🔎 Pricing Preview")
        final_price = 0.0
        price_source = "CURRENT_PRICE"
        try:
            if owner_price > 0:
                final_price = float(owner_price)
                price_source = "OWNER_PRICE"
            elif selling_price_input > 0:
                final_price = float(selling_price_input)
                price_source = "MANUAL_SELLING_PRICE"
            elif purchase_price > 0:
                result = pricing_service.calculate_selling_price(
                    cost=purchase_price,
                    product_id=None,
                )
                if isinstance(result, dict):
                    final_price = float(
                        result.get("selling_price", purchase_price)
                        or purchase_price
                    )
                elif isinstance(result, (int, float)):
                    final_price = float(result)
                else:
                    final_price = float(purchase_price)
                price_source = "PRICING_SERVICE"

            markup = 0.0
            if purchase_price > 0:
                markup = (
                    (final_price - purchase_price) / purchase_price
                ) * 100

            st.info(
                f"""💰 Pricing Preview

Cost: {purchase_price:,.2f} MMK
Markup: {markup:,.2f} %
Final Selling Price: {final_price:,.2f} MMK
Price Source: {price_source}"""
            )

        except Exception as e:
            final_price = (
                float(selling_price_input)
                if selling_price_input > 0
                else float(purchase_price)
            )
            price_source = "FALLBACK"
            st.warning(f"⚠️ Pricing Preview Error: {e}")

        # ======================================================================
        # SUBMIT
        # ======================================================================
        submit = st.form_submit_button(
            "📝 Submit Product Request",
            use_container_width=True,
        )

    # ==========================================================================
    # NO SUBMIT
    # ==========================================================================
    if not submit:
        return

    # ==========================================================================
    # VALIDATION
    # ==========================================================================
    errors = []
    name = name.strip()
    sku = sku.strip()
    barcode = barcode.strip()
    category = category.strip()
    brand = brand.strip()
    batch_no = batch_no.strip()
    supplier_code = supplier_code.strip()
    country = country.strip()
    description = description.strip()

    # --------------------------------------------------------------------------
    # REQUIRED
    # --------------------------------------------------------------------------
    if not name:
        errors.append("Product Name is required.")
    if not sku:
        errors.append("SKU is required.")
    if purchase_price <= 0:
        errors.append("Purchase Cost must be greater than 0.")
    if warehouse_id is None:
        errors.append("Warehouse is required.")

    # --------------------------------------------------------------------------
    # STOCK RULES
    # --------------------------------------------------------------------------
    if max_stock > 0 and max_stock < minimum_stock:
        errors.append("Max Stock cannot be lower than Min Stock.")
    if reorder_level > 0 and max_stock > 0:
        if reorder_level > max_stock:
            errors.append("Reorder Level cannot be greater than Max Stock.")

    # --------------------------------------------------------------------------
    # PRICING RULES
    # --------------------------------------------------------------------------
    if selling_price_input > 0:
        if selling_price_input < purchase_price:
            st.warning("⚠️ Selling Price is lower than Purchase Cost.")
    if owner_price > 0:
        if owner_price < purchase_price:
            st.warning("⚠️ Owner Selling Price is lower than Purchase Cost.")

    # --------------------------------------------------------------------------
    # BATCH RULE
    # --------------------------------------------------------------------------
    if batch_controlled and not batch_no:
        errors.append("Batch No is required when Batch Control is enabled.")

    # --------------------------------------------------------------------------
    # EXPIRY RULE
    # --------------------------------------------------------------------------
    if expiry_controlled:
        if not expiry_date:
            errors.append("Expiry Date is required when Expiry Control is enabled.")
        if mfg_date and expiry_date:
            if expiry_date <= mfg_date:
                errors.append("Expiry Date must be later than Manufacturing Date.")

    # --------------------------------------------------------------------------
    # OPENING STOCK RULE
    # --------------------------------------------------------------------------
    if initial_qty > 0:
        if batch_controlled and not batch_no:
            errors.append(
                "Opening Stock requires Batch No when Batch Control is enabled."
            )
        if expiry_controlled and not expiry_date:
            errors.append(
                "Opening Stock requires Expiry Date when Expiry Control is enabled."
            )

    # ==========================================================================
    # VALIDATION RESULT
    # ==========================================================================
    if errors:
        st.warning("⚠️ Please complete the required information before submitting.")
        for error in errors:
            st.error(f"• {error}")
        st.info(
            "💡 Your entered information has been preserved. "
            "Correct the fields above and submit again."
        )
        return

    # ==========================================================================
    # DUPLICATE CHECK
    # ==========================================================================
    duplicate_error = _check_duplicate_product(
        db_client,
        sku,
        barcode,
    )
    if duplicate_error:
        st.error(f"❌ {duplicate_error}")
        st.info("💡 Form data has been preserved.")
        return

    # ==========================================================================
    # PRODUCT DATA
    # ==========================================================================
    product_data = {
        "name": name,
        "sku": sku,
        "barcode": barcode or None,
        "category": category or None,
        "brand_name": brand or None,
        "unit": unit,
        "purchase_price": float(purchase_price),
        "selling_price": float(final_price),
        "owner_selling_price": (
            float(owner_price) if owner_price > 0 else None
        ),
        "final_selling_price": float(final_price),
        "price_source": price_source,
        "minimum_stock": int(minimum_stock),
        "max_stock": float(max_stock),
        "reorder_level": int(reorder_level),
        "tax_rate": float(tax_rate),
        "is_expiry_controlled": bool(expiry_controlled),
        "is_batch_controlled": bool(batch_controlled),
        "track_expiry": bool(expiry_controlled),
        "track_batches": bool(batch_controlled),
        "country_of_origin": country or None,
        "description": description or None,
    }

    # ==========================================================================
    # OPENING BATCH DATA
    # ==========================================================================
    opening_batch_data = {
        "batch_no": batch_no or None,
        "mfg_date": (mfg_date.isoformat() if mfg_date else None),
        "expiry_date": (expiry_date.isoformat() if expiry_date else None),
        "quantity": int(initial_qty),
        "unit_cost": float(purchase_price),
        "supplier_code": supplier_code or None,
        "warehouse_id": int(warehouse_id),
    }

    # ==========================================================================
    # REQUEST PAYLOAD
    # ==========================================================================
    request_product_data = {
        **product_data,
        "opening_batch": opening_batch_data,
    }

    # ==========================================================================
    # MAKER-CHECKER RPC
    # ==========================================================================
    try:
        server_db = privileged_db()
        response = (
            server_db.rpc(
                "request_product_create_rpc",
                {
                    "p_product_data": request_product_data,
                    "p_warehouse_id": int(warehouse_id),
                    "p_initial_qty": int(initial_qty),
                    "p_reason": "Product creation request from Inventory UI",
                    "p_requested_by": current_user_id,
                },
            )
            .execute()
        )
        result = response.data

        # ----------------------------------------------------------------------
        # Normalize RPC response
        # ----------------------------------------------------------------------
        if isinstance(result, list):
            result = result[0] if result else None
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
                f"""Request ID: {request_id}
Status: {status}
Requested By: {current_username}
Requester Role: {requester_role}
Opening Stock: {initial_qty}
Batch No: {batch_no or "N/A"}
Expiry Date: {expiry_date.isoformat() if expiry_date else "N/A"}
Selling Price: {final_price:,.2f} MMK

⚠️ Product / Stock / Batch / FIFO Cost Layer have NOT been created yet.
Admin or Manager approval is required.

💡 Form data has been preserved. Press 🧹 Clear Form when you want to enter another product."""
            )

            # ------------------------------------------------------------------
            # CACHE INVALIDATION
            # ------------------------------------------------------------------
            try:
                CacheManager.bump("inventory_version")
                CacheManager.bump("product_version")
            except Exception:
                pass

            return

        # ==========================================================================
        # RPC BUSINESS FAILURE
        # ==========================================================================
        error_status = result.get("status", "ERROR")
        error_message = result.get("message", "Product request failed.")
        st.error(f"❌ [{error_status}] {error_message}")
        st.info("💡 Form data has been preserved.")
        return

    # ==========================================================================
    # EXCEPTION
    # ==========================================================================
    except Exception as e:
        st.error(f"❌ Product Request Error: {e}")
        st.info("💡 Form data has been preserved.")
        return


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = ["render_product_create"]
