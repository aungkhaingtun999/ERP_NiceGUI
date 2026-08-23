import hashlib
import pandas as pd
import streamlit as st
from datetime import datetime, timezone

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
    show_notification,
)


# ==============================================================================
# PAGE
# ==============================================================================

def run():

    show_notification()
    require_admin()

    st.title("👥 User Management")
    st.caption("Control users, roles and access rights with Maker-Checker")

    supabase = privileged_db()

    current_user = get_current_user()
    current_shop_id = get_current_shop_id()
    is_owner = is_shop_owner()
    is_maker_user = is_maker()
    is_checker_user = is_checker()
    current_user_id = st.session_state.get("user_id")

    # ==========================================================================
    # HELPER FUNCTIONS
    # ==========================================================================

    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def safe_dict(value):
        """
        Convert None / unexpected values to a safe dictionary.
        Prevents:
            'NoneType' object has no attribute 'get'
        """
        return value if isinstance(value, dict) else {}

    def get_relation_id(value):
        """
        Extract ID from Supabase relationship result.

        Examples:
            {"id": 10, "username": "admin"} -> 10
            None -> None
            10 -> 10
        """
        if isinstance(value, dict):
            return value.get("id")
        return value

    def get_role_name(role_id):
        if role_id is None:
            return "Unknown"

        role = next(
            (
                r
                for r in roles
                if r.get("id") == role_id
            ),
            None,
        )

        return role.get("name", "Unknown") if role else "Unknown"

    def get_shop_name(shop_id):
        if shop_id is None:
            return "N/A"

        shop = next(
            (
                s
                for s in shops
                if s.get("id") == shop_id
            ),
            None,
        )

        return shop.get("name", "N/A") if shop else "N/A"

    def normalize_create_request(req):
        """
        Normalize Supabase relationship fields.

        requested_by can be:
            dict
            None

        Always convert it to a safe dict.
        """
        req = safe_dict(req)

        return {
            **req,
            "requested_by": safe_dict(
                req.get("requested_by")
            ),
        }

    def normalize_edit_request(req):
        """
        Normalize edit request relationship fields.
        """
        req = safe_dict(req)

        return {
            **req,
            "requested_by": safe_dict(
                req.get("requested_by")
            ),
            "user_id": safe_dict(
                req.get("user_id")
            ),
        }

    # ==========================================================================
    # ACTIVITY LOG
    # ==========================================================================

    def create_activity_log(user_id, action, description):
        try:
            supabase.table("user_activity_logs").insert({
                "user_id": user_id,
                "action": action,
                "description": description,
                "created_at": datetime.now().isoformat(),
            }).execute()
        except Exception:
            pass

    # ==========================================================================
    # OWNER HELPERS
    # ==========================================================================

    def validate_owner_change(current_tenant, new_tenant):
        """
        Owner -> Admin -> Other

        An Owner cannot directly change to staff/manager.
        """

        if (
            current_tenant == "owner"
            and new_tenant != "owner"
            and new_tenant != "admin"
        ):
            return (
                False,
                "⚠️ Owner must first be changed to **Admin**, then to other roles.",
            )

        return True, ""

    def is_last_owner(user_id):
        """
        Check if selected user is the last Owner.
        """

        owner_count = sum(
            1
            for u in users
            if safe_dict(u).get("tenant_role") == "owner"
        )

        if owner_count <= 1:

            user = next(
                (
                    u
                    for u in users
                    if safe_dict(u).get("id") == user_id
                ),
                None,
            )

            if (
                user
                and safe_dict(user).get("tenant_role") == "owner"
            ):
                return True

        return False

    def can_approve_request(requested_by_id):
        """
        Maker-Checker self approval protection.
        """

        if requested_by_id == current_user_id:

            owner_count = sum(
                1
                for u in users
                if safe_dict(u).get("tenant_role") == "owner"
            )

            current_is_only_owner = (
                owner_count == 1
                and len(users) > 0
                and safe_dict(users[0]).get("id") == current_user_id
            )

            if current_is_only_owner:
                return (
                    True,
                    "🔑 You are the only Owner. You can self-approve.",
                )

            return (
                False,
                "⛔ You cannot approve your own request. Ask another Owner.",
            )

        return True, ""

    # ==========================================================================
    # LOAD ROLES
    # ==========================================================================

    try:

        roles_resp = (
            supabase
            .table("roles")
            .select("id,name")
            .execute()
        )

        roles = roles_resp.data or []

        # Make sure every role is a dict
        roles = [
            safe_dict(role)
            for role in roles
            if isinstance(role, dict)
        ]

    except Exception as e:

        st.error(f"Role loading failed: {e}")
        return

    if not roles:

        st.warning(
            "Roles table is empty. Please create roles first."
        )
        return

    role_map = {
        r.get("name"): r.get("id")
        for r in roles
        if r.get("name") is not None
    }

    role_names = list(role_map.keys())

    if not role_names:

        st.error("No valid roles were found.")
        return
# ==========================================================================
# LOAD SHOPS
# MULTI-TENANT STRICT
#
# IMPORTANT:
# tenant Owner != Global/SaaS Owner
#
# A normal Owner can only see their own shop.
# ==========================================================================

try:

    # ----------------------------------------------------------------------
    # Current tenant shop is mandatory for normal tenant users
    # ----------------------------------------------------------------------

    if current_shop_id is not None:

        shops_resp = (
            supabase
            .table("shops")
            .select("id,name,code")
            .eq(
                "id",
                current_shop_id,
            )
            .execute()
        )

    else:

        shops_resp = type(
            "Response",
            (),
            {
                "data": []
            }
        )()

    shops = shops_resp.data or []

    shops = [
        safe_dict(shop)
        for shop in shops
        if isinstance(shop, dict)
    ]

