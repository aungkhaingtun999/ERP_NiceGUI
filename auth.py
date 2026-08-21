# ==============================================================================
# auth.py
# ERP ENTERPRISE AUTHENTICATION SYSTEM V32
# SECURITY + ROLE + SESSION + MULTI-TENANT MANAGEMENT
# With Supabase Auth Integration
# ==============================================================================

import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import streamlit as st

# V30 DATABASE CORE
from erp_core.base_repo import db

supabase = db()

# ==================================================
# SECURITY CONSTANTS
# ==================================================

SESSION_IDLE_TIMEOUT = 1800  # 30 Minutes
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15

# ==================================================
# ROLE CONSTANTS
# ==================================================

ROLE_ADMIN = 1
ROLE_MANAGER = 2
ROLE_CASHIER = 3

ROLE_MAP = {
    ROLE_ADMIN: "Admin",
    ROLE_MANAGER: "Manager",
    ROLE_CASHIER: "Cashier",
}

# ==================================================
# TENANT ROLE CONSTANTS
# ==================================================

TENANT_ROLE_OWNER = "owner"
TENANT_ROLE_ADMIN = "admin"
TENANT_ROLE_MANAGER = "manager"
TENANT_ROLE_STAFF = "staff"

TENANT_ROLE_MAP = {
    TENANT_ROLE_OWNER: "Owner",
    TENANT_ROLE_ADMIN: "Admin",
    TENANT_ROLE_MANAGER: "Manager",
    TENANT_ROLE_STAFF: "Staff",
}

# ==================================================
# AUDIT LOGGING
# ==================================================


def log_auth_event(user_id, event_type, status="success"):
    try:
        supabase.table("auth_logs").insert(
            {
                "user_id": user_id,
                "event": event_type,
                "status": status,
                "ip_address": "system",
            }
        ).execute()
    except Exception:
        pass


def log_audit_trail(user_id, action, table_name=None, record_id=None, old_data=None, new_data=None):
    """Log audit trail for compliance"""
    try:
        # Get current user's shop_id
        user = get_current_user()
        shop_id = user.get('shop_id') if user else None
        branch_id = user.get('branch_id') if user else None
        
        supabase.table("audit_trail").insert({
            "user_id": user_id,
            "shop_id": shop_id,
            "branch_id": branch_id,
            "action": action,
            "table_name": table_name,
            "record_id": record_id,
            "old_data": old_data,
            "new_data": new_data,
            "ip_address": "system",
            "user_agent": "ERP_System"
        }).execute()
    except Exception:
        pass


# ==================================================
# PASSWORD ENGINE
# ==================================================


def verify_password(user, password):
    stored = user.get("password_hash")

    if not stored:
        return False

    stored = str(stored).strip()

    # bcrypt
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), stored.encode("utf-8")
            )
        except Exception:
            return False

    # Legacy SHA256
    sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    if hmac.compare_digest(stored, sha256_hash) or hmac.compare_digest(
        stored, password
    ):
        upgrade_password(user["id"], password)
        return True

    return False


def upgrade_password(user_id, password):
    try:
        new_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode()

        supabase.table("users").update({"password_hash": new_hash}).eq(
            "id", user_id
        ).execute()
    except Exception:
        pass


# ==================================================
# USER QUERY (Case-Insensitive)
# ==================================================


def get_user_by_username(username):
    """Get user by username from custom users table (case-insensitive)"""
    try:
        result = (
            supabase.table("users")
            .select("*")
            .ilike("username", username.strip())
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception as e:
        print(f"Get user error: {e}")
        return None


def get_user_by_id(user_id):
    """Get user by ID from custom users table"""
    try:
        result = (
            supabase.table("users")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception as e:
        print(f"Get user by id error: {e}")
        return None


# ==================================================
# LOGIN ENGINE (Multi-Tenant)
# ==================================================


def login_user(username, password):
    # 1. Get user from custom users table (case-insensitive)
    user = get_user_by_username(username)

    if not user:
        return False, "User not found. Please check username."

    # 2. Check if account is locked
    locked_until = user.get("locked_until")

    if locked_until:
        lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))

        if datetime.now(timezone.utc) < lock_time:
            return False, "Account locked. Try again later."

    # 3. Verify password
    if not verify_password(user, password):
        # Update failed attempts
        attempts = user.get("failed_attempts", 0) + 1
        update_data = {"failed_attempts": attempts}

        if attempts >= MAX_FAILED_ATTEMPTS:
            update_data["locked_until"] = (
                datetime.now(timezone.utc)
                + timedelta(minutes=LOCK_DURATION_MINUTES)
            ).isoformat()

        try:
            supabase.table("users").update(update_data).eq(
                "id", user["id"]
            ).execute()
        except Exception:
            pass

        return False, "Invalid password."

    # 4. Login success - Reset failed attempts
    try:
        supabase.table("users").update(
            {
                "failed_attempts": 0,
                "locked_until": None,
                "last_login": datetime.now(timezone.utc).isoformat()
            }
        ).eq("id", user["id"]).execute()
    except Exception:
        pass

    # 5. Build session
    build_session(user)

    # 6. Log event
    log_auth_event(user["id"], "login")
    log_audit_trail(user["id"], "LOGIN", "users", user["id"])

    return True, "Success"


