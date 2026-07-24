import streamlit as st
from auth import is_authenticated, logout, ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER
from utils.notification import show_notification_history
# ==========================================================
# ERP MENU MASTER
# ==========================================================
MENU = {
    ROLE_ADMIN: [
        ("🏠", "Dashboard", "3_Admin_Dashboard"),
        ("🛒", "POS", "1_POS"),
        ("📦", "Inventory", "2_Inventory"),
        ("📱", "Mobile Inventory", "2_Mobile_Inventory"),
        ("🧾", "Receipt", "2_Receipt"),
        ("🧾", "Receipt Viewer", "6_Receipt_Viewer"),
        ("🛍", "Purchase", "7_Purchase"),
        ("🔁", "Transfer", "8_Transfer"),
        ("👥", "Customers", "9_Customers"),
        ("🏭", "Suppliers", "10_Suppliers"),
        ("↩️", "Refund", "5_Refund"),
        ("✅", "Refund Approval", "6_Refund_Approval"),
        ("📊", "Refund Report", "6_Refund_Report"),
        ("📈", "Reports", "3_Reports"),
        ("👤", "Users", "4_Users"),
        ("⚙️", "Settings", "12_Settings"),
    ],
    ROLE_MANAGER: [
        ("🏠", "Dashboard", "3_Admin_Dashboard"),
        ("🛒", "POS", "1_POS"),
        ("📦", "Inventory", "2_Inventory"),
        ("📱", "Mobile Inventory", "2_Mobile_Inventory"),
        ("🧾", "Receipt Viewer", "6_Receipt_Viewer"),
        ("🛍", "Purchase", "7_Purchase"),
        ("🔁", "Transfer", "8_Transfer"),
        ("👥", "Customers", "9_Customers"),
        ("🏭", "Suppliers", "10_Suppliers"),
        ("↩️", "Refund", "5_Refund"),
        ("✅", "Refund Approval", "6_Refund_Approval"),
        ("📊", "Refund Report", "6_Refund_Report"),
        ("📈", "Reports", "3_Reports"),
    ],
    ROLE_CASHIER: [
        ("🛒", "POS", "1_POS"),
        ("🧾", "Receipt Viewer", "6_Receipt_Viewer"),
        ("↩️", "Refund", "5_Refund"),
    ]
}

# ==========================================================
# ACTIVE PAGE
# ==========================================================
def get_active_page():
    if "active_page" not in st.session_state:
        user = st.session_state.get("user", {})
        if user.get("role_id") == ROLE_ADMIN:
            st.session_state.active_page = "3_Admin_Dashboard"
        else:
            st.session_state.active_page = "1_POS"
    return st.session_state.get("active_page", "1_POS")

# ==========================================================
# SIDEBAR
# ==========================================================
def show_sidebar():
    if not is_authenticated():
        return

    user = st.session_state.get("user", {})
    role_display = user.get("role", "Unknown")

    with st.sidebar:
        st.title("🏭 Myanmar ERP")
        st.caption("Enterprise Edition")
        st.divider()

        # USER CARD
        st.success(f"👤 {user.get('full_name', 'User')}")
        st.caption(f"Username : {user.get('username', '')}")
        st.caption(f"Role : {role_display}")
        
        # MY PROFILE BUTTON (Custom Router v30.12 Integration)
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state.active_page = "13_Profile"
            st.rerun()
# ==========================================================
# NOTIFICATIONS
# ==========================================================

   with st.expander("🔔 Notifications", expanded=False):
    show_notification_history()            
            
        st.divider()

        # LANGUAGE
        if "language" not in st.session_state:
            st.session_state.language = "English"
        st.session_state.language = st.selectbox(
            "Language",
            ["English", "မြန်မာ"],
            index=0 if st.session_state.language == "English" else 1
        )
        st.divider()

        # NAVIGATION
        st.subheader("📂 Navigation")
        active = get_active_page()
        pages = MENU.get(user.get("role_id"), [])

        for icon, title, page_id in pages:
            label = f"{icon} {title}"
            if active == page_id:
                label = f"✅ {label}"

            if st.button(label, key=f"nav_{page_id}", use_container_width=True):
                st.session_state.active_page = page_id
                st.rerun()

        st.divider()

        # STATUS
        st.success("🟢 System Online")
        st.caption("Database : Connected")
        st.caption("Session : Active")
        st.caption("ERP Version : Enterprise")
        st.divider()

        # LOGOUT
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            logout()
