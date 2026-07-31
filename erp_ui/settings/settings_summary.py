import streamlit as st

from .pending_settings import get_pending_settings_df


def render_settings_summary(settings):

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


    pending_df = get_pending_settings_df()


    if not pending_df.empty:


        st.warning(
            f"⏳ Pending Changes : {len(pending_df)} request(s) waiting approval"
        )


        display_df = pending_df[
            [
                "setting_key",
                "old_value",
                "new_value",
                "created_at"
            ]
        ].rename(
            columns={
                "setting_key": "Setting",
                "old_value": "Current",
                "new_value": "Pending",
                "created_at": "Requested At"
            }
        )


        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


    else:


        st.success(
            "✔ No Pending Setting Changes"
        )


    st.divider()