# ==================================================
# SESSION BUILDER (Multi-Tenant)
# ==================================================


def build_session(user):
    role_id = int(user.get("role_id", ROLE_CASHIER))
    user_id = user.get("id")
    username = user.get("username") or "Unknown"
    
    # Get tenant info
    shop_id = user.get("shop_id")
    branch_id = user.get("branch_id")
    tenant_role = user.get("tenant_role", TENANT_ROLE_STAFF)

    st.session_state.user = {
        "id": user_id,
        "username": username,
        "full_name": user.get("full_name", username),
        "role_id": role_id,
        "role": ROLE_MAP.get(role_id, "Cashier"),
        "shop_id": shop_id,
        "branch_id": branch_id,
        "tenant_role": tenant_role,
        "tenant_role_name": TENANT_ROLE_MAP.get(tenant_role, "Staff"),
        "is_active": bool(user.get("is_active", True)),
        "last_activity": time.time(),
    }

    # Session state shortcuts
    st.session_state["user_id"] = user_id
    st.session_state["username"] = username
    st.session_state["role_id"] = role_id
    st.session_state["shop_id"] = shop_id
    st.session_state["branch_id"] = branch_id
    st.session_state["tenant_role"] = tenant_role
    st.session_state["id"] = user_id


# ==================================================
# CURRENT USER HELPERS
# ==================================================


def get_current_user():
    return st.session_state.get("user") or {}


def current_user():
    return get_current_user()


def get_current_role_id():
    user = get_current_user()
    return user.get("role_id") if user else None


def get_current_shop_id():
    user = get_current_user()
    return user.get("shop_id") if user else None


def get_current_branch_id():
    user = get_current_user()
    return user.get("branch_id") if user else None


def get_current_tenant_role():
    user = get_current_user()
    return user.get("tenant_role", TENANT_ROLE_STAFF) if user else TENANT_ROLE_STAFF


def is_shop_owner():
    user = get_current_user()
    if not user:
        return False
    tenant_role = user.get("tenant_role", TENANT_ROLE_STAFF)
    return tenant_role in [TENANT_ROLE_OWNER, TENANT_ROLE_ADMIN]


# ==================================================
# AUTH GUARDS
# ==================================================


def is_authenticated():
    user = st.session_state.get("user")

    if not user:
        return False

    if not user.get("is_active", False):
        return False

    if (time.time() - user.get("last_activity", 0)) > SESSION_IDLE_TIMEOUT:
        logout()
        return False

    user["last_activity"] = time.time()
    return True


def require_login():
    if not is_authenticated():
        login_page()
        st.stop()
    return current_user()


def require_admin():
    user = require_login()

    if user["role_id"] != ROLE_ADMIN:
        st.error("⛔ Admin privileges required.")
        st.stop()

    return user


def require_role(role_id):
    user = require_login()

    if user["role_id"] != role_id:
        st.error(f"⛔ Requires {ROLE_MAP.get(role_id)}")
        st.stop()

    return user


# ==================================================
# MULTI-TENANT GUARDS
# ==================================================


def require_shop_owner():
    """Require user to be shop owner or admin"""
    require_login()
    user = get_current_user()
    tenant_role = user.get("tenant_role", TENANT_ROLE_STAFF)
    
    if tenant_role not in [TENANT_ROLE_OWNER, TENANT_ROLE_ADMIN]:
        st.error("⛔ Shop owner or admin privileges required.")
        st.stop()
    
    return user


def require_shop_access():
    """Require user to have a shop assigned"""
    require_login()
    user = get_current_user()
    
    if not user.get("shop_id"):
        st.error("⛔ No shop assigned. Please contact administrator.")
        st.stop()
    
    return user


def require_branch_access():
    """Require user to have a branch assigned"""
    require_login()
    user = get_current_user()
    
    if not user.get("branch_id"):
        st.error("⛔ No branch assigned. Please contact administrator.")
        st.stop()
    
    return user


