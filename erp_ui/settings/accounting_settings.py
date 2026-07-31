# ==============================================================================
# erp_ui/settings/accounting_settings.py
# ERP ACCOUNTING & TAX SETTINGS COMPONENT v3.0
#
# Maker - Checker Approval Workflow
# Request → Approval → Apply
#
# Features
# - Tax Rate Request
# - Discount Policy Request
# - Duplicate Pending Notification
# - No Change Notification
# - Success Notification
# ==============================================================================

import streamlit as st

from erp_core.services.settings_service import SettingsService
from utils.notification import notify_success, notify_error


# ==============================================================================
# ACCOUNTING SETTINGS UI
# ==============================================================================

def render_accounting_settings(settings, user):

    st.subheader("🧾 Accounting & Tax")

    # --------------------------------------------------------------------------
    # CURRENT TAX RATE
    # --------------------------------------------------------------------------

    tax_value = settings.get("DEFAULT_TAX_RATE", 0)

    try:
        active_tax_rate = float(tax_value)
    except Exception:
        active_tax_rate = 0.0

    st.caption(f"Current Tax Rate : {active_tax_rate:.2f}%")

    tax_rate = st.number_input(
        "Change Tax Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=active_tax_rate,
        step=0.1
    )

    st.divider()

    # --------------------------------------------------------------------------
    # DISCOUNT POLICY
    # --------------------------------------------------------------------------

    current_discount = settings.get("DISCOUNT_POLICY", "allowed")

    discount_policy = st.selectbox(
        "Discount Policy",
        ["allowed", "restricted"],
        index=0 if current_discount == "allowed" else 1
    )

    st.divider()

    # --------------------------------------------------------------------------
    # SUBMIT REQUEST
    # --------------------------------------------------------------------------

    if st.button(
        "📤 Submit Accounting Change Request",
        use_container_width=True
    ):

        try:

            messages = []
            errors = []

            # ==============================================================
            # TAX RATE REQUEST
            # ==============================================================

            tax_result = SettingsService.request_change(
                "DEFAULT_TAX_RATE",
                str(tax_rate),
                "Accounting Tax Rate Change",
                user["id"]
            )

            if tax_result.get("success"):
                messages.append("Tax Rate request created")
            else:
                errors.append(
                    tax_result.get("message", "Tax request failed")
                )

            # ==============================================================
            # DISCOUNT POLICY REQUEST
            # ==============================================================

            discount_result = SettingsService.request_change(
                "DISCOUNT_POLICY",
                discount_policy,
                "Discount Policy Change",
                user["id"]
            )

            if discount_result.get("success"):
                messages.append("Discount Policy request created")
            else:
                errors.append(
                    discount_result.get("message", "Discount request failed")
                )

            # ==============================================================
            # NOTIFICATIONS
            # ==============================================================

            if messages:

                notify_success(
                    "⏳ Approval request submitted successfully"
                )

                for msg in messages:
                    st.success(msg)

            if errors:

                for err in errors:
                    notify_error(err)

            st.rerun()

        except Exception as e:

            notify_error(
                f"Accounting Request Failed : {e}"
            )
