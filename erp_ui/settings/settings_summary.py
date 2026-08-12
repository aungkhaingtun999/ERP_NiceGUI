# ==============================================================================
# erp_ui/settings/settings_summary.py
# ERP SETTINGS SUMMARY + PENDING REQUESTS
# ==============================================================================

import streamlit as st

from .pending_settings import get_pending_settings_df

from erp_core.services.settings_service import SettingsService

from erp_core.loaders.settings_loader import clear_settings_cache

from utils.notification import (
    notify_success,
    notify_error,
)


# ==============================================================================
# SUMMARY UI
# ==============================================================================

def render_settings_summary(settings, user):

    st.markdown("### ⚡ Current Configuration")

    # အချက်အလက်များများပြားသောကြောင့် row 2 ခုခွဲ၍ ဖော်ပြခြင်း
    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)

    with row1_c1:
        st.metric("Tax Rate", f"{settings.get('DEFAULT_TAX_RATE', '0')}%")
    with row1_c2:
        st.metric("Pricing", settings.get("PRICING_PRIORITY", "OWNER_FIRST"))
    with row1_c3:
        st.metric("Low Stock", settings.get("MIN_STOCK_ALERT", "0"))
    with row1_c4:
        st.metric("Currency", settings.get("CURRENCY", "MMK"))

    st.markdown("---")
    st.markdown("#### 📊 Markup & Default Settings")

    row2_c1, row2_c2, row2_c3, row2_c4, row2_c5 = st.columns(5)

    with row2_c1:
        st.metric("Product Markup", f"{settings.get('PRODUCT_MARKUP_PERCENT', '15')}%")
    with row2_c2:
        st.metric("Category Markup", f"{settings.get('CATEGORY_MARKUP_PERCENT', '20')}%")
    with row2_c3:
        st.metric("Global Markup", f"{settings.get('DEFAULT_MARKUP_PERCENT', '20')}%")
    with row2_c4:
        st.metric("Default Min Stock", settings.get('DEFAULT_MINIMUM_STOCK', '5'))
    with row2_c5:
        st.metric("Default Tax Rate", f"{settings.get('DEFAULT_TAX_RATE', '5')}%")

    st.caption(
        f"💳 Payment Methods: {settings.get('PAYMENT_METHODS', 'Cash')}"
    )

    st.divider()

    pending_df = get_pending_settings_df()

    if pending_df.empty:
        st.success("✔ No Pending Setting Changes")
        st.divider()
        return

    st.warning(
        f"⏳ Pending Changes: {len(pending_df)} request(s) waiting approval"
    )

    st.markdown("#### Pending Requests")

    for _, row in pending_df.iterrows():

        with st.container(border=True):

            st.markdown(
                f"""
**⚙ Setting:** `{row['setting_key']}`

**Current:** `{row['old_value']}`

**Pending:** `{row['new_value']}`

**Requested At:** `{row['created_at']}`
"""
            )

            reason = row.get("reason")

            if reason:
                st.caption(f"📝 Reason: {reason}")

            if row.get("requested_by") == user.get("id"):

                if st.button(
                    "🗑 Cancel Request",
                    key=f"cancel_{row['id']}",
                    use_container_width=True
                ):

                    try:

                        result = SettingsService.cancel_request(
                            row["id"],
                            user["id"]
                        )

                        if result.get("success"):
                            clear_settings_cache()
                            notify_success("Request Cancelled Successfully")
                            st.rerun()

                        else:
                            notify_error(
                                result.get("message", "Cancel failed")
                            )

                    except Exception as e:
                        notify_error(str(e))

    st.divider()
