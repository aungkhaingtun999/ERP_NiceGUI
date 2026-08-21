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

    # ---------------------------------
    # bcrypt
    # ---------------------------------
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), stored.encode("utf-8")
            )
        except Exception:
            return False

    # ---------------------------------
    # Legacy SHA256 / Plain Migration
    # ---------------------------------
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
# SUPABASE AUTH INTEGRATION
# ==================================================


def sync_with_supabase_auth(username, password, user_data=None):
    """
    Sync custom user with Supabase Auth.
    Creates or signs in the user with Supabase Auth.
    """
    email = f"{username}@nexora-erp.local"
    
    try:
        # Try to sign in with existing Supabase Auth user
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Store session tokens
        if auth_response.session:
            st.session_state["access_token"] = auth_response.session.access_token
            st.session_state["refresh_token"] = auth_response.session.refresh_token
            return True
            
    except Exception as sign_in_error:
        # If sign in fails, try to sign up
        try:
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "username": username,
                        "full_name": user_data.get("full_name", "") if user_data else "",
                        "role_id": user_data.get("role_id", ROLE_CASHIER) if user_data else ROLE_CASHIER,
                        "shop_id": user_data.get("shop_id") if user_data else None,
                        "branch_id": user_data.get("branch_id") if user_data else None,
                        "tenant_role": user_data.get("tenant_role", TENANT_ROLE_STAFF) if user_data else TENANT_ROLE_STAFF,
                    }
                }
            })
            
            # Store session tokens
            if auth_response.session:
                st.session_state["access_token"] = auth_response.session.access_token
                st.session_state["refresh_token"] = auth_response.session.refresh_token
                return True
                
        except Exception as sign_up_error:
            print(f"Supabase Auth sync failed: {sign_up_error}")
            return False
    
    return False


# ==================================================
# USER QUERY
# ==================================================


def get_user(username):
    try:
        result = (
            supabase.table("users")
            .select("*")
            .eq("username", username.strip())
            .eq("is_active", True)
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception:
        st.error("Authentication Database Error")
        return None


def get_user_by_id(user_id):
    try:
        result = (
            supabase.table("users")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception:
        return None


# ==================================================
# LOGIN ENGINE
# ==================================================


def login_user(username, password):
    user = get_user(username)

    if not user:
        return False, "User not found."

    locked_until = user.get("locked_until")

    if locked_until:
        lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))

        if datetime.now(timezone.utc) < lock_time:
            return False, "Account locked. Try again later."

    if verify_password(user, password):
        # Update failed attempts
        try:
            supabase.table("users").update(
                {"failed_attempts": 0, "locked_until": None}
            ).eq("id", user["id"]).execute()
        except Exception:
            pass

        # Sync with Supabase Auth (for RLS policies)
        sync_with_supabase_auth(username, password, user)

        # Build session
        build_session(user)

        # Log event
        log_auth_event(user["id"], "login")
        log_audit_trail(user["id"], "LOGIN", "users", user["id"])

        return True, "Success"

    else:
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

        log_auth_event(user["id"], "login", "failed")

        return False, "Invalid password."


# ==================================================
# SESSION BUILDER (Multi-Tenant)
# ==================================================


def build_session(user):
    role_id = int(user.get("role_id", ROLE_CASHIER))
    user_id = user.get("id")
    username = user.get("username") or user.get("email") or "Unknown"
    
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

    # IMPORTANT UUID SESSION
    st.session_state["user_id"] = user_id
    st.session_state["username"] = username
    st.session_state["role_id"] = role_id
    st.session_state["shop_id"] = shop_id
    st.session_state["branch_id"] = branch_id
    st.session_state["tenant_role"] = tenant_role

    # backup id
    st.session_state["id"] = user_id


# ==================================================
# CURRENT USER & ROLE HELPERS
# ==================================================


def get_current_user():
    return st.session_state.get("user") or {}


def current_user():
    return get_current_user()


def get_current_role_id():
    user = get_current_user()
    if not user:
        return None
    return user.get("role_id")


def get_current_shop_id():
    """Get current user's shop_id"""
    user = get_current_user()
    return user.get("shop_id") if user else None


def get_current_branch_id():
    """Get current user's branch_id"""
    user = get_current_user()
    return user.get("branch_id") if user else None


def get_current_tenant_role():
    """Get current user's tenant_role"""
    user = get_current_user()
    return user.get("tenant_role", TENANT_ROLE_STAFF) if user else TENANT_ROLE_STAFF


def is_shop_owner():
    """Check if current user is shop owner or admin"""
    user = get_current_user()
    if not user:
        return False
    tenant_role = user.get("tenant_role", TENANT_ROLE_STAFF)
    return tenant_role in [TENANT_ROLE_OWNER, TENANT_ROLE_ADMIN]


# ==================================================
# AUTH GUARDS & PERMISSIONS
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
        success, msg = login_user(username, password)

        if success:
            st.rerun()
        else:
            st.error(msg)


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

        # Check if username already exists
        existing = get_user(username)
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

        # Sync with Supabase Auth
        sync_with_supabase_auth(username, password, new_user)

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

        # Update Supabase Auth password
        try:
            email = f"{user['username']}@nexora-erp.local"
            supabase.auth.update_user({
                "email": email,
                "password": new_password
            })
        except Exception:
            pass

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

        # Update Supabase Auth password
        try:
            email = f"{user['username']}@nexora-erp.local"
            supabase.auth.update_user({
                "email": email,
                "password": new_password
            })
        except Exception:
            pass

        # Log audit
        log_audit_trail(admin_user_id or user_id, "PASSWORD_RESET", "users", user_id)

        return True, "Password reset successfully"

    except Exception as e:
        return False, str(e)


# ==================================================
# LOGOUT
# ==================================================


def logout():
    # Sign out from Supabase Auth
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

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
            
            # Show tenant info
            if user.get('shop_id'):
                st.caption(f"🏪 Shop: {user.get('shop_id', 'N/A')[:8]}...")
            if user.get('branch_id'):
                st.caption(f"📍 Branch: {user.get('branch_id', 'N/A')[:8]}...")
            if user.get('tenant_role'):
                st.caption(f"🔑 {user.get('tenant_role_name', 'Staff')}")

            if st.button("🚪 Logout"):
                logout()
