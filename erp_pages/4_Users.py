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
    st.caption("Control users, roles and access rights")

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
    # LOAD DATA
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

    try:
        if is_owner:
            branches_resp = supabase.table("branches").select("id,name,shop_id").execute()
        else:
            branches_resp = supabase.table("branches").select("id,name,shop_id").eq("shop_id", current_shop_id).execute()
        branches = branches_resp.data or []
    except Exception:
        branches = []

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
    # STATISTICS - 2 ROWS
    # ==========================================================================

    total = len(users)
    active = sum(1 for u in users if u.get("is_active"))
    inactive = total - active
    owners = sum(1 for u in users if u.get("tenant_role") == "owner")
    pending = len(pending_requests)

    # Row 1: Main stats
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("👥 Users", total)
    c2.metric("🟢 Active", active)
    c3.metric("🔴 Inactive", inactive)
    c4.metric("👑 Owners", owners)
    c5.metric("⏳ Pending", pending)
    c6.metric("🛡 Roles", len(roles))

    st.divider()

    # ==========================================================================
    # SEARCH + CREATE BUTTON
    # ==========================================================================

    col1, col2 = st.columns([4, 1])
    with col1:
        search = st.text_input("🔍 Search", placeholder="Search by username or full name...", label_visibility="collapsed")
    with col2:
        if st.button("➕ New User", use_container_width=True, type="primary"):
            st.session_state.show_create = not st.session_state.get("show_create", False)

    # ==========================================================================
    # CREATE FORM (Toggle)
    # ==========================================================================

    if st.session_state.get("show_create", False):
        with st.container(border=True):
            st.subheader("📝 Create User Request")
            st.caption("Fill in the details and submit for approval")
            
            with st.form("create_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    username = st.text_input("Username *", placeholder="Min 3 characters")
                    full_name = st.text_input("Full Name *")
                    password = st.text_input("Password *", type="password", placeholder="Min 6 characters")
                
                with col2:
                    selected_role = st.selectbox("System Role *", role_names)
                    tenant_role = st.selectbox("Tenant Role *", ["staff", "manager", "admin", "owner"])
                    active = st.checkbox("Active", value=True)
                
                col_btn1, col_btn2 = st.columns([1, 5])
                with col_btn1:
                    if st.form_submit_button("✅ Submit", use_container_width=True, type="primary"):
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
                                    "shop_id": current_shop_id,
                                    "branch_id": None,
                                    "tenant_role": tenant_role,
                                    "is_active": active,
                                    "status": "pending",
                                    "requested_at": datetime.now().isoformat()
                                }).execute()
                                notify_success(f"✅ Request for '{username}' submitted")
                                st.session_state.show_create = False
                                st.rerun()
                with col_btn2:
                    if st.form_submit_button("❌ Cancel", use_container_width=True):
                        st.session_state.show_create = False
                        st.rerun()

    # ==========================================================================
    # USERS TABLE
    # ==========================================================================

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
            
            data.append({
                "User": u.get("username"),
                "Name": u.get("full_name"),
                "Shop": shop_name,
                "Tenant": u.get("tenant_role", "staff"),
                "Role": role_name,
                "Status": "🟢" if u.get("is_active") else "🔴",
                "ID": u.get("id"),
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"📊 Showing {len(filtered)} of {len(users)} users")
    else:
        st.info("No users found")

    st.divider()

    # ==========================================================================
    # EDIT USER
    # ==========================================================================

    st.subheader("✏️ Edit User")
    
    if filtered:
        user_opts = {str(u["id"]): f"{u['username']} - {u['full_name']}" for u in filtered}
        selected_id = st.selectbox("Select User", options=list(user_opts.keys()), format_func=lambda x: user_opts[x], key="edit_select")
        
        if selected_id:
            selected = next((u for u in filtered if str(u["id"]) == selected_id), None)
            
            if selected:
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**User:** `{selected.get('username')}`")
                        new_name = st.text_input("Full Name", value=selected.get("full_name", ""))
                        current_role = next((r["name"] for r in roles if r["id"] == selected["role_id"]), role_names[0])
                        new_role = st.selectbox("System Role", role_names, index=role_names.index(current_role))
                    
                    with col2:
                        tenant_opts = ["staff", "manager", "admin", "owner"]
                        current_tenant = selected.get("tenant_role", "staff")
                        new_tenant = st.selectbox("Tenant Role", tenant_opts, index=tenant_opts.index(current_tenant))
                        new_active = st.toggle("Active", value=selected.get("is_active", True))
                    
                    with col3:
                        st.write("**Actions**")
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
                                st.info("⚠️ Protected")
                        
                        with col_c:
                            with st.popover("🔐 Reset Password"):
                                new_pass = st.text_input("New Password", type="password", placeholder="Min 6 chars")
                                if st.button("Save Password", use_container_width=True):
                                    if new_pass and len(new_pass) >= 6:
                                        supabase.table("users").update({"password_hash": hash_password(new_pass)}).eq("id", selected_id).execute()
                                        notify_success("✅ Password reset")
                                        st.rerun()
                                    else:
                                        notify_error("❌ Min 6 chars")
    else:
        st.info("No users to edit")

    # ==========================================================================
    # PENDING APPROVALS
    # ==========================================================================

    if (is_checker_user or is_owner) and pending_requests:
        st.divider()
        st.subheader(f"⏳ Pending Approvals ({len(pending_requests)})")
        
        for req in pending_requests:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{req.get('username')}** - {req.get('full_name')}")
                    st.caption(f"Role: {next((r['name'] for r in roles if r['id'] == req.get('role_id')), 'Unknown')} | Tenant: {req.get('tenant_role', 'staff')}")
                    requested_by = req.get('requested_by', {})
                    if requested_by:
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
    # RECENT ACTIVITY
    # ==========================================================================

    st.divider()
    with st.expander("📋 Recent Activity", expanded=False):
        try:
            logs = supabase.table("user_activity_logs").select(
                "action, description, created_at"
            ).order("created_at", desc=True).limit(30).execute()
            
            if logs.data:
                df = pd.DataFrame(logs.data)
                if "created_at" in df.columns:
                    df["created_at"] = df["created_at"].apply(lambda x: x[:19] if x else "")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No activity logs found")
        except Exception as e:
            st.error(f"Error loading activity: {e}")


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
