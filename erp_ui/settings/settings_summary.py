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


    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.metric(
            "Tax Rate",
            f"{settings.get('DEFAULT_TAX_RATE', '0')}%"
        )


    with c2:

        st.metric(
            "Pricing",
            settings.get(
                "PRICING_PRIORITY",
                "OWNER_FIRST"
            )
        )


    with c3:

        st.metric(
            "Low Stock",
            settings.get(
                "MIN_STOCK_ALERT",
                "0"
            )
        )


    with c4:

        st.metric(
            "Currency",
            settings.get(
                "CURRENCY",
                "MMK"
            )
        )


    st.caption(
        f"💳 Payment Methods : {settings.get('PAYMENT_METHODS', 'Cash')}"
    )


    st.divider()


    pending_df = get_pending_settings_df()


    if pending_df.empty:

        st.success(
            "✔ No Pending Setting Changes"
        )

        st.divider()

        return


    st.warning(
        f"⏳ Pending Changes : {len(pending_df)} request(s) waiting approval"
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

                            notify_success(
                                "Request Cancelled Successfully"
                            )

                            st.rerun()


                        else:

                            notify_error(
                                result.get(
                                    "message",
                                    "Cancel failed"
                                )
                            )


                    except Exception as e:

                        notify_error(str(e))


    st.divider()
