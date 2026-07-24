# ==========================================================
# utils/notification.py
# ERP ENTERPRISE NOTIFICATION ENGINE v2
# ==========================================================

import streamlit as st


def _notify(msg_type, message):
    st.session_state["notification"] = {
        "type": msg_type,
        "message": message
    }


def notify_success(message):
    _notify("success", message)


def notify_error(message):
    _notify("error", message)


def notify_warning(message):
    _notify("warning", message)


def notify_info(message):
    _notify("info", message)


def show_notification():

    data = st.session_state.pop("notification", None)

    if not data:
        return

    msg_type = data.get("type")
    message = data.get("message")

    if msg_type == "success":
        st.success(message, icon="✅")

    elif msg_type == "error":
        st.error(message, icon="❌")

    elif msg_type == "warning":
        st.warning(message, icon="⚠️")

    elif msg_type == "info":
        st.info(message, icon="ℹ️")
