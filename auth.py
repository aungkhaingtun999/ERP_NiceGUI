# ============================================================
# auth.py
# ERP ENTERPRISE AUTHENTICATION
# MULTI-TENANT
# SHA-256 PASSWORD AUTH
# SUPABASE USERS TABLE
# MAKER / CHECKER
# ============================================================

import hashlib
import time
from datetime import datetime, timedelta, timezone

import streamlit as st

from supabase_client import get_supabase


# ============================================================
# SUPABASE
# ============================================================

supabase = get_supabase()


# ============================================================
# SESSION / LOGIN SETTINGS
# ============================================================

SESSION_IDLE_TIMEOUT = 1800

# Maximum failed attempts before account lockout
MAX_FAILED_ATTEMPTS = 10  # Changed from 5 to 10

# Lock duration after exceeding max failed attempts
LOCK_DURATION_MINUTES = 30  # Increased from 15 to 30 minutes


# ============================================================
# SYSTEM ROLES
# ============================================================

ROLE_ADMIN = 1
ROLE_MANAGER = 2
ROLE_CASHIER = 3

ROLE_MAP = {
    ROLE_ADMIN: "Admin",
    ROLE_MANAGER: "Manager",
    ROLE_CASHIER: "Cashier",
}


# ============================================================
# TENANT ROLES
# ============================================================

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


# ============================================================
# PASSWORD
# ============================================================

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    if password is None:
        password = ""
    
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def verify_password(user, password):
    """Verify password against stored hash"""
    if not user:
        return False
    
    stored = user.get("password_hash")
    
    if not stored:
        return False
    
    stored = str(stored).strip()
    
    return hash_password(password) == stored


# ============================================================
# USER LOOKUP
# ============================================================

def get_user_by_username(username):
    """Get user by username from database"""
    try:
        clean_username = str(
            username or ""
        ).strip()
        
        if not clean_username:
            return None
        
        result = (
            supabase
            .table("users")
            .select("*")
            .eq("username", clean_username)
            .limit(1)
            .execute()
        )
        
        data = result.data or []
        
        return data[0] if data else None
    
    except Exception as e:
        st.error(f"Error fetching user: {str(e)}")
        return None


# ============================================================
# ACCOUNT LOCK
# ============================================================

def is_account_locked(user):
    """Check if user account is locked"""
    if not user:
        return False
    
    locked_until = user.get("locked_until")
    
    if not locked_until:
        return False
    
    try:
        locked_time = datetime.fromisoformat(
            str(locked_until).replace(
                "Z",
                "+00:00"
            )
        )
        
        if locked_time.tzinfo is None:
            locked_time = locked_time.replace(
                tzinfo=timezone.utc
            )
        
        return datetime.now(
            timezone.utc
        ) < locked_time
    
    except Exception:
        return False


# ============================================================
# FAILED LOGIN
# ============================================================

def record_failed_login(user):
    """Record failed login attempt and lock account if needed"""
    if not user:
        return
    
    try:
        attempts = int(
            user.get("failed_attempts") or 0
        ) + 1
        
        data = {
            "failed_attempts": attempts
        }
        
        if attempts >= MAX_FAILED_ATTEMPTS:
            data["locked_until"] = (
                datetime.now(timezone.utc)
                + timedelta(
                    minutes=LOCK_DURATION_MINUTES
                )
            ).isoformat()
        
        (
            supabase
            .table("users")
            .update(data)
            .eq("id", user.get("id"))
            .execute()
        )
    
    except Exception as e:
        print(f"Error recording failed login: {str(e)}")


# ============================================================
# RESET LOGIN STATE
# ============================================================

def reset_login_state(user):
    """Reset login state after successful login"""
    if not user:
        return
    
    try:
        (
            supabase
            .table("users")
            .update({
                "failed_attempts": 0,
                "locked_until": None,
                "last_login": datetime.now(
                    timezone.utc
                ).isoformat()
            })
            .eq("id", user.get("id"))
            .execute()
        )
    
    except Exception as e:
        print(f"Error resetting login state: {str(e)}")


# ============================================================
# LOGIN
# ============================================================

