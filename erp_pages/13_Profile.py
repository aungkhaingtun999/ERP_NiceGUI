# ==============================================================================
# erp_pages/13_Profile.py
# ERP ENTERPRISE
# MULTI-TENANT USER PROFILE
#
# Responsibilities:
# - Current user profile
# - Tenant context
# - Account status
# - Password change
#
# IMPORTANT:
# - User can only view their own profile
# - Tenant context is READ-ONLY here
# - Password change is handled by auth.change_password()
# - Never directly mutate Streamlit widget keys after rendering
# ==============================================================================

import streamlit as st

from auth import (
    require_login,
    change_password,
    get_current_user,
    get_current_tenant_context,
    get_current_tenant_role,
    TENANT_ROLE_MAP,
)


# ==============================================================================
# HELPERS
# ==============================================================================

def safe_value(value, default="—"):
    """
    Return a display-safe value.
    """

    if value is None:
        return default

    if isinstance(value, str) and not value.strip():
        return default

    return value


def tenant_role_name(role):
    """
    Convert tenant role key into display name.
    """

    if not role:
        return "—"

    return TENANT_ROLE_MAP.get(
        role,
        str(role).title()
    )


# ==============================================================================
# PASSWORD FORM RESET
# ==============================================================================

def reset_password_form():
    """
    Reset password form by changing a form version.

    We intentionally DO NOT do:

        st.session_state.some_widget_key = ""

    after the widget has already been rendered.

    Streamlit does not allow direct mutation of an already-created
    widget key during the same script run.
    """

    current_version = st.session_state.get(
        "profile_password_form_version",
        0
    )

    st.session_state[
        "profile_password_form_version"
    ] = current_version + 1


# ==============================================================================
# PROFILE HEADER
# ==============================================================================

def render_profile_header(user):
    """
    Render basic account information.
    """

    st.title("👤 My Profile")

    st.caption(
        "Manage your personal account and security settings."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("👤 Account")

        st.write(
            f"**Username:** "
            f"{safe_value(user.get('username'))}"
        )

        st.write(
            f"**Full Name:** "
            f"{safe_value(user.get('full_name'))}"
        )

        role = safe_value(
            user.get("role")
        )

        st.write(
            f"**System Role:** {role}"
        )

    with col2:

        st.subheader("🔐 Status")

        is_active = bool(
            user.get(
                "is_active",
                False
            )
        )

        if is_active:

            st.success(
                "🟢 Account Active"
            )

        else:

            st.error(
                "🔴 Account Inactive"
            )

        st.write(
            f"**User ID:** "
            f"`{safe_value(user.get('id'))}`"
        )


# ==============================================================================
# TENANT CONTEXT
# ==============================================================================

def render_tenant_context(
    user,
    tenant_context
):
    """
    Display current Multi-Tenant context.

    READ ONLY.

    Profile page must never allow a user to arbitrarily change:
        shop_id
        branch_id
        tenant_role

    Those values are controlled by the authorization layer.
    """

    st.divider()

    st.subheader("🏢 Tenant Context")

    tenant_role = (
        user.get("tenant_role")
        or get_current_tenant_role()
    )

    shop_id = tenant_context.get(
        "shop_id"
    )

    branch_id = tenant_context.get(
        "branch_id"
    )

    shop_name = (
        tenant_context.get("shop_name")
        or user.get("shop_name")
    )

    shop_code = tenant_context.get(
        "shop_code"
    )

    branch_name = (
        tenant_context.get("branch_name")
        or user.get("branch_name")
    )

    branch_code = tenant_context.get(
        "branch_code"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.info(
            "🏷️ Tenant Role"
        )

        st.write(
            f"**{tenant_role_name(tenant_role)}**"
        )

    with col2:

        st.info(
            "🏪 Shop"
        )

        st.write(
            f"**{safe_value(shop_name)}**"
        )

        if shop_code:

            st.caption(
                f"Code: {shop_code}"
            )

        if shop_id is not None:

            st.caption(
                f"Shop ID: {shop_id}"
            )

    with col3:

        st.info(
            "🏬 Branch"
        )

        st.write(
            f"**{safe_value(branch_name)}**"
        )

        if branch_code:

            st.caption(
                f"Code: {branch_code}"
            )

        if branch_id is not None:

            st.caption(
                f"Branch ID: {branch_id}"
            )

    st.caption(
        "🔒 Tenant assignment is controlled by the "
        "authorization and User Management system."
    )


# ==============================================================================
# PASSWORD CHANGE
# ==============================================================================

def render_change_password(user):
    """
    Render secure password change form.
    """

    st.divider()

    st.subheader("🔐 Change Password")

    st.caption(
        "Change the password for your current account."
    )

    form_version = st.session_state.get(
        "profile_password_form_version",
        0
    )

    with st.form(
        key=f"profile_password_form_{form_version}",
        clear_on_submit=True,
    ):

        current_password = st.text_input(
            "Current Password",
            type="password",
            key=f"profile_current_password_{form_version}",
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key=f"profile_new_password_{form_version}",
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            key=f"profile_confirm_password_{form_version}",
        )

        submitted = st.form_submit_button(
            "💾 Change Password",
            use_container_width=True,
        )

    if not submitted:
        return

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    if not current_password:

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

    if len(new_password) < 6:

        st.error(
            "New password must be at least 6 characters."
        )

        return

    if current_password == new_password:

        st.error(
            "New password must be different from "
            "current password."
        )

        return

    # ------------------------------------------------------------------
    # USER ID
    # ------------------------------------------------------------------

    user_id = user.get(
        "id"
    )

    if not user_id:

        st.error(
            "Unable to identify the current user."
        )

        return

    # ------------------------------------------------------------------
    # CHANGE PASSWORD
    # ------------------------------------------------------------------

    success, message = change_password(
        user_id,
        current_password,
        new_password,
    )

    if success:

        st.success(
            message
        )

        st.session_state[
            "profile_password_changed"
        ] = True

        # --------------------------------------------------------------
        # Rerun.
        #
        # clear_on_submit=True already clears the submitted form.
        # The new form version also guarantees a fresh widget state.
        # --------------------------------------------------------------

        reset_password_form()

        st.rerun()

    else:

        st.error(
            message
        )


# ==============================================================================
# SECURITY INFORMATION
# ==============================================================================

def render_security_information(user):
    """
    Basic security information.

    No sensitive password information is displayed.
    """

    st.divider()

    st.subheader("🛡️ Security")

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            "**Password:** Protected"
        )

        st.caption(
            "Your password is stored as a secure password hash."
        )

    with col2:

        st.write(
            "**Session:** Active"
        )

        st.caption(
            "Your session is protected by the ERP authentication system."
        )


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run():

    # ------------------------------------------------------------------
    # LOGIN REQUIRED
    # ------------------------------------------------------------------

    require_login()

    # ------------------------------------------------------------------
    # CURRENT USER
    # ------------------------------------------------------------------

    user = get_current_user()

    if not user:

        st.error(
            "Unable to load the current user profile."
        )

        return

    # ------------------------------------------------------------------
    # TENANT CONTEXT
    # ------------------------------------------------------------------

    tenant_context = (
        get_current_tenant_context()
        or {}
    )

    # ------------------------------------------------------------------
    # PAGE
    # ------------------------------------------------------------------

    render_profile_header(
        user
    )

    render_tenant_context(
        user,
        tenant_context
    )

    render_change_password(
        user
    )

    render_security_information(
        user
    )


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":

    run()
