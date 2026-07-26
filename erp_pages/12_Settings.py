# ==============================================================================
# erp_pages/12_Settings.py
# ERP ENTERPRISE CONTROL CENTER v2.0
# PART 1 / 4
# ==============================================================================

import streamlit as st

from supabase_client import supabase

from utils.notification import (
    notify_success,
    notify_error,
    notify_warning
)


# ==============================================================================
# SECURITY
# ==============================================================================

def require_admin():

    user = st.session_state.get("user")

    if not user:

        st.error("⛔ Please login first")

        st.stop()

    if user.get("role_id") != 1:

        st.error("⛔ Access Denied")

        st.stop()

    return user


# ==============================================================================
# LOAD SETTINGS
# ==============================================================================

@st.cache_data(ttl=60)

def load_settings():

    try:

        rows = (

            supabase

            .table("settings")

            .select("*")

            .execute()

            .data

            or []

        )

        return {

            row["key"]: row["value"]

            for row in rows

        }

    except Exception as e:

        st.error(e)

        return {}


# ==============================================================================
# SAVE SETTING
# ==============================================================================

def save_setting(

    key,

    value

):

    supabase.table("settings").upsert(

        {

            "key": key,

            "value": str(value)

        },

        on_conflict="key"

    ).execute()


# ==============================================================================
# HELPERS
# ==============================================================================

def get_bool(

    settings,

    key,

    default=False

):

    return (

        str(

            settings.get(

                key,

                default

            )

        ).lower()

        ==

        "true"

    )


def get_float(

    settings,

    key,

    default=0.0

):

    try:

        return float(

            settings.get(

                key,

                default

            )

        )

    except Exception:

        return float(default)


def get_text(

    settings,

    key,

    default=""

):

    return str(

        settings.get(

            key,

            default

        )

    )


# ==============================================================================
# MAIN
# ==============================================================================

