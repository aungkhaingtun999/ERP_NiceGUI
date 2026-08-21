# ==============================================================================
# auth.py
# ERP ENTERPRISE AUTHENTICATION SYSTEM V31
# SECURITY + ROLE + SESSION MANAGEMENT
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
# SESSION BUILDER
# ==================================================


def build_session(user):
    role_id = int(user.get("role_id", ROLE_CASHIER))
    user_id = user.get("id")
    username = user.get("username") or user.get("email") or "Unknown"

    st.session_state.user = {
        "id": user_id,
        "username": username,
        "full_name": user.get("full_name", username),
        "role_id": role_id,
        "role": ROLE_MAP.get(role_id, "Cashier"),
        "is_active": bool(user.get("is_active", True)),
        "last_activity": time.time(),
    }

    # IMPORTANT UUID SESSION
    st.session_state["user_id"] = user_id
    st.session_state["username"] = username
    st.session_state["role_id"] = role_id

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
# USER CREATION
# ==================================================


def create_user(username, full_name, password, role_id=ROLE_CASHIER):
    """
    Create a new user with both custom auth and Supabase Auth.
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
            "is_active": True,
            "failed_attempts": 0,
            "created_at": "now()",
            "updated_at": "now()"
        }

        # Insert into custom users table
        result = supabase.table("users").insert(new_user).execute()

        if not result.data:
            return False, "Failed to create user"

        # Sync with Supabase Auth
        sync_with_supabase_auth(username, password, new_user)

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

        return True, "Password changed successfully"

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

    # Clear all session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()


# ==================================================
# SIDEBAR USER PANEL
# ==================================================


def auth_sidebar():
    if is_authenticated():
        user = current_user()

        with st.sidebar:
            st.success(f"👤 {user['full_name']}")

            st.caption(f"Role: {user['role']}")

            if st.button("🚪 Logout"):
                logout()
