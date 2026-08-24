# ==============================================================================
# erp_pages/4_Users.py
# ERP ENTERPRISE USER MANAGEMENT
# NICE GUI VERSION
# Maker-Checker Workflow
# ==============================================================================

from typing import Dict, Any, Optional, List
import hashlib
import pandas as pd
from datetime import datetime, timezone
from nicegui import ui

from auth import (
    require_admin,
    get_current_shop_id,
    is_shop_owner,
    get_current_user,
    is_maker,
    is_checker,
)
from erp_core import privileged_db
from utils.notification import (
    notify_error,
    notify_success,
    notify_warning,
)


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main user management page."""
    
    require_admin()
    
    target = container or ui.column()
    
    with target:
        ui.label('👥 User Management').classes('text-3xl font-bold mb-2')
        ui.label('Control users, roles and access rights with Maker-Checker').classes('text-gray-500 mb-4')
        
        supabase = privileged_db()
        current_user = get_current_user()
        current_shop_id = get_current_shop_id()
        is_owner = is_shop_owner()
        is_maker_user = is_maker()
        is_checker_user = is_checker()
        current_user_id = current_user.get("id") if current_user else None
        
        # ======================================================================
        # HELPER FUNCTIONS
        # ======================================================================
        
        def hash_password(password: str) -> str:
            return hashlib.sha256(password.encode("utf-8")).hexdigest()
        
        def safe_dict(value):
            return value if isinstance(value, dict) else {}
        
        def get_role_name(role_id):
            if role_id is None:
                return "Unknown"
            role = next((r for r in roles if r.get("id") == role_id), None)
            return role.get("name", "Unknown") if role else "Unknown"
        
        def get_shop_name(shop_id):
            if shop_id is None:
                return "N/A"
            shop = next((s for s in shops if s.get("id") == shop_id), None)
            return shop.get("name", "N/A") if shop else "N/A"
        
        # ======================================================================
        # LOAD DATA
        # ======================================================================
        
        # Load roles
        try:
            roles_resp = supabase.table("roles").select("id,name").execute()
            roles = [safe_dict(r) for r in (roles_resp.data or []) if isinstance(r, dict)]
        except Exception as e:
            ui.notify(f"Role loading failed: {e}", type='error', position='top')
            return
        
        if not roles:
            ui.notify('Roles table is empty. Please create roles first.', type='warning', position='top')
            return
        
        role_map = {r.get("name"): r.get("id") for r in roles if r.get("name") is not None}
        role_names = list(role_map.keys())
        
        # Load shops
        shops = []
        try:
            if current_shop_id is not None:
                shops_resp = (
                    supabase.table("shops")
                    .select("id,name,code")
                    .eq("id", current_shop_id)
                    .execute()
                )
                shops = [safe_dict(s) for s in (shops_resp.data or []) if isinstance(s, dict)]
        except Exception:
            shops = []
        
        # Load users
        users = []
        try:
            query = supabase.table("users").select("""
                id, username, full_name, role_id, is_active,
                shop_id, branch_id, tenant_role, created_at, last_login
            """)
            
            if current_shop_id is None:
                ui.notify('Tenant shop context is missing.', type='error', position='top')
            else:
                query = query.eq("shop_id", current_shop_id)
                users_resp = query.execute()
                users = [safe_dict(u) for u in (users_resp.data or []) if isinstance(u, dict)]
        except Exception as e:
            ui.notify(f"User loading failed: {e}", type='error', position='top')
            users = []
        
        # Load pending requests
        pending_create_requests = []
        pending_edit_requests = []
        
        if is_checker_user or is_owner:
            try:
                create_resp = (
                    supabase.table("user_create_requests")
                    .select("*, requested_by(id, username, full_name)")
                    .eq("status", "pending")
                    .order("requested_at", desc=True)
                    .execute()
                )
                pending_create_requests = create_resp.data or []
            except Exception:
                pass
            
            try:
                edit_resp = (
                    supabase.table("user_edit_requests")
                    .select("*, requested_by(id, username, full_name), user_id(id, username, full_name)")
                    .eq("status", "pending")
                    .order("requested_at", desc=True)
                    .execute()
                )
                pending_edit_requests = edit_resp.data or []
            except Exception:
                pass
        
        # ======================================================================
        # STATISTICS
        # ======================================================================
        
        total = len(users)
        active = sum(1 for u in users if safe_dict(u).get("is_active"))
        inactive = total - active
        owners = sum(1 for u in users if safe_dict(u).get("tenant_role") == "owner")
        pending_total = len(pending_create_requests) + len(pending_edit_requests)
        
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            stats = [
                ("👥 Users", total, "bg-blue-50"),
                ("🟢 Active", active, "bg-green-50"),
                ("🔴 Inactive", inactive, "bg-red-50"),
                ("👑 Owners", owners, "bg-purple-50"),
                ("⏳ Pending", pending_total, "bg-orange-50"),
                ("🛡 Roles", len(roles), "bg-teal-50"),
            ]
            
            for label, value, color in stats:
                with ui.card().classes(f'p-4 flex-1 min-w-[150px] {color}'):
                    ui.label(label).classes('text-sm text-gray-600')
                    ui.label(str(value)).classes('text-2xl font-bold')
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # TABS
        # ======================================================================
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_users = ui.tab('📋 Users', icon='people')
            tab_create = ui.tab('➕ Create Request', icon='person_add')
            tab_edit = ui.tab('✏️ Edit Request', icon='edit')
            tab_approve = ui.tab('✅ Approvals', icon='check_circle')
        
        with ui.tab_panels(tabs, value=tab_users).classes('w-full'):
            # USERS TAB
            with ui.tab_panel(tab_users):
                render_users_tab(users, roles, shops, role_names, current_user_id, is_maker_user, is_owner)
            
            # CREATE REQUEST TAB
            with ui.tab_panel(tab_create):
                render_create_tab(shops, role_names, current_user_id, is_maker_user, is_owner, supabase)
            
            # EDIT REQUEST TAB
            with ui.tab_panel(tab_edit):
                render_edit_tab(users, roles, shops, role_names, current_user_id, is_maker_user, is_owner, supabase)
            
            # APPROVALS TAB
            with ui.tab_panel(tab_approve):
                render_approvals_tab(
                    pending_create_requests,
                    pending_edit_requests,
                    users,
                    roles,
                    shops,
                    current_user_id,
                    is_checker_user,
                    is_owner,
                    current_shop_id,
                    supabase
                )


# ==============================================================================
# USERS TAB
# ==============================================================================

def render_users_tab(users, roles, shops, role_names, current_user_id, is_maker_user, is_owner):
    """Render users list tab."""
    
    search_input = ui.input('🔍 Search', placeholder='Search by username or full name...').classes('w-full mb-4')
    
    users_container = ui.column().classes('w-full')
    
    def refresh_users(search_text: str = ""):
        users_container.clear()
        
        filtered = users
        if search_text:
            search_lower = search_text.lower()
            filtered = [
                u for u in users
                if search_lower in str(u.get("username", "")).lower()
                or search_lower in str(u.get("full_name", "")).lower()
            ]
        
        if not filtered:
            with users_container:
                ui.label('📭 No users found').classes('text-gray-500')
            return
        
        with users_container:
            rows = []
            for u in filtered:
                role_name = next((r.get("name", "Unknown") for r in roles if r.get("id") == u.get("role_id")), "Unknown")
                shop_name = next((s.get("name", "N/A") for s in shops if s.get("id") == u.get("shop_id")), "N/A")
                
                rows.append({
                    "User": u.get("username", ""),
                    "Name": u.get("full_name", ""),
                    "Shop": shop_name,
                    "Tenant": u.get("tenant_role", "staff"),
                    "Role": role_name,
                    "Status": "🟢" if u.get("is_active") else "🔴",
                })
            
            columns = [
                {'name': col, 'label': col, 'field': col, 'sortable': True}
                for col in rows[0].keys()
            ]
            
            ui.table(columns=columns, rows=rows, row_key='User', pagination=10).classes('w-full')
            ui.label(f'📊 {len(filtered)} users').classes('text-sm text-gray-500')
    
    search_input.on_value_change(lambda e: refresh_users(e.value or ""))
    refresh_users()


# ==============================================================================
# CREATE REQUEST TAB
# ==============================================================================

def render_create_tab(shops, role_names, current_user_id, is_maker_user, is_owner, supabase):
    """Render create user request tab."""
    
    if not is_maker_user and not is_owner:
        ui.notify('Only Admin (Maker) can create user requests.', type='warning', position='top')
        return
    
    ui.label('📝 Create New User Request').classes('text-xl font-bold mb-2')
    ui.label('Submit for approval. Owner (Checker) must approve.').classes('text-gray-500 mb-4')
    
    with ui.card().classes('w-full p-4'):
        with ui.row().classes('w-full gap-4 flex-wrap'):
            with ui.column().classes('flex-1 min-w-[250px]'):
                username = ui.input('Username *', placeholder='Min 3 chars').classes('w-full mb-2')
                full_name = ui.input('Full Name *').classes('w-full mb-2')
                password = ui.input('Password *', password=True, placeholder='Min 6 chars').classes('w-full mb-2')
            
            with ui.column().classes('flex-1 min-w-[250px]'):
                tenant_role = ui.select(
                    ['staff', 'manager', 'admin', 'owner'],
                    label='Tenant Role',
                    value='staff',
                ).classes('w-full mb-2')
                
                selected_role = ui.select(role_names, label='System Role').classes('w-full mb-2')
                
                active = ui.switch('Active', value=True).classes('mb-2')
        
        submit_btn = ui.button(
            '📤 Submit Request',
            on_click=lambda: handle_create_submit(
                username.value, full_name.value, password.value,
                tenant_role.value, selected_role.value, active.value,
                shops, role_names, current_user_id, supabase, submit_btn
            )
        ).classes('w-full bg-primary text-white mt-4')


def handle_create_submit(username, full_name, password, tenant_role, selected_role, active, shops, role_names, current_user_id, supabase, submit_btn):
    """Handle create request submission."""
    try:
        if not username or not password or not full_name:
            ui.notify('All fields required', type='error', position='top')
            return
        
        if len(username) < 3:
            ui.notify('Username min 3 chars', type='error', position='top')
            return
        
        if len(password) < 6:
            ui.notify('Password min 6 chars', type='error', position='top')
            return
        
        submit_btn.disable()
        submit_btn.text = '⏳ Submitting...'
        
        # Check existing
        existing = supabase.table("users").select("id").eq("username", username).execute()
        
        if existing.data:
            ui.notify(f"Username '{username}' exists", type='error', position='top')
            return
        
        # Get shop ID
        selected_shop_id = shops[0].get("id") if shops else None
        
        # Get role ID
        role_map = {r.get("name"): r.get("id") for r in role_names}
        role_id = role_map.get(selected_role)
        
        # Insert request
        supabase.table("user_create_requests").insert({
            "requested_by": current_user_id,
            "username": username,
            "full_name": full_name,
            "password_hash": hashlib.sha256(password.encode()).hexdigest(),
            "role_id": role_id,
            "shop_id": selected_shop_id,
            "branch_id": None,
            "tenant_role": tenant_role,
            "is_active": active,
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
        }).execute()
        
        ui.notify(f"Request for '{username}' submitted", type='positive', position='top')
    
    except Exception as e:
        ui.notify(f'Error: {e}', type='error', position='top')
    
    finally:
        submit_btn.enable()
        submit_btn.text = '📤 Submit Request'


# ==============================================================================
# EDIT REQUEST TAB (Simplified)
# ==============================================================================

def render_edit_tab(users, roles, shops, role_names, current_user_id, is_maker_user, is_owner, supabase):
    """Render edit user request tab."""
    
    if not is_maker_user and not is_owner:
        ui.notify('Only Admin (Maker) can edit users.', type='warning', position='top')
        return
    
    ui.label('✏️ Edit User Request').classes('text-xl font-bold mb-4')
    
    if not users:
        ui.label('No users available').classes('text-gray-500')
        return
    
    # User selection
    opts = {str(u.get("id")): f"{u.get('username', '')} - {u.get('full_name', '')}" for u in users if u.get("id")}
    
    selected_id = ui.select(list(opts.keys()), label='Select User').classes('w-full mb-4')
    
    edit_container = ui.column().classes('w-full')
    
    def load_edit_form():
        edit_container.clear()
        user_id = selected_id.value
        
        selected = next((u for u in users if str(u.get("id")) == user_id), None)
        
        if not selected:
            return
        
        with edit_container:
            current_tenant = selected.get("tenant_role") or "staff"
            
            with ui.card().classes('w-full p-4'):
                ui.label(f'User: {selected.get("username", "")}').classes('font-bold mb-2')
                ui.label(f'Current Role: {next((r.get("name", "Unknown") for r in roles if r.get("id") == selected.get("role_id")), "Unknown")}').classes('text-gray-600 mb-4')
                
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    with ui.column().classes('flex-1 min-w-[250px]'):
                        new_name = ui.input('Full Name', value=selected.get("full_name", "") or "").classes('w-full mb-2')
                        
                        current_role = next((r.get("name", "Unknown") for r in roles if r.get("id") == selected.get("role_id")), "Unknown")
                        if current_role not in role_names:
                            current_role = role_names[0]
                        
                        new_role = ui.select(role_names, label='System Role', value=current_role).classes('w-full mb-2')
                    
                    with ui.column().classes('flex-1 min-w-[250px]'):
                        tenant_opts = ["staff", "manager", "admin", "owner"]
                        current_idx = tenant_opts.index(current_tenant) if current_tenant in tenant_opts else 0
                        
                        new_tenant = ui.select(tenant_opts, label='Tenant Role', value=current_tenant).classes('w-full mb-2')
                        new_active = ui.switch('Active', value=bool(selected.get("is_active", True))).classes('mb-2')
                
                submit_btn = ui.button(
                    '📤 Submit Edit Request',
                    on_click=lambda: handle_edit_submit(
                        selected, new_name.value, new_role.value,
                        new_tenant.value, new_active.value,
                        role_names, current_user_id, supabase, submit_btn
                    )
                ).classes('w-full bg-primary text-white')
    
    selected_id.on_value_change(lambda e: load_edit_form())
    load_edit_form()


def handle_edit_submit(selected, new_name, new_role, new_tenant, new_active, role_names, current_user_id, supabase, submit_btn):
    """Handle edit request submission."""
    try:
        submit_btn.disable()
        submit_btn.text = '⏳ Submitting...'
        
        # Check pending
        existing = (
            supabase.table("user_edit_requests")
            .select("id")
            .eq("user_id", selected["id"])
            .eq("status", "pending")
            .execute()
        )
        
        if existing.data:
            ui.notify('Pending request already exists', type='warning', position='top')
            return
        
        # Get role ID
        role_map = {r: i for i, r in enumerate(role_names)}
        new_role_id = role_map.get(new_role)
        
        supabase.table("user_edit_requests").insert({
            "requested_by": current_user_id,
            "user_id": selected["id"],
            "new_full_name": new_name,
            "new_role_id": new_role_id,
            "new_tenant_role": new_tenant,
            "new_is_active": new_active,
            "old_full_name": selected.get("full_name"),
            "old_role_id": selected.get("role_id"),
            "old_tenant_role": selected.get("tenant_role", "staff"),
            "old_is_active": selected.get("is_active", True),
            "status": "pending",
            "requested_at": datetime.now().isoformat(),
        }).execute()
        
        ui.notify(f"Edit request for '{selected.get('username', '')}' submitted", type='positive', position='top')
    
    except Exception as e:
        ui.notify(f'Error: {e}', type='error', position='top')
    
    finally:
        submit_btn.enable()
        submit_btn.text = '📤 Submit Edit Request'


# ==============================================================================
# APPROVALS TAB (Simplified)
# ==============================================================================

def render_approvals_tab(pending_create, pending_edit, users, roles, shops, current_user_id, is_checker_user, is_owner, current_shop_id, supabase):
    """Render approvals tab."""
    
    if not is_checker_user and not is_owner:
        ui.notify('Only Owner (Checker) can approve/reject requests.', type='warning', position='top')
        return
    
    # Create requests
    ui.label(f'📝 Create Requests ({len(pending_create)})').classes('text-xl font-bold mb-4')
    
    if not pending_create:
        ui.label('No pending create requests').classes('text-gray-500')
    else:
        for idx, req in enumerate(pending_create):
            with ui.card().classes('w-full p-4 mb-4 border border-gray-200'):
                ui.label(f"Create: {req.get('username', 'Unknown')} - {req.get('full_name', '')}").classes('font-bold')
                
                req_by = req.get("requested_by", {})
                ui.label(f"By: {req_by.get('full_name', 'Unknown')}").classes('text-sm text-gray-500')
                
                with ui.row().classes('w-full gap-2 mt-2'):
                    approve_btn = ui.button(
                        '✅ Approve',
                        on_click=lambda r=req: handle_approve_create(r, current_user_id, supabase, approve_btn)
                    ).classes('flex-1 bg-green-500 text-white')
                    
                    reject_btn = ui.button(
                        '❌ Reject',
                        on_click=lambda r=req: handle_reject_create(r, current_user_id, supabase, reject_btn)
                    ).classes('flex-1 bg-red-500 text-white')
    
    ui.separator().classes('my-4')
    
    # Edit requests
    ui.label(f'✏️ Edit Requests ({len(pending_edit)})').classes('text-xl font-bold mb-4')
    
    if not pending_edit:
        ui.label('No pending edit requests').classes('text-gray-500')
    else:
        for idx, req in enumerate(pending_edit):
            with ui.card().classes('w-full p-4 mb-4 border border-gray-200'):
                target_user = req.get("user_id", {})
                ui.label(f"Edit: {target_user.get('username', 'Unknown')}").classes('font-bold')
                
                with ui.row().classes('w-full gap-2 mt-2'):
                    approve_btn = ui.button(
                        '✅ Approve',
                        on_click=lambda r=req: handle_approve_edit(r, current_user_id, supabase, approve_btn)
                    ).classes('flex-1 bg-green-500 text-white')
                    
                    reject_btn = ui.button(
                        '❌ Reject',
                        on_click=lambda r=req: handle_reject_edit(r, current_user_id, supabase, reject_btn)
                    ).classes('flex-1 bg-red-500 text-white')


def handle_approve_create(req, current_user_id, supabase, approve_btn):
    """Handle create request approval."""
    try:
        approve_btn.disable()
        
        # Insert user
        supabase.table("users").insert({
            "username": req.get("username"),
            "full_name": req.get("full_name"),
            "password_hash": req.get("password_hash"),
            "role_id": req.get("role_id"),
            "shop_id": req.get("shop_id"),
            "tenant_role": req.get("tenant_role", "staff"),
            "is_active": req.get("is_active", True),
        }).execute()
        
        # Mark approved
        supabase.table("user_create_requests").update({
            "status": "approved",
            "checked_by": current_user_id,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", req["id"]).execute()
        
        ui.notify(f"User '{req.get('username')}' created", type='positive', position='top')
    
    except Exception as e:
        ui.notify(f'Error: {e}', type='error', position='top')
    
    finally:
        approve_btn.enable()


def handle_reject_create(req, current_user_id, supabase, reject_btn):
    """Handle create request rejection."""
    try:
        reject_btn.disable()
        
        supabase.table("user_create_requests").update({
            "status": "rejected",
            "checked_by": current_user_id,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "rejection_reason": "Rejected",
        }).eq("id", req["id"]).execute()
        
        ui.notify('Request rejected', type='warning', position='top')
    
    except Exception as e:
        ui.notify(f'Error: {e}', type='error', position='top')
    
    finally:
        reject_btn.enable()


def handle_approve_edit(req, current_user_id, supabase, approve_btn):
    """Handle edit request approval."""
    try:
        approve_btn.disable()
        
        target_id = req.get("user_id", {}).get("id")
        update_data = {}
        
        if req.get("new_full_name") is not None:
            update_data["full_name"] = req.get("new_full_name")
        if req.get("new_role_id") is not None:
            update_data["role_id"] = req.get("new_role_id")
        if req.get("new_tenant_role") is not None:
            update_data["tenant_role"] = req.get("new_tenant_role")
        if req.get("new_is_active") is not None:
            update_data["is_active"] = req.get("new_is_active")
        
        if update_data:
            supabase.table("users").update(update_data).eq("id", target_id).execute()
        
        supabase.table("user_edit_requests").update({
            "status": "approved",
            "checked_by": current_user_id,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", req["id"]).execute()
        
        ui.notify('User updated', type='positive', position='top')
    
    except Exception as e:
        ui.notify(f'Error: {e}', type='error', position='top')
    
    finally:
        approve_btn.enable()


def handle_reject_edit(req, current_user_id, supabase, reject_btn):
    """Handle edit request rejection."""
    try:
        reject_btn.disable()
        
        supabase.table("user_edit_requests").update({
            "status": "rejected",
            "checked_by": current_user_id,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "rejection_reason": "Rejected",
        }).eq("id", req["id"]).execute()
        
        ui.notify('Request rejected', type='warning', position='top')
    
    except Exception as e:
        ui.notify(f'Error: {e}', type='error', position='top')
    
    finally:
        reject_btn.enable()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
