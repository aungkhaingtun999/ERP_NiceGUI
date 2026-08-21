# ============================================================
# auth.py - SIMPLIFIED MULTI-TENANT (No RLS)
# ============================================================

import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import streamlit as st

from erp_core.base_repo import db

supabase = db()

# ==================================================
# CONSTANTS
# ==================================================

SESSION_IDLE_TIMEOUT = 1800  # 30 Minutes
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15

ROLE_ADMIN = 1
ROLE_MANAGER = 2
ROLE_CASHIER = 3

ROLE_MAP = {
    ROLE_ADMIN: "Admin",
    ROLE_MANAGER: "Manager",
    ROLE_CASHIER: "Cashier",
}

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
# PASSWORD ENGINE
# ==================================================

def verify_password(user, password):
    stored = user.get("password_hash")
    if not stored:
        return False
    stored = str(stored).strip()

    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False

    sha256_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(stored, sha256_hash):
        upgrade_password(user["id"], password)
        return True
    if hmac.compare_digest(stored, password):
        upgrade_password(user["id"], password)
        return True
    return False


def upgrade_password(user_id, password):
    try:
        new_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode()
        supabase.table("users").update({"password_hash": new_hash}).eq("id", user_id).execute()
    except Exception:
        pass

# ==================================================
# USER QUERY - FIXED
# ==================================================

def get_user_by_username(username):
    """Get user by username - case insensitive (Fixed)"""
    try:
        # ပထမ - တိကျတဲ့ username နဲ့ ရှာပါ
        result = supabase.table("users").select("*").eq("username", username.strip()).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        # ဒုတိယ - အကုန်ဆွဲပြီး case-insensitive ရှာပါ
        all_result = supabase.table("users").select("*").execute()
        
        if all_result.data:
            username_lower = username.strip().lower()
            for user in all_result.data:
                if user.get("username", "").lower() == username_lower:
                    return user
        
        return None
        
    except Exception as e:
        print(f"Get user error: {e}")
        return None

# ==================================================
# LOGIN
# ==================================================

def login_user(username, password):
    user = get_user_by_username(username)
    if not user:
        return False, "User not found. Please check username."

    if not user.get("is_active", False):
        return False, "Account is disabled. Please contact administrator."

    locked_until = user.get("locked_until")
    if locked_until:
        try:
            lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) < lock_time:
                return False, "Account locked. Try again later."
        except Exception:
            pass

    if not verify_password(user, password):
        attempts = user.get("failed_attempts", 0) + 1
        update_data = {"failed_attempts": attempts}
        if attempts >= MAX_FAILED_ATTEMPTS:
            update_data["locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)).isoformat()
        try:
            supabase.table("users").update(update_data).eq("id", user["id"]).execute()
        except Exception:
            pass
        return False, "Invalid password."

    try:
        supabase.table("users").update({
            "failed_attempts": 0,
            "locked_until": None,
            "last_login": datetime.now(timezone.utc).isoformat()
        }).eq("id", user["id"]).execute()
    except Exception:
        pass

    build_session(user)
    return True, "Success"

# ==================================================
# SESSION BUILDER
# ==================================================

def build_session(user):
    role_id = int(user.get("role_id", ROLE_CASHIER))
    user_id = user.get("id")
    username = user.get("username") or "Unknown"
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

    st.session_state["user_id"] = user_id
    st.session_state["username"] = username
    st.session_state["role_id"] = role_id
    st.session_state["shop_id"] = shop_id
    st.session_state["branch_id"] = branch_id
    st.session_state["tenant_role"] = tenant_role
    st.session_state["id"] = user_id

# ==================================================
# AUTH GUARDS
# ==================================================

def get_current_user():
    return st.session_state.get("user") or {}

def get_current_shop_id():
    user = get_current_user()
    return user.get("shop_id")

def get_current_branch_id():
    user = get_current_user()
    return user.get("branch_id")

def get_current_tenant_role():
    user = get_current_user()
    return user.get("tenant_role", TENANT_ROLE_STAFF)

def is_shop_owner():
    user = get_current_user()
    tenant_role = user.get("tenant_role", TENANT_ROLE_STAFF)
    return tenant_role in [TENANT_ROLE_OWNER, TENANT_ROLE_ADMIN]

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
    return get_current_user()

def require_admin():
    user = require_login()
    if user["role_id"] != ROLE_ADMIN:
        st.error("⛔ Admin privileges required.")
        st.stop()
    return user

def require_shop_owner():
    require_login()
    if not is_shop_owner():
        st.error("⛔ Shop owner or admin privileges required.")
        st.stop()
    return get_current_user()

def require_shop_access():
    require_login()
    if not get_current_shop_id():
        st.error("⛔ No shop assigned. Please contact administrator.")
        st.stop()
    return get_current_user()

# ==================================================
# LOGIN UI - WITH DEBUG
# ==================================================

def login_page():
    st.title("🔐 ERP Enterprise Login")
    
    # DEBUG - Show all users from database
    with st.expander("🔍 Database Debug (Click to expand)"):
        try:
            all_users = supabase.table("users").select("username, full_name, shop_id, tenant_role, is_active").execute()
            st.write("📋 Users in database:")
            st.dataframe(all_users.data)
        except Exception as e:
            st.error(f"❌ Cannot fetch users: {e}")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if not username or not password:
            st.error("Username and password required")
        else:
            # DEBUG
            st.write(f"🔍 Trying to login with: '{username}'")
            success, msg = login_user(username, password)
            if success:
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error(f"❌ {msg}")

# ==================================================
# LOGOUT
# ==================================================

def logout():
    for key in list(st.session_state.keys()):
        try:
            del st.session_state[key]
        except Exception:
            pass
    st.rerun()

# ==================================================
# SIDEBAR
# ==================================================

def auth_sidebar():
    if is_authenticated():
        user = get_current_user()
        with st.sidebar:
            st.success(f"👤 {user['full_name']}")
            st.caption(f"Role: {user['role']}")
            if user.get('shop_id'):
                st.caption(f"🏪 Shop: {user.get('shop_id', 'N/A')[:8]}...")
            if user.get('tenant_role'):
                st.caption(f"🔑 {user.get('tenant_role_name', 'Staff')}")
            if st.button("🚪 Logout"):
                logout()
