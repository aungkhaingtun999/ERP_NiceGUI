# ==============================================================================
# auth.py
# ERP ENTERPRISE AUTHENTICATION SYSTEM
# SECURITY + ROLE + SESSION + MULTI-TENANT
# NICE GUI VERSION
# ==============================================================================

import hashlib
import hmac
import time
from typing import Dict, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta, timezone

import bcrypt
from nicegui import ui, app, context

from erp_core.base_repo import db


# ==============================================================================
# DATABASE
# ==============================================================================

supabase = db()


# ==============================================================================
# SECURITY CONSTANTS
# ==============================================================================

SESSION_IDLE_TIMEOUT = 1800  # 30 minutes
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


# ==============================================================================
# ROLE CONSTANTS
# ==============================================================================

ROLE_ADMIN = 1
ROLE_MANAGER = 2
ROLE_CASHIER = 3

ROLE_MAP = {
    ROLE_ADMIN: "Admin",
    ROLE_MANAGER: "Manager",
    ROLE_CASHIER: "Cashier",
}


# ==============================================================================
# TENANT ROLE CONSTANTS
# ==============================================================================

TENANT_ROLE_STAFF = "staff"
TENANT_ROLE_MANAGER = "manager"
TENANT_ROLE_ADMIN = "admin"
TENANT_ROLE_OWNER = "owner"

TENANT_ROLE_MAP = {
    TENANT_ROLE_STAFF: "Staff",
    TENANT_ROLE_MANAGER: "Manager",
    TENANT_ROLE_ADMIN: "Admin",
    TENANT_ROLE_OWNER: "Owner",
}

TENANT_ROLE_HIERARCHY = {
    TENANT_ROLE_STAFF: 1,
    TENANT_ROLE_MANAGER: 2,
    TENANT_ROLE_ADMIN: 3,
    TENANT_ROLE_OWNER: 4,
}


# ==============================================================================
# SESSION STATE MANAGEMENT
# ==============================================================================

