# ==============================================================================
# erp_ui/settings/pricing_settings.py
# ERP ENTERPRISE PRICING SETTINGS COMPONENT v2.0
#
# Compatible:
#   PricingService v8
#   SettingsService v6
#   public.settings
#   settings_change_requests
#   Maker - Checker Workflow
#
# IMPORTANT:
#   This UI NEVER directly updates public.settings.
#
# Workflow:
#
#   Pricing Settings UI
#          ↓
#   SettingsService.request_change()
#          ↓
#   settings_change_requests
#          ↓
#   PENDING
#          ↓
#   Checker Approval
#          ↓
#   approve_setting_change_rpc
#          ↓
#   public.settings
#
# ==============================================================================


import streamlit as st

from erp_core.services.settings_service import (
    SettingsService,
)

from erp_core.loaders.settings_loader import (
    get_bool,
)

from utils.notification import (
    notify_success,
    notify_error,
)


# ==============================================================================
# SUPPORTED PRICING SETTINGS
# ==============================================================================

PRICING_METHODS = [
    "MARKUP",
    "MARGIN",
]


PRICING_PRIORITIES = [
    "OWNER_FIRST",
    "PRODUCT_FIRST",
    "CATEGORY_FIRST",
]


PRICING_PRIORITY_LABELS = {

    "OWNER_FIRST":
        "Owner Price → Product → Category → Global",

    "PRODUCT_FIRST":
        "Product → Category → Global",

    "CATEGORY_FIRST":
        "Category → Product → Global",

}


# ==============================================================================
# USER ID
# ==============================================================================


def _get_user_id(user):

    if not user:

        return None

    return (
        user.get("id")
        or
        user.get("user_id")
    )


# ==============================================================================
# SAFE FLOAT
# ==============================================================================


def _safe_float(value, default=0.0):

    try:

        return float(value)

    except Exception:

        return default


# ==============================================================================
# SAFE BOOL
# ==============================================================================


def _setting_bool(settings, key, default=False):

    try:

        return get_bool(
            settings,
            key,
            default,
        )

    except Exception:

        value = settings.get(
            key,
            default,
        )

        if isinstance(value, bool):

            return value

        return str(
            value
        ).strip().lower() in (
            "true",
            "1",
            "yes",
            "on",
        )


# ==============================================================================
# CREATE ONE MAKER REQUEST
# ==============================================================================


def _request_setting_change(
    setting_key,
    old_value,
    new_value,
    reason,
    user_id,
):

    result = SettingsService.request_change(

        setting_key=setting_key,

        new_value=new_value,

        reason=reason,

        requested_by=user_id,

    )

    return result


# ==============================================================================
# MAIN PRICING UI
# ==============================================================================


