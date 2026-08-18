# ==============================================================================
# ERP ENTERPRISE REFUND APPROVAL CENTER
#
# FINAL REFUND WORKFLOW
#
# RPC ONLY:
#   approve_refund_rpc
#   reject_refund_rpc
#
# STATUS FLOW:
#   PENDING -> APPROVED
#   PENDING -> REJECTED
#
# IMPORTANT:
#   Approve = restore stock + inventory log + FIFO layer
#   Reject  = status only
# ==============================================================================

import streamlit as st

from database import db
from auth import require_login


# ==============================================================================
# ALLOWED ROLES
# ==============================================================================

ALLOWED_ROLE_IDS = {
    1,  # Admin
    2,  # Manager
}


# ==============================================================================
# SAFE NUMBER
# ==============================================================================

def safe_float(value):

    try:

        return float(value or 0)

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


# ==============================================================================
# APPROVE
# ==============================================================================

def handle_approval(
    refund_id,
    approver_id,
):

    try:

        result = (
            db()
            .rpc(
                "approve_refund_rpc",
                {
                    "p_refund_id": int(refund_id),
                    "p_manager_id": approver_id,
                },
            )
            .execute()
        )

        data = result.data

        if (
            isinstance(data, dict)
            and data.get("success") is True
        ):

            st.success(
                f"Refund ID {refund_id} approved successfully."
            )

            st.rerun()

        else:

            message = (
                data.get("message")
                if isinstance(data, dict)
                else str(data)
            )

            st.error(
                f"Approval failed: {message}"
            )

    except Exception as e:

        st.error(
            f"Approval error: {e}"
        )


# ==============================================================================
# REJECT
# ==============================================================================

def handle_rejection(
    refund_id,
    approver_id,
    reason,
):

    reason = (reason or "").strip()

    if not reason:

        st.warning(
            "Reject reason is required."
        )

        return


    try:

        result = (
            db()
            .rpc(
                "reject_refund_rpc",
                {
                    "p_refund_id": int(refund_id),
                    "p_manager_id": approver_id,
                    "p_reason": reason,
                },
            )
            .execute()
        )

        data = result.data

        if (
            isinstance(data, dict)
            and data.get("success") is True
        ):

            st.success(
                f"Refund ID {refund_id} rejected successfully."
            )

            st.rerun()

        else:

            message = (
                data.get("message")
                if isinstance(data, dict)
                else str(data)
            )

            st.error(
                f"Rejection failed: {message}"
            )

    except Exception as e:

        st.error(
            f"Rejection error: {e}"
        )


# ==============================================================================
# MAIN
# ==============================================================================

def run():

    # ==========================================================================
    # AUTH
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

    try:

        role_id = int(
            user.get("role_id")
        )

    except (
        TypeError,
        ValueError,
    ):

        role_id = None


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


    role_name = (
        "Admin"
        if role_id == 1
        else "Manager"
    )


    st.caption(
        f"Authorized Approver: {role_name}"
    )


    # ==========================================================================
    # LOAD PENDING REFUNDS
    # ==========================================================================

    try:

        response = (
            db()
            .table("refunds")
            .select(
                "*"
            )
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

        refunds = (
            response.data
            if response
            and hasattr(response, "data")
            and response.data
            else []
        )

    except Exception as e:

        st.error(
            f"Error loading pending refunds: {e}"
        )

        st.stop()


    # ==========================================================================
    # EMPTY
    # ==========================================================================

    if not refunds:

        st.success(
            "✅ No Pending Refunds"
        )

        return


    # ==========================================================================
    # SUMMARY
    # ==========================================================================

    total_pending = len(refunds)

    total_amount = sum(
        safe_float(
            refund.get("refund_amount")
        )
        for refund in refunds
    )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Pending Refunds",
            total_pending,
        )


    with col2:

        st.metric(
            "Pending Amount",
            f"{total_amount:,.0f} MMK",
        )


    st.divider()


    # ==========================================================================
    # REFUND QUEUE
    # ==========================================================================

    for refund in refunds:

        refund_id = refund.get("id")

        sale_id = refund.get("sale_id")

        refund_amount = safe_float(
            refund.get("refund_amount")
        )

        refund_date = (
            refund.get("refund_date")
            or "-"
        )

        reason = (
            refund.get("reason")
            or "-"
        )


        with st.container(
            border=True
        ):

            # ==============================================================
            # HEADER
            # ==============================================================

            col1, col2, col3, col4 = st.columns(
                [1, 1, 2, 2]
            )


            with col1:

                st.caption(
                    "Refund ID"
                )

                st.write(
                    f"**{refund_id}**"
                )


            with col2:

                st.caption(
                    "Sale ID"
                )

                st.write(
                    f"**{sale_id}**"
                )


            with col3:

                st.caption(
                    "Refund Amount"
                )

                st.write(
                    f"**{refund_amount:,.0f} MMK**"
                )


            with col4:

                st.caption(
                    "Refund Date"
                )

                st.write(
                    f"**{refund_date}**"
                )


            # ==============================================================
            # REASON
            # ==============================================================

            st.caption(
                "Reason"
            )

            st.write(
                reason
            )


            # ==============================================================
            # STATUS
            # ==============================================================

            st.warning(
                "⏳ PENDING — Waiting for Manager Approval"
            )


            st.divider()


            # ==============================================================
            # ACTIONS
            # ==============================================================

            approve_col, reject_col = st.columns(
                [1, 2]
            )


            # ==============================================================
            # APPROVE
            # ==============================================================

            with approve_col:

                if st.button(
                    "✅ Approve Refund",
                    key=f"approve_refund_{refund_id}",
                    type="primary",
                    use_container_width=True,
                ):

                    handle_approval(
                        refund_id,
                        user["id"],
                    )


            # ==============================================================
            # REJECT
            # ==============================================================

            with reject_col:

                reject_reason = st.text_input(
                    "Reject Reason",
                    key=f"reject_reason_{refund_id}",
                    placeholder="Enter reason for rejection...",
                )


                if st.button(
                    "❌ Reject Refund",
                    key=f"reject_refund_{refund_id}",
                    use_container_width=True,
                ):

                    handle_rejection(
                        refund_id,
                        user["id"],
                        reject_reason,
                    )


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="Refund Approval",
        layout="wide",
    )

    run()
