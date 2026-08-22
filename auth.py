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

MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15


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

    if password is None:
        password = ""

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def verify_password(user, password):

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

    except Exception:
        return None


# ============================================================
# ACCOUNT LOCK
# ============================================================

def is_account_locked(user):

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

    if not user:
        return

    try:

        attempts = int(
            user.get("failed_attempts") or 0
        ) + 1

        data = {
            "failed_attempts": attempts
        }

        if attempts >= MAX_FAILED_ATTEMPTS=5:
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

    except Exception:
        pass


# ============================================================
# RESET LOGIN STATE
# ============================================================

def reset_login_state(user):

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

    except Exception:
        pass


# ============================================================
# LOGIN
# ============================================================

def login_user(username, password):

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

        return False, "Invalid password"

    reset_login_state(user)

    build_session(user)

    return True, "Success"


# ============================================================
# SESSION BUILDER
# ============================================================

def build_session(user):

    if not user:
        return

    role_id = user.get(
        "role_id",
        ROLE_CASHIER
    )

    try:
        role_id = int(role_id)
    except Exception:
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

    # --------------------------------------------------------
    # BACKWARD COMPATIBILITY
    # --------------------------------------------------------

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

    user = st.session_state.get("user")

    return user if isinstance(
        user,
        dict
    ) else {}


# ============================================================
# CURRENT USER ID
# ============================================================

def get_current_user_id():

    user = get_current_user()

    return user.get("id")


# ============================================================
# SHOP
# ============================================================

def get_current_shop_id():

    user = get_current_user()

    return user.get("shop_id")


# ============================================================
# BRANCH
# ============================================================

def get_current_branch_id():

    user = get_current_user()

    return user.get("branch_id")


# ============================================================
# TENANT ROLE
# ============================================================

def get_current_tenant_role():

    user = get_current_user()

    return user.get(
        "tenant_role",
        TENANT_ROLE_STAFF
    )


# ============================================================
# OWNER
# ============================================================

def is_shop_owner():

    return (
        get_current_tenant_role()
        == TENANT_ROLE_OWNER
    )


# ============================================================
# ADMIN
# ============================================================

def is_tenant_admin():

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

    return is_shop_owner()


# ============================================================
# AUTHENTICATED
# ============================================================

def is_authenticated():

    user = get_current_user()

    if not user:
        return False

    if not bool(
        user.get("is_active", False)
    ):
        return False

    last_activity = user.get(
        "last_activity"
    )

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

    return True


# ============================================================
# REQUIRE LOGIN
# ============================================================

def require_login():

    if not is_authenticated():

        login_page()

        st.stop()

    return get_current_user()


# ============================================================
# REQUIRE ADMIN
# ============================================================

def require_admin():

    user = require_login()

    if user.get("role_id") != ROLE_ADMIN:

        st.error(
            "⛔ Admin privileges required."
        )

        st.stop()

    return user


# ============================================================
# REQUIRE TENANT ADMIN
# ============================================================

def require_tenant_admin():

    user = require_login()

    if not is_tenant_admin():

        st.error(
            "⛔ Owner or Tenant Admin privileges required."
        )

        st.stop()

    return user


# ============================================================
# REQUIRE OWNER
# ============================================================

def require_owner():

    user = require_login()

    if not is_shop_owner():

        st.error(
            "⛔ Owner privileges required."
        )

        st.stop()

    return user


# ============================================================
# REQUIRE SHOP OWNER
# BACKWARD COMPATIBILITY
# ============================================================

def require_shop_owner():

    return require_tenant_admin()


# ============================================================
# REQUIRE SHOP ACCESS
# ============================================================

def require_shop_access():

    user = require_login()

    if not user.get("shop_id"):

        st.error(
            "⛔ No shop assigned. "
            "Please contact administrator."
        )

        st.stop()

    return user


# ============================================================
# REQUIRE MAKER
# ============================================================

def require_maker():

    user = require_login()

    if not is_maker():

        st.error(
            "⛔ Admin (Maker) privileges required."
        )

        st.stop()

    return user


# ============================================================
# REQUIRE CHECKER
# ============================================================

def require_checker():

    user = require_login()

    if not is_checker():

        st.error(
            "⛔ Owner (Checker) privileges required."
        )

        st.stop()

    return user


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    st.title("🔐 ERP Enterprise Login")

    username = st.text_input(
        "Username",
        key="login_username"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        if st.button(
            "Login",
            use_container_width=True,
            type="primary"
        ):

            if not username or not password:

                st.error(
                    "Username and password required"
                )

                return

            success, message = login_user(
                username,
                password
            )

            if success:

                st.rerun()

            st.error(
                f"❌ {message}"
            )


# ============================================================
# LOGOUT
# ============================================================

def logout():

    keys = list(
        st.session_state.keys()
    )

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

    if not is_authenticated():
        return

    user = get_current_user()

    with st.sidebar:

        st.success(
            f"👤 {user.get('full_name', 'User')}"
        )

        st.caption(
            f"Role: {user.get('role', 'Unknown')}"
        )

        st.caption(
            f"Tenant: "
            f"{user.get('tenant_role_name', 'Staff')}"
        )

        if user.get("shop_id"):

            st.caption(
                f"🏪 Shop ID: "
                f"{user.get('shop_id')}"
            )

        if user.get("branch_id"):

            st.caption(
                f"🏬 Branch ID: "
                f"{user.get('branch_id')}"
            )

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            logout()