class AuthSession:
    """Authentication session manager for NiceGUI"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def get_session(self, client_id: str = None) -> Dict[str, Any]:
        """Get or create session for client"""
        if client_id is None:
            client_id = context.client.id if context.client else "default"
        
        if client_id not in self._sessions:
            self._sessions[client_id] = {}
        
        return self._sessions[client_id]
    
    def set_user(self, user_data: Dict[str, Any], client_id: str = None):
        """Set user in session"""
        session = self.get_session(client_id)
        session["user"] = user_data
        
        # Also set individual session variables
        session["user_id"] = user_data.get("id")
        session["username"] = user_data.get("username")
        session["role_id"] = user_data.get("role_id")
        session["shop_id"] = user_data.get("shop_id")
        session["branch_id"] = user_data.get("branch_id")
        session["tenant_role"] = user_data.get("tenant_role")
        session["shop_name"] = user_data.get("shop_name")
        session["branch_name"] = user_data.get("branch_name")
        session["tenant_context"] = user_data.get("tenant_context")
        session["id"] = user_data.get("id")
    
    def clear(self, client_id: str = None):
        """Clear session"""
        session = self.get_session(client_id)
        session.clear()
    
    def get(self, key: str, default=None, client_id: str = None):
        """Get value from session"""
        session = self.get_session(client_id)
        return session.get(key, default)

# Global auth session instance
auth_session = AuthSession()


# ==============================================================================
# AUTH LOG
# ==============================================================================

def log_auth_event(user_id, event_type, status="success"):
    """Log authentication events"""
    try:
        supabase.table("auth_logs").insert({
            "user_id": user_id,
            "event": event_type,
            "status": status,
            "ip_address": "system",
        }).execute()
    except Exception:
        pass


# ==============================================================================
# PASSWORD ENGINE
# ==============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(user: Dict[str, Any], password: str) -> bool:
    """
    Verify password against stored password hash.
    Supports: bcrypt, legacy SHA256, legacy plain password
    """
    stored = user.get("password_hash")
    
    if not stored:
        return False
    
    stored = str(stored).strip()
    
    # BCRYPT
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                stored.encode("utf-8")
            )
        except Exception:
            return False
    
    # LEGACY SHA256 / PLAIN PASSWORD
    sha256_hash = hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()
    
    if hmac.compare_digest(stored, sha256_hash) or hmac.compare_digest(stored, password):
        upgrade_password(user["id"], password)
        return True
    
    return False


def upgrade_password(user_id, password: str):
    """Upgrade legacy password to bcrypt"""
    try:
        new_hash = hash_password(password)
        supabase.table("users").update({
            "password_hash": new_hash
        }).eq("id", user_id).execute()
    except Exception:
        pass


# ==============================================================================
# CHANGE PASSWORD
# ==============================================================================

def change_password(user_id, old_password: str, new_password: str) -> Tuple[bool, str]:
    """
    Change authenticated user's password.
    Returns: (success, message)
    """
    try:
        # VALIDATION
        if not user_id:
            return False, "User ID is required."
        
        if not old_password:
            return False, "Current password is required."
        
        if not new_password:
            return False, "New password is required."
        
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters."
        
        if old_password == new_password:
            return False, "New password must be different from current password."
        
        # LOAD CURRENT USER
        result = supabase.table("users").select(
            "id, username, password_hash, is_active"
        ).eq("id", user_id).eq("is_active", True).limit(1).execute()
        
        if not result.data:
            return False, "User not found or inactive."
        
        user = result.data[0]
        
        # VERIFY OLD PASSWORD
        if not verify_password(user, old_password):
            log_auth_event(user_id, "password_change", "failed")
            return False, "Current password is incorrect."
        
        # HASH NEW PASSWORD
        new_hash = hash_password(new_password)
        
        # UPDATE PASSWORD
        update_result = supabase.table("users").update({
            "password_hash": new_hash,
            "failed_attempts": 0,
            "locked_until": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            return False, "Password update failed."
        
        # AUDIT
        log_auth_event(user_id, "password_change", "success")
        
        return True, "Password changed successfully."
    
    except Exception as e:
        log_auth_event(user_id, "password_change", "failed")
        return False, f"Password change error: {str(e)}"


# ==============================================================================
# USER QUERY
# ==============================================================================

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    try:
        result = supabase.table("users").select("*").eq(
            "username", username.strip()
        ).eq("is_active", True).limit(1).execute()
        
        return result.data[0] if result.data else None
    
    except Exception:
        ui.notify("Authentication Database Error", type='error', position='top')
        return None


# ==============================================================================
# TENANT CONTEXT
# ==============================================================================

def build_tenant_context(user: Dict[str, Any]) -> Dict[str, Any]:
    """Build tenant context from user data"""
    shop_id = user.get("shop_id")
    branch_id = user.get("branch_id")
    tenant_role = user.get("tenant_role", TENANT_ROLE_STAFF)
    
    context = {
        "shop_id": shop_id,
        "branch_id": branch_id,
        "tenant_role": tenant_role,
        "shop_name": None,
        "shop_code": None,
        "branch_name": None,
        "branch_code": None,
    }
    
    # SHOP
    if shop_id:
        try:
            response = supabase.table("shops").select(
                "name, code"
            ).eq("id", shop_id).limit(1).execute()
            
            if response.data:
                shop = response.data[0]
                context["shop_name"] = shop.get("name")
                context["shop_code"] = shop.get("code")
        except Exception:
            pass
    
    # BRANCH
    if branch_id:
        try:
            response = supabase.table("branches").select(
                "name, code"
            ).eq("id", branch_id).limit(1).execute()
            
            if response.data:
                branch = response.data[0]
                context["branch_name"] = branch.get("name")
                context["branch_code"] = branch.get("code")
        except Exception:
            pass
    
    return context


# ==============================================================================
# LOGIN
# ==============================================================================

def login_user(username: str, password: str) -> Tuple[bool, str]:
    """Authenticate user"""
    user = get_user(username)
    
    if not user:
        return False, "User not found."
    
    locked_until = user.get("locked_until")
    
    if locked_until:
        try:
            lock_time = datetime.fromisoformat(
                str(locked_until).replace("Z", "+00:00")
            )
            
            if datetime.now(timezone.utc) < lock_time:
                return False, "Account locked. Try again later."
        except Exception:
            pass
    
    # PASSWORD SUCCESS
    if verify_password(user, password):
        supabase.table("users").update({
            "failed_attempts": 0,
            "locked_until": None,
        }).eq("id", user["id"]).execute()
        
        build_session(user)
        log_auth_event(user["id"], "login")
        
        return True, "Success"
    
    # PASSWORD FAILED
    attempts = user.get("failed_attempts", 0) + 1
    
    update_data = {"failed_attempts": attempts}
    
    if attempts >= MAX_FAILED_ATTEMPTS:
        update_data["locked_until"] = (
            datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
        ).isoformat()
    
    supabase.table("users").update(update_data).eq("id", user["id"]).execute()
    
    log_auth_event(user["id"], "login", "failed")
    
    return False, "Invalid password."


# ==============================================================================
# SESSION
# ==============================================================================

def build_session(user: Dict[str, Any]):
    """Build session for authenticated user"""
    role_id = int(user.get("role_id", ROLE_CASHIER))
    user_id = user.get("id")
    username = user.get("username") or user.get("email") or "Unknown"
    
    tenant_context = build_tenant_context(user)
    
    session_user = {
        "id": user_id,
        "username": username,
        "full_name": user.get("full_name", username),
        "role_id": role_id,
        "role": ROLE_MAP.get(role_id, "Cashier"),
        "is_active": bool(user.get("is_active", True)),
        "last_activity": time.time(),
        # MULTI TENANT
        "shop_id": tenant_context.get("shop_id"),
        "branch_id": tenant_context.get("branch_id"),
        "tenant_role": tenant_context.get("tenant_role"),
        "shop_name": tenant_context.get("shop_name"),
        "branch_name": tenant_context.get("branch_name"),
        "tenant_context": tenant_context,
    }
    
    # Store in auth session
    auth_session.set_user(session_user)
    
    return session_user


# ==============================================================================
# CURRENT USER
# ==============================================================================

def get_current_user() -> Dict[str, Any]:
    """Get current user from session"""
    return auth_session.get("user", {})


def current_user() -> Dict[str, Any]:
    """Alias for get_current_user"""
    return get_current_user()


def get_current_role_id() -> Optional[int]:
    """Get current user's role ID"""
    user = get_current_user()
    return user.get("role_id") if user else None


