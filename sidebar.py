# ==============================================================================
# sidebar.py
# ERP ENTERPRISE SIDEBAR ENGINE
# Custom Router v30.12+
# Role Based Navigation
# ==============================================================================

import streamlit as st

from auth import (
    is_authenticated,
    logout,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_CASHIER,
)

from utils.notification import (
    show_notification_history
)


# ==============================================================================
# ERP MENU MASTER
# ==============================================================================

MENU = {

    ROLE_ADMIN: [
        ("🏠", "Dashboard", "3_Admin_Dashboard"),
        ("🛒", "POS", "1_POS"),
        ("📦", "Inventory", "2_Inventory"),
        ("📱", "Mobile Inventory", "2_Mobile_Inventory"),
        ("🧾", "Receipt", "2_Receipt"),
        ("🛍", "Purchase", "7_Purchase"),
        ("🔁", "Transfer", "8_Transfer"),
        ("👥", "Customers", "9_Customers"),
        ("🏭", "Suppliers", "10_Suppliers"),

        ("↩️", "Refund", "5_Refund"),
        ("✅", "Refund Approval", "6_Refund_Approval"),
        ("📊", "Refund Report", "6_Refund_Report"),

        ("📈", "Reports", "3_Reports"),
        ("💰", "Pricing Report", "11_Pricing_Report"),
        ("📥", "Price Import", "13_Price_Import"),

        ("🔐", "Integrity Check", "14_Integrity"),

        ("👤", "Users", "4_Users"),
        ("⚙️", "Settings", "12_Settings"),
        ("✅", "Settings Approval", "13_Settings_Approval"),

        # Direct Profile Page
        ("👤", "My Profile", "__PROFILE__"),

        ("🧪", "System Test Center", "99_System_Test"),
    ],

    ROLE_MANAGER: [
        ("🏠", "Dashboard", "3_Admin_Dashboard"),
        ("🛒", "POS", "1_POS"),
        ("📦", "Inventory", "2_Inventory"),
        ("📱", "Mobile Inventory", "2_Mobile_Inventory"),
        ("🛍", "Purchase", "7_Purchase"),
        ("🔁", "Transfer", "8_Transfer"),
        ("👥", "Customers", "9_Customers"),
        ("🏭", "Suppliers", "10_Suppliers"),

        ("↩️", "Refund", "5_Refund"),
        ("✅", "Refund Approval", "6_Refund_Approval"),
        ("📊", "Refund Report", "6_Refund_Report"),

        ("📈", "Reports", "3_Reports"),
        ("💰", "Pricing Report", "11_Pricing_Report"),
        ("📥", "Price Import", "13_Price_Import"),

        ("🔐", "Integrity Check", "14_Integrity"),

        ("👤", "My Profile", "__PROFILE__"),
    ],

    ROLE_CASHIER: [
        ("🛒", "POS", "1_POS"),
        ("↩️", "Refund", "5_Refund"),
        ("💰", "Pricing Report", "11_Pricing_Report"),
        ("🔐", "Integrity Check", "14_Integrity"),

        ("👤", "My Profile", "13_Profile"),
    ],
}


# ==============================================================================
# ACTIVE PAGE MANAGEMENT
# ==============================================================================

def get_active_page():

    if "active_page" not in st.session_state:

        user = st.session_state.get(
            "user",
            {}
        )

        if user.get("role_id") == ROLE_ADMIN:

            st.session_state.active_page = (
                "3_Admin_Dashboard"
            )

        else:

            st.session_state.active_page = "1_POS"

    return st.session_state.get(
        "active_page",
        "1_POS"
    )


# ==============================================================================
# USER INFORMATION
# ==============================================================================

def get_user_display():

    user = st.session_state.get(
        "user",
        {}
    )

    return {
        "name": user.get(
            "full_name",
            "User"
        ),
        "username": user.get(
            "username",
            ""
        ),
        "role": user.get(
            "role",
            "Unknown"
        ),
    }