def render_pricing_settings(
    settings,
    user,
):

    settings = settings or {}

    st.subheader(
        "💰 Pricing Engine"
    )

    st.info(
        """
Pricing Engine

Owner First
    ↓
Product Markup
    ↓
Category Markup
    ↓
Global Markup

The settings below are Maker-Checker controlled.
Changing a value creates a PENDING request.
The value becomes active only after Checker approval.
"""
    )

    st.divider()

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================

    user_id = _get_user_id(
        user
    )

    if not user_id:

        st.error(
            "⛔ Cannot identify current user."
        )

        return

    user_id = str(
        user_id
    )

    # ==========================================================================
    # CURRENT VALUES
    # ==========================================================================

    current_global_markup = _safe_float(
        settings.get(
            "DEFAULT_MARKUP_PERCENT",
            20,
        ),
        20.0,
    )

    current_priority = str(
        settings.get(
            "PRICING_PRIORITY",
            "OWNER_FIRST",
        )
    ).strip().upper()

    if current_priority not in PRICING_PRIORITIES:

        current_priority = "OWNER_FIRST"

    current_method = str(
        settings.get(
            "PRICING_METHOD",
            "MARKUP",
        )
    ).strip().upper()

    if current_method not in PRICING_METHODS:

        current_method = "MARKUP"

    current_product_markup = _safe_float(
        settings.get(
            "PRODUCT_MARKUP_PERCENT",
            15,
        ),
        15.0,
    )

    current_category_markup = _safe_float(
        settings.get(
            "CATEGORY_MARKUP_PERCENT",
            20,
        ),
        20.0,
    )

    current_product_enabled = _setting_bool(
        settings,
        "ENABLE_PRODUCT_MARKUP",
        True,
    )

    current_category_enabled = _setting_bool(
        settings,
        "ENABLE_CATEGORY_MARKUP",
        True,
    )

    current_manual_override = _setting_bool(
        settings,
        "ALLOW_MANUAL_PRICE_OVERRIDE",
        True,
    )

    # ==========================================================================
    # GLOBAL MARKUP
    # ==========================================================================

    st.markdown(
        "### 🌍 Global Pricing"
    )

    global_markup = st.number_input(
        "Global Markup (%)",
        min_value=0.0,
        max_value=500.0,
        value=current_global_markup,
        step=1.0,
        key="pricing_global_markup",
    )

    # ==========================================================================
    # PRODUCT / CATEGORY DEFAULT MARKUP
    # ==========================================================================

    col1, col2 = st.columns(2)

    with col1:

        product_markup = st.number_input(
            "Product Default Markup (%)",
            min_value=0.0,
            max_value=500.0,
            value=current_product_markup,
            step=1.0,
            key="pricing_product_markup",
        )

    with col2:

        category_markup = st.number_input(
            "Category Default Markup (%)",
            min_value=0.0,
            max_value=500.0,
            value=current_category_markup,
            step=1.0,
            key="pricing_category_markup",
        )

    st.divider()

    # ==========================================================================
    # PRICING PRIORITY
    # ==========================================================================

    st.markdown(
        "### ⚙ Pricing Priority"
    )

    pricing_priority = st.selectbox(
        "Which rule has priority?",
        PRICING_PRIORITIES,
        index=PRICING_PRIORITIES.index(
            current_priority
        ),
        format_func=lambda value:
            PRICING_PRIORITY_LABELS.get(
                value,
                value,
            ),
        key="pricing_priority",
    )

    # ==========================================================================
    # CALCULATION METHOD
    # ==========================================================================

    pricing_method = st.selectbox(
        "📊 Calculation Method",
        PRICING_METHODS,
        index=PRICING_METHODS.index(
            current_method
        ),
        key="pricing_method",
    )

    if pricing_method == "MARKUP":

        st.caption(
            "Example: Cost 100 + 20% markup = Selling Price 120"
        )

    else:

        st.caption(
            "Example: Cost 100 with 20% target margin = Selling Price 125"
        )

    st.divider()

    # ==========================================================================
    # ENABLE RULES
    # ==========================================================================

    st.markdown(
        "### 🔧 Pricing Rules"
    )

    col3, col4 = st.columns(2)

    with col3:

        enable_product_markup = st.toggle(
            "☑ Enable Product Markup",
            value=current_product_enabled,
            key="enable_product_markup",
        )

    with col4:

        enable_category_markup = st.toggle(
            "☑ Enable Category Markup",
            value=current_category_enabled,
            key="enable_category_markup",
        )

    allow_manual_override = st.toggle(
        "✏ Allow Manual Selling Price Override",
        value=current_manual_override,
        key="allow_manual_price_override",
    )

    st.divider()

    # ==========================================================================
    # CHANGE SUMMARY
    # ==========================================================================

    changes = []

    if _safe_float(
        global_markup
    ) != current_global_markup:

        changes.append(
            (
                "DEFAULT_MARKUP_PERCENT",
                current_global_markup,
                global_markup,
            )
        )

    if _safe_float(
        product_markup
    ) != current_product_markup:

        changes.append(
            (
                "PRODUCT_MARKUP_PERCENT",
                current_product_markup,
                product_markup,
            )
        )

    if _safe_float(
        category_markup
    ) != current_category_markup:

        changes.append(
            (
                "CATEGORY_MARKUP_PERCENT",
                current_category_markup,
                category_markup,
            )
        )

    if pricing_priority != current_priority:

        changes.append(
            (
                "PRICING_PRIORITY",
                current_priority,
                pricing_priority,
            )
        )

    if pricing_method != current_method:

        changes.append(
            (
                "PRICING_METHOD",
                current_method,
                pricing_method,
            )
        )

    if enable_product_markup != current_product_enabled:

        changes.append(
            (
                "ENABLE_PRODUCT_MARKUP",
                current_product_enabled,
                enable_product_markup,
            )
        )

    if enable_category_markup != current_category_enabled:

        changes.append(
            (
                "ENABLE_CATEGORY_MARKUP",
                current_category_enabled,
                enable_category_markup,
            )
        )

    if allow_manual_override != current_manual_override:

        changes.append(
            (
                "ALLOW_MANUAL_PRICE_OVERRIDE",
                current_manual_override,
                allow_manual_override,
            )
        )

    # ==========================================================================
    # CHANGE PREVIEW
    # ==========================================================================

    if changes:

        st.warning(
            f"⚠ {len(changes)} pricing setting(s) changed."
        )

        with st.expander(
            "🔍 Review Changes",
            expanded=True,
        ):

            for (
                key,
                old_value,
                new_value,
            ) in changes:

                st.write(
                    f"**{key}**  "
                    f"`{old_value}` → `{new_value}`"
                )

    else:

        st.success(
            "✔ Pricing settings are unchanged."
        )

    # ==========================================================================
    # REASON
    # ==========================================================================

    reason = st.text_area(
        "📝 Change Reason",
        placeholder=(
            "Explain why these pricing settings "
            "need to be changed..."
        ),
        key="pricing_change_reason",
    )

    # ==========================================================================
    # SUBMIT MAKER REQUEST
    # ==========================================================================

    if st.button(
        "📤 Submit Pricing Change for Approval",
        type="primary",
        use_container_width=True,
        disabled=not changes,
    ):

        if not reason.strip():

            notify_error(
                "Change reason is required."
            )

            return

        success_count = 0

        failed = []

        for (
            setting_key,
            old_value,
            new_value,
        ) in changes:

            try:

                result = _request_setting_change(

                    setting_key=setting_key,

                    old_value=old_value,

                    new_value=new_value,

                    reason=reason.strip(),

                    user_id=user_id,

                )

                if result.get(
                    "success",
                    False,
                ):

                    success_count += 1

                else:

                    failed.append(
                        f"{setting_key}: "
                        f"{result.get('message', 'Unknown error')}"
                    )

            except Exception as e:

                failed.append(
                    f"{setting_key}: {e}"
                )

        # ----------------------------------------------------------------------
        # RESULT
        # ----------------------------------------------------------------------

        if success_count:

            notify_success(
                f"{success_count} pricing setting change request(s) "
                "submitted for Checker approval."
            )

        if failed:

            for message in failed:

                notify_error(
                    message
                )

        if success_count:

            st.rerun()


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "render_pricing_settings",
]
