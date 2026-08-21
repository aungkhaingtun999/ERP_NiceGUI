import hashlib
import pandas as pd
import streamlit as st
from datetime import datetime

from auth import (
    require_admin, 
    get_current_shop_id, 
    is_shop_owner, 
    get_current_user,
    is_maker,
    is_checker
)
from database import get_supabase
from utils.notification import (
    notify_error,
    notify_success,
    notify_warning,
    show_notification,
)


# ==============================================================================
# PAGE
# ==============================================================================

def run():

    show_notification()
    require_admin()

    st.title("👥 User Management")
    st.caption("Control users, roles and access rights with Maker-Checker")

    supabase = get_supabase()
    
    current_user = get_current_user()
    current_shop_id = get_current_shop_id()
    is_owner = is_shop_owner()
    is_maker_user = is_maker()
    is_checker_user = is_checker()

    # --------------------------------------------------------------------------
    # PASSWORD HASH
    # --------------------------------------------------------------------------

    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # --------------------------------------------------------------------------
    # ACTIVITY LOG
    # --------------------------------------------------------------------------

    def create_activity_log(user_id, action, description):
        try:
            supabase.table("user_activity_logs").insert({
                "user_id": user_id,
                "action": action,
                "description": description,
                "created_at": datetime.now().isoformat()
            }).execute()
        except Exception:
            pass

    # --------------------------------------------------------------------------
    # HELPER: Owner to Admin check
    # --------------------------------------------------------------------------

    def validate_owner_change(current_tenant, new_tenant):
        """Validate owner role change: Owner -> must go to Admin first"""
        if current_tenant == "owner" and new_tenant != "owner" and new_tenant != "admin":
            return False, "⚠️ Owner must first be changed to **Admin**, then to other roles."
        return True, ""

    # --------------------------------------------------------------------------
    # LOAD ROLES
    # --------------------------------------------------------------------------

    try:
        roles_resp = supabase.table("roles").select("id,name").execute()
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
    # LOAD USERS
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
    # LOAD PENDING REQUESTS
    # --------------------------------------------------------------------------

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

    total = len(users)
    active = sum(1 for u in users if u.get("is_active"))
    inactive = total - active
    owners = sum(1 for u in users if u.get("tenant_role") == "owner")
    pending_total = len(pending_create_requests) + len(pending_edit_requests)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("👥 Users", total)
    c2.metric("🟢 Active", active)
    c3.metric("🔴 Inactive", inactive)
    c4.metric("👑 Owners", owners)
    c5.metric("⏳ Pending", pending_total)
    c6.metric("🛡 Roles", len(roles))

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

        search = st.text_input("🔍 Search", placeholder="Search by username or full name...", label_visibility="collapsed", key="search_users")

        if search:
            search = search.lower()
            filtered = [u for u in users if search in str(u.get("username", "")).lower() or search in str(u.get("full_name", "")).lower()]
        else:
            filtered = users

        if not filtered:
            st.info("📭 No users found")
        else:
            rows = []
            for u in filtered:
                role_name = next((r["name"] for r in roles if r["id"] == u["role_id"]), "Unknown")
                shop_name = next((s["name"] for s in shops if s["id"] == u.get("shop_id")), "N/A")
                rows.append({
                    "User": u.get("username"),
                    "Name": u.get("full_name"),
                    "Shop": shop_name,
                    "Tenant": u.get("tenant_role", "staff"),
                    "Role": role_name,
                    "Status": "🟢" if u.get("is_active") else "🔴",
                })
            
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(f"📊 {len(filtered)} users")

        st.divider()

        # ----------------------------------------------------------------------
        # EDIT USER - Request Form (Maker)
        # ----------------------------------------------------------------------

        st.subheader("✏️ Edit User (Request)")

        if filtered:
            opts = {str(u["id"]): f"{u['username']} - {u['full_name']}" for u in filtered}
            selected_id = st.selectbox("Select User to Edit", options=list(opts.keys()), format_func=lambda x: opts[x], key="edit_select_main")
            
            if selected_id:
                selected = next((u for u in filtered if str(u["id"]) == selected_id), None)
                
                if selected:
                    with st.container(border=True):
                        st.caption(f"**Current User:** `{selected.get('username')}`")
                        st.caption(f"**Current Role:** {next((r['name'] for r in roles if r['id'] == selected['role_id']), 'Unknown')}")
                        
                        current_tenant = selected.get("tenant_role", "staff")
                        is_owner_user = current_tenant == "owner"
                        
                        # ✅ Owner validation message
                        if is_owner_user:
                            st.info("🔑 **Owner → Admin → Other**: Owner must first be changed to **Admin**, then to other roles.")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_name = st.text_input("New Full Name", value=selected.get("full_name", ""), key="edit_new_name_main")
                            current_role = next((r["name"] for r in roles if r["id"] == selected["role_id"]), role_names[0])
                            new_role = st.selectbox("New System Role", role_names, index=role_names.index(current_role), key="edit_new_role_main")
                        
                        with col2:
                            tenant_opts = ["staff", "manager", "admin", "owner"]
                            current_tenant_idx = tenant_opts.index(current_tenant) if current_tenant in tenant_opts else 0
                            new_tenant = st.selectbox("New Tenant Role", tenant_opts, index=current_tenant_idx, key="edit_new_tenant_main")
                            new_active = st.toggle("New Status", value=selected.get("is_active", True), key="edit_new_active_main")
                        
                        # ✅ Validate Owner change
                        valid, msg = validate_owner_change(current_tenant, new_tenant)
                        if not valid:
                            st.warning(msg)
                        
                        # Check if anything changed
                        has_changes = (
                            new_name != selected.get("full_name") or
                            new_role != current_role or
                            new_tenant != current_tenant or
                            new_active != selected.get("is_active", True)
                        )
                        
                        if not has_changes:
                            st.info("ℹ️ No changes detected")
                        elif not valid:
                            st.warning("⚠️ Please change Owner to **Admin** first, then to other roles.")
                        else:
                            if st.button("📤 Submit Edit Request", use_container_width=True, type="primary", key="submit_edit_main"):
                                if is_maker_user or is_owner:
                                    existing = supabase.table("user_edit_requests").select("id").eq("user_id", selected_id).eq("status", "pending").execute()
                                    if existing.data:
                                        notify_warning("⚠️ This user already has a pending edit request")
                                    else:
                                        supabase.table("user_edit_requests").insert({
                                            "requested_by": st.session_state.get("user_id"),
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
                                            st.session_state.get("user_id"),
                                            "EDIT_USER_REQUEST",
                                            f"Requested to edit user '{selected['username']}'"
                                        )
                                        
                                        notify_success(f"✅ Edit request for '{selected['username']}' submitted for approval")
                                        st.rerun()
                                else:
                                    notify_error("❌ Only Admin (Maker) can submit edit requests")
        else:
            st.info("No users")

    # ==========================================================================
    # TAB 2: CREATE USER REQUEST
    # ==========================================================================

    with tab2:

        if not is_maker_user and not is_owner:
            st.warning("⚠️ Only Admin (Maker) can create user requests.")
        else:
            st.subheader("📝 Create New User Request")
            st.caption("Submit for approval. Owner (Checker) must approve.")

            with st.form("create_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    username = st.text_input("Username *", placeholder="Min 3 chars", key="create_username")
                    full_name = st.text_input("Full Name *", key="create_fullname")
                    password = st.text_input("Password *", type="password", placeholder="Min 6 chars", key="create_password")
                
                with col2:
                    if len(shops) > 1 and is_owner:
                        selected_shop = st.selectbox("Shop", shop_names, key="create_shop")
                        selected_shop_id = shop_map[selected_shop]
                    else:
                        selected_shop_id = shops[0]["id"] if shops else None
                    
                    tenant_role = st.selectbox("Tenant Role", ["staff", "manager", "admin", "owner"], key="create_tenant")
                    selected_role = st.selectbox("System Role", role_names, key="create_role")
                    active = st.checkbox("Active", value=True, key="create_active")
                
                if st.form_submit_button("📤 Submit Request", use_container_width=True, type="primary"):
                    if not username or not password or not full_name:
                        notify_error("❌ All fields required")
                    elif len(username) < 3:
                        notify_error("❌ Username min 3 chars")
                    elif len(password) < 6:
                        notify_error("❌ Password min 6 chars")
                    else:
                        existing = supabase.table("users").select("id").eq("username", username).execute()
                        if existing.data:
                            notify_error(f"❌ Username '{username}' exists")
                        else:
                            supabase.table("user_create_requests").insert({
                                "requested_by": st.session_state.get("user_id"),
                                "username": username,
                                "full_name": full_name,
                                "password_hash": hash_password(password),
                                "role_id": role_map[selected_role],
                                "shop_id": selected_shop_id,
                                "branch_id": None,
                                "tenant_role": tenant_role,
                                "is_active": active,
                                "status": "pending",
                                "requested_at": datetime.now().isoformat()
                            }).execute()
                            notify_success(f"✅ Request for '{username}' submitted")
                            st.rerun()

    # ==========================================================================
    # TAB 3: EDIT REQUEST
    # ==========================================================================

    with tab3:

        if not is_maker_user and not is_owner:
            st.warning("⚠️ Only Admin (Maker) can edit users.")
        else:
            st.subheader("✏️ Edit User Request")
            st.caption("Select a user and submit edit request for approval")

            if not filtered:
                st.info("No users available")
            else:
                opts = {str(u["id"]): f"{u['username']} - {u['full_name']}" for u in filtered}
                selected_id = st.selectbox("Select User", options=list(opts.keys()), format_func=lambda x: opts[x], key="edit_tab_select")
                
                if selected_id:
                    selected = next((u for u in filtered if str(u["id"]) == selected_id), None)
                    
                    if selected:
                        pending_edit = supabase.table("user_edit_requests").select("id").eq("user_id", selected_id).eq("status", "pending").execute()
                        if pending_edit.data:
                            st.warning("⚠️ This user already has a pending edit request")
                        
                        current_tenant = selected.get("tenant_role", "staff")
                        is_owner_user = current_tenant == "owner"
                        
                        if is_owner_user:
                            st.info("🔑 **Owner → Admin → Other**: Owner must first be changed to **Admin**, then to other roles.")
                        
                        with st.container(border=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.caption(f"**Current User:** `{selected.get('username')}`")
                                new_name = st.text_input("New Full Name", value=selected.get("full_name", ""), key="edit_tab_name")
                                current_role = next((r["name"] for r in roles if r["id"] == selected["role_id"]), role_names[0])
                                new_role = st.selectbox("New System Role", role_names, index=role_names.index(current_role), key="edit_tab_role")
                            
                            with col2:
                                tenant_opts = ["staff", "manager", "admin", "owner"]
                                current_tenant_idx = tenant_opts.index(current_tenant) if current_tenant in tenant_opts else 0
                                new_tenant = st.selectbox("New Tenant Role", tenant_opts, index=current_tenant_idx, key="edit_tab_tenant")
                                new_active = st.toggle("New Status", value=selected.get("is_active", True), key="edit_tab_active")
                            
                            # ✅ Validate Owner change
                            valid, msg = validate_owner_change(current_tenant, new_tenant)
                            if not valid:
                                st.warning(msg)
                            
                            if not pending_edit.data and valid:
                                if st.button("📤 Submit Edit Request", use_container_width=True, type="primary", key="submit_edit_tab"):
                                    supabase.table("user_edit_requests").insert({
                                        "requested_by": st.session_state.get("user_id"),
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
                                    notify_success(f"✅ Edit request for '{selected['username']}' submitted")
                                    st.rerun()
                            elif pending_edit.data:
                                notify_warning("⚠️ Pending request already exists")

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
                            st.caption(f"Role: {next((r['name'] for r in roles if r['id'] == req.get('role_id')), 'Unknown')} | Tenant: {req.get('tenant_role', 'staff')}")
                            requested_by = req.get('requested_by', {})
                            if requested_by:
                                st.caption(f"By: {requested_by.get('full_name', 'Unknown')}")
                            
                            # ✅ Show if same user
                            if requested_by and requested_by.get('id') == st.session_state.get('user_id'):
                                st.warning("⚠️ You requested this. You cannot approve your own request.")
                        
                        with col2:
                            # ✅ Check if requester is same as current user
                            requester_id = req.get('requested_by', {}).get('id')
                            current_user_id = st.session_state.get('user_id')
                            
                            # ✅ Can approve if: different user OR (same user but only owner)
                            can_approve = requester_id != current_user_id
                            
                            if not can_approve:
                                # Check if user is the only owner (can self-approve)
                                owners = supabase.table("users").select("id").eq("tenant_role", "owner").execute()
                                if owners.data and len(owners.data) == 1 and owners.data[0]["id"] == current_user_id:
                                    can_approve = True
                                    st.info("🔑 You are the only Owner. You can self-approve.")
                                else:
                                    st.warning("⛔ You cannot approve your own request. Ask another Owner.")
                            
                            if can_approve:
                                if st.button("✅ Approve", key=f"app_c_{req['id']}_{idx}", use_container_width=True, type="primary"):
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
                                    supabase.table("user_create_requests").update({
                                        "status": "approved",
                                        "checked_by": st.session_state.get("user_id"),
                                        "checked_at": datetime.now().isoformat()
                                    }).eq("id", req["id"]).execute()
                                    notify_success(f"✅ {req['username']} created")
                                    st.rerun()
                        
                        with col3:
                            # ✅ Reject: always allowed
                            with st.popover("❌ Reject"):
                                reason = st.text_input("Reason", key=f"rej_c_{req['id']}_{idx}")
                                if st.button("Confirm", key=f"rej_c_confirm_{req['id']}_{idx}"):
                                    supabase.table("user_create_requests").update({
                                        "status": "rejected",
                                        "checked_by": st.session_state.get("user_id"),
                                        "checked_at": datetime.now().isoformat(),
                                        "rejection_reason": reason or "No reason"
                                    }).eq("id", req["id"]).execute()
                                    notify_warning(f"❌ {req['username']} rejected")
                                    st.rerun()
            
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
                            target_user = req.get('user_id', {})
                            st.write(f"**Edit: {target_user.get('username', 'Unknown')}**")
                            st.caption(f"Current: {req.get('old_full_name')} → New: {req.get('new_full_name')}")
                            st.caption(f"Role: {next((r['name'] for r in roles if r['id'] == req.get('old_role_id')), 'Unknown')} → {next((r['name'] for r in roles if r['id'] == req.get('new_role_id')), 'Unknown')}")
                            st.caption(f"Status: {'🟢' if req.get('old_is_active') else '🔴'} → {'🟢' if req.get('new_is_active') else '🔴'}")
                            requested_by = req.get('requested_by', {})
                            if requested_by:
                                st.caption(f"By: {requested_by.get('full_name', 'Unknown')}")
                            
                            # ✅ Show if same user
                            if requested_by and requested_by.get('id') == st.session_state.get('user_id'):
                                st.warning("⚠️ You requested this. You cannot approve your own request.")
                        
                        with col2:
                            # ✅ Validate Owner change
                            old_tenant = req.get('old_tenant_role')
                            new_tenant = req.get('new_tenant_role')
                            valid, msg = validate_owner_change(old_tenant, new_tenant)
                            
                            if not valid:
                                st.warning(msg)
                                st.info("ℹ️ This request cannot be approved. Please change Owner to **Admin** first.")
                            else:
                                # ✅ Check if requester is same as current user
                                requester_id = req.get('requested_by', {}).get('id')
                                current_user_id = st.session_state.get('user_id')
                                
                                can_approve = requester_id != current_user_id
                                
                                if not can_approve:
                                    # Check if user is the only owner
                                    owners = supabase.table("users").select("id").eq("tenant_role", "owner").execute()
                                    if owners.data and len(owners.data) == 1 and owners.data[0]["id"] == current_user_id:
                                        can_approve = True
                                        st.info("🔑 You are the only Owner. You can self-approve.")
                                    else:
                                        st.warning("⛔ You cannot approve your own request. Ask another Owner.")
                                
                                if can_approve:
                                    if st.button("✅ Approve", key=f"app_e_{req['id']}_{idx}", use_container_width=True, type="primary"):
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
                                            "checked_by": st.session_state.get("user_id"),
                                            "checked_at": datetime.now().isoformat()
                                        }).eq("id", req["id"]).execute()
                                        
                                        notify_success(f"✅ {target_user.get('username', 'User')} updated")
                                        st.rerun()
                        
                        with col3:
                            with st.popover("❌ Reject"):
                                reason = st.text_input("Reason", key=f"rej_e_{req['id']}_{idx}")
                                if st.button("Confirm", key=f"rej_e_confirm_{req['id']}_{idx}"):
                                    supabase.table("user_edit_requests").update({
                                        "status": "rejected",
                                        "checked_by": st.session_state.get("user_id"),
                                        "checked_at": datetime.now().isoformat(),
                                        "rejection_reason": reason or "No reason"
                                    }).eq("id", req["id"]).execute()
                                    notify_warning(f"❌ Edit request rejected")
                                    st.rerun()


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
