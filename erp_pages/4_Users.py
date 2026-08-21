import hashlib
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any, List

from auth import (
    require_admin,
    require_maker,
    require_checker,
    get_current_shop_id,
    is_shop_owner,
    get_current_user,
    is_maker,
    is_checker,
    get_current_tenant_role
)
from database import get_supabase
from utils.notification import (
    notify_error,
    notify_success,
    notify_warning,
    notify_info,
    show_notification,
)


# ==============================================================================
# CONSTANTS
# ==============================================================================

TENANT_ROLES = ["staff", "manager", "admin", "owner"]
TENANT_ROLE_LABELS = {
    "staff": "👤 Staff",
    "manager": "📋 Manager",
    "admin": "🔧 Admin",
    "owner": "👑 Owner"
}
SYSTEM_ROLE_MAP = {1: "Admin", 2: "Manager", 3: "Cashier"}


# ==============================================================================
# PAGE
# ==============================================================================

def run():

    show_notification()
    require_admin()

    st.title("👥 User Management")
    st.caption("Multi-Tenant User Management with Maker-Checker Workflow")

    supabase = get_supabase()

    # Current user info
    current_user = get_current_user()
    current_user_id = current_user.get("id")
    current_shop_id = get_current_shop_id()
    is_owner = is_shop_owner()
    is_maker_user = is_maker()
    is_checker_user = is_checker()
    tenant_role = get_current_tenant_role()

    # ==========================================================================
    # HELPER FUNCTIONS
    # ==========================================================================

    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def create_activity_log(user_id: str, action: str, description: str):
        try:
            supabase.table("user_activity_logs").insert({
                "user_id": user_id,
                "action": action,
                "description": description,
                "created_at": datetime.now().isoformat()
            }).execute()
        except Exception:
            pass

    def validate_username(username: str) -> tuple:
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        if not username.isalnum() and '_' not in username:
            return False, "Username can only contain letters, numbers and underscore"
        return True, ""

    def validate_password(password: str) -> tuple:
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters"
        return True, ""

    def validate_owner_change(current_tenant: str, new_tenant: str) -> tuple:
        if current_tenant == "owner" and new_tenant not in ["owner", "admin"]:
            return False, "⚠️ Owner must first be changed to **Admin**, then to other roles."
        return True, ""

    def can_approve_request(requested_by: str) -> tuple:
        """Check if current user can approve a request"""
        current_user_id = st.session_state.get("user_id")
        
        if requested_by == current_user_id:
            # Check if user is the only owner (can self-approve)
            owners = supabase.table("users").select("id").eq("tenant_role", "owner").execute()
            if owners.data and len(owners.data) == 1 and owners.data[0]["id"] == current_user_id:
                return True, "🔑 You are the only Owner. You can self-approve."
            return False, "⛔ You cannot approve your own request. Ask another Owner."
        
        return True, ""

    # ==========================================================================
    # LOAD DATA
    # ==========================================================================

    # Load roles
    try:
        roles_resp = supabase.table("roles").select("id,name").execute()
        roles = roles_resp.data or []
    except Exception as e:
        st.error(f"Failed to load roles: {e}")
        return

    if not roles:
        st.warning("⚠️ Roles table is empty. Please create roles first.")
        return

    role_map = {r["name"]: r["id"] for r in roles}
    role_names = list(role_map.keys())

    # Load shops
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

    # Load branches
    try:
        if is_owner:
            branches_resp = supabase.table("branches").select("id,name,shop_id").execute()
        else:
            branches_resp = supabase.table("branches").select("id,name,shop_id").eq("shop_id", current_shop_id).execute()
        branches = branches_resp.data or []
    except Exception:
        branches = []

    # Load users
    try:
        query = supabase.table("users").select(
            "id, username, full_name, role_id, is_active, shop_id, branch_id, tenant_role, created_at, last_login"
        )
        if not is_owner and current_shop_id:
            query = query.eq("shop_id", current_shop_id)
        users_resp = query.execute()
        users = users_resp.data or []
    except Exception as e:
        st.error(f"Failed to load users: {e}")
        return

    # Load pending create requests
    pending_create_requests = []
    if is_checker_user or is_owner:
        try:
            requests_resp = (
                supabase.table("user_create_requests")
                .select("*, requested_by(id, username, full_name)")
                .eq("status", "pending")
                .order("requested_at", desc=True)
                .execute()
            )
            pending_create_requests = requests_resp.data or []
        except Exception:
            pass

    # Load pending edit requests
    pending_edit_requests = []
    if is_checker_user or is_owner:
        try:
            edit_req_resp = (
                supabase.table("user_edit_requests")
                .select("*, requested_by(id, username, full_name), user_id(id, username, full_name)")
                .eq("status", "pending")
                .order("requested_at", desc=True)
                .execute()
            )
            pending_edit_requests = edit_req_resp.data or []
        except Exception:
            pass

    # ==========================================================================
    # STATISTICS
    # ==========================================================================

    total_users = len(users)
    active_users = sum(1 for u in users if u.get("is_active"))
    inactive_users = total_users - active_users
    owner_count = sum(1 for u in users if u.get("tenant_role") == "owner")
    pending_total = len(pending_create_requests) + len(pending_edit_requests)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("👥 Total", total_users)
    col2.metric("🟢 Active", active_users)
    col3.metric("🔴 Inactive", inactive_users)
    col4.metric("👑 Owners", owner_count)
    col5.metric("⏳ Pending", pending_total)
    col6.metric("🛡 Roles", len(roles))

    st.divider()

    # ==========================================================================
    # TABS
    # ==========================================================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Users",
        "➕ Create Request",
        "✏️ Edit Request",
        "✅ Approvals"
    ])

    # ==========================================================================
    # TAB 1: USERS
    # ==========================================================================

    with tab1:

        # Search
        search = st.text_input(
            "🔍 Search Users",
            placeholder="Search by username or full name...",
            label_visibility="collapsed",
            key="search_users"
        )

        if search:
            search = search.lower()
            filtered_users = [
                u for u in users
                if search in str(u.get("username", "")).lower()
                or search in str(u.get("full_name", "")).lower()
            ]
        else:
            filtered_users = users

        # User table
        if not filtered_users:
            st.info("📭 No users found")
        else:
            display_data = []
            for u in filtered_users:
                role_name = next((r["name"] for r in roles if r["id"] == u["role_id"]), "Unknown")
                shop_name = next((s["name"] for s in shops if s["id"] == u.get("shop_id")), "N/A")
                display_data.append({
                    "User": u.get("username"),
                    "Name": u.get("full_name"),
                    "Shop": shop_name,
                    "Tenant": TENANT_ROLE_LABELS.get(u.get("tenant_role", "staff"), "Staff"),
                    "Role": role_name,
                    "Status": "🟢 Active" if u.get("is_active") else "🔴 Inactive",
                })

            st.dataframe(
                pd.DataFrame(display_data),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "User": st.column_config.TextColumn("Username", width="small"),
                    "Tenant": st.column_config.TextColumn("Tenant Role", width="small"),
                }
            )
            st.caption(f"📊 Showing {len(filtered_users)} of {total_users} users")

        st.divider()

        # Edit User Section
        st.subheader("✏️ Edit User")

        if not filtered_users:
            st.info("No users available")
        else:
            user_options = {str(u["id"]): f"{u['username']} - {u['full_name']}" for u in filtered_users}
            selected_user_id = st.selectbox(
                "Select User",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x],
                key="edit_user_select"
            )

            if selected_user_id:
                selected_user = next((u for u in filtered_users if str(u["id"]) == selected_user_id), None)

                if selected_user:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns(3)

                        current_tenant = selected_user.get("tenant_role", "staff")
                        current_role = next((r["name"] for r in roles if r["id"] == selected_user["role_id"]), role_names[0])
                        is_owner_user = current_tenant == "owner"
                        owner_count_total = sum(1 for u in users if u.get("tenant_role") == "owner")
                        is_last_owner = is_owner_user and owner_count_total <= 1

                        with col1:
                            st.caption(f"**User:** `{selected_user.get('username')}`")
                            st.caption(f"**Current Role:** {current_role}")
                            new_name = st.text_input("Full Name", value=selected_user.get("full_name", ""), key="edit_name")

                        with col2:
                            new_role = st.selectbox(
                                "System Role",
                                role_names,
                                index=role_names.index(current_role),
                                key="edit_role"
                            )
                            new_active = st.toggle("Active", value=selected_user.get("is_active", True), key="edit_active")

                        with col3:
                            tenant_options = TENANT_ROLES
                            current_idx = tenant_options.index(current_tenant) if current_tenant in tenant_options else 0
                            new_tenant = st.selectbox(
                                "Tenant Role",
                                tenant_options,
                                index=current_idx,
                                key="edit_tenant",
                                format_func=lambda x: TENANT_ROLE_LABELS.get(x, x)
                            )

                            if is_last_owner:
                                st.warning("⚠️ This is the last Owner. Cannot change tenant role.")

                        # Validate
                        valid, msg = validate_owner_change(current_tenant, new_tenant)
                        if is_last_owner and new_tenant != "owner":
                            valid = False
                            msg = "⚠️ Cannot change the last Owner. Create another Owner first."

                        has_changes = (
                            new_name != selected_user.get("full_name") or
                            new_role != current_role or
                            new_tenant != current_tenant or
                            new_active != selected_user.get("is_active", True)
                        )

                        col_a, col_b, col_c = st.columns(3)

                        # Direct Update (Owner only)
                        with col_a:
                            if is_owner or is_checker_user:
                                if st.button("💾 Update Direct", use_container_width=True, type="primary", key="update_direct"):
                                    if not valid:
                                        notify_error(msg)
                                    elif not has_changes:
                                        notify_info("No changes detected")
                                    else:
                                        try:
                                            update_data = {
                                                "full_name": new_name,
                                                "role_id": role_map[new_role],
                                                "tenant_role": new_tenant,
                                                "is_active": new_active,
                                            }
                                            supabase.table("users").update(update_data).eq("id", selected_user_id).execute()
                                            create_activity_log(
                                                current_user_id,
                                                "UPDATE_USER_DIRECT",
                                                f"Directly updated user '{selected_user['username']}'"
                                            )
                                            notify_success(f"✅ '{selected_user['username']}' updated")
                                            st.rerun()
                                        except Exception as e:
                                            notify_error(f"❌ Update failed: {e}")
                            else:
                                st.info("👑 Only Owner can update directly")

                        # Submit Request (Maker)
                        with col_b:
                            if is_maker_user or is_owner:
                                if st.button("📤 Submit Request", use_container_width=True, key="submit_edit"):
                                    if not valid:
                                        notify_error(msg)
                                    elif not has_changes:
                                        notify_info("No changes to submit")
                                    else:
                                        try:
                                            # Check existing pending request
                                            existing = supabase.table("user_edit_requests").select("id").eq("user_id", selected_user_id).eq("status", "pending").execute()
                                            if existing.data:
                                                notify_warning("⚠️ Pending request already exists")
                                            else:
                                                supabase.table("user_edit_requests").insert({
                                                    "requested_by": current_user_id,
                                                    "user_id": selected_user_id,
                                                    "new_full_name": new_name,
                                                    "new_role_id": role_map[new_role],
                                                    "new_tenant_role": new_tenant,
                                                    "new_is_active": new_active,
                                                    "old_full_name": selected_user.get("full_name"),
                                                    "old_role_id": selected_user["role_id"],
                                                    "old_tenant_role": current_tenant,
                                                    "old_is_active": selected_user.get("is_active", True),
                                                    "status": "pending",
                                                    "requested_at": datetime.now().isoformat()
                                                }).execute()
                                                create_activity_log(
                                                    current_user_id,
                                                    "EDIT_USER_REQUEST",
                                                    f"Submitted edit request for '{selected_user['username']}'"
                                                )
                                                notify_success(f"✅ Edit request for '{selected_user['username']}' submitted")
                                                st.rerun()
                                        except Exception as e:
                                            notify_error(f"❌ Failed: {e}")
                            else:
                                st.info("🔧 Only Maker can submit request")

                        # Reset Password
                        with col_c:
                            if selected_user.get("username") != "admin":
                                with st.popover("🔐 Reset Password"):
                                    new_pass = st.text_input("New Password", type="password", placeholder="Min 6 chars")
                                    if st.button("Save Password", use_container_width=True):
                                        if new_pass and len(new_pass) >= 6:
                                            try:
                                                supabase.table("users").update({"password_hash": hash_password(new_pass)}).eq("id", selected_user_id).execute()
                                                create_activity_log(
                                                    current_user_id,
                                                    "RESET_PASSWORD",
                                                    f"Reset password for '{selected_user['username']}'"
                                                )
                                                notify_success("✅ Password reset")
                                                st.rerun()
                                            except Exception as e:
                                                notify_error(f"❌ Failed: {e}")
                                        else:
                                            notify_error("❌ Password must be at least 6 characters")
                            else:
                                st.info("🔒 Admin protected")

    # ==========================================================================
    # TAB 2: CREATE REQUEST
    # ==========================================================================

    with tab2:

        if not is_maker_user and not is_owner:
            st.warning("⚠️ Only Admin (Maker) can create user requests.")
        else:
            st.subheader("📝 Create New User Request")
            st.caption("Submit for approval. Owner (Checker) must approve.")

            with st.form("create_request_form", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    username = st.text_input("Username *", placeholder="Min 3 characters", key="create_username")
                    full_name = st.text_input("Full Name *", key="create_fullname")
                    password = st.text_input("Password *", type="password", placeholder="Min 6 characters", key="create_password")

                with col2:
                    if len(shops) > 1 and is_owner:
                        selected_shop = st.selectbox("Shop", shop_names, key="create_shop")
                        selected_shop_id = shop_map[selected_shop]
                    else:
                        selected_shop_id = shops[0]["id"] if shops else None

                    tenant_role = st.selectbox(
                        "Tenant Role *",
                        TENANT_ROLES,
                        format_func=lambda x: TENANT_ROLE_LABELS.get(x, x),
                        key="create_tenant"
                    )
                    selected_role = st.selectbox("System Role *", role_names, key="create_role")
                    is_active = st.checkbox("Active", value=True, key="create_active")

                st.caption("⚠️ Fields with * are required")
                st.info("📌 Request will be sent to Owner (Checker) for approval")

                if st.form_submit_button("📤 Submit Request", use_container_width=True, type="primary"):
                    valid, msg = validate_username(username)
                    if not valid:
                        notify_error(msg)
                    elif not full_name or len(full_name.strip()) < 2:
                        notify_error("❌ Full name must be at least 2 characters")
                    else:
                        valid, msg = validate_password(password)
                        if not valid:
                            notify_error(msg)
                        else:
                            try:
                                existing = supabase.table("users").select("id").eq("username", username).execute()
                                if existing.data:
                                    notify_error(f"❌ Username '{username}' already exists")
                                else:
                                    supabase.table("user_create_requests").insert({
                                        "requested_by": current_user_id,
                                        "username": username,
                                        "full_name": full_name,
                                        "password_hash": hash_password(password),
                                        "role_id": role_map[selected_role],
                                        "shop_id": selected_shop_id,
                                        "branch_id": None,
                                        "tenant_role": tenant_role,
                                        "is_active": is_active,
                                        "status": "pending",
                                        "requested_at": datetime.now().isoformat()
                                    }).execute()
                                    create_activity_log(
                                        current_user_id,
                                        "CREATE_USER_REQUEST",
                                        f"Requested to create user '{username}'"
                                    )
                                    notify_success(f"✅ Request for '{username}' submitted for approval")
                                    st.rerun()
                            except Exception as e:
                                notify_error(f"❌ Failed: {e}")

    # ==========================================================================
    # TAB 3: EDIT REQUEST
    # ==========================================================================

    with tab3:

        if not is_maker_user and not is_owner:
            st.warning("⚠️ Only Admin (Maker) can submit edit requests.")
        else:
            st.subheader("✏️ Edit User Request")
            st.caption("Select a user and submit edit request for approval")

            if not filtered_users:
                st.info("No users available")
            else:
                opts = {str(u["id"]): f"{u['username']} - {u['full_name']}" for u in filtered_users}
                selected_id = st.selectbox("Select User", options=list(opts.keys()), format_func=lambda x: opts[x], key="edit_tab_select")

                if selected_id:
                    selected = next((u for u in filtered_users if str(u["id"]) == selected_id), None)

                    if selected:
                        # Check existing pending
                        pending = supabase.table("user_edit_requests").select("id").eq("user_id", selected_id).eq("status", "pending").execute()
                        if pending.data:
                            st.warning("⚠️ This user already has a pending edit request")

                        current_tenant = selected.get("tenant_role", "staff")
                        is_owner_user = current_tenant == "owner"
                        owner_count_total = sum(1 for u in users if u.get("tenant_role") == "owner")
                        is_last_owner = is_owner_user and owner_count_total <= 1

                        if is_last_owner:
                            st.warning("⚠️ This is the last Owner. Cannot submit edit request.")

                        with st.container(border=True):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.caption(f"**User:** `{selected.get('username')}`")
                                new_name = st.text_input("New Full Name", value=selected.get("full_name", ""), key="edit_tab_name", disabled=is_last_owner)
                                current_role = next((r["name"] for r in roles if r["id"] == selected["role_id"]), role_names[0])
                                new_role = st.selectbox("New System Role", role_names, index=role_names.index(current_role), key="edit_tab_role", disabled=is_last_owner)

                            with col2:
                                tenant_options = TENANT_ROLES
                                current_idx = tenant_options.index(current_tenant) if current_tenant in tenant_options else 0
                                new_tenant = st.selectbox(
                                    "New Tenant Role",
                                    tenant_options,
                                    index=current_idx,
                                    key="edit_tab_tenant",
                                    format_func=lambda x: TENANT_ROLE_LABELS.get(x, x),
                                    disabled=is_last_owner
                                )
                                new_active = st.toggle("New Status", value=selected.get("is_active", True), key="edit_tab_active", disabled=is_last_owner)

                            valid, msg = validate_owner_change(current_tenant, new_tenant)
                            if not valid:
                                st.warning(msg)

                            if not is_last_owner and not pending.data and valid:
                                if st.button("📤 Submit Edit Request", use_container_width=True, type="primary", key="submit_tab_edit"):
                                    try:
                                        supabase.table("user_edit_requests").insert({
                                            "requested_by": current_user_id,
                                            "user_id": selected_id,
                                            "new_full_name": new_name,
                                            "new_role_id": role_map[new_role],
                                            "new_tenant_role": new_tenant,
                                            "new_is_active": new_active,
                                            "old_full_name": selected.get("full_name"),
                                            "old_role_id": selected["role_id"],
                                            "old_tenant_role": current_tenant,
                                            "old_is_active": selected.get("is_active", True),
                                            "status": "pending",
                                            "requested_at": datetime.now().isoformat()
                                        }).execute()
                                        create_activity_log(
                                            current_user_id,
                                            "EDIT_USER_REQUEST",
                                            f"Submitted edit request for '{selected['username']}'"
                                        )
                                        notify_success(f"✅ Edit request for '{selected['username']}' submitted")
                                        st.rerun()
                                    except Exception as e:
                                        notify_error(f"❌ Failed: {e}")
                            elif pending.data:
                                notify_info("📌 Pending request already exists")

    # ==========================================================================
    # TAB 4: APPROVALS
    # ==========================================================================

    with tab4:

        if not is_checker_user and not is_owner:
            st.warning("⚠️ Only Owner (Checker) can approve/reject requests.")
        else:

            # ------------------------------------------------------------------
            # CREATE REQUESTS
            # ------------------------------------------------------------------

            st.subheader(f"📝 Create Requests ({len(pending_create_requests)})")

            if not pending_create_requests:
                st.info("No pending create requests")
            else:
                for idx, req in enumerate(pending_create_requests):
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            st.write(f"**Create: {req.get('username')}** - {req.get('full_name')}")
                            st.caption(f"Role: {next((r['name'] for r in roles if r['id'] == req.get('role_id')), 'Unknown')}")
                            st.caption(f"Tenant: {TENANT_ROLE_LABELS.get(req.get('tenant_role', 'staff'), 'Staff')}")
                            requested_by = req.get('requested_by', {})
                            if requested_by:
                                st.caption(f"By: {requested_by.get('full_name', 'Unknown')}")

                        with col2:
                            requester_id = req.get('requested_by', {}).get('id')
                            can_approve, msg = can_approve_request(requester_id)

                            if can_approve:
                                if st.button("✅ Approve", key=f"app_c_{req['id']}_{idx}", use_container_width=True, type="primary"):
                                    try:
                                        # Create user
                                        supabase.table("users").insert({
                                            "username": req.get("username"),
                                            "full_name": req.get("full_name"),
                                            "password_hash": req.get("password_hash"),
                                            "role_id": req.get("role_id"),
                                            "shop_id": req.get("shop_id"),
                                            "branch_id": req.get("branch_id"),
                                            "tenant_role": req.get("tenant_role", "staff"),
                                            "is_active": req.get("is_active", True),
                                        }).execute()

                                        # Update request
                                        supabase.table("user_create_requests").update({
                                            "status": "approved",
                                            "checked_by": current_user_id,
                                            "checked_at": datetime.now().isoformat()
                                        }).eq("id", req["id"]).execute()

                                        create_activity_log(
                                            current_user_id,
                                            "APPROVE_CREATE",
                                            f"Approved user creation for '{req['username']}'"
                                        )
                                        notify_success(f"✅ {req['username']} created")
                                        st.rerun()
                                    except Exception as e:
                                        notify_error(f"❌ Approval failed: {e}")
                            else:
                                st.warning(msg)

                        with col3:
                            with st.popover("❌ Reject"):
                                reason = st.text_input("Reason", key=f"rej_c_{req['id']}_{idx}")
                                if st.button("Confirm Reject", key=f"rej_c_confirm_{req['id']}_{idx}"):
                                    try:
                                        supabase.table("user_create_requests").update({
                                            "status": "rejected",
                                            "checked_by": current_user_id,
                                            "checked_at": datetime.now().isoformat(),
                                            "rejection_reason": reason or "No reason provided"
                                        }).eq("id", req["id"]).execute()
                                        create_activity_log(
                                            current_user_id,
                                            "REJECT_CREATE",
                                            f"Rejected user creation for '{req['username']}': {reason or 'No reason'}"
                                        )
                                        notify_warning(f"❌ {req['username']} rejected")
                                        st.rerun()
                                    except Exception as e:
                                        notify_error(f"❌ Rejection failed: {e}")

            st.divider()

            # ------------------------------------------------------------------
            # EDIT REQUESTS
            # ------------------------------------------------------------------

            st.subheader(f"✏️ Edit Requests ({len(pending_edit_requests)})")

            if not pending_edit_requests:
                st.info("No pending edit requests")
            else:
                for idx, req in enumerate(pending_edit_requests):
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            target = req.get('user_id', {})
                            st.write(f"**Edit: {target.get('username', 'Unknown')}**")
                            st.caption(f"Name: {req.get('old_full_name')} → {req.get('new_full_name')}")
                            st.caption(f"System Role: {next((r['name'] for r in roles if r['id'] == req.get('old_role_id')), 'Unknown')} → {next((r['name'] for r in roles if r['id'] == req.get('new_role_id')), 'Unknown')}")
                            st.caption(f"Tenant: {TENANT_ROLE_LABELS.get(req.get('old_tenant_role', 'staff'), 'Staff')} → {TENANT_ROLE_LABELS.get(req.get('new_tenant_role', 'staff'), 'Staff')}")
                            requested_by = req.get('requested_by', {})
                            if requested_by:
                                st.caption(f"By: {requested_by.get('full_name', 'Unknown')}")

                        with col2:
                            # Check if this edit would remove last owner
                            target_id = req.get("user_id")
                            target_user = next((u for u in users if u["id"] == target_id), None)
                            is_target_owner = target_user and target_user.get("tenant_role") == "owner"
                            owner_count_total = sum(1 for u in users if u.get("tenant_role") == "owner")
                            is_last_owner = is_target_owner and owner_count_total <= 1

                            if is_last_owner and req.get("new_tenant_role") != "owner":
                                st.warning("🚫 Cannot change last Owner! Create another Owner first.")
                            else:
                                requester_id = req.get('requested_by', {}).get('id')
                                can_approve, msg = can_approve_request(requester_id)

                                if can_approve:
                                    if st.button("✅ Approve", key=f"app_e_{req['id']}_{idx}", use_container_width=True, type="primary"):
                                        try:
                                            update_data = {}
                                            if req.get('new_full_name'):
                                                update_data["full_name"] = req.get('new_full_name')
                                            if req.get('new_role_id'):
                                                update_data["role_id"] = req.get('new_role_id')
                                            if req.get('new_tenant_role'):
                                                update_data["tenant_role"] = req.get('new_tenant_role')
                                            if req.get('new_is_active') is not None:
                                                update_data["is_active"] = req.get('new_is_active')

                                            supabase.table("users").update(update_data).eq("id", req["user_id"]).execute()

                                            supabase.table("user_edit_requests").update({
                                                "status": "approved",
                                                "checked_by": current_user_id,
                                                "checked_at": datetime.now().isoformat()
                                            }).eq("id", req["id"]).execute()

                                            create_activity_log(
                                                current_user_id,
                                                "APPROVE_EDIT",
                                                f"Approved edit for '{target.get('username', 'user')}'"
                                            )
                                            notify_success(f"✅ {target.get('username', 'User')} updated")
                                            st.rerun()
                                        except Exception as e:
                                            notify_error(f"❌ Approval failed: {e}")
                                else:
                                    st.warning(msg)

                        with col3:
                            with st.popover("❌ Reject"):
                                reason = st.text_input("Reason", key=f"rej_e_{req['id']}_{idx}")
                                if st.button("Confirm Reject", key=f"rej_e_confirm_{req['id']}_{idx}"):
                                    try:
                                        supabase.table("user_edit_requests").update({
                                            "status": "rejected",
                                            "checked_by": current_user_id,
                                            "checked_at": datetime.now().isoformat(),
                                            "rejection_reason": reason or "No reason provided"
                                        }).eq("id", req["id"]).execute()
                                        create_activity_log(
                                            current_user_id,
                                            "REJECT_EDIT",
                                            f"Rejected edit for '{target.get('username', 'user')}': {reason or 'No reason'}"
                                        )
                                        notify_warning(f"❌ Edit request rejected")
                                        st.rerun()
                                    except Exception as e:
                                        notify_error(f"❌ Rejection failed: {e}")


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