def get_current_shop_id() -> Optional[str]:
    """Get current shop ID"""
    return auth_session.get("shop_id")


def get_current_branch_id() -> Optional[str]:
    """Get current branch ID"""
    return auth_session.get("branch_id")


def get_current_tenant_role() -> str:
    """Get current tenant role"""
    return auth_session.get("tenant_role", TENANT_ROLE_STAFF)


def get_current_tenant_context() -> Optional[Dict[str, Any]]:
    """Get current tenant context"""
    return auth_session.get("tenant_context")


# ==============================================================================
# TENANT PERMISSIONS
# ==============================================================================

def is_shop_owner() -> bool:
    """Check if current user is shop owner"""
    return get_current_tenant_role() == TENANT_ROLE_OWNER


def is_shop_admin() -> bool:
    """Check if current user is shop admin or owner"""
    return get_current_tenant_role() in [TENANT_ROLE_ADMIN, TENANT_ROLE_OWNER]


def is_shop_manager() -> bool:
    """Check if current user is shop manager or higher"""
    return get_current_tenant_role() in [
        TENANT_ROLE_MANAGER,
        TENANT_ROLE_ADMIN,
        TENANT_ROLE_OWNER,
    ]


# ==============================================================================
# MAKER / CHECKER
# ==============================================================================

def is_maker() -> bool:
    """Check if user has maker permission"""
    tenant_role = get_current_tenant_role()
    return tenant_role in [TENANT_ROLE_ADMIN, TENANT_ROLE_OWNER]


def is_checker() -> bool:
    """Check if user has checker permission"""
    tenant_role = get_current_tenant_role()
    return tenant_role in [TENANT_ROLE_ADMIN, TENANT_ROLE_OWNER]


# ==============================================================================
# AUTHENTICATION
# ==============================================================================

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    user = get_current_user()
    
    if not user:
        return False
    
    if not user.get("is_active", False):
        return False
    
    last_activity = user.get("last_activity", 0)
    
    if time.time() - last_activity > SESSION_IDLE_TIMEOUT:
        logout()
        return False
    
    # Update last activity
    user["last_activity"] = time.time()
    auth_session.get_session()["user"] = user
    
    return True


def require_login() -> Dict[str, Any]:
    """Require authentication, return current user"""
    if not is_authenticated():
        ui.notify("Please login first.", type='warning', position='top')
        return {}
    
    return current_user()


def require_admin() -> Dict[str, Any]:
    """Require admin role"""
    user = require_login()
    
    if user.get("role_id") != ROLE_ADMIN:
        ui.notify("Admin privileges required.", type='error', position='top')
        return {}
    
    return user


def require_role(role_id: int) -> Dict[str, Any]:
    """Require specific role"""
    user = require_login()
    
    if user.get("role_id") != role_id:
        ui.notify(
            f"Requires {ROLE_MAP.get(role_id)}",
            type='error',
            position='top'
        )
        return {}
    
    return user


def require_tenant_role(min_tenant_role: str) -> Dict[str, Any]:
    """Require minimum tenant role"""
    user = require_login()
    
    current_role = user.get("tenant_role", TENANT_ROLE_STAFF)
    current_level = TENANT_ROLE_HIERARCHY.get(current_role, 0)
    required_level = TENANT_ROLE_HIERARCHY.get(min_tenant_role, 0)
    
    if current_level < required_level:
        ui.notify(
            f"Requires {TENANT_ROLE_MAP.get(min_tenant_role)} or higher.",
            type='error',
            position='top'
        )
        return {}
    
    return user


