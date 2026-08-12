# ==============================================================================
# erp_ui/settings/pricing_settings.py
# ERP PRICING SETTINGS COMPONENT
# ==============================================================================
"""
erp_ui/settings/pricing_settings.py

ERP PRICING SETTINGS COMPONENT v2.0

Database Driven Pricing Engine

Settings Source:
DEFAULT_MARKUP_PERCENT
PRODUCT_MARKUP_PERCENT
CATEGORY_MARKUP_PERCENT
PRICING_PRIORITY
ENABLE_PRODUCT_MARKUP
ENABLE_CATEGORY_MARKUP
PRICING_METHOD
AUTO_UPDATE_SELLING_PRICE
ALLOW_MANUAL_PRICE_OVERRIDE
"""

import streamlit as st

from erp_core.loaders.settings_loader import get_bool
from erp_core.services.settings_service import SettingsService
from utils.notification import notify_success, notify_error


# ==============================================================================
# HELPERS
# ==============================================================================

def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


# ==============================================================================
# PRICING UI
# ==============================================================================

def render_pricing_settings(settings, user):
    st.subheader("💰 Pricing Engine")
    st.info(
        """ 
        Pricing Priority
        
        ① Owner Price
        ↓
        ② Product Markup
        ↓
        ③ Category Markup
        ↓
        ④ Global Markup
        """
    )

    st.divider()

    # --------------------------------------------------------------------------
    # DEFAULT MARKUP SETTINGS
    # --------------------------------------------------------------------------
    st.markdown("#### 📌 Default Markup Settings")
    col1, col2, col3 = st.columns(3)

    with col1:
        default_markup = st.number_input(
            "🌍 Global Markup (%)",
            min_value=0.0,
            max_value=500.0,
            value=_to_float(settings.get("DEFAULT_MARKUP_PERCENT", 20)),
            step=1.0,
            help="Fallback markup when Product and Category markup are not available."
        )

    with col2:
        product_markup_default = st.number_input(
            "📦 Product Default Markup (%)",
            min_value=0.0,
            max_value=500.0,
            value=_to_float(settings.get("PRODUCT_MARKUP_PERCENT", 15)),
            step=1.0,
            help="Default markup for newly created products."
        )

    with col3:
        category_markup_default = st.number_input(
            "🗂 Category Default Markup (%)",
            min_value=0.0,
            max_value=500.0,
            value=_to_float(settings.get("CATEGORY_MARKUP_PERCENT", 20)),
            step=1.0,
            help="Default markup for newly created categories."
        )

    st.divider()

    # --------------------------------------------------------------------------
    # PRIORITY
    # --------------------------------------------------------------------------
    st.markdown("#### ⚙ Pricing Priority")
    priority_options = [
        "OWNER_FIRST",
        "PRODUCT_FIRST",
        "CATEGORY_FIRST",
    ]
    priority_labels = {
        "OWNER_FIRST": "Owner → Product → Category → Global",
        "PRODUCT_FIRST": "Product → Category → Global",
        "CATEGORY_FIRST": "Category → Product → Global",
    }
    current_priority = settings.get("PRICING_PRIORITY", "OWNER_FIRST")
    
    pricing_priority = st.selectbox(
        "Pricing Priority",
        priority_options,
        index=(
            priority_options.index(current_priority)
            if current_priority in priority_options
            else 0
        ),
        format_func=lambda x: priority_labels.get(x, x),
        help="Controls which markup source is selected first by the pricing engine."
    )

    st.divider()

    # --------------------------------------------------------------------------
    # ENABLE RULES
    # --------------------------------------------------------------------------
    st.markdown("#### 🧠 Pricing Rules")
    col4, col5 = st.columns(2)

    with col4:
        enable_product_markup = st.toggle(
            "☑ Enable Product Markup",
            value=get_bool(settings, "ENABLE_PRODUCT_MARKUP", True),
            help="Allow product-level markup_percent to override category/global pricing."
        )

    with col5:
        enable_category_markup = st.toggle(
            "☑ Enable Category Markup",
            value=get_bool(settings, "ENABLE_CATEGORY_MARKUP", True),
            help="Allow category-level markup_percent to be used by the pricing engine."
        )

    st.divider()

    # --------------------------------------------------------------------------
    # CALCULATION METHOD
    # --------------------------------------------------------------------------
    st.markdown("#### 📊 Calculation Method")
    current_method = settings.get("PRICING_METHOD", "MARKUP")
    
    pricing_method = st.selectbox(
        "Method",
        ["MARKUP", "MARGIN"],
        index=(0 if current_method == "MARKUP" else 1),
        help="MARKUP = Cost + %. MARGIN = Target profit margin %."
    )

    st.divider()

    # --------------------------------------------------------------------------
    # AUTOMATION
    # --------------------------------------------------------------------------
    st.markdown("#### 🔄 Automation")
    col6, col7 = st.columns(2)

    with col6:
        auto_update_price = st.toggle(
            "Auto Update Selling Price",
            value=get_bool(settings, "AUTO_UPDATE_SELLING_PRICE", True),
            help="Automatically recalculate selling price when purchase cost changes."
        )

    with col7:
        allow_manual_override = st.toggle(
            "Allow Manual Price Override",
            value=get_bool(settings, "ALLOW_MANUAL_PRICE_OVERRIDE", True),
            help="Allow users to enter owner_selling_price manually."
        )

    st.divider()

    # --------------------------------------------------------------------------
    # SAVE / REQUEST APPROVAL
    # --------------------------------------------------------------------------
    st.markdown("#### 📨 Submit Change Request")
    if st.button("📨 Submit Pricing Change Request", use_container_width=True):
        try:
            changes = [
                ("DEFAULT_MARKUP_PERCENT", default_markup, "Change global markup percent"),
                ("PRODUCT_MARKUP_PERCENT", product_markup_default, "Change default product markup percent"),
                ("CATEGORY_MARKUP_PERCENT", category_markup_default, "Change default category markup percent"),
                ("PRICING_PRIORITY", pricing_priority, "Change pricing priority"),
                ("ENABLE_PRODUCT_MARKUP", enable_product_markup, "Enable or disable product markup rule"),
                ("ENABLE_CATEGORY_MARKUP", enable_category_markup, "Enable or disable category markup rule"),
                ("PRICING_METHOD", pricing_method, "Change pricing calculation method"),
                ("AUTO_UPDATE_SELLING_PRICE", auto_update_price, "Change auto update selling price rule"),
                ("ALLOW_MANUAL_PRICE_OVERRIDE", allow_manual_override, "Change manual price override permission"),
            ]
            
            for key, value, reason in changes:
                SettingsService.request_change(
                    key=key,
                    new_value=str(value),
                    reason=reason,
                    requested_by=user["id"]
                )
                
            notify_success("✅ Pricing change request submitted for approval")
            st.rerun()
            
        except Exception as e:
            notify_error(f"Pricing Request Failed : {e}")


           