def login_user(username, password):
    """Authenticate user with username and password"""
    username = str(
        username or ""
    ).strip()
    
    if not username:
        return False, "Username required"
    
    if not password:
        return False, "Password required"
    
    user = get_user_by_username(username)
    
    if not user:
        return False, "User not found"
    
    if not bool(
        user.get("is_active", False)
    ):
        return False, "Account is disabled"
    
    if is_account_locked(user):
        return (
            False,
            "Account temporarily locked. Please try again later."
        )
    
    if not verify_password(
        user,
        password
    ):
        record_failed_login(user)
        
        # Get updated failed attempts count
        updated_user = get_user_by_username(username)
        if updated_user:
            failed_attempts = int(
                updated_user.get("failed_attempts") or 0
            )
            remaining_attempts = MAX_FAILED_ATTEMPTS - failed_attempts
            
            if remaining_attempts > 0:
                return False, f"Invalid password. {remaining_attempts} attempts remaining."
            else:
                return False, "Invalid password. Account locked due to too many failed attempts."
        
        return False, "Invalid password"
    
    reset_login_state(user)
    build_session(user)
    
    return True, "Success"


# ============================================================
# SESSION BUILDER
# ============================================================

def build_session(user):
    """Build session data for authenticated user"""
    if not user:
        return
    
    role_id = user.get(
        "role_id",
        ROLE_CASHIER
    )
    
    try:
        role_id = int(role_id)
    except (TypeError, ValueError):
        role_id = ROLE_CASHIER
    
    user_id = user.get("id")
    username = str(
        user.get("username")
        or "Unknown"
    )
    full_name = (
        user.get("full_name")
        or username
    )
    shop_id = user.get("shop_id")
    branch_id = user.get("branch_id")
    tenant_role = (
        user.get("tenant_role")
        or TENANT_ROLE_STAFF
    )
    
    session_user = {
        "id": user_id,
        "username": username,
        "full_name": full_name,
        "role_id": role_id,
        "role": ROLE_MAP.get(
            role_id,
            "Cashier"
        ),
        "shop_id": shop_id,
        "branch_id": branch_id,
        "tenant_role": tenant_role,
        "tenant_role_name": TENANT_ROLE_MAP.get(
            tenant_role,
            "Staff"
        ),
        "is_active": bool(
            user.get(
                "is_active",
                True
            )
        ),
        "last_activity": time.time(),
    }
    
    st.session_state["user"] = session_user
    
    # Backward compatibility
    st.session_state["user_id"] = user_id
    st.session_state["username"] = username
    st.session_state["role_id"] = role_id
    st.session_state["shop_id"] = shop_id
    st.session_state["branch_id"] = branch_id
    st.session_state["tenant_role"] = tenant_role
    st.session_state["id"] = user_id


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user():
    """Get current authenticated user"""
    user = st.session_state.get("user")
    return user if isinstance(user, dict) else {}


# ============================================================
# CURRENT USER ID
# ============================================================

def get_current_user_id():
    """Get current user ID"""
    user = get_current_user()
    return user.get("id")


# ============================================================
# SHOP
# ============================================================

def get_current_shop_id():
    """Get current shop ID"""
    user = get_current_user()
    return user.get("shop_id")


# ============================================================
# BRANCH
# ============================================================

def get_current_branch_id():
    """Get current branch ID"""
    user = get_current_user()
    return user.get("branch_id")


# ============================================================
# TENANT ROLE
# ============================================================

def get_current_tenant_role():
    """Get current tenant role"""
    user = get_current_user()
    return user.get(
        "tenant_role",
        TENANT_ROLE_STAFF
    )


# ============================================================
# OWNER
# ============================================================

def is_shop_owner():
    """Check if current user is shop owner"""
    return (
        get_current_tenant_role()
        == TENANT_ROLE_OWNER
    )


# ============================================================
# ADMIN
# ============================================================

def is_tenant_admin():
    """Check if current user is tenant admin"""
    return (
        get_current_tenant_role()
        in {
            TENANT_ROLE_OWNER,
            TENANT_ROLE_ADMIN
        }
    )


# ============================================================
# MAKER
# ============================================================

def is_maker():
    """Check if current user is maker (admin)"""
    user = get_current_user()
    if not user:
        return False
    return (
        user.get("role_id")
        == ROLE_ADMIN
    )