def run():

    user = require_admin()

    settings = load_settings()

    st.title("⚙ ERP Control Center")

    st.success(

        f"Welcome Admin : "

        f"{user.get('full_name','Admin')}"

    )

    st.caption(

        "Enterprise Configuration Center"

    )

    st.divider()
    # ==========================================================
    # 💰 PRICING ENGINE
    # ==========================================================

    st.subheader("💰 Pricing Engine")

    st.caption("""
Pricing Priority

Product Markup
      ↓
Category Markup
      ↓
Global Default Markup
""")

    # ----------------------------------------------------------
    # Global Default Markup
    # ----------------------------------------------------------

    default_markup = st.number_input(
default_markup = st.number_input(

    "🌐 Global Default Markup (%)",

    min_value=0.0,

    max_value=500.0,

    value=float(
        get_float(
            "DEFAULT_MARKUP_PERCENT",
            20.0
        )
    ),

    step=1.0

)

    # ----------------------------------------------------------
    # Pricing Priority
    # ----------------------------------------------------------

    priority_options = [
        "PRODUCT_FIRST",
        "CATEGORY_FIRST",
        "GLOBAL_FIRST"
    ]

    current_priority = settings_map.get(
        "PRICING_PRIORITY",
        "PRODUCT_FIRST"
    )

    pricing_priority = st.selectbox(
        "⚙ Pricing Priority",
        priority_options,
        index=(
            priority_options.index(current_priority)
            if current_priority in priority_options
            else 0
        )
    )

    # ----------------------------------------------------------
    # Enable Rules
    # ----------------------------------------------------------

    enable_product_markup = st.toggle(
        "Enable Product Markup",
        value=get_bool(
            "ENABLE_PRODUCT_MARKUP",
            True
        )
    )

    enable_category_markup = st.toggle(
        "Enable Category Markup",
        value=get_bool(
            "ENABLE_CATEGORY_MARKUP",
            True
        )
    )

    # ----------------------------------------------------------
    # Price Calculation Method
    # ----------------------------------------------------------

    pricing_method = st.selectbox(
        "Pricing Method",
        [
            "MARKUP",
            "MARGIN"
        ],
        index=(
            0
            if settings_map.get(
                "PRICING_METHOD",
                "MARKUP"
            ) == "MARKUP"
            else 1
        )
    )

    auto_update_price = st.toggle(
        "Auto Update Selling Price",
        value=get_bool(
            "AUTO_UPDATE_SELLING_PRICE",
            True
        )
    )

    allow_manual_override = st.toggle(
        "Allow Manual Price Override",
        value=get_bool(
            "ALLOW_MANUAL_PRICE_OVERRIDE",
            True
        )
    )

    st.divider()

    st.markdown("### 🧪 Pricing Preview")

    preview_cost = st.number_input(
        "Sample Cost",
        min_value=0.0,
        value=1000.0,
        step=100.0
    )

    preview_product_markup = st.number_input(
        "Sample Product Markup (%)",
        value=50.0,
        step=1.0
    )

    preview_category_markup = st.number_input(
        "Sample Category Markup (%)",
        value=30.0,
        step=1.0
    )
        # ==========================================================
    # 💰 PRICING ENGINE
    # ==========================================================

    st.subheader("💰 Pricing Engine")

    st.info(
        """
Pricing Priority

① Product Markup
        ↓
② Category Markup
        ↓
③ Global Default Markup

System will automatically use the first available rule.
"""
    )

    st.divider()

    # ==========================================================
    # GLOBAL DEFAULT
    # ==========================================================

    default_markup = st.number_input(
        "🌍 Global Default Markup (%)",
        min_value=0.0,
        max_value=500.0,
        value=get_float("DEFAULT_MARKUP_PERCENT", 20),
        step=1.0,
    )

    # ==========================================================
    # PRIORITY
    # ==========================================================

    priority_options = [
        "PRODUCT_FIRST",
        "CATEGORY_FIRST",
        "GLOBAL_FIRST",
    ]

    priority_labels = {
        "PRODUCT_FIRST": "Product → Category → Global",
        "CATEGORY_FIRST": "Category → Product → Global",
        "GLOBAL_FIRST": "Global Only",
    }

    current_priority = settings_map.get(
        "PRICING_PRIORITY",
        "PRODUCT_FIRST",
    )

    pricing_priority = st.selectbox(
        "Priority Rule",
        priority_options,
        index=priority_options.index(current_priority)
        if current_priority in priority_options
        else 0,
        format_func=lambda x: priority_labels[x],
    )

    # ==========================================================
    # ENABLE FLAGS
    # ==========================================================

    enable_product_markup = st.toggle(
        "Enable Product Markup",
        value=get_bool(
            "ENABLE_PRODUCT_MARKUP",
            True,
        ),
    )

    enable_category_markup = st.toggle(
        "Enable Category Markup",
        value=get_bool(
            "ENABLE_CATEGORY_MARKUP",
            True,
        ),
    )

    st.divider()

    # ==========================================================
    # PRICE METHOD
    # ==========================================================

    pricing_method = st.selectbox(
        "Pricing Method",
        [
            "MARKUP",
            "MARGIN",
        ],
        index=0
        if settings_map.get(
            "PRICING_METHOD",
            "MARKUP",
        )
        == "MARKUP"
        else 1,
    )

    auto_update = st.toggle(
        "Auto Update Selling Price",
        value=get_bool(
            "AUTO_UPDATE_SELLING_PRICE",
            True,
        ),
    )

    allow_override = st.toggle(
        "Allow Manual Price Override",
        value=get_bool(
            "ALLOW_MANUAL_PRICE_OVERRIDE",
            True,
        ),
    )

    st.divider()

    # ==========================================================
    # SAVE
    # ==========================================================

    if st.button(
        "💾 Save Pricing Settings",
        use_container_width=True,
    ):

        try:

            save_setting(
                "DEFAULT_MARKUP_PERCENT",
                default_markup,
            )

            save_setting(
                "PRICING_PRIORITY",
                pricing_priority,
            )

            save_setting(
                "ENABLE_PRODUCT_MARKUP",
                enable_product_markup,
            )

            save_setting(
                "ENABLE_CATEGORY_MARKUP",
                enable_category_markup,
            )

            save_setting(
                "PRICING_METHOD",
                pricing_method,
            )

            save_setting(
                "AUTO_UPDATE_SELLING_PRICE",
                auto_update,
            )

            save_setting(
                "ALLOW_MANUAL_PRICE_OVERRIDE",
                allow_override,
            )

            st.cache_data.clear()

            notify_success(
                "Pricing Engine settings saved successfully."
            )

            st.rerun()

        except Exception as e:

            notify_error(str(e))
    # ==========================================================
    # PRICING PREVIEW
    # ==========================================================

    st.subheader("🔎 Pricing Rule Preview")


    product_status = (
        "✅ Enabled"
        if enable_product_markup
        else
        "❌ Disabled"
    )


    category_status = (
        "✅ Enabled"
        if enable_category_markup
        else
        "❌ Disabled"
    )


    priority_text = {

        "PRODUCT_FIRST":
            "Product Markup → Category Markup → Global Default",

        "CATEGORY_FIRST":
            "Category Markup → Product Markup → Global Default",

        "GLOBAL_FIRST":
            "Global Default Only"

    }


    st.success(

        f"""
### Current Pricing Engine

🟢 Product Markup:
{product_status}


🟢 Category Markup:
{category_status}


⚙️ Priority:

{priority_text.get(
    pricing_priority,
    pricing_priority
)}


🌍 Global Default Markup:

{default_markup}%


💰 Pricing Method:

{pricing_method}


🔄 Auto Update Selling Price:

{"Enabled" if auto_update else "Disabled"}


✏️ Manual Override:

{"Allowed" if allow_override else "Disabled"}

"""
    )



    # ==========================================================
    # EXAMPLE CALCULATION
    # ==========================================================

    st.subheader(
        "🧮 Example Calculation"
    )


    example_cost = st.number_input(

        "Test Cost Price",

        min_value=0.0,

        value=1000.0,

        step=100.0

    )


    example_price = (

        example_cost

        +

        (
            example_cost

            *

            default_markup

            /

            100
        )

    )


    st.info(

        f"""
Example:

Cost Price:
{example_cost:,.2f}


Global Markup:
{default_markup}%


Estimated Selling Price:

{example_price:,.2f}

"""

    )



    st.divider()



    # ==========================================================
    # SYSTEM STATUS
    # ==========================================================

    st.subheader(
        "🖥 System Status"
    )


    st.success(
        """
✔ ERP Core Active

✔ Warehouse Engine Ready

✔ Inventory Connected

✔ Sales Engine Connected

✔ Pricing Engine Connected

✔ Settings Database Synced

✔ Product / Category / Global Markup Ready
"""
    )


    st.success(
        "🚀 ERP Control Center Fully Operational"
    )



# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    st.set_page_config(

        page_title="ERP Control Center",

        page_icon="⚙️",

        layout="wide"

    )

    run()