except Exception as e:

    st.error(
        f"Shop loading failed: {e}"
    )

    shops = []

    # ==========================================================================
    # LOAD BRANCHES
    # ==========================================================================

    try:

        if is_owner:

            branches_resp = (
                supabase
                .table("branches")
                .select("id,name,shop_id")
                .execute()
            )

        else:

            branches_resp = (
                supabase
                .table("branches")
                .select("id,name,shop_id")
                .eq("shop_id", current_shop_id)
                .execute()
            )

        branches = branches_resp.data or []

        branches = [
            safe_dict(branch)
            for branch in branches
            if isinstance(branch, dict)
        ]

    except Exception:

        branches = []

    # ==========================================================================
    # LOAD USERS
    # STRICT MULTI-TENANT FILTER
    #
    # IMPORTANT:
    # - Owner is NOT automatically a global owner.
    # - Every tenant user is restricted to current_shop_id.
    # - shop003 Owner can only see shop003 users.
    # ==========================================================================

    try:

        query = (
            supabase
            .table("users")
            .select(
                """
                id,
                username,
                full_name,
                role_id,
                is_active,
                shop_id,
                branch_id,
                tenant_role,
                created_at,
                last_login
                """
            )
        )

        # ----------------------------------------------------------------------
        # STRICT TENANT FILTER
        #
        # Owner is also restricted to the current shop.
        # Example:
        #   akt -> shop003
        #   akt can only see shop003 users.
        # ----------------------------------------------------------------------

        if current_shop_id is None:

            st.error(
                "❌ Tenant shop context is missing. "
                "User list cannot be loaded."
            )

            users = []

        else:

            query = query.eq(
                "shop_id",
                current_shop_id,
            )

            # --------------------------------------------------------------
            # EXECUTE QUERY
            # --------------------------------------------------------------

            users_resp = query.execute()

            users = users_resp.data or []

            users = [
                safe_dict(user)
                for user in users
                if isinstance(user, dict)
            ]

    except Exception as e:

        st.error(
            f"User loading failed: {e}"
        )

        users = []

    # ==========================================================================
    # LOAD PENDING CREATE REQUESTS
    # ==========================================================================
    # ==========================================================================
    # LOAD PENDING EDIT REQUESTS
    # ==========================================================================

    pending_edit_requests = []

    if is_checker_user or is_owner:

        try:

            edit_req_resp = (
                supabase
                .table("user_edit_requests")
                .select(
                    """
                    *,
                    requested_by(id, username, full_name),
                    user_id(id, username, full_name)
                    """
                )
                .eq("status", "pending")
                .order(
                    "requested_at",
                    desc=True,
                )
                .execute()
            )

            raw_edit_requests = edit_req_resp.data or []

            pending_edit_requests = [
                normalize_edit_request(req)
                for req in raw_edit_requests
            ]

        except Exception:

            pending_edit_requests = []

    # ==========================================================================
    # STATISTICS
    # ==========================================================================

    total = len(users)

    active = sum(
        1
        for u in users
        if safe_dict(u).get("is_active")
    )

    inactive = total - active

    owners = sum(
        1
        for u in users
        if safe_dict(u).get("tenant_role") == "owner"
    )

    pending_total = (
        len(pending_create_requests)
        + len(pending_edit_requests)
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("👥 Users", total)
    c2.metric("🟢 Active", active)
    c3.metric("🔴 Inactive", inactive)
    c4.metric("👑 Owners", owners)
    c5.metric("⏳ Pending", pending_total)
    c6.metric("🛡 Roles", len(roles))

    st.divider()

    # ==========================================================================
    # TABS
    # ==========================================================================

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📋 Users",
            "➕ Create Request",
            "✏️ Edit Request",
            "✅ Approvals",
        ]
    )

    # ==========================================================================
    # TAB 1: USERS
    # ==========================================================================

    with tab1:

        search = st.text_input(
            "🔍 Search",
            placeholder="Search by username or full name...",
            label_visibility="collapsed",
            key="search_users",
        )

        if search:

            search_lower = search.lower()

            filtered = [
                u
                for u in users
                if (
                    search_lower
                    in str(
                        safe_dict(u).get("username", "")
                    ).lower()
                    or
                    search_lower
                    in str(
                        safe_dict(u).get("full_name", "")
                    ).lower()
                )
            ]

        else:

            filtered = users

        if not filtered:

            st.info("📭 No users found")

        else:

            rows = []

            for u in filtered:

                u = safe_dict(u)

                role_name = get_role_name(
                    u.get("role_id")
                )

                shop_name = get_shop_name(
                    u.get("shop_id")
                )

                rows.append(
                    {
                        "User": u.get("username", ""),
                        "Name": u.get("full_name", ""),
                        "Shop": shop_name,
                        "Tenant": u.get(
                            "tenant_role",
                            "staff",
                        ),
                        "Role": role_name,
                        "Status": (
                            "🟢"
                            if u.get("is_active")
                            else "🔴"
                        ),
                    }
                )

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                f"📊 {len(filtered)} users"
            )

        st.divider()

        # ----------------------------------------------------------------------
        # EDIT USER
        # ----------------------------------------------------------------------

        st.subheader("✏️ Edit User")

        if filtered:

            opts = {
                str(safe_dict(u).get("id")):
                f"{safe_dict(u).get('username', '')} - "
                f"{safe_dict(u).get('full_name', '')}"
                for u in filtered
                if safe_dict(u).get("id") is not None
            }

            if opts:

                selected_id = st.selectbox(
                    "Select User",
                    options=list(opts.keys()),
                    format_func=lambda x: opts[x],
                    key="edit_select_main",
                )

                if selected_id:

                    selected = next(
                        (
                            u
                            for u in filtered
                            if str(
                                safe_dict(u).get("id")
                            ) == selected_id
                        ),
                        None,
                    )

                    selected = safe_dict(selected)

                    if selected:

                        with st.container(border=True):

                            st.caption(
                                f"**User:** "
                                f"`{selected.get('username', '')}`"
                            )

                            st.caption(
                                f"**Current Role:** "
                                f"{get_role_name(selected.get('role_id'))}"
                            )

                            current_tenant = (
                                selected.get(
                                    "tenant_role"
                                )
                                or "staff"
                            )

                            is_owner_user = (
                                current_tenant == "owner"
                            )

                            last_owner = is_last_owner(
                                selected_id
                            )

                            if is_owner_user:

                                st.info(
                                    "🔑 **Owner → Admin → Other**: "
                                    "Owner must first be changed to "
                                    "**Admin**, then to other roles."
                                )

                            if last_owner:

                                st.error(
                                    "🚫 **This is the last Owner!** "
                                    "Cannot edit. Create another Owner first."
                                )

                            col1, col2, col3 = st.columns(3)

                            with col1:

                                new_name = st.text_input(
                                    "Full Name",
                                    value=selected.get(
                                        "full_name",
                                        "",
                                    ) or "",
                                    key="edit_name_main",
                                    disabled=last_owner,
                                )

                                current_role = get_role_name(
                                    selected.get("role_id")
                                )

                                if current_role not in role_names:
                                    current_role = role_names[0]

                                new_role = st.selectbox(
                                    "System Role",
                                    role_names,
                                    index=role_names.index(
                                        current_role
                                    ),
                                    key="edit_role_main",
                                    disabled=last_owner,
                                )

                            with col2:

                                tenant_opts = [
                                    "staff",
                                    "manager",
                                    "admin",
                                    "owner",
                                ]

                                current_tenant_idx = (
                                    tenant_opts.index(
                                        current_tenant
                                    )
                                    if current_tenant
                                    in tenant_opts
                                    else 0
                                )

                                new_tenant = st.selectbox(
                                    "Tenant Role",
                                    tenant_opts,
                                    index=current_tenant_idx,
                                    key="edit_tenant_main",
                                    disabled=last_owner,
                                )

                                new_active = st.toggle(
                                    "Active",
                                    value=bool(
                                        selected.get(
                                            "is_active",
                                            True,
                                        )
                                    ),
                                    key="edit_active_main",
                                    disabled=last_owner,
                                )

                            with col3:

                                st.write("**Actions**")

                                valid, msg = (
                                    validate_owner_change(
                                        current_tenant,
                                        new_tenant,
                                    )
                                )

                                if (
                                    not valid
                                    and not last_owner
                                ):
                                    st.warning(msg)

                                has_changes = (
                                    new_name
                                    != selected.get(
                                        "full_name"
                                    )
                                    or
                                    new_role
                                    != current_role
                                    or
                                    new_tenant
                                    != current_tenant
                                    or
                                    new_active
                                    != selected.get(
                                        "is_active",
                                        True,
                                    )
                                )

                                col_a, col_b, col_c = (
                                    st.columns(3)
                                )

                                # ------------------------------------------------
                                # MAKER-CHECKER ONLY
                                # ------------------------------------------------

                                with col_a:

                                    if last_owner:

                                        st.info(
                                            "🔒 Last Owner cannot be edited"
                                        )

                                    elif is_maker_user or is_owner:

                                        st.info(
                                            "🔐 Edit must go through Maker-Checker approval."
                                        )

                                    else:

                                        st.info(
                                            "🔧 Only Maker can submit edit request."
                                        )

                                # ------------------------------------------------
                                # SUBMIT EDIT REQUEST
                                # ------------------------------------------------

                                with col_b:

                                    if (
                                        (
                                            is_maker_user
                                            or is_owner
                                        )
                                        and not last_owner
                                    ):

                                        if st.button(
                                            "📤 Submit Request",
                                            use_container_width=True,
                                            key="submit_edit_main",
                                        ):

                                            if not valid:

                                                notify_error(msg)

                                            elif not has_changes:

                                                notify_warning(
                                                    "No changes to submit"
                                                )

                                            else:

                                                existing = (
                                                    supabase
                                                    .table(
                                                        "user_edit_requests"
                                                    )
                                                    .select("id")
                                                    .eq(
                                                        "user_id",
                                                        selected_id,
                                                    )
                                                    .eq(
                                                        "status",
                                                        "pending",
                                                    )
                                                    .execute()
                                                )

                                                if existing.data:

                                                    notify_warning(
                                                        "⚠️ Pending request "
                                                        "already exists"
                                                    )

                                                else:

                                                    (
                                                        supabase
                                                        .table(
                                                            "user_edit_requests"
                                                        )
                                                        .insert(
                                                            {
                                                                "requested_by": current_user_id,
                                                                "user_id": selected_id,
                                                                "new_full_name": new_name,
                                                                "new_role_id": role_map[
                                                                    new_role
                                                                ],
                                                                "new_tenant_role": new_tenant,
                                                                "new_is_active": new_active,
                                                                "old_full_name": selected.get(
                                                                    "full_name"
                                                                ),
                                                                "old_role_id": selected.get(
                                                                    "role_id"
                                                                ),
                                                                "old_tenant_role": current_tenant,
                                                                "old_is_active": selected.get(
                                                                    "is_active",
                                                                    True,
                                                                ),
                                                                "status": "pending",
                                                                "requested_at": datetime.now().isoformat(),
                                                            }
                                                        )
                                                        .execute()
                                                    )

                                                    create_activity_log(
                                                        current_user_id,
                                                        "EDIT_USER_REQUEST",
                                                        f"Requested to edit user "
                                                        f"'{selected.get('username', '')}'",
                                                    )

                                                    notify_success(
                                                        f"✅ Edit request for "
                                                        f"'{selected.get('username', '')}' "
                                                        f"submitted"
                                                    )

                                                    st.rerun()

                                    else:

                                        if last_owner:

                                            st.info(
                                                "🔒 Last Owner cannot be edited"
                                            )

                                        else:

                                            st.info(
                                                "🔧 Only Maker can submit request"
                                            )

                                # ------------------------------------------------
                                # RESET PASSWORD
                                # ------------------------------------------------

                                with col_c:

                                    if (
                                        selected.get("username")
                                        != "admin"
                                    ):

                                        with st.popover(
                                            "🔐 Reset"
                                        ):

                                            new_pass = st.text_input(
                                                "New Password",
                                                type="password",
                                                placeholder="Min 6 chars",
                                                key="reset_pass_main",
                                            )

                                            if st.button(
                                                "Save",
                                                use_container_width=True,
                                                key="reset_save_main",
                                            ):

                                                if (
                                                    new_pass
                                                    and len(new_pass)
                                                    >= 6
                                                ):

                                                    (
                                                        supabase
                                                        .table("users")
                                                        .update(
                                                            {
                                                                "password_hash": hash_password(
                                                                    new_pass
                                                                )
                                                            }
                                                        )
                                                        .eq(
                                                            "id",
                                                            selected_id,
                                                        )
                                                        .execute()
                                                    )

                                                    notify_success(
                                                        "✅ Password reset"
                                                    )

                                                    st.rerun()

                                                else:

                                                    notify_error(
                                                        "❌ Min 6 chars"
                                                    )

                                    else:

                                        st.info("🔒")

        else:

            st.info("No users")

    # ==========================================================================
    # TAB 2: CREATE USER REQUEST
    # ==========================================================================

    with tab2:

        if not is_maker_user and not is_owner:

            st.warning(
                "⚠️ Only Admin (Maker) can create user requests."
            )

        else:

            st.subheader(
                "📝 Create New User Request"
            )

            st.caption(
                "Submit for approval. Owner (Checker) must approve."
            )

            with st.form(
                "create_form",
                clear_on_submit=True,
            ):

                col1, col2 = st.columns(2)

                with col1:

                    username = st.text_input(
                        "Username *",
                        placeholder="Min 3 chars",
                        key="create_username",
                    )

                    full_name = st.text_input(
                        "Full Name *",
                        key="create_fullname",
                    )

                    password = st.text_input(
                        "Password *",
                        type="password",
                        placeholder="Min 6 chars",
                        key="create_password",
                    )

                with col2:

                    if (
                        len(shops) > 1
                        and is_owner
                    ):

                        selected_shop = st.selectbox(
                            "Shop",
                            shop_names,
                            key="create_shop",
                        )

                        selected_shop_id = (
                            shop_map.get(
                                selected_shop
                            )
                        )

                    else:

                        selected_shop_id = (
                            shops[0].get("id")
                            if shops
                            else None
                        )

                    tenant_role = st.selectbox(
                        "Tenant Role",
                        [
                            "staff",
                            "manager",
                            "admin",
                            "owner",
                        ],
                        key="create_tenant",
                    )

                    selected_role = st.selectbox(
                        "System Role",
                        role_names,
                        key="create_role",
                    )

                    active = st.checkbox(
                        "Active",
                        value=True,
                        key="create_active",
                    )

                if st.form_submit_button(
                    "📤 Submit Request",
                    use_container_width=True,
                    type="primary",
                ):

                    if (
                        not username
                        or not password
                        or not full_name
                    ):

                        notify_error(
                            "❌ All fields required"
                        )

                    elif len(username) < 3:

                        notify_error(
                            "❌ Username min 3 chars"
                        )

                    elif len(password) < 6:

                        notify_error(
                            "❌ Password min 6 chars"
                        )

                    elif not selected_shop_id:

                        notify_error(
                            "❌ No Shop available for this user"
                        )

                    else:

                        existing = (
                            supabase
                            .table("users")
                            .select("id")
                            .eq(
                                "username",
                                username,
                            )
                            .execute()
                        )

                        if existing.data:

                            notify_error(
                                f"❌ Username "
                                f"'{username}' exists"
                            )

                        else:

                            (
                                supabase
                                .table(
                                    "user_create_requests"
                                )
                                .insert(
                                    {
                                        "requested_by": current_user_id,
                                        "username": username,
                                        "full_name": full_name,
                                        "password_hash": hash_password(
                                            password
                                        ),
                                        "role_id": role_map[
                                            selected_role
                                        ],
                                        "shop_id": selected_shop_id,
                                        "branch_id": None,
                                        "tenant_role": tenant_role,
                                        "is_active": active,
                                        "status": "pending",
                                        "requested_at": datetime.now().isoformat(),
                                    }
                                )
                                .execute()
                            )

                            notify_success(
                                f"✅ Request for "
                                f"'{username}' submitted"
                            )

                            st.rerun()

    # ==========================================================================
    # TAB 3: EDIT REQUEST
    # ==========================================================================

    with tab3:

        if not is_maker_user and not is_owner:

            st.warning(
                "⚠️ Only Admin (Maker) can edit users."
            )

        else:

            st.subheader(
                "✏️ Edit User Request"
            )

            st.caption(
                "Select a user and submit edit request for approval"
            )

            if not filtered:

                st.info(
                    "No users available"
                )

            else:

                opts = {
                    str(safe_dict(u).get("id")):
                    f"{safe_dict(u).get('username', '')} - "
                    f"{safe_dict(u).get('full_name', '')}"
                    for u in filtered
                    if safe_dict(u).get("id") is not None
                }

                if opts:

                    selected_id = st.selectbox(
                        "Select User",
                        options=list(opts.keys()),
                        format_func=lambda x: opts[x],
                        key="edit_tab_select",
                    )

                    if selected_id:

                        selected = next(
                            (
                                u
                                for u in filtered
                                if str(
                                    safe_dict(u).get("id")
                                ) == selected_id
                            ),
                            None,
                        )

                        selected = safe_dict(selected)

                        if selected:

                            pending_edit = (
                                supabase
                                .table(
                                    "user_edit_requests"
                                )
                                .select("id")
                                .eq(
                                    "user_id",
                                    selected_id,
                                )
                                .eq(
                                    "status",
                                    "pending",
                                )
                                .execute()
                            )

                            pending_edit_data = (
                                pending_edit.data or []
                            )

                            if pending_edit_data:

                                st.warning(
                                    "⚠️ This user already has "
                                    "a pending edit request"
                                )

                            current_tenant = (
                                selected.get(
                                    "tenant_role"
                                )
                                or "staff"
                            )

                            is_owner_user = (
                                current_tenant == "owner"
                            )

                            last_owner = is_last_owner(
                                selected_id
                            )

                            if is_owner_user:

                                st.info(
                                    "🔑 **Owner → Admin → Other**: "
                                    "Owner must first be changed to "
                                    "**Admin**, then to other roles."
                                )

                            if last_owner:

                                st.error(
                                    "🚫 **This is the last Owner!** "
                                    "Cannot submit edit request. "
                                    "Create another Owner first."
                                )

                            with st.container(
                                border=True
                            ):

                                col1, col2 = (
                                    st.columns(2)
                                )

                                with col1:

                                    st.caption(
                                        f"**Current User:** "
                                        f"`{selected.get('username', '')}`"
                                    )

                                    current_role = get_role_name(
                                        selected.get("role_id")
                                    )

                                    if current_role not in role_names:
                                        current_role = role_names[0]

                                    new_name = st.text_input(
                                        "New Full Name",
                                        value=selected.get(
                                            "full_name",
                                            "",
                                        ) or "",
                                        key="edit_tab_name",
                                        disabled=last_owner,
                                    )

                                    new_role = st.selectbox(
                                        "New System Role",
                                        role_names,
                                        index=role_names.index(
                                            current_role
                                        ),
                                        key="edit_tab_role",
                                        disabled=last_owner,
                                    )

                                with col2:

                                    tenant_opts = [
                                        "staff",
                                        "manager",
                                        "admin",
                                        "owner",
                                    ]

                                    current_tenant_idx = (
                                        tenant_opts.index(
                                            current_tenant
                                        )
                                        if current_tenant
                                        in tenant_opts
                                        else 0
                                    )

                                    new_tenant = st.selectbox(
                                        "New Tenant Role",
                                        tenant_opts,
                                        index=current_tenant_idx,
                                        key="edit_tab_tenant",
                                        disabled=last_owner,
                                    )

                                    new_active = st.toggle(
                                        "New Status",
                                        value=bool(
                                            selected.get(
                                                "is_active",
                                                True,
                                            )
                                        ),
                                        key="edit_tab_active",
                                        disabled=last_owner,
                                    )

                                valid, msg = (
                                    validate_owner_change(
                                        current_tenant,
                                        new_tenant,
                                    )
                                )

                                if (
                                    not valid
                                    and not last_owner
                                ):

                                    st.warning(msg)

                                if (
                                    not pending_edit_data
                                    and valid
                                    and not last_owner
                                ):

                                    if st.button(
                                        "📤 Submit Edit Request",
                                        use_container_width=True,
                                        type="primary",
                                        key="submit_edit_tab",
                                    ):

                                        (
                                            supabase
                                            .table(
                                                "user_edit_requests"
                                            )
                                            .insert(
                                                {
                                                    "requested_by": current_user_id,
                                                    "user_id": selected_id,
                                                    "new_full_name": new_name,
                                                    "new_role_id": role_map[
                                                        new_role
                                                    ],
                                                    "new_tenant_role": new_tenant,
                                                    "new_is_active": new_active,
                                                    "old_full_name": selected.get(
                                                        "full_name"
                                                    ),
                                                    "old_role_id": selected.get(
                                                        "role_id"
                                                    ),
                                                    "old_tenant_role": current_tenant,
                                                    "old_is_active": selected.get(
                                                        "is_active",
                                                        True,
                                                    ),
                                                    "status": "pending",
                                                    "requested_at": datetime.now().isoformat(),
                                                }
                                            )
                                            .execute()
                                        )

                                        notify_success(
                                            f"✅ Edit request for "
                                            f"'{selected.get('username', '')}' "
                                            f"submitted"
                                        )

                                        st.rerun()

                                elif pending_edit_data:

                                    notify_warning(
                                        "⚠️ Pending request already exists"
                                    )

                                elif last_owner:

                                    notify_warning(
                                        "⚠️ Cannot submit request "
                                        "for last Owner"
                                    )
    
        # ==========================================================================
    # TAB 4: APPROVALS
    # ==========================================================================

    with tab4:

        # ----------------------------------------------------------------------
        # CHECKER ACCESS
        # ----------------------------------------------------------------------

        if not is_checker_user and not is_owner:

            st.warning(
                "⚠️ Only Owner (Checker) can approve/reject requests."
            )

        else:

            # ==================================================================
            # CREATE REQUESTS
            # ==================================================================

            st.subheader(
                f"📝 Create Requests "
                f"({len(pending_create_requests)})"
            )

            if not pending_create_requests:

                st.info(
                    "No pending create requests"
                )

            else:

                for idx, req in enumerate(
                    pending_create_requests
                ):

                    req = safe_dict(req)

                    requested_by = safe_dict(
                        req.get("requested_by")
                    )

                    requester_id = (
                        requested_by.get("id")
                    )

                    request_id = req.get("id")

                    username = (
                        str(
                            req.get("username") or ""
                        ).strip()
                    )

                    with st.container(
                        border=True
                    ):

                        col1, col2, col3 = (
                            st.columns(
                                [3, 1, 1]
                            )
                        )

                        # ------------------------------------------------------
                        # REQUEST DETAILS
                        # ------------------------------------------------------

                        with col1:

                            st.write(
                                f"**Create: "
                                f"{username or 'Unknown'}** "
                                f"- "
                                f"{req.get('full_name', '')}"
                            )

                            st.caption(
                                f"Role: "
                                f"{get_role_name(req.get('role_id'))} "
                                f"| Tenant: "
                                f"{req.get('tenant_role', 'staff')}"
                            )

                            st.caption(
                                f"Shop: "
                                f"{get_shop_name(req.get('shop_id'))}"
                            )

                            if requested_by:

                                st.caption(
                                    f"By: "
                                    f"{requested_by.get('full_name', 'Unknown')}"
                                )

                            else:

                                st.caption(
                                    "By: Unknown requester"
                                )

                        # ------------------------------------------------------
                        # APPROVE CREATE
                        # ------------------------------------------------------

                        with col2:

                            can_approve, msg = (
                                can_approve_request(
                                    requester_id
                                )
                            )

                            if can_approve:

                                if st.button(
                                    "✅ Approve",
                                    key=(
                                        f"app_c_"
                                        f"{request_id}_{idx}"
                                    ),
                                    use_container_width=True,
                                    type="primary",
                                ):

                                    # ==================================================
                                    # 1. BASIC VALIDATION
                                    # ==================================================

                                    if not username:

                                        notify_error(
                                            "❌ Username is empty."
                                        )

                                        st.stop()

                                    # ==================================================
                                    # 2. TENANT VALIDATION
                                    # ==================================================

                                    request_shop_id = (
                                        req.get("shop_id")
                                    )

                                    if (
                                        not is_owner
                                        and current_shop_id
                                        and request_shop_id
                                        != current_shop_id
                                    ):

                                        notify_error(
                                            "⛔ This request belongs to another Shop."
                                        )

                                        st.stop()

                                    # ==================================================
                                    # 3. DUPLICATE USERNAME CHECK
                                    # ==================================================

                                    existing_user_resp = (
                                        supabase
                                        .table("users")
                                        .select(
                                            "id,username"
                                        )
                                        .eq(
                                            "username",
                                            username,
                                        )
                                        .limit(1)
                                        .execute()
                                    )

                                    existing_users = (
                                        existing_user_resp.data
                                        or []
                                    )

                                    if existing_users:

                                        existing_user = (
                                            safe_dict(
                                                existing_users[0]
                                            )
                                        )

                                        existing_username = (
                                            existing_user.get(
                                                "username"
                                            )
                                            or username
                                        )

                                        notify_error(
                                            f"❌ Username "
                                            f"'{existing_username}' "
                                            f"already exists. "
                                            f"Request cannot be approved."
                                        )

                                        (
                                            supabase
                                            .table(
                                                "user_create_requests"
                                            )
                                            .update(
                                                {
                                                    "status": "rejected",
                                                    "checked_by": current_user_id,
                                                    "checked_at": datetime.now(
                                                        timezone.utc
                                                    ).isoformat(),
                                                    "rejection_reason": (
                                                        "Username already exists "
                                                        "in users table."
                                                    ),
                                                }
                                            )
                                            .eq(
                                                "id",
                                                request_id,
                                            )
                                            .eq(
                                                "status",
                                                "pending",
                                            )
                                            .execute()
                                        )

                                        create_activity_log(
                                            current_user_id,
                                            "REJECT_CREATE_DUPLICATE",
                                            (
                                                f"Create request for "
                                                f"'{username}' rejected "
                                                f"because username already exists."
                                            ),
                                        )

                                        st.rerun()

                                    # ==================================================
                                    # 4. INSERT NEW USER
                                    # ==================================================

                                    try:

                                        (
                                            supabase
                                            .table("users")
                                            .insert(
                                                {
                                                    "username": username,
                                                    "full_name": req.get(
                                                        "full_name"
                                                    ),
                                                    "password_hash": req.get(
                                                        "password_hash"
                                                    ),
                                                    "role_id": req.get(
                                                        "role_id"
                                                    ),
                                                    "shop_id": req.get(
                                                        "shop_id"
                                                    ),
                                                    "branch_id": req.get(
                                                        "branch_id"
                                                    ),
                                                    "tenant_role": req.get(
                                                        "tenant_role",
                                                        "staff",
                                                    ),
                                                    "is_active": req.get(
                                                        "is_active",
                                                        True,
                                                    ),
                                                    "failed_attempts": 0,
                                                    "locked_until": None,
                                                }
                                            )
                                            .execute()
                                        )

                                    except Exception as e:

                                        error_text = str(e)

                                        # ------------------------------------------
                                        # DUPLICATE RACE CONDITION
                                        # ------------------------------------------

                                        if (
                                            "23505"
                                            in error_text
                                            or
                                            "users_username_key"
                                            in error_text
                                        ):

                                            (
                                                supabase
                                                .table(
                                                    "user_create_requests"
                                                )
                                                .update(
                                                    {
                                                        "status": "rejected",
                                                        "checked_by": current_user_id,
                                                        "checked_at": datetime.now(
                                                            timezone.utc
                                                        ).isoformat(),
                                                        "rejection_reason": (
                                                            "Username already "
                                                            "exists in users table."
                                                        ),
                                                    }
                                                )
                                                .eq(
                                                    "id",
                                                    request_id,
                                                )
                                                .eq(
                                                    "status",
                                                    "pending",
                                                )
                                                .execute()
                                            )

                                            create_activity_log(
                                                current_user_id,
                                                "REJECT_CREATE_DUPLICATE",
                                                (
                                                    f"Create request for "
                                                    f"'{username}' rejected "
                                                    f"because username already exists."
                                                ),
                                            )

                                            notify_error(
                                                f"❌ Username "
                                                f"'{username}' already exists."
                                            )

                                            st.rerun()

                                        else:

                                            notify_error(
                                                f"❌ User creation failed: "
                                                f"{error_text}"
                                            )

                                            st.stop()

                                    # ==================================================
                                    # 5. MARK REQUEST APPROVED
                                    # ==================================================

                                    try:

                                        (
                                            supabase
                                            .table(
                                                "user_create_requests"
                                            )
                                            .update(
                                                {
                                                    "status": "approved",
                                                    "checked_by": current_user_id,
                                                    "checked_at": datetime.now(
                                                        timezone.utc
                                                    ).isoformat(),
                                                }
                                            )
                                            .eq(
                                                "id",
                                                request_id,
                                            )
                                            .eq(
                                                "status",
                                                "pending",
                                            )
                                            .execute()
                                        )

                                    except Exception as e:

                                        notify_error(
                                            f"⚠️ User was created, "
                                            f"but request status update failed: "
                                            f"{e}"
                                        )

                                        st.stop()

                                    # ==================================================
                                    # 6. ACTIVITY LOG
                                    # ==================================================

                                    create_activity_log(
                                        current_user_id,
                                        "APPROVE_CREATE_USER",
                                        (
                                            f"Approved and created user "
                                            f"'{username}'"
                                        ),
                                    )

                                    # ==================================================
                                    # 7. SUCCESS
                                    # ==================================================

                                    notify_success(
                                        f"✅ "
                                        f"{username} "
                                        f"created successfully."
                                    )

                                    st.rerun()

                            else:

                                st.warning(
                                    msg
                                )

                        # ------------------------------------------------------
                        # REJECT CREATE
                        # ------------------------------------------------------

                        with col3:

                            with st.popover(
                                "❌ Reject"
                            ):

                                reason = st.text_input(
                                    "Reason",
                                    key=(
                                        f"rej_c_"
                                        f"{request_id}_"
                                        f"{idx}"
                                    ),
                                )

                                if st.button(
                                    "Confirm",
                                    key=(
                                        f"rej_c_confirm_"
                                        f"{request_id}_"
                                        f"{idx}"
                                    ),
                                    use_container_width=True,
                                ):

                                    (
                                        supabase
                                        .table(
                                            "user_create_requests"
                                        )
                                        .update(
                                            {
                                                "status": "rejected",
                                                "checked_by": current_user_id,
                                                "checked_at": datetime.now(
                                                    timezone.utc
                                                ).isoformat(),
                                                "rejection_reason": (
                                                    reason
                                                    or "No reason"
                                                ),
                                            }
                                        )
                                        .eq(
                                            "id",
                                            request_id,
                                        )
                                        .eq(
                                            "status",
                                            "pending",
                                        )
                                        .execute()
                                    )

                                    create_activity_log(
                                        current_user_id,
                                        "REJECT_CREATE_USER",
                                        (
                                            f"Rejected create request "
                                            f"for '{username}'. "
                                            f"Reason: "
                                            f"{reason or 'No reason'}"
                                        ),
                                    )

                                    notify_warning(
                                        f"❌ "
                                        f"{username} "
                                        f"rejected"
                                    )

                                    st.rerun()

            # ==================================================================
            # EDIT REQUESTS
            # ==================================================================

            st.divider()

            st.subheader(
                f"✏️ Edit Requests "
                f"({len(pending_edit_requests)})"
            )

            if not pending_edit_requests:

                st.info(
                    "No pending edit requests"
                )

            else:

                for idx, req in enumerate(
                    pending_edit_requests
                ):

                    req = safe_dict(req)

                    requested_by = safe_dict(
                        req.get("requested_by")
                    )

                    target_user = safe_dict(
                        req.get("user_id")
                    )

                    requester_id = (
                        requested_by.get("id")
                    )

                    target_id = (
                        target_user.get("id")
                    )

                    request_id = (
                        req.get("id")
                        or f"unknown_{idx}"
                    )

                    # ----------------------------------------------------------
                    # EXTRA TENANT SAFETY
                    # ----------------------------------------------------------

                    target_shop_id = (
                        target_user.get("shop_id")
                    )

                    if (
                        not is_owner
                        and current_shop_id
                        and target_shop_id
                        != current_shop_id
                    ):

                        continue

                    with st.container(
                        border=True
                    ):

                        col1, col2, col3 = (
                            st.columns(
                                [3, 1, 1]
                            )
                        )

                        # ------------------------------------------------------
                        # REQUEST DETAILS
                        # ------------------------------------------------------

                        with col1:

                            st.write(
                                f"**Edit: "
                                f"{target_user.get('username', 'Unknown')}**"
                            )

                            st.caption(
                                f"Current: "
                                f"{req.get('old_full_name', '')} "
                                f"→ New: "
                                f"{req.get('new_full_name', '')}"
                            )

                            st.caption(
                                f"Role: "
                                f"{get_role_name(req.get('old_role_id'))} "
                                f"→ "
                                f"{get_role_name(req.get('new_role_id'))}"
                            )

                            st.caption(
                                f"Tenant: "
                                f"{req.get('old_tenant_role', 'staff')} "
                                f"→ "
                                f"{req.get('new_tenant_role', 'staff')}"
                            )

                            st.caption(
                                f"Status: "
                                f"{'🟢' if req.get('old_is_active') else '🔴'} "
                                f"→ "
                                f"{'🟢' if req.get('new_is_active') else '🔴'}"
                            )

                            st.caption(
                                f"Shop: "
                                f"{get_shop_name(target_shop_id)}"
                            )

                            if requested_by:

                                st.caption(
                                    f"By: "
                                    f"{requested_by.get('full_name', 'Unknown')}"
                                )

                            else:

                                st.caption(
                                    "By: Unknown requester"
                                )

                        # ------------------------------------------------------
                        # APPROVE EDIT
                        # ------------------------------------------------------

                        with col2:

                            target_user_data = next(
                                (
                                    u
                                    for u in users
                                    if safe_dict(u).get("id")
                                    == target_id
                                ),
                                None,
                            )

                            if target_user_data:

                                target_user_data = safe_dict(
                                    target_user_data
                                )

                                is_owner_target = (
                                    target_user_data.get(
                                        "tenant_role"
                                    )
                                    == "owner"
                                )

                                owner_count = sum(
                                    1
                                    for u in users
                                    if safe_dict(u).get(
                                        "tenant_role"
                                    )
                                    == "owner"
                                )

                                is_last_owner_target = (
                                    is_owner_target
                                    and owner_count <= 1
                                )

                                # ----------------------------------------------
                                # LAST OWNER PROTECTION
                                # ----------------------------------------------

                                if (
                                    is_last_owner_target
                                    and req.get(
                                        "new_tenant_role"
                                    )
                                    != "owner"
                                ):

                                    st.warning(
                                        "🚫 **Cannot change last Owner!** "
                                        "Create another Owner first."
                                    )

                                    st.info(
                                        "ℹ️ This request cannot be "
                                        "approved until another Owner "
                                        "is created."
                                    )

                                else:

                                    can_approve, msg = (
                                        can_approve_request(
                                            requester_id
                                        )
                                    )

                                    if can_approve:

                                        if st.button(
                                            "✅ Approve",
                                            key=(
                                                f"tab4_edit_approve_"
                                                f"{request_id}_"
                                                f"{target_id}_"
                                                f"{idx}"
                                            ),
                                            use_container_width=True,
                                            type="primary",
                                        ):

                                            # ----------------------------------
                                            # FINAL TENANT SAFETY CHECK
                                            # ----------------------------------

                                            if (
                                                not is_owner
                                                and current_shop_id
                                                and target_shop_id
                                                != current_shop_id
                                            ):

                                                notify_error(
                                                    "⛔ You cannot approve "
                                                    "a request from another Shop."
                                                )

                                                st.stop()

                                            update_data = {}

                                            if req.get(
                                                "new_full_name"
                                            ) is not None:

                                                update_data[
                                                    "full_name"
                                                ] = req.get(
                                                    "new_full_name"
                                                )

                                            if req.get(
                                                "new_role_id"
                                            ) is not None:

                                                update_data[
                                                    "role_id"
                                                ] = req.get(
                                                    "new_role_id"
                                                )

                                            if req.get(
                                                "new_tenant_role"
                                            ) is not None:

                                                update_data[
                                                    "tenant_role"
                                                ] = req.get(
                                                    "new_tenant_role"
                                                )

                                            if req.get(
                                                "new_is_active"
                                            ) is not None:

                                                update_data[
                                                    "is_active"
                                                ] = req.get(
                                                    "new_is_active"
                                                )

                                            # ----------------------------------
                                            # APPLY USER UPDATE
                                            # ----------------------------------

                                            if update_data:

                                                try:

                                                    (
                                                        supabase
                                                        .table("users")
                                                        .update(
                                                            update_data
                                                        )
                                                        .eq(
                                                            "id",
                                                            target_id,
                                                        )
                                                        .eq(
                                                            "shop_id",
                                                            current_shop_id
                                                            if not is_owner
                                                            else target_shop_id,
                                                        )
                                                        .execute()
                                                    )

                                                except Exception as e:

                                                    notify_error(
                                                        f"❌ User update failed: "
                                                        f"{e}"
                                                    )

                                                    st.stop()

                                            # ----------------------------------
                                            # MARK REQUEST APPROVED
                                            # ----------------------------------

                                            try:

                                                (
                                                    supabase
                                                    .table(
                                                        "user_edit_requests"
                                                    )
                                                    .update(
                                                        {
                                                            "status": "approved",
                                                            "checked_by": current_user_id,
                                                            "checked_at": datetime.now(
                                                                timezone.utc
                                                            ).isoformat(),
                                                        }
                                                    )
                                                    .eq(
                                                        "id",
                                                        request_id,
                                                    )
                                                    .eq(
                                                        "status",
                                                        "pending",
                                                    )
                                                    .execute()
                                                )

                                            except Exception as e:

                                                notify_error(
                                                    f"⚠️ User updated, "
                                                    f"but request status "
                                                    f"update failed: {e}"
                                                )

                                                st.stop()

                                            create_activity_log(
                                                current_user_id,
                                                "APPROVE_EDIT_USER",
                                                (
                                                    f"Approved edit request "
                                                    f"for user "
                                                    f"'{target_user.get('username', 'User')}'"
                                                ),
                                            )

                                            notify_success(
                                                f"✅ "
                                                f"{target_user.get('username', 'User')} "
                                                f"updated"
                                            )

                                            st.rerun()

                                    else:

                                        st.warning(
                                            msg
                                        )

                            else:

                                st.warning(
                                    "⚠️ Target user record "
                                    "could not be found."
                                )

                                st.caption(
                                    "This request cannot be safely approved "
                                    "until the target user exists."
                                )

                        # ------------------------------------------------------
                        # REJECT EDIT
                        # ------------------------------------------------------

                        with col3:

                            with st.popover(
                                "❌ Reject"
                            ):

                                reason = st.text_input(
                                    "Reason",
                                    key=(
                                        f"tab4_edit_reject_reason_"
                                        f"{request_id}_"
                                        f"{target_id}_"
                                        f"{idx}"
                                    ),
                                )

                                if st.button(
                                    "Confirm",
                                    key=(
                                        f"tab4_edit_reject_confirm_"
                                        f"{request_id}_"
                                        f"{target_id}_"
                                        f"{idx}"
                                    ),
                                    use_container_width=True,
                                ):

                                    # ------------------------------------------
                                    # FINAL TENANT SAFETY CHECK
                                    # ------------------------------------------

                                    if (
                                        not is_owner
                                        and current_shop_id
                                        and target_shop_id
                                        != current_shop_id
                                    ):

                                        notify_error(
                                            "⛔ You cannot reject "
                                            "a request from another Shop."
                                        )

                                        st.stop()

                                    (
                                        supabase
                                        .table(
                                            "user_edit_requests"
                                        )
                                        .update(
                                            {
                                                "status": "rejected",
                                                "checked_by": current_user_id,
                                                "checked_at": datetime.now(
                                                    timezone.utc
                                                ).isoformat(),
                                                "rejection_reason": (
                                                    reason
                                                    or "No reason"
                                                ),
                                            }
                                        )
                                        .eq(
                                            "id",
                                            request_id,
                                        )
                                        .eq(
                                            "status",
                                            "pending",
                                        )
                                        .execute()
                                    )

                                    create_activity_log(
                                        current_user_id,
                                        "REJECT_EDIT_USER",
                                        (
                                            f"Rejected edit request "
                                            f"for user "
                                            f"'{target_user.get('username', 'User')}'. "
                                            f"Reason: "
                                            f"{reason or 'No reason'}"
                                        ),
                                    )

                                    notify_warning(
                                        "❌ Edit request rejected"
                                    )

                                    st.rerun()


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
