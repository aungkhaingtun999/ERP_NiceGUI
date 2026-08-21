import hashlib
import pandas as pd
import streamlit as st
from datetime import datetime

from auth import require_admin, get_current_shop_id, is_shop_owner, get_current_user
from database import get_supabase
from utils.notification import (
    notify_error,
    notify_success,
    notify_warning,
    notify_info,
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
                    "created_at": datetime.now().isoformat()
                }
            ).execute()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # VALIDATION FUNCTIONS
    # --------------------------------------------------------------------------

    def validate_username(username):
        """Validate username format"""
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        if not username.isalnum() and '_' not in username:
            return False, "Username can only contain letters, numbers and underscore"
        return True, ""

    def validate_password(password):
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        return True, ""

    def validate_full_name(full_name):
        """Validate full name"""
        if not full_name or len(full_name.strip()) < 2:
            return False, "Full name must be at least 2 characters long"
        return True, ""

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
    # LOAD SHOPS
    # --------------------------------------------------------------------------

    try:
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
            "id, username, full_name, role_id, is_active, shop_id, branch_id, tenant_role, created_at, last_login"
        )
        
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

    search = st.text_input("🔍 Search User", placeholder="Search by username or full name...")

    if search:
        search = search.lower()
        users = [
            u for u in users
            if search in str(u.get("username", "")).lower()
            or search in str(u.get("full_name", "")).lower()
        ]

    # --------------------------------------------------------------------------
    # STATISTICS ROW
    # --------------------------------------------------------------------------

    col1, col2, col3, col4, col5 = st.columns(5)
    total_users = len(users)
    active_users = sum(1 for u in users if u.get("is_active", False))
    inactive_users = total_users - active_users
    shop_owners = sum(1 for u in users if u.get("tenant_role") == "owner")
    staff_users = total_users - shop_owners

    with col1:
        st.metric("👥 Total Users", total_users)
    with col2:
        st.metric("🟢 Active", active_users, delta=f"{active_users}" if active_users > 0 else None)
    with col3:
        st.metric("🔴 Inactive", inactive_users, delta=f"-{inactive_users}" if inactive_users > 0 else None)
    with col4:
        st.metric("👑 Shop Owners", shop_owners)
    with col5:
        st.metric("👤 Staff", staff_users)

    st.divider()

    # --------------------------------------------------------------------------
    # CREATE USER (Multi-Tenant with Full Validation)
    # --------------------------------------------------------------------------

    with st.expander("➕ Create New User", expanded=False):

        with st.form("create_user_form"):

            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input(
                    "Username *",
                    placeholder="Enter username (min 3 characters)",
                    help="Letters, numbers and underscore only"
                )
                full_name = st.text_input(
                    "Full Name *",
                    placeholder="Enter full name"
                )
                password = st.text_input(
                    "Password *",
                    type="password",
                    placeholder="Enter password (min 6 characters)",
                    help="Minimum 6 characters"
                )

            with col2:
                # Shop selection
                if len(shops) > 1 and is_owner:
                    selected_shop = st.selectbox("Shop *", shop_names)
                    selected_shop_id = shop_map[selected_shop]
                else:
                    selected_shop_id = shops[0]["id"] if shops else None
                    if shops:
                        st.info(f"🏪 Shop: {shops[0]['name']}")

                # Branch selection
                if selected_shop_id:
                    branch_options = [b for b in branches if b.get("shop_id") == selected_shop_id]
                else:
                    branch_options = []
                
                branch_names = [b["name"] for b in branch_options] if branch_options else ["No Branch"]
                selected_branch = st.selectbox("Branch", branch_names)
                selected_branch_id = branch_options[0]["id"] if branch_options and selected_branch != "No Branch" else None

                tenant_role = st.selectbox(
                    "Tenant Role *",
                    ["staff", "manager", "admin", "owner"],
                    help="staff=Normal user, manager=Can manage team, admin=Can manage shop, owner=Full access"
                )

                selected_role = st.selectbox("System Role *", role_names)
                active = st.checkbox("Active", value=True)

            st.caption("⚠️ Fields with * are required")

            submit = st.form_submit_button("✅ Create User", use_container_width=True)

            if submit:

                # =============================================
                # VALIDATION
                # =============================================

                errors = []

                # Validate username
                valid, msg = validate_username(username)
                if not valid:
                    errors.append(msg)

                # Validate password
                valid, msg = validate_password(password)
                if not valid:
                    errors.append(msg)

                # Validate full name
                valid, msg = validate_full_name(full_name)
                if not valid:
                    errors.append(msg)

                # Show validation errors
                if errors:
                    for error in errors:
                        notify_error(f"❌ {error}")
                    return

                # =============================================
                # CREATE USER
                # =============================================

                try:
                    # Check if username already exists
                    existing = supabase.table("users").select("id").eq("username", username).execute()
                    
                    if existing.data and len(existing.data) > 0:
                        notify_error(f"❌ Username '{username}' already exists. Please choose a different username.")
                    
                    else:
                        # Create user
                        new_user = {
                            "username": username,
                            "full_name": full_name,
                            "password_hash": hash_password(password),
                            "role_id": role_map[selected_role],
                            "shop_id": selected_shop_id,
                            "branch_id": selected_branch_id,
                            "tenant_role": tenant_role,
                            "is_active": active,
                            "created_at": datetime.now().isoformat()
                        }
                        
                        result = supabase.table("users").insert(new_user).execute()

                        if result.data:
                            # Get created user ID
                            new_user_id = result.data[0].get("id")
                            
                            # Log activity
                            create_activity_log(
                                st.session_state.get("user_id"),
                                "CREATE_USER",
                                f"Created user '{username}' with role '{selected_role}' and tenant role '{tenant_role}'"
                            )

                            # Success notification with details
                            st.success(f"""
                            ✅ **User created successfully!**

                            | Field | Value |
                            |-------|-------|
                            | **Username** | `{username}` |
                            | **Full Name** | {full_name} |
                            | **System Role** | {selected_role} |
                            | **Tenant Role** | {tenant_role} |
                            | **Status** | {"🟢 Active" if active else "🔴 Inactive"} |
                            """)
                            
                            st.balloons()
                            st.rerun()
                        else:
                            notify_error("❌ Failed to create user: No data returned")

                except Exception as e:
                    error_msg = str(e)
                    if "duplicate key value violates unique constraint" in error_msg:
                        notify_error(f"❌ Username '{username}' already exists. Please choose a different username.")
                    else:
                        notify_error(f"❌ Create user failed: {error_msg}")

    st.divider()

    # ==============================================================================
    # USER TABLE (Multi-Tenant)
    # ==============================================================================

    st.subheader("📋 Users")

    if not users:
        st.info("📭 No users found. Create your first user above.")
    else:
        # Convert to DataFrame for display
        table_rows = []
        for u in users:
            role_name = next(
                (r["name"] for r in roles if r["id"] == u["role_id"]),
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

            # Format dates
            created_at = u.get("created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        created_at = created_at[:10]
                except:
                    created_at = "N/A"
            else:
                created_at = "N/A"

            table_rows.append({
                "Username": u.get("username"),
                "Full Name": u.get("full_name"),
                "Shop": shop_name,
                "Branch": branch_name,
                "Tenant Role": u.get("tenant_role", "staff"),
                "System Role": role_name,
                "Status": "🟢 Active" if u.get("is_active") else "🔴 Disabled",
                "Created": created_at,
            })

        df_users = pd.DataFrame(table_rows)

        st.dataframe(
            df_users,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.TextColumn(
                    "Status",
                    help="User account status"
                ),
                "Created": st.column_config.TextColumn(
                    "Created",
                    help="User creation date"
                ),
            }
        )

        st.caption(f"📊 Showing {len(users)} users")

        st.divider()

        # ----------------------------------------------------------------------
        # EDIT USER (Multi-Tenant)
        # ----------------------------------------------------------------------

        st.subheader("✏️ Edit User")

        if not users:
            st.info("No users available to edit")
        else:
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
                (u for u in users if str(u["id"]) == selected_user_id),
                None,
            )

            if selected_user:
                # Display user info
                with st.container(border=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Username:** `{selected_user.get('username')}`")
                    with col2:
                        st.write(f"**Created:** {selected_user.get('created_at', 'N/A')[:10] if selected_user.get('created_at') else 'N/A'}")

                current_role_name = next(
                    (r["name"] for r in roles if r["id"] == selected_user["role_id"]),
                    role_names[0],
                )

                col1, col2 = st.columns(2)

                with col1:
                    new_full_name = st.text_input(
                        "Full Name",
                        value=selected_user.get("full_name", ""),
                    )
                    new_role = st.selectbox(
                        "System Role",
                        role_names,
                        index=role_names.index(current_role_name),
                    )

                with col2:
                    # Shop selection
                    if is_owner and len(shops) > 1:
                        current_shop_name = next(
                            (s["name"] for s in shops if s["id"] == selected_user.get("shop_id")),
                            shop_names[0] if shop_names else ""
                        )
                        new_shop = st.selectbox("Shop", shop_names, index=shop_names.index(current_shop_name) if current_shop_name in shop_names else 0)
                        new_shop_id = shop_map[new_shop]
                    else:
                        new_shop_id = selected_user.get("shop_id") or current_shop_id
                        
                    # Filter branches
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

                col1, col2, col3 = st.columns(3)

                # UPDATE
                with col1:
                    if st.button("💾 Update User", use_container_width=True, type="primary"):
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

                            notify_success(f"✅ User '{selected_user['username']}' updated successfully")
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

                                notify_success(f"✅ User '{selected_user['username']}' deleted successfully")
                                st.rerun()

                            except Exception as e:
                                notify_error(f"❌ Delete failed: {e}")

                # RESET PASSWORD
                with col3:
                    with st.popover("🔐 Reset Password"):
                        new_password = st.text_input(
                            "New Password",
                            type="password",
                            placeholder="Enter new password (min 6 chars)"
                        )
                        
                        if st.button("💾 Save Password", use_container_width=True):
                            if not new_password:
                                notify_error("❌ Password required")
                            elif len(new_password) < 6:
                                notify_error("❌ Password must be at least 6 characters")
                            else:
                                try:
                                    supabase.table("users").update({
                                        "password_hash": hash_password(new_password)
                                    }).eq("id", selected_user_id).execute()

                                    create_activity_log(
                                        st.session_state.get("user_id"),
                                        "RESET_PASSWORD",
                                        f"Reset password for {selected_user['username']}",
                                    )

                                    notify_success(f"✅ Password reset successfully for '{selected_user['username']}'")
                                    st.rerun()

                                except Exception as e:
                                    notify_error(f"❌ Reset failed: {e}")

                st.divider()

                # ------------------------------------------------------------------
                # USER LOGIN HISTORY
                # ------------------------------------------------------------------

                with st.expander("📋 Login History", expanded=False):
                    try:
                        login_logs = (
                            supabase.table("user_activity_logs")
                            .select("action, description, created_at")
                            .eq("user_id", selected_user_id)
                            .order("created_at", desc=True)
                            .limit(20)
                            .execute()
                        )
                        
                        if login_logs.data:
                            st.dataframe(login_logs.data, use_container_width=True, hide_index=True)
                        else:
                            st.info("No login history found")
                    except Exception as e:
                        st.error(f"Failed to load login history: {e}")

    # ==============================================================================
    # ACTIVITY LOG (All Users)
    # ==============================================================================

    st.divider()

    with st.expander("📝 Recent User Activity Log", expanded=False):

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
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
