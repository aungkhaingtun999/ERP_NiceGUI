# ============================================================
# auth.py
# ERP ENTERPRISE AUTHENTICATION
# SHA-256 PASSWORD AUTH
# SUPABASE USERS TABLE
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
# CONSTANTS
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
# PASSWORD HASH
# ============================================================

def hash_password(password: str) -> str:
    """
    Hash password using SHA-256.

    Database password_hash must contain the hexadecimal
    SHA-256 digest.
    """

    if password is None:
        password = ""

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# PASSWORD VERIFY
# ============================================================

def verify_password(user, password):
    """
    Verify entered password against users.password_hash.
    """

    if not user:
        return False

    stored = user.get("password_hash")

    if not stored:
        return False

    stored = str(stored).strip()

    calculated = hash_password(password)

    return calculated == stored


# ============================================================
# USER QUERY
# ============================================================

def get_user_by_username(username):
    """
    Get active/user record by username.
    """

    try:
        clean_username = (username or "").strip()

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

        if result.data:
            return result.data[0]

        return None

    except Exception as e:
        print(f"Authentication user query error: {e}")
        return None


# ============================================================
# ACCOUNT LOCK CHECK
# ============================================================

def is_account_locked(user):
    """
    Check whether account is currently locked.
    """

    locked_until = user.get("locked_until")

    if not locked_until:
        return False

    try:
        locked_time = datetime.fromisoformat(
            str(locked_until).replace("Z", "+00:00")
        )

        if locked_time.tzinfo is None:
            locked_time = locked_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        if now < locked_time:
            return True

        return False

    except Exception:
        return False


# ============================================================
# UPDATE FAILED LOGIN
# ============================================================

def record_failed_login(user):
    """
    Increment failed login attempts.
    Lock account after MAX_FAILED_ATTEMPTS.
    """

    try:
        attempts = int(user.get("failed_attempts") or 0) + 1

        update_data = {
            "failed_attempts": attempts
        }

        if attempts >= MAX_FAILED_ATTEMPTS:

            locked_until = (
                datetime.now(timezone.utc)
                + timedelta(minutes=LOCK_DURATION_MINUTES)
            )

            update_data["locked_until"] = locked_until.isoformat()

        supabase \
            .table("users") \
            .update(update_data) \
            .eq("id", user["id"]) \
            .execute()

    except Exception as e:
        print(f"Failed login update error: {e}")


# ============================================================
# RESET LOGIN STATE
# ============================================================

def reset_login_state(user):
    """
    Reset failed attempts after successful login.
    """

    try:
        supabase \
            .table("users") \
            .update({
                "failed_attempts": 0,
                "locked_until": None,
                "last_login": datetime.now(timezone.utc).isoformat()
            }) \
            .eq("id", user["id"]) \
            .execute()

    except Exception as e:
        print(f"Login state update error: {e}")


# ============================================================
# LOGIN
# ============================================================

def login_user(username, password):

    username = (username or "").strip()

    if not username:
        return False, "Username required"

    if not password:
        return False, "Password required"

    # --------------------------------------------------------
    # GET USER
    # --------------------------------------------------------

    user = get_user_by_username(username)

    if not user:
        return False, "User not found"

    # --------------------------------------------------------
    # ACTIVE CHECK
    # --------------------------------------------------------

    if not bool(user.get("is_active", False)):
        return False, "Account is disabled"

    # --------------------------------------------------------
    # LOCK CHECK
    # --------------------------------------------------------

    if is_account_locked(user):
        return (
            False,
            "Account temporarily locked. Please try again later."
        )

    # --------------------------------------------------------
    # PASSWORD CHECK
    # --------------------------------------------------------

    if not verify_password(user, password):

        record_failed_login(user)

        return False, "Invalid password"

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    reset_login_state(user)

    build_session(user)

    return True, "Success"


# ============================================================
# SESSION BUILDER
# ============================================================

