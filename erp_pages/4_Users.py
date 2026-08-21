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

    # Admin Guard (Only admin can access this page)
    require_admin()

    st.title("👥 User Management (Admin Panel)")
    st.caption("Control users, roles and access rights with Maker-Checker workflow")

    supabase = get_supabase()
    
    # Get current user and shop info
    current_user = get_current_user()
    current_shop_id = get_current_shop_id()
    is_owner = is_shop_owner()
    is_maker_user = is_maker()
    is_checker_user = is_checker()

    # Show user role badge
    if is_maker_user:
        st.info("🔑 You are a **Maker (Admin)** - You can create user requests")
    if is_checker_user:
        st.success("👑 You are a **Checker (Owner)** - You can approve/reject requests")
    if is_maker_user and is_checker_user:
        st.warning("⚡ You are both Maker and Checker - You can full control")

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
    # LOAD PENDING REQUESTS (for Checker/Owner)
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

    # ==============================================================================
    # TABS
    # ==============================================================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Users",
        "➕ Create User Request (Maker)",
        "✅ Pending Approvals (Checker)",
        "📊 Summary"
    ])

    # ==============================================================================
    # TAB 1: USERS
    # ==============================================================================

    with tab1:

        # Search
        search = st.text_input("🔍 Search User", placeholder="Search by username or full name...")

        if search:
            search = search.lower()
            filtered_users = [
                u for u in users
                if search in str(u.get("username", "")).lower()
                or search in str(u.get("full_name", "")).lower()
            ]
        else:
            filtered_users = users

        if not filtered_users:
            st.info("📭 No users found")
        else:
            table_rows = []
            for u in filtered_users:
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
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            st.caption(f"📊 Showing {len(filtered_users)} users")

    # ==============================================================================
    # TAB 2: CREATE USER REQUEST (MAKER)
    # ==============================================================================

    with tab2:

        if not is_maker_user and not is_owner:
            st.warning("⚠️ Only Admin (Maker) can create user requests.")
        else:
            st.subheader("📝 Create New User Request")
            st.caption("Fill in the details and submit for approval. An Owner (Checker) must approve this request.")

            with st.form("create_user_request_form"):

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
                    if len(shops) > 1 and is_owner:
                        selected_shop = st.selectbox("Shop *", shop_names)
                        selected_shop_id = shop_map[selected_shop]
                    else:
                        selected_shop_id = shops[0]["id"] if shops else None
                        if shops:
                            st.info(f"🏪 Shop: {shops[0]['name']}")

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
                st.info("📌 This request will be sent to Owner (Checker) for approval.")

                submit = st.form_submit_button("📤 Submit Request", use_container_width=True, type="primary")

                if submit:
                    if not username or not password or not full_name:
                        notify_error("❌ Username, password and full name are required")
                    elif len(username) < 3:
                        notify_error("❌ Username must be at least 3 characters long")
                    elif len(password) < 6:
                        notify_error("❌ Password must be at least 6 characters long")
                    else:
                        try:
                            # Check if username already exists
                            existing = supabase.table("users").select("id").eq("username", username).execute()
                            if existing.data and len(existing.data) > 0:
                                notify_error(f"❌ Username '{username}' already exists. Please choose a different username.")
                            else:
                                # Create request
                                request_data = {
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
                                }
                                
                                supabase.table("user_create_requests").insert(request_data).execute()
                                
                                create_activity_log(
                                    st.session_state.get("user_id"),
                                    "CREATE_USER_REQUEST",
                                    f"Requested to create user '{username}' with role '{selected_role}'"
                                )
                                
                                st.success(f"""
                                ✅ **User request submitted successfully!**

                                | Field | Value |
                                |-------|-------|
                                | **Username** | `{username}` |
                                | **Full Name** | {full_name} |
                                | **System Role** | {selected_role} |
                                | **Tenant Role** | {tenant_role} |
                                | **Status** | ⏳ Pending Approval |
                                """)
                                
                                st.info("📌 An Owner (Checker) needs to approve this request.")
                                st.rerun()
                                
                        except Exception as e:
                            notify_error(f"❌ Failed to submit request: {str(e)}")

    # ==============================================================================
    # TAB 3: PENDING APPROVALS (CHECKER)
    # ==============================================================================

    with tab3:

        if not is_checker_user and not is_owner:
            st.warning("⚠️ Only Owner (Checker) can approve/reject requests.")
        else:
            st.subheader("✅ Pending User Creation Requests")
            st.caption("Review and approve/reject user creation requests from Admins (Makers).")

            if not pending_requests:
                st.info("📭 No pending requests")
            else:
                for req in pending_requests:
                    with st.container(border=True):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Username:** `{req.get('username')}`")
                            st.write(f"**Full Name:** {req.get('full_name')}")
                            st.write(f"**Tenant Role:** {req.get('tenant_role', 'staff')}")
                            st.write(f"**System Role:** {next((r['name'] for r in roles if r['id'] == req.get('role_id')), 'Unknown')}")
                            
                            requested_by = req.get('requested_by', {})
                            if requested_by:
                                st.write(f"**Requested By:** {requested_by.get('full_name', 'Unknown')} ({requested_by.get('username', 'unknown')})")
                            st.write(f"**Requested At:** {req.get('requested_at', 'N/A')[:19] if req.get('requested_at') else 'N/A'}")

                        with col2:
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                if st.button("✅ Approve", key=f"approve_{req['id']}", use_container_width=True, type="primary"):
                                    try:
                                        # 1. Create the user
                                        new_user = {
                                            "username": req.get("username"),
                                            "full_name": req.get("full_name"),
                                            "password_hash": req.get("password_hash"),
                                            "role_id": req.get("role_id"),
                                            "shop_id": req.get("shop_id"),
                                            "branch_id": req.get("branch_id"),
                                            "tenant_role": req.get("tenant_role", "staff"),
                                            "is_active": req.get("is_active", True),
                                            "created_at": datetime.now().isoformat()
                                        }
                                        
                                        result = supabase.table("users").insert(new_user).execute()
                                        
                                        # 2. Update request status
                                        supabase.table("user_create_requests").update({
                                            "status": "approved",
                                            "checked_by": st.session_state.get("user_id"),
                                            "checked_at": datetime.now().isoformat()
                                        }).eq("id", req["id"]).execute()
                                        
                                        create_activity_log(
                                            st.session_state.get("user_id"),
                                            "APPROVE_USER_REQUEST",
                                            f"Approved user creation for '{req.get('username')}'"
                                        )
                                        
                                        notify_success(f"✅ User '{req.get('username')}' created successfully!")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        notify_error(f"❌ Approval failed: {str(e)}")
                            
                            with col_b:
                                if st.button("❌ Reject", key=f"reject_{req['id']}", use_container_width=True):
                                    reason = st.text_input("Rejection Reason:", key=f"reason_{req['id']}")
                                    
                                    if st.button("Confirm Reject", key=f"confirm_{req['id']}"):
                                        try:
                                            supabase.table("user_create_requests").update({
                                                "status": "rejected",
                                                "checked_by": st.session_state.get("user_id"),
                                                "checked_at": datetime.now().isoformat(),
                                                "rejection_reason": reason or "No reason provided"
                                            }).eq("id", req["id"]).execute()
                                            
                                            create_activity_log(
                                                st.session_state.get("user_id"),
                                                "REJECT_USER_REQUEST",
                                                f"Rejected user creation for '{req.get('username')}': {reason or 'No reason'}"
                                            )
                                            
                                            notify_warning(f"❌ Request for '{req.get('username')}' rejected")
                                            st.rerun()
                                            
                                        except Exception as e:
                                            notify_error(f"❌ Rejection failed: {str(e)}")

    # ==============================================================================
    # TAB 4: SUMMARY
    # ==============================================================================

    with tab4:

        total = len(users)
        active_count = sum(1 for u in users if u.get("is_active", False))
        inactive_count = total - active_count
        
        # Count by shop
        shop_counts = {}
        for u in users:
            shop_id = u.get("shop_id")
            if shop_id:
                shop_name = next((s["name"] for s in shops if s["id"] == shop_id), "Unknown")
                shop_counts[shop_name] = shop_counts.get(shop_name, 0) + 1

        # Count pending requests
        pending_count = len(pending_requests)

        st.subheader("📊 System Summary")

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("👥 Total Users", total)
        c2.metric("🟢 Active", active_count)
        c3.metric("🔴 Inactive", inactive_count)
        c4.metric("🛡 Roles", len(roles))
        c5.metric("⏳ Pending Requests", pending_count, delta="Needs approval" if pending_count > 0 else "All clear")

        if shop_counts:
            st.divider()
            st.subheader("🏪 Users by Shop")
            cols = st.columns(min(len(shop_counts), 4))
            for idx, (shop_name, count) in enumerate(shop_counts.items()):
                cols[idx % 4].metric(shop_name, count)

        # Show recent approvals/rejections
        st.divider()
        st.subheader("📋 Recent Approval History")

        try:
            history = (
                supabase.table("user_create_requests")
                .select("*, requested_by(id, username, full_name), checked_by(id, username, full_name)")
                .neq("status", "pending")
                .order("checked_at", desc=True)
                .limit(20)
                .execute()
            )
            
            if history.data:
                history_rows = []
                for h in history.data:
                    checked_by = h.get('checked_by', {})
                    history_rows.append({
                        "Username": h.get("username"),
                        "Status": "✅ Approved" if h.get("status") == "approved" else "❌ Rejected",
                        "Checked By": checked_by.get("full_name", "Unknown") if checked_by else "Unknown",
                        "Checked At": h.get("checked_at", "N/A")[:19] if h.get("checked_at") else "N/A",
                        "Reason": h.get("rejection_reason", "-") if h.get("status") == "rejected" else "-"
                    })
                
                df_history = pd.DataFrame(history_rows)
                st.dataframe(df_history, use_container_width=True, hide_index=True)
            else:
                st.info("No approval history found")
                
        except Exception as e:
            st.error(f"Failed to load history: {e}")


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