# ============================================================
# CHECKER
# ============================================================

def is_checker():
    """Check if current user is checker (owner)"""
    return is_shop_owner()


# ============================================================
# AUTHENTICATED
# ============================================================

def is_authenticated():
    """Check if user is authenticated and session is valid"""
    user = get_current_user()
    
    if not user:
        return False
    
    if not bool(
        user.get("is_active", False)
    ):
        return False
    
    last_activity = user.get("last_activity")
    
    if not last_activity:
        return False
    
    if (
        time.time()
        - last_activity
        > SESSION_IDLE_TIMEOUT
    ):
        logout()
        return False
    
    user["last_activity"] = time.time()
    st.session_state["user"] = user  # Update session
    
    return True


# ============================================================
# REQUIRE LOGIN
# ============================================================

def require_login():
    """Require user to be logged in"""
    if not is_authenticated():
        login_page()
        st.stop()
    
    return get_current_user()


# ============================================================
# REQUIRE ADMIN
# ============================================================

def require_admin():
    """Require admin role"""
    user = require_login()
    
    if user.get("role_id") != ROLE_ADMIN:
        st.error("⛔ Admin privileges required.")
        st.stop()
    
    return user


# ============================================================
# REQUIRE TENANT ADMIN
# ============================================================

def require_tenant_admin():
    """Require tenant admin role"""
    user = require_login()
    
    if not is_tenant_admin():
        st.error("⛔ Owner or Tenant Admin privileges required.")
        st.stop()
    
    return user


# ============================================================
# REQUIRE OWNER
# ============================================================

def require_owner():
    """Require owner role"""
    user = require_login()
    
    if not is_shop_owner():
        st.error("⛔ Owner privileges required.")
        st.stop()
    
    return user


# ============================================================
# REQUIRE SHOP OWNER (BACKWARD COMPATIBILITY)
# ============================================================

def require_shop_owner():
    """Require shop owner (backward compatibility)"""
    return require_tenant_admin()


# ============================================================
# REQUIRE SHOP ACCESS
# ============================================================

def require_shop_access():
    """Require shop access"""
    user = require_login()
    
    if not user.get("shop_id"):
        st.error("⛔ No shop assigned. Please contact administrator.")
        st.stop()
    
    return user


# ============================================================
# REQUIRE MAKER
# ============================================================

def require_maker():
    """Require maker role"""
    user = require_login()
    
    if not is_maker():
        st.error("⛔ Admin (Maker) privileges required.")
        st.stop()
    
    return user


# ============================================================
# REQUIRE CHECKER
# ============================================================

def require_checker():
    """Require checker role"""
    user = require_login()
    
    if not is_checker():
        st.error("⛔ Owner (Checker) privileges required.")
        st.stop()
    
    return user


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():
    """Display login page"""
    st.title("🔐 ERP Enterprise Login")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            submit_button = st.form_submit_button(
                "Login",
                use_container_width=True
            )
            
            if submit_button:
                if not username or not password:
                    st.error("Username and password required")
                else:
                    success, message = login_user(username, password)
                    
                    if success:
                        st.success("Login successful! Redirecting...")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        # Show information about login attempts
        st.info(f"ℹ️ Maximum {MAX_FAILED_ATTEMPTS} failed login attempts before account is locked.")


# ============================================================
# LOGOUT
# ============================================================

def logout():
    """Logout user and clear session"""
    keys = list(st.session_state.keys())
    
    for key in keys:
        try:
            del st.session_state[key]
        except Exception:
            pass
    
    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def auth_sidebar():
    """Display authentication info in sidebar"""
    if not is_authenticated():
        return
    
    user = get_current_user()
    
    with st.sidebar:
        st.success(f"👤 {user.get('full_name', 'User')}")
        st.caption(f"Role: {user.get('role', 'Unknown')}")
        st.caption(f"Tenant: {user.get('tenant_role_name', 'Staff')}")
        
        if user.get("shop_id"):
            st.caption(f"🏪 Shop ID: {user.get('shop_id')}")
        
        if user.get("branch_id"):
            st.caption(f"🏬 Branch ID: {user.get('branch_id')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