# ==============================================================================
# ROLE PERMISSION
# ==============================================================================

def has_permission(permission_key: str) -> bool:
    """Check if current user has specific permission"""
    try:
        role_id = get_current_role_id()
        
        if not role_id:
            return False
        
        response = supabase.table("role_permissions").select("""
            allowed,
            permissions(permission_key)
        """).eq("role_id", role_id).execute()
        
        for item in (response.data or []):
            permission = item.get("permissions")
            
            if permission and permission.get("permission_key") == permission_key:
                return bool(item.get("allowed", False))
        
        return False
    
    except Exception:
        return False


# ==============================================================================
# LOGIN UI
# ==============================================================================

def login_page(container: Optional[Any] = None, on_success: Optional[Callable] = None):
    """
    Render login page
    
    Args:
        container: NiceGUI container to render in
        on_success: Callback function after successful login
    """
    target = container or ui.column()
    
    with target:
        with ui.card().classes('w-96 mx-auto mt-20 p-6'):
            ui.label('ERP Enterprise Login').classes('text-2xl font-bold text-center mb-4')
            
            username_input = ui.input('Username').classes('w-full mb-2')
            password_input = ui.input('Password', password=True, password_toggle_button=True).classes('w-full mb-4')
            
            def handle_login():
                success, message = login_user(
                    username_input.value,
                    password_input.value
                )
                
                if success:
                    ui.notify('Login successful!', type='positive', position='top')
                    if on_success:
                        on_success()
                else:
                    ui.notify(message, type='error', position='top')
            
            ui.button(
                'Login',
                on_click=handle_login
            ).classes('w-full bg-blue-500 text-white')


# ==============================================================================
# LOGOUT
# ==============================================================================

def logout():
    """Clear session and logout"""
    auth_session.clear()
    ui.notify('Logged out successfully.', type='info', position='top')


# ==============================================================================
# SIDEBAR AUTH PANEL
# ==============================================================================

def auth_sidebar(session_state: Dict[str, Any] = None):
    """Render authentication info in sidebar"""
    if not is_authenticated():
        return
    
    user = current_user()
    
    with ui.column().classes('w-full gap-1'):
        ui.label(f"User: {user.get('full_name', 'User')}").classes('text-green-600 font-semibold')
        ui.label(f"Role: {user.get('role', 'Unknown')}").classes('text-sm text-gray-600')
        
        tenant_role = user.get("tenant_role")
        shop_name = user.get("shop_name")
        branch_name = user.get("branch_name")
        
        if tenant_role:
            ui.label(
                f"Tenant Role: {TENANT_ROLE_MAP.get(tenant_role, tenant_role)}"
            ).classes('text-sm text-gray-600')
        
        if shop_name:
            ui.label(f"Shop: {shop_name}").classes('text-sm text-gray-600')
        
        if branch_name:
            ui.label(f"Branch: {branch_name}").classes('text-sm text-gray-600')


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    # SYSTEM ROLES
    "ROLE_ADMIN",
    "ROLE_MANAGER",
    "ROLE_CASHIER",
    "ROLE_MAP",
    
    # TENANT ROLES
    "TENANT_ROLE_STAFF",
    "TENANT_ROLE_MANAGER",
    "TENANT_ROLE_ADMIN",
    "TENANT_ROLE_OWNER",
    "TENANT_ROLE_MAP",
    "TENANT_ROLE_HIERARCHY",
    
    # PASSWORD
    "hash_password",
    "verify_password",
    "upgrade_password",
    "change_password",
    
    # USER
    "get_user",
    "login_user",
    
    # SESSION
    "build_session",
    "build_tenant_context",
    "get_current_user",
    "current_user",
    "get_current_role_id",
    "get_current_shop_id",
    "get_current_branch_id",
    "get_current_tenant_role",
    "get_current_tenant_context",
    "auth_session",
    
    # TENANT PERMISSIONS
    "is_shop_owner",
    "is_shop_admin",
    "is_shop_manager",
    
    # MAKER CHECKER
    "is_maker",
    "is_checker",
    
    # AUTH GUARDS
    "is_authenticated",
    "require_login",
    "require_admin",
    "require_role",
    "require_tenant_role",
    "has_permission",
    
    # UI
    "login_page",
    "logout",
    "auth_sidebar",
    
    # AUDIT
    "log_auth_event",
]
