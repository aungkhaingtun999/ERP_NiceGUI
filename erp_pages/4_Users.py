import hashlib
import pandas as pd
import streamlit as st

from auth import require_admin, get_current_shop_id, is_shop_owner, get_current_user
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
    
    # Get current user and shop info
    current_user = get_current_user()
    current_shop_id = get_current_shop_id()
    is_owner = is_shop_owner()

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
    # LOAD SHOPS (for shop selection)
    # --------------------------------------------------------------------------

    try:
        # Owner/Admin can see all shops, others only their own
        if is_owner:
            shops_resp = supabase.table("shops").select("id,name,code").execute()
        else:
            shops_resp = supabase.table("shops").select("id,name,code").eq("id", current_shop_id).execute()
        
        shops = shops_resp.data or []
    except Exception:
        shops = []

    shop_map = {s["name"]: s["id"] for s in shops}
    shop_names = list(shop_map.keys())

    # --------------------------------------------------------------------------
    # LOAD BRANCHES
    # --------------------------------------------------------------------------

    try:
        if is_owner:
            branches_resp = supabase.table("branches").select("id,name,shop_id").execute()
        else:
            branches_resp = supabase.table("branches").select("id,name,shop_id").eq("shop_id", current_shop_id).execute()
        
        branches = branches_resp.data or []
    except Exception:
        branches = []

    # --------------------------------------------------------------------------
    # LOAD USERS (Multi-Tenant)
    # --------------------------------------------------------------------------

    try:
        query = supabase.table("users").select(
            "id, username, full_name, role_id, is_active, shop_id, branch_id, tenant_role"
        )
        
        # Owner/Admin can see all users, others only their shop
        if not is_owner and current_shop_id:
            query = query.eq("shop_id", current_shop_id)
        
        users_resp = query.execute()
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
    # CREATE USER (Multi-Tenant)
    # --------------------------------------------------------------------------

    with st.expander("➕ Create New User"):

        with st.form("create_user_form"):

            username = st.text_input("Username")
            full_name = st.text_input("Full Name")
            password = st.text_input("Password", type="password")

            # Shop selection
            if len(shops) > 1 and is_owner:
                selected_shop = st.selectbox("Shop", shop_names)
                selected_shop_id = shop_map[selected_shop]
            else:
                selected_shop_id = shops[0]["id"] if shops else None
                if shops:
                    st.info(f"🏪 Shop: {shops[0]['name']}")

            # Branch selection (filter by selected shop)
            if selected_shop_id:
                branch_options = [b for b in branches if b.get("shop_id") == selected_shop_id]
            else:
                branch_options = []
            
            branch_names = [b["name"] for b in branch_options] if branch_options else ["No Branch"]
            selected_branch = st.selectbox("Branch", branch_names)
            selected_branch_id = branch_options[0]["id"] if branch_options and selected_branch != "No Branch" else None

            # Tenant Role
            tenant_role = st.selectbox(
                "Tenant Role",
                ["staff", "manager", "admin", "owner"],
                help="staff=Normal user, manager=Can manage team, admin=Can manage shop, owner=Full access"
            )

            selected_role = st.selectbox("Role", role_names)
            active = st.checkbox("Active", value=True)

            submit = st.form_submit_button("Create User")

            if submit:

                if not username or not password:

                    notify_error("Username and password required")

                else:

                    try:

                        # Check if username already exists
                        existing = supabase.table("users").select("id").eq("username", username).execute()
                        
                        if existing.data and len(existing.data) > 0:
                            notify_error(f"❌ Username '{username}' already exists. Please choose a different username.")
                        
                        else:
                            supabase.table("users").insert(
                                {
                                    "username": username,
                                    "full_name": full_name,
                                    "password_hash": hash_password(password),
                                    "role_id": role_map[selected_role],
                                    "shop_id": selected_shop_id,
                                    "branch_id": selected_branch_id,
                                    "tenant_role": tenant_role,
                                    "is_active": active,
                                }
                            ).execute()

                            notify_success(f"✅ User '{username}' created successfully")
                            st.rerun()

                    except Exception as e:
                        
                        error_msg = str(e)
                        
                        if "duplicate key value violates unique constraint" in error_msg:
                            notify_error(f"❌ Username '{username}' already exists. Please choose a different username.")
                        else:
                            notify_error(f"❌ Create user failed: {e}")

    st.divider()

    # ==============================================================================
    # USER TABLE (Multi-Tenant)
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
            
            shop_name = next(
                (s["name"] for s in shops if s["id"] == u.get("shop_id")),
                "N/A",
            )
            
            branch_name = next(
                (b["name"] for b in branches if b["id"] == u.get("branch_id")),
                "N/A",
            )

            table_rows.append(
                {
                    "Username": u.get("username"),
                    "Full Name": u.get("full_name"),
                    "Shop": shop_name,
                    "Branch": branch_name,
                    "Tenant Role": u.get("tenant_role", "staff"),
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
        # EDIT USER (Multi-Tenant)
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
            
            # Shop selection (only if owner/admin)
            if is_owner and len(shops) > 1:
                current_shop_name = next(
                    (s["name"] for s in shops if s["id"] == selected_user.get("shop_id")),
                    shop_names[0] if shop_names else ""
                )
                new_shop = st.selectbox("Shop", shop_names, index=shop_names.index(current_shop_name) if current_shop_name in shop_names else 0)
                new_shop_id = shop_map[new_shop]
            else:
                new_shop_id = selected_user.get("shop_id") or current_shop_id
                
            # Filter branches by selected shop
            if new_shop_id:
                branch_options = [b for b in branches if b.get("shop_id") == new_shop_id]
            else:
                branch_options = []
                
            branch_names = [b["name"] for b in branch_options] if branch_options else ["No Branch"]
            current_branch_name = next(
                (b["name"] for b in branches if b["id"] == selected_user.get("branch_id")),
                branch_names[0] if branch_names else "No Branch"
            )
            
            if branch_names:
                new_branch = st.selectbox("Branch", branch_names, index=branch_names.index(current_branch_name) if current_branch_name in branch_names else 0)
                new_branch_id = branch_options[branch_names.index(new_branch)]["id"] if branch_options else None
            else:
                new_branch_id = None
                st.info("No branches available")

            # Tenant Role
            current_tenant_role = selected_user.get("tenant_role", "staff")
            tenant_role_options = ["staff", "manager", "admin", "owner"]
            new_tenant_role = st.selectbox(
                "Tenant Role",
                tenant_role_options,
                index=tenant_role_options.index(current_tenant_role) if current_tenant_role in tenant_role_options else 0,
                help="staff=Normal user, manager=Can manage team, admin=Can manage shop, owner=Full access"
            )

            new_active = st.toggle("Active", value=selected_user.get("is_active", True))

            col1, col2 = st.columns(2)

            # UPDATE
            with col1:

                if st.button("💾 Update User", use_container_width=True):

                    try:

                        update_data = {
                            "full_name": new_full_name,
                            "role_id": role_map[new_role],
                            "shop_id": new_shop_id,
                            "branch_id": new_branch_id,
                            "tenant_role": new_tenant_role,
                            "is_active": new_active,
                        }
                        
                        supabase.table("users").update(update_data).eq("id", selected_user_id).execute()

                        create_activity_log(
                            st.session_state.get("user_id"),
                            "UPDATE_USER",
                            f"Updated user {selected_user['username']}",
                        )

                        notify_success("✅ User updated successfully")
                        st.rerun()

                    except Exception as e:

                        notify_error(f"❌ Update failed: {e}")

            # DELETE
            with col2:

                if selected_user.get("username") == "admin":

                    st.info("⚠️ System admin cannot be deleted")

                else:

                    if st.button("🗑 Delete User", use_container_width=True):

                        try:

                            supabase.table("users").delete().eq("id", selected_user_id).execute()

                            create_activity_log(
                                st.session_state.get("user_id"),
                                "DELETE_USER",
                                f"Deleted user {selected_user['username']}",
                            )

                            notify_success("✅ User deleted successfully")
                            st.rerun()

                        except Exception as e:

                            notify_error(f"❌ Delete failed: {e}")

            st.divider()

            # ------------------------------------------------------------------
            # RESET PASSWORD
            # ------------------------------------------------------------------

            st.subheader("🔐 Reset Password")

            new_password = st.text_input(
                "New Password",
                type="password",
            )

            if st.button("💾 Save Password", use_container_width=True):

                if not new_password:

                    notify_error("❌ Password required")

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

                        notify_success("✅ Password reset successfully")
                        st.rerun()

                    except Exception as e:

                        notify_error(f"❌ Reset failed: {e}")

    # ==============================================================================
    # SUMMARY
    # ==============================================================================

    total = len(users)
    active_count = sum(
        1 for u in users if u.get("is_active", False)
    )
    
    # Count by shop
    shop_counts = {}
    for u in users:
        shop_id = u.get("shop_id")
        if shop_id:
            shop_name = next((s["name"] for s in shops if s["id"] == shop_id), "Unknown")
            shop_counts[shop_name] = shop_counts.get(shop_name, 0) + 1

    st.divider()
    st.subheader("📊 System Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("👥 Users", total)
    c2.metric("🟢 Active", active_count)
    c3.metric("🔴 Disabled", total - active_count)
    c4.metric("🛡 Roles", len(roles))
    
    # Shop distribution
    if shop_counts:
        st.divider()
        st.subheader("🏪 Users by Shop")
        for shop_name, count in shop_counts.items():
            st.metric(shop_name, count)

    # ==============================================================================
    # ACTIVITY LOG
    # ==============================================================================

    st.divider()

    with st.expander("📝 User Activity Log", expanded=False):

        try:

            logs = (
                supabase.table("user_activity_logs")
                .select("action, description, created_at")
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
