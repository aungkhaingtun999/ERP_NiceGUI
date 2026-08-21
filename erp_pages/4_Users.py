import hashlib
import pandas as pd
import streamlit as st
from datetime import datetime

from auth import (
    require_admin, 
    require_maker, 
    require_checker,
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

    # Notification
    show_notification()

    # Admin Guard
    require_admin()

    st.title("👥 User Management")
    st.caption("Control users, roles and access rights")

    supabase = get_supabase()
    
    # Get current user and shop info
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

    pending_requests = []
    if is_checker_user or is_owner:
        try:
            requests_resp = (
                supabase.table("user_create_requests")
                .select("*, requested_by(id, username, full_name)")
                .eq("status", "pending")
                .order("requested_at", desc=True)
                .execute()
            )
            pending_requests = requests_resp.data or []
        except Exception:
            pass

    # ==========================================================================
    # STATISTICS ROW - COMPACT
    # ==========================================================================

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👥 Users", len(users))
    col2.metric("🟢 Active", sum(1 for u in users if u.get("is_active")))
    col3.metric("🔴 Inactive", sum(1 for u in users if not u.get("is_active")))
    col4.metric("👑 Owners", sum(1 for u in users if u.get("tenant_role") == "owner"))
    col5.metric("⏳ Pending", len(pending_requests))

    st.divider()

    # ==========================================================================
    # TABS - COMPACT
    # ==========================================================================

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Users", "➕ Create", "✅ Approvals", "📊 Summary"])

    # ==========================================================================
    # TAB 1: USERS
    # ==========================================================================

    with tab1:
        search = st.text_input("🔍 Search", placeholder="Search user...", key="search_user")
        
        if search:
            search = search.lower()
            filtered = [u for u in users if search in str(u.get("username", "")).lower() or search in str(u.get("full_name", "")).lower()]
        else:
            filtered = users

        if filtered:
            data = []
            for u in filtered:
                role_name = next((r["name"] for r in roles if r["id"] == u["role_id"]), "Unknown")
                shop_name = next((s["name"] for s in shops if s["id"] == u.get("shop_id")), "N/A")
                branch_name = next((b["name"] for b in branches if b["id"] == u.get("branch_id")), "N/A")
                
                data.append({
                    "User": u.get("username"),
                    "Name": u.get("full_name"),
                    "Shop": shop_name,
                    "Branch": branch_name,
                    "Tenant": u.get("tenant_role", "staff"),
                    "Role": role_name,
                    "Status": "✅" if u.get("is_active") else "❌",
                })
            
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        else:
            st.info("No users found")

        st.divider()

        # Edit Section - Compact
        st.subheader("✏️ Edit User")
        
        user_options = {str(u["id"]): f"{u['username']}" for u in users}
        if user_options:
            selected_id = st.selectbox("Select User", options=list(user_options.keys()), format_func=lambda x: user_options[x], key="edit_user")
            selected = next((u for u in users if str(u["id"]) == selected_id), None)
            
            if selected:
                with st.expander(f"✏️ Editing: {selected.get('username')}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_name = st.text_input("Full Name", value=selected.get("full_name", ""), key="edit_name")
                        current_role = next((r["name"] for r in roles if r["id"] == selected["role_id"]), role_names[0])
                        new_role = st.selectbox("System Role", role_names, index=role_names.index(current_role), key="edit_role")
                        
                        # Tenant Role - Compact
                        tenant_options = ["staff", "manager", "admin", "owner"]
                        current_tenant = selected.get("tenant_role", "staff")
                        new_tenant = st.selectbox("Tenant Role", tenant_options, index=tenant_options.index(current_tenant), key="edit_tenant")
                    
                    with col2:
                        new_active = st.toggle("Active", value=selected.get("is_active", True), key="edit_active")
                        
                        # Password reset - Compact
                        with st.popover("🔐 Reset Password"):
                            new_pass = st.text_input("New Password", type="password", placeholder="Min 6 chars", key="reset_pass")
                            if st.button("Save Password", use_container_width=True):
                                if new_pass and len(new_pass) >= 6:
                                    supabase.table("users").update({"password_hash": hash_password(new_pass)}).eq("id", selected_id).execute()
                                    notify_success("✅ Password reset")
                                    st.rerun()
                                else:
                                    notify_error("❌ Password must be at least 6 chars")
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        if st.button("💾 Update", use_container_width=True, type="primary"):
                            supabase.table("users").update({
                                "full_name": new_name,
                                "role_id": role_map[new_role],
                                "tenant_role": new_tenant,
                                "is_active": new_active,
                            }).eq("id", selected_id).execute()
                            notify_success(f"✅ Updated {selected['username']}")
                            st.rerun()
                    
                    with col_b:
                        if selected.get("username") != "admin":
                            if st.button("🗑 Delete", use_container_width=True):
                                supabase.table("users").delete().eq("id", selected_id).execute()
                                notify_success(f"✅ Deleted {selected['username']}")
                                st.rerun()
                        else:
                            st.info("⚠️ Admin protected")
        else:
            st.info("No users to edit")

    # ==========================================================================
    # TAB 2: CREATE USER
    # ==========================================================================

    with tab2:
        if not is_maker_user and not is_owner:
            st.warning("⚠️ Only Admin can create user requests")
        else:
            st.subheader("📝 Create User Request")
            
            with st.form("create_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    username = st.text_input("Username *", placeholder="Min 3 chars")
                    full_name = st.text_input("Full Name *")
                    password = st.text_input("Password *", type="password", placeholder="Min 6 chars")
                
                with col2:
                    shop_name = shop_names[0] if shop_names else None
                    selected_shop_id = shop_map.get(shop_name) if shop_name else None
                    
                    if selected_shop_id:
                        branch_opts = [b for b in branches if b.get("shop_id") == selected_shop_id]
                    else:
                        branch_opts = []
                    
                    branch_names = [b["name"] for b in branch_opts] if branch_opts else ["No Branch"]
                    selected_branch = st.selectbox("Branch", branch_names)
                    selected_branch_id = branch_opts[0]["id"] if branch_opts and selected_branch != "No Branch" else None
                    
                    tenant_role = st.selectbox("Tenant Role", ["staff", "manager", "admin", "owner"])
                    selected_role = st.selectbox("System Role", role_names)
                    active = st.checkbox("Active", value=True)
                
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
                                "branch_id": selected_branch_id,
                                "tenant_role": tenant_role,
                                "is_active": active,
                                "status": "pending",
                                "requested_at": datetime.now().isoformat()
                            }).execute()
                            notify_success(f"✅ Request for '{username}' submitted")
                            st.rerun()

    # ==========================================================================
    # TAB 3: APPROVALS
    # ==========================================================================

    with tab3:
        if not is_checker_user and not is_owner:
            st.warning("⚠️ Only Owner can approve requests")
        elif not pending_requests:
            st.info("📭 No pending requests")
        else:
            st.subheader(f"⏳ Pending Requests ({len(pending_requests)})")
            
            for req in pending_requests:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{req.get('username')}** - {req.get('full_name')}")
                        st.caption(f"Role: {next((r['name'] for r in roles if r['id'] == req.get('role_id')), 'Unknown')} | Tenant: {req.get('tenant_role', 'staff')}")
                        requested_by = req.get('requested_by', {})
                        st.caption(f"Requested by: {requested_by.get('full_name', 'Unknown')}")
                    
                    with col2:
                        if st.button("✅ Approve", key=f"app_{req['id']}", use_container_width=True, type="primary"):
                            new_user = {
                                "username": req.get("username"),
                                "full_name": req.get("full_name"),
                                "password_hash": req.get("password_hash"),
                                "role_id": req.get("role_id"),
                                "shop_id": req.get("shop_id"),
                                "branch_id": req.get("branch_id"),
                                "tenant_role": req.get("tenant_role", "staff"),
                                "is_active": req.get("is_active", True),
                            }
                            supabase.table("users").insert(new_user).execute()
                            supabase.table("user_create_requests").update({
                                "status": "approved",
                                "checked_by": st.session_state.get("user_id"),
                                "checked_at": datetime.now().isoformat()
                            }).eq("id", req["id"]).execute()
                            notify_success(f"✅ {req['username']} created")
                            st.rerun()
                    
                    with col3:
                        with st.popover("❌ Reject"):
                            reason = st.text_input("Reason", key=f"reason_{req['id']}")
                            if st.button("Confirm Reject", key=f"rej_{req['id']}"):
                                supabase.table("user_create_requests").update({
                                    "status": "rejected",
                                    "checked_by": st.session_state.get("user_id"),
                                    "checked_at": datetime.now().isoformat(),
                                    "rejection_reason": reason or "No reason"
                                }).eq("id", req["id"]).execute()
                                notify_warning(f"❌ {req['username']} rejected")
                                st.rerun()

    # ==========================================================================
    # TAB 4: SUMMARY
    # ==========================================================================

    with tab4:
        col1, col2, col3 = st.columns(3)
        col1.metric("👥 Total", len(users))
        col2.metric("🟢 Active", sum(1 for u in users if u.get("is_active")))
        col3.metric("⏳ Pending", len(pending_requests))
        
        # Shop distribution - Compact
        if shops:
            st.divider()
            st.subheader("🏪 Users by Shop")
            cols = st.columns(min(len(shops), 4))
            for idx, shop in enumerate(shops):
                count = sum(1 for u in users if u.get("shop_id") == shop["id"])
                cols[idx % 4].metric(shop["name"], count)
        
        # Recent history - Compact
        st.divider()
        with st.expander("📋 Recent History", expanded=False):
            try:
                history = supabase.table("user_create_requests").select(
                    "username, status, checked_at, rejection_reason"
                ).neq("status", "pending").order("checked_at", desc=True).limit(20).execute()
                
                if history.data:
                    df = pd.DataFrame(history.data)
                    df["Status"] = df["status"].apply(lambda x: "✅ Approved" if x == "approved" else "❌ Rejected")
                    df = df[["username", "Status", "checked_at", "rejection_reason"]]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No history")
            except Exception as e:
                st.error(f"Error: {e}")


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
