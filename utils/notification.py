# ==========================================================
# utils/notification.py
# ERP ENTERPRISE NOTIFICATION ENGINE v3
# ==========================================================

import streamlit as st


# ----------------------------------------------------------
# TOAST (Auto Hide)
# ----------------------------------------------------------

def toast_success(message):

    st.toast(message, icon="✅")

    _add_history(
        "success",
        message
    )


def toast_error(message):
    st.toast(message, icon="❌")


def toast_warning(message):
    st.toast(message, icon="⚠️")


def toast_info(message):
    st.toast(message, icon="ℹ️")


# ----------------------------------------------------------
# STICKY NOTIFICATION
# ----------------------------------------------------------

def _notify(msg_type, message):

    st.session_state["notification"] = {
        "type": msg_type,
        "message": message
    }

    _add_history(msg_type, message)


def notify_success(message):
    _notify("success", message)


def notify_error(message):
    _notify("error", message)


def notify_warning(message):
    _notify("warning", message)


def notify_info(message):
    _notify("info", message)


# ----------------------------------------------------------
# SHOW STICKY MESSAGE
# ----------------------------------------------------------

def show_notification():

    data = st.session_state.get("notification")

    if not data:
        return

    t = data["type"]
    m = data["message"]

    if t == "success":
        st.success(m)

    elif t == "error":
        st.error(m)

    elif t == "warning":
        st.warning(m)

    else:
        st.info(m)


# ----------------------------------------------------------
# CLEAR
# ----------------------------------------------------------

def clear_notification():

    st.session_state.pop("notification", None)
# ----------------------------------------------------------
# NOTIFICATION HISTORY
# ----------------------------------------------------------

MAX_HISTORY = 50


def _add_history(msg_type, message):

    if "notification_history" not in st.session_state:
        st.session_state.notification_history = []

    st.session_state.notification_history.insert(
        0,
        {
            "type": msg_type,
            "message": message
        }
    )

    st.session_state.notification_history = (
        st.session_state.notification_history[:MAX_HISTORY]
    )


def show_notification_history():

    history = st.session_state.get(
        "notification_history",
        []
    )

    if not history:
        st.info("No notifications.")
        return

    for item in history:

        icon = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }.get(
            item.get("type"),
            "•"
        )

        st.write(
            f"{icon} {item.get('message','')}"
    )