def build_session(user):

    role_id = int(
        user.get("role_id", ROLE_CASHIER)
    )

    user_id = user.get("id")

    username = (
        user.get("username")
        or "Unknown"
    )

    shop_id = user.get("shop_id")

    branch_id = user.get("branch_id")

    tenant_role = (
        user.get("tenant_role")
        or TENANT_ROLE_STAFF
    )

    st.session_state.user = {

        "id": user_id,

        "username": username,

        "full_name": (
            user.get("full_name")
            or username
        ),

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
            user.get("is_active", True)
        ),

        "last_activity": time.time(),
    }

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

    return st.session_state.get(
        "user",
        {}
    )


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
# SHOP OWNER
# ============================================================

def is_shop_owner():

    user = get_current_user()

    tenant_role = user.get(
        "tenant_role",
        TENANT_ROLE_STAFF
    )

    return tenant_role in [
        TENANT_ROLE_OWNER,
        TENANT_ROLE_ADMIN
    ]


# ============================================================
# MAKER
# ============================================================

def is_maker():

    user = get_current_user()

    if not user:
        return False

    return user.get("role_id") == ROLE_ADMIN


# ============================================================
# CHECKER
# ============================================================

def is_checker():

    user = get_current_user()

    if not user:
        return False

    return user.get(
        "tenant_role"
    ) == TENANT_ROLE_OWNER


# ============================================================
# AUTHENTICATED
# ============================================================

def is_authenticated():

    user = st.session_state.get("user")

    if not user:
        return False

    if not user.get(
        "is_active",
        False
    ):
        return False

    last_activity = user.get(
        "last_activity",
        0
    )

    if (
        time.time() - last_activity
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
# REQUIRE SHOP OWNER
# ============================================================

def require_shop_owner():

    require_login()

    if not is_shop_owner():

        st.error(
            "⛔ Shop owner or admin privileges required."
        )

        st.stop()

    return get_current_user()


# ============================================================
# REQUIRE SHOP ACCESS
# ============================================================

def require_shop_access():

    require_login()

    if not get_current_shop_id():

        st.error(
            "⛔ No shop assigned. "
            "Please contact administrator."
        )

        st.stop()

    return get_current_user()


# ============================================================
# REQUIRE MAKER
# ============================================================

def require_maker():

    require_login()

    if not is_maker():

        st.error(
            "⛔ Admin (Maker) privileges required."
        )

        st.stop()


# ============================================================
# REQUIRE CHECKER
# ============================================================

def require_checker():

    require_login()

    if not is_checker():

        st.error(
            "⛔ Owner (Checker) privileges required."
        )

        st.stop()


# ============================================================
# LOGIN UI
# ============================================================

def login_page():

    st.title("🔐 ERP Enterprise Login")

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        if st.button(
            "Login",
            use_container_width=True
        ):

            if not username or not password:

                st.error(
                    "Username and password required"
                )

            else:

                success, msg = login_user(
                    username,
                    password
                )

                if success:

                    st.success(
                        "✅ Login successful!"
                    )

                    st.rerun()

                else:

                    st.error(
                        f"❌ {msg}"
                    )


# ============================================================
# LOGOUT
# ============================================================

def logout():

    for key in list(
        st.session_state.keys()
    ):

        try:
            del st.session_state[key]

        except Exception:
            pass

    st.rerun()


# ============================================================
# SIDEBAR
# ============================================================

def auth_sidebar():

    if is_authenticated():

        user = get_current_user()

        with st.sidebar:

            st.success(
                f"👤 {user.get('full_name', 'User')}"
            )

            st.caption(
                f"Role: {user.get('role', 'Unknown')}"
            )

            if user.get("shop_id"):

                shop_id = str(
                    user.get("shop_id")
                )

                st.caption(
                    f"🏪 Shop: {shop_id[:8]}..."
                )

            if user.get("tenant_role"):

                st.caption(
                    f"🔑 "
                    f"{user.get('tenant_role_name', 'Staff')}"
                )

            if st.button("🚪 Logout"):

                logout()