def has_permission(permission_key):
    try:
        role_id = get_current_role_id()

        if not role_id:
            return False

        response = (
            supabase.table("role_permissions")
            .select(
                """
                allowed,
                permissions(
                    permission_key
                )
                """
            )
            .eq("role_id", role_id)
            .execute()
        )

        permissions = response.data or []

        for item in permissions:
            permission = item.get("permissions")

            if permission:
                if permission.get("permission_key") == permission_key:
                    return item.get("allowed", False)

        return False

    except Exception as e:
        st.error(f"Permission check error: {e}")
        return False


# ==================================================
# LOGIN UI
# ==================================================


def login_page():
    st.title("🔐 ERP Enterprise Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if not username or not password:
            st.error("Username and password required")
        else:
            success, msg = login_user(username, password)

            if success:
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error(f"❌ {msg}")


# ==================================================
# USER CREATION (Multi-Tenant)
# ==================================================


def create_user(username, full_name, password, role_id=ROLE_CASHIER, shop_id=None, branch_id=None, tenant_role=TENANT_ROLE_STAFF):
    """
    Create a new user with both custom auth and Supabase Auth.
    Supports Multi-Tenant with shop_id and branch_id.
    """
    try:
        import uuid

        # Check if username already exists (case-insensitive)
        existing = get_user_by_username(username)
        if existing:
            return False, "Username already exists"

        # Hash password (SHA256 for initial, will be upgraded to bcrypt)
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        # Generate UUID
        user_id = str(uuid.uuid4())

        # Create user data
        new_user = {
            "id": user_id,
            "username": username.strip(),
            "full_name": full_name,
            "password_hash": password_hash,
            "role_id": role_id,
            "shop_id": shop_id,
            "branch_id": branch_id,
            "tenant_role": tenant_role,
            "is_active": True,
            "failed_attempts": 0,
        }

        # Insert into custom users table
        result = supabase.table("users").insert(new_user).execute()

        if not result.data:
            return False, "Failed to create user"

        # Log audit
        log_audit_trail(user_id, "USER_CREATED", "users", user_id, None, new_user)

        return True, "User created successfully!"

    except Exception as e:
        return False, f"Error: {str(e)}"


# ==================================================
# PASSWORD MANAGEMENT
# ==================================================


def change_password(user_id, old_password, new_password):
    try:
        # Current user load
        result = (
            supabase.table("users")
            .select("*")
            .eq("id", user_id)
            .single()
            .execute()
        )

        user = result.data

        if not user:
            return False, "User not found"

        # Verify old password
        if not verify_password(user, old_password):
            return False, "Old password is incorrect"

        # Hash new password
        new_hash = bcrypt.hashpw(
            new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode()

        # Update custom users table
        supabase.table("users").update(
            {"password_hash": new_hash}
        ).eq("id", user_id).execute()

        # Log audit
        log_audit_trail(user_id, "PASSWORD_CHANGED", "users", user_id)

        return True, "Password changed successfully"

    except Exception as e:
        return False, str(e)


def reset_password(user_id, new_password, admin_user_id=None):
    """Reset user password (admin only)"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, "User not found"

        # Hash new password
        new_hash = bcrypt.hashpw(
            new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode()

        # Update custom users table
        supabase.table("users").update(
            {"password_hash": new_hash}
        ).eq("id", user_id).execute()

        # Log audit
        log_audit_trail(admin_user_id or user_id, "PASSWORD_RESET", "users", user_id)

        return True, "Password reset successfully"

    except Exception as e:
        return False, str(e)


# ==================================================
# LOGOUT
# ==================================================


def logout():
    # Log audit
    user_id = st.session_state.get("user_id")
    if user_id:
        log_audit_trail(user_id, "LOGOUT", "sessions")

    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


# ==================================================
# SIDEBAR USER PANEL (Multi-Tenant)
# ==================================================


def auth_sidebar():
    if is_authenticated():
        user = current_user()

        with st.sidebar:
            st.success(f"👤 {user['full_name']}")
            st.caption(f"Role: {user['role']}")
            
            if user.get('shop_id'):
                st.caption(f"🏪 Shop ID: {user.get('shop_id', 'N/A')[:8]}...")
            if user.get('branch_id'):
                st.caption(f"📍 Branch ID: {user.get('branch_id', 'N/A')[:8]}...")
            if user.get('tenant_role'):
                st.caption(f"🔑 {user.get('tenant_role_name', 'Staff')}")

            if st.button("🚪 Logout"):
                logout()