# ==============================================================================
#  PASSWORD CHANGE
# ==============================================================================

    # --------------------------------------------------------------------------
    
    
    # --------------------------------------------------------------------------
    # CHANGE PASSWORD
    # --------------------------------------------------------------------------

    st.subheader(
        "🔐 Change Password"
    )

    # IMPORTANT:
    #
    # Do NOT manually modify:
    #
    #   st.session_state.profile_old_password
    #   st.session_state.profile_new_password
    #   st.session_state.profile_confirm_password
    #
    # after the widgets have been rendered.
    #
    # clear_on_submit=True lets Streamlit clear the form fields safely.
    # --------------------------------------------------------------------------

    with st.form(
        "profile_change_password_form",
        clear_on_submit=True
    ):

        old_password = st.text_input(
            "Current Password",
            type="password"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "💾 Change Password",
            use_container_width=True
        )

    # --------------------------------------------------------------------------
    # PROCESS PASSWORD CHANGE
    # --------------------------------------------------------------------------

    if not submitted:

        return

    # --------------------------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------------------------

    if not old_password:

        st.error(
            "Current password is required."
        )

        return

    if not new_password:

        st.error(
            "New password is required."
        )

        return

    if not confirm_password:

        st.error(
            "Please confirm the new password."
        )

        return

    if new_password != confirm_password:

        st.error(
            "New passwords do not match."
        )

        return

    # --------------------------------------------------------------------------
    # CURRENT USER ID
    # --------------------------------------------------------------------------

    user_id = user.get(
        "id"
    )

    if not user_id:

        st.error(
            "Unable to identify the current user."
        )

        return

    # --------------------------------------------------------------------------
    # CHANGE PASSWORD
    # --------------------------------------------------------------------------

    success, message = change_password(
        user_id,
        old_password,
        new_password
    )

    # --------------------------------------------------------------------------
    # RESULT
    # --------------------------------------------------------------------------

    if success:

        st.success(
            message
        )

        st.info(
            "🔐 Your password has been updated successfully."
        )

    else:

        st.error(
            message
        )


# ==============================================================================
# NAVIGATION BUTTON
# ==============================================================================

def render_menu_item(
    icon,
    title,
    page_id,
    active
):

    label = (
        f"{icon} {title}"
    )

    if active == page_id:

        label = (
            f"✅ {label}"
        )

    if st.button(
        label,
        key=f"nav_{page_id}",
        use_container_width=True
    ):

        # ----------------------------------------------------------------------
        # DIRECT PROFILE
        # ----------------------------------------------------------------------

        if page_id == "__PROFILE__":

            st.session_state.active_page = (
                "__PROFILE__"
            )

            st.rerun()

        # ----------------------------------------------------------------------
        # NORMAL PAGE
        # ----------------------------------------------------------------------

        st.session_state.active_page = (
            page_id
        )

        st.rerun()


# ==============================================================================
# SIDEBAR MAIN
# ==============================================================================

def show_sidebar():

    if not is_authenticated():

        return

    user = st.session_state.get(
        "user",
        {}
    )

    role_id = user.get(
        "role_id"
    )

    with st.sidebar:

        # ----------------------------------------------------------------------
        # HEADER
        # ----------------------------------------------------------------------

        st.title(
            "🏭 Myanmar ERP"
        )

        st.caption(
            "Enterprise Edition"
        )

        st.divider()

        # ----------------------------------------------------------------------
        # USER CARD
        # ----------------------------------------------------------------------

        info = get_user_display()

        st.success(
            f"👤 {info['name']}"
        )

        st.caption(
            f"Username : "
            f"{info['username']}"
        )

        st.caption(
            f"Role : "
            f"{info['role']}"
        )

        st.divider()

        # ----------------------------------------------------------------------
        # NOTIFICATIONS
        # ----------------------------------------------------------------------

        with st.expander(
            "🔔 Notifications"
        ):

            show_notification_history()

        st.divider()

        # ----------------------------------------------------------------------
        # LANGUAGE
        # ----------------------------------------------------------------------

        if "language" not in st.session_state:

            st.session_state.language = (
                "English"
            )

        st.session_state.language = st.selectbox(
            "Language",
            [
                "English",
                "မြန်မာ"
            ],
            index=(
                0
                if st.session_state.language
                == "English"
                else 1
            )
        )

        st.divider()

        # ----------------------------------------------------------------------
        # NAVIGATION
        # ----------------------------------------------------------------------

        st.subheader(
            "📂 Navigation"
        )

        active = get_active_page()

        pages = MENU.get(
            role_id,
            []
        )

        for icon, title, page_id in pages:

            render_menu_item(
                icon,
                title,
                page_id,
                active
            )

        st.divider()

        # ----------------------------------------------------------------------
        # SYSTEM STATUS
        # ----------------------------------------------------------------------

        st.success(
            "🟢 System Online"
        )

        st.caption(
            "Database : Connected"
        )

        st.caption(
            "Session : Active"
        )

        st.caption(
            "ERP Version : Enterprise"
        )

        st.divider()

        # ----------------------------------------------------------------------
        # LOGOUT
        # ----------------------------------------------------------------------

        if st.button(
            "🚪 Logout",
            key="logout_btn",
            use_container_width=True
        ):

            logout()

