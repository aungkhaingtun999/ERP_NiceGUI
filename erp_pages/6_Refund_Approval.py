import streamlit as st

from database import db
from auth import require_login
from utils.ui import show_table


# ==============================================================================
# ALLOWED ROLES
# ==============================================================================

# Admin    = role_id 1
# Manager  = role_id 2
#
# Both are allowed to access Refund Approval Center.

ALLOWED_ROLE_IDS = {
    1,  # Admin
    2,  # Manager
}


# ==============================================================================
# ACTION FUNCTIONS
# ==============================================================================

def handle_approval(
    refund_id,
    approver_id,
):

    try:

        result = db().rpc(
            "approve_refund_rpc",
            {
                "p_refund_id": refund_id,
                "p_manager_id": approver_id,
            },
        ).execute()

        # ----------------------------------------------------------------------
        # RPC response
        # ----------------------------------------------------------------------

        if (
            isinstance(result.data, dict)
            and result.data.get("success")
        ):

            st.success(
                f"Refund ID {refund_id} successfully approved."
            )

            st.rerun()

        else:

            st.error(
                f"Approval failed: {result.data}"
            )

    except Exception as e:

        st.error(
            f"Approval error: {e}"
        )


# ==============================================================================
# REJECTION
# ==============================================================================

def handle_rejection(
    refund_id,
    approver_id,
    reason,
):

    try:

        result = db().rpc(
            "reject_refund_rpc",
            {
                "p_refund_id": refund_id,
                "p_manager_id": approver_id,
                "p_reason": reason,
            },
        ).execute()

        if (
            isinstance(result.data, dict)
            and result.data.get("success")
        ):

            st.success(
                f"Refund ID {refund_id} rejected."
            )

            st.rerun()

        else:

            st.error(
                f"Rejection failed: {result.data}"
            )

    except Exception as e:

        st.error(
            f"Rejection error: {e}"
        )


# ==============================================================================
# MAIN RUN FUNCTION
# ==============================================================================

def run():

    st.set_page_config(
        page_title="Refund Approval",
        layout="wide",
    )

    # ==========================================================================
    # AUTHENTICATION
    # ==========================================================================

    user = require_login()

    if not user:

        st.error(
            "Authentication required."
        )

        st.stop()

    # ==========================================================================
    # ROLE
    # ==========================================================================

    role_id = user.get(
        "role_id"
    )

    try:

        role_id = int(role_id)

    except (
        TypeError,
        ValueError,
    ):

        role_id = None

    # ==========================================================================
    # ADMIN + MANAGER ACCESS
    # ==========================================================================

    if role_id not in ALLOWED_ROLE_IDS:

        st.error(
            "⛔ Access Denied. "
            "Admin or Manager permission required."
        )

        st.stop()

    # ==========================================================================
    # PAGE
    # ==========================================================================

    st.title(
        "✅ Refund Approval Center"
    )

    # --------------------------------------------------------------------------
    # Display current approver role
    # --------------------------------------------------------------------------

    if role_id == 1:

        role_name = "Admin"

    else:

        role_name = "Manager"

    st.caption(
        f"Authorized Approver: {role_name}"
    )

    # ==========================================================================
    # LOAD PENDING REFUNDS
    # ==========================================================================

    try:

        refunds = (
            db()
            .table("refunds")
            .select("*")
            .eq(
                "status",
                "PENDING",
            )
            .order(
                "id",
                desc=True,
            )
            .execute()
        )

        data = (
            refunds.data
            or []
        )

    except Exception as e:

        st.error(
            f"Error loading data: {e}"
        )

        st.stop()

    # ==========================================================================
    # DISPLAY
    # ==========================================================================

    if not data:

        st.info(
            "No Pending Refunds"
        )

        return

    st.subheader(
        f"Pending Refund Count : {len(data)}"
    )

    # ==========================================================================
    # REFUND QUEUE
    # ==========================================================================

    for refund in data:

        refund_id = refund.get(
            "id"
        )

        with st.container(
            border=True
        ):

            col1, col2, col3 = st.columns(
                3
            )

            # ------------------------------------------------------------------
            # REFUND INFORMATION
            # ------------------------------------------------------------------

            with col1:

                st.write(
                    f"**Refund ID:** {refund_id}"
                )

                st.write(
                    f"**Sale ID:** "
                    f"{refund.get('sale_id')}"
                )

            # ------------------------------------------------------------------
            # AMOUNT
            # ------------------------------------------------------------------

            with col2:

                refund_amount = refund.get(
                    "refund_amount"
                )

                try:

                    refund_amount = float(
                        refund_amount or 0
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    refund_amount = 0.0

                st.write(
                    f"**Amount:** "
                    f"{refund_amount:,.0f} MMK"
                )

            # ------------------------------------------------------------------
            # DATE / STATUS
            # ------------------------------------------------------------------

            with col3:

                st.write(
                    f"**Date:** "
                    f"{refund.get('refund_date')}"
                )

                st.write(
                    f"**Status:** "
                    f"{refund.get('status')}"
                )

            # ------------------------------------------------------------------
            # ACTIONS
            # ------------------------------------------------------------------

            app_col, rej_col = st.columns(
                [1, 2]
            )

            # ------------------------------------------------------------------
            # APPROVE
            # ------------------------------------------------------------------

            with app_col:

                if st.button(
                    "✅ Approve",
                    key=f"approve_{refund_id}",
                    type="primary",
                    use_container_width=True,
                ):

                    handle_approval(
                        refund_id,
                        user["id"],
                    )

            # ------------------------------------------------------------------
            # REJECT
            # ------------------------------------------------------------------

            with rej_col:

                reject_reason = st.text_input(
                    "Reject Reason",
                    key=f"reject_reason_{refund_id}",
                )

                if st.button(
                    "❌ Reject",
                    key=f"reject_{refund_id}",
                    use_container_width=True,
                ):

                    if not reject_reason.strip():

                        st.warning(
                            "Please enter reject reason."
                        )

                    else:

                        handle_rejection(
                            refund_id,
                            user["id"],
                            reject_reason.strip(),
                        )


# ==============================================================================
# DIRECT EXECUTION
# ==============================================================================

if __name__ == "__main__":

    run()
