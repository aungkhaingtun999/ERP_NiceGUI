import hashlib
import pandas as pd
import streamlit as st

from auth import require_admin
from database import get_supabase
from utils.notification import (
    notify_error,
    notify_success,
    show_notification,
)


# ==============================================================================
# PAGE
# ==============================================================================

def run():

    # Notification
    show_notification()

    # Admin Guard
    require_admin()

    st.title("👥 User Management (Admin Panel)")
    st.caption("Control users, roles and access rights")

    supabase = get_supabase()

    # --------------------------------------------------------------------------
    # PASSWORD HASH
    # --------------------------------------------------------------------------

    def hash_password(password: str) -> str:
        return hashlib.sha256(
            password.encode("utf-8")
        ).hexdigest()

    # --------------------------------------------------------------------------
    # ACTIVITY LOG
    # --------------------------------------------------------------------------

    def create_activity_log(user_id, action, description):

        try:

            supabase.table("user_activity_logs").insert(
                {
                    "user_id": user_id,
                    "action": action,
                    "description": description,
                }
            ).execute()

        except Exception:
            pass

    # --------------------------------------------------------------------------
    # LOAD ROLES
    # --------------------------------------------------------------------------

    try:

        roles_resp = (
            supabase.table("roles")
            .select("id,name")
            .execute()
        )

        roles = roles_resp.data or []

    except Exception as e:

        st.error(f"Role loading failed: {e}")
        return

    if not roles:

        st.warning("Roles table is empty. Please create roles first.")
        return

    role_map = {r["name"]: r["id"] for r in roles}
    role_names = list(role_map.keys())

    # --------------------------------------------------------------------------
    # LOAD USERS
    # --------------------------------------------------------------------------

    try:

        users_resp = (
            supabase.table("users")
            .select(
                "id, username, full_name, role_id, is_active"
            )
            .execute()
        )

        users = users_resp.data or []

    except Exception as e:

        st.error(f"User loading failed: {e}")
        return

    # --------------------------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------------------------

    search = st.text_input("🔍 Search User")

    if search:

        search = search.lower()

        users = [
            u
            for u in users
            if search in str(u.get("username", "")).lower()
            or search in str(u.get("full_name", "")).lower()
        ]

    # --------------------------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------------------------

    with st.expander("➕ Create New User"):

        with st.form("create_user_form"):

            username = st.text_input("Username")
            full_name = st.text_input("Full Name")
            password = st.text_input(
                "Password",
                type="password"
            )

            selected_role = st.selectbox(
                "Role",
                role_names
            )

            active = st.checkbox(
                "Active",
                value=True
            )

            submit = st.form_submit_button("Create User")

            if submit:

                if not username or not password:

                    notify_error(
                        "Username and password required"
                    )

                else:

                    try:

                        supabase.table("users").insert(
                            {
                                "username": username,
                                "full_name": full_name,
                                "password_hash": hash_password(password),
                                "role_id": role_map[selected_role],
                                "is_active": active,
                            }
                        ).execute()

                        notify_success(
                            f"User '{username}' created successfully"
                        )

                        st.rerun()

                    except Exception as e:

                        notify_error(f"Create user failed: {e}")

    st.divider()

    # ==============================================================================
    # USER TABLE
    # ==============================================================================

    st.subheader("📋 Users")

    if not users:

        st.info("No users found")

    else:

        table_rows = []

        for u in users:

            role_name = next(
                (
                    r["name"]
                    for r in roles
                    if r["id"] == u["role_id"]
                ),
                "Unknown",
            )

            table_rows.append(
                {
                    "Username": u.get("username"),
                    "Full Name": u.get("full_name"),
                    "Role": role_name,
                    "Status": (
                        "🟢 Active"
                        if u.get("is_active")
                        else "🔴 Disabled"
                    ),
                }
            )

        df_users = pd.DataFrame(table_rows)

        st.dataframe(
            df_users,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # ----------------------------------------------------------------------
        # EDIT USER
        # ----------------------------------------------------------------------

        st.subheader("✏ Edit User")

        user_options = {
            str(u["id"]): f"{u['username']} - {u['full_name']}"
            for u in users
        }

        selected_user_id = st.selectbox(
            "Select User",
            options=list(user_options.keys()),
            format_func=lambda x: user_options[x],
        )

        selected_user = next(
            (
                u
                for u in users
                if str(u["id"]) == selected_user_id
            ),
            None,
        )

        if selected_user:

            current_role_name = next(
                (
                    r["name"]
                    for r in roles
                    if r["id"] == selected_user["role_id"]
                ),
                role_names[0],
            )

            new_full_name = st.text_input(
                "Full Name",
                value=selected_user.get("full_name", ""),
            )

            new_role = st.selectbox(
                "Role",
                role_names,
                index=role_names.index(current_role_name),
            )

            new_active = st.toggle(
                "Active",
                value=selected_user.get("is_active", True),
            )

            col1, col2 = st.columns(2)

            # UPDATE
            with col1:

                if st.button(
                    "💾 Update User",
                    use_container_width=True,
                ):

                    try:

                        supabase.table("users").update(
                            {
                                "full_name": new_full_name,
                                "role_id": role_map[new_role],
                                "is_active": new_active,
                            }
                        ).eq("id", selected_user_id).execute()

                        create_activity_log(
                            st.session_state.get("user_id"),
                            "UPDATE_USER",
                            f"Updated user {selected_user['username']}",
                        )

                        notify_success(
                            "User updated successfully"
                        )

                        st.rerun()

                    except Exception as e:

                        notify_error(f"Update failed: {e}")

            # DELETE
            with col2:

                if selected_user.get("username") == "admin":

                    st.info(
                        "System admin cannot be deleted"
                    )

                else:

                    if st.button(
                        "🗑 Delete User",
                        use_container_width=True,
                    ):

                        try:

                            supabase.table("users").delete().eq(
                                "id",
                                selected_user_id,
                            ).execute()

                            create_activity_log(
                                st.session_state.get("user_id"),
                                "DELETE_USER",
                                f"Deleted user {selected_user['username']}",
                            )

                            notify_success(
                                "User deleted successfully"
                            )

                            st.rerun()

                        except Exception as e:

                            notify_error(f"Delete failed: {e}")

            st.divider()

            # ------------------------------------------------------------------
            # RESET PASSWORD
            # ------------------------------------------------------------------

            st.subheader("🔐 Reset Password")

            new_password = st.text_input(
                "New Password",
                type="password",
            )

            if st.button(
                "💾 Save Password",
                use_container_width=True,
            ):

                if not new_password:

                    notify_error("Password required")

                else:

                    try:

                        supabase.table("users").update(
                            {
                                "password_hash": hash_password(new_password)
                            }
                        ).eq("id", selected_user_id).execute()

                        create_activity_log(
                            st.session_state.get("user_id"),
                            "RESET_PASSWORD",
                            f"Reset password for {selected_user['username']}",
                        )

                        notify_success(
                            "Password reset successfully"
                        )

                        st.rerun()

                    except Exception as e:

                        notify_error(f"Reset failed: {e}")

    # ==============================================================================
    # SUMMARY
    # ==============================================================================

    total = len(users)
    active_count = sum(
        1 for u in users if u.get("is_active", False)
    )

    st.divider()
    st.subheader("📊 System Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("👥 Users", total)
    c2.metric("🟢 Active", active_count)
    c3.metric("🔴 Disabled", total - active_count)
    c4.metric("🛡 Roles", len(roles))

    # ==============================================================================
    # ACTIVITY LOG
    # ==============================================================================

    st.divider()

    with st.expander(
        "📝 User Activity Log",
        expanded=False,
    ):

        try:

            logs = (
                supabase.table("user_activity_logs")
                .select(
                    "action, description, created_at"
                )
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )

            activity_logs = logs.data or []

            if activity_logs:

                st.dataframe(
                    activity_logs,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info("No activity logs found")

        except Exception as e:

            st.error(f"Activity log loading failed: {e}")

    # ==============================================================================
    # PERMISSION MATRIX
    # ==============================================================================

    st.divider()
    st.subheader("👑 Permission Matrix")

    try:

        permissions = (
            supabase.table("permissions")
            .select("*")
            .execute()
            .data
            or []
        )

        if permissions:

            for role in roles:

                st.markdown(f"### 🛡 {role['name']}")

                for perm in permissions:

                    current = (
                        supabase.table("role_permissions")
                        .select("allowed")
                        .eq("role_id", role["id"])
                        .eq("permission_id", perm["id"])
                        .execute()
                    )

                    allowed = False

                    if current.data:
                        allowed = current.data[0]["allowed"]

                    new_value = st.checkbox(
                        perm["permission_name"],
                        value=allowed,
                        key=f"{role['id']}_{perm['id']}",
                    )

                    if new_value != allowed:

                        if current.data:

                            supabase.table("role_permissions").update(
                                {"allowed": new_value}
                            ).eq("role_id", role["id"]).eq(
                                "permission_id",
                                perm["id"],
                            ).execute()

                        else:

                            supabase.table("role_permissions").insert(
                                {
                                    "role_id": role["id"],
                                    "permission_id": perm["id"],
                                    "allowed": new_value,
                                }
                            ).execute()

                        st.rerun()

        else:

            st.info("No permissions found in database.")

    except Exception as e:

        st.error(f"Permission Matrix Error: {e}")


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
