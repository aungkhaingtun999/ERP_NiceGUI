# ==============================================================================
# erp_pages/inventory/warehouse_transfer_approval.py
# ERP ENTERPRISE WAREHOUSE TRANSFER APPROVAL QUEUE v1.0
# MAKER-CHECKER
# ==============================================================================

import time
import streamlit as st

from erp_core import privileged_db


# ==============================================================================
# USER LOOKUP
# ==============================================================================

def _load_users(client):

    try:

        response = (
            client.table('users')
            .select('id,username,full_name')
            .execute()
        )

        users = response.data or []

        return {
            str(u['id']): u
            for u in users
            if u.get('id')
        }

    except Exception:

        return {}


def _user_name(user_id, cache):

    if not user_id:
        return 'Unknown'

    user = cache.get(str(user_id))

    if not user:
        return str(user_id)

    return (
        user.get('username')
        or user.get('full_name')
        or str(user_id)
    )


# ==============================================================================
# MAIN
# ==============================================================================

def render_warehouse_transfer_approval_queue():

    st.subheader('🚚 Warehouse Transfer Approval Queue')

    current_user = st.session_state.get('user') or {}

    current_user_id = current_user.get('id')

    current_username = (
        current_user.get('username')
        or current_user.get('full_name')
        or 'Unknown User'
    )

    if not current_user_id:

        st.error('Login required.')
        return

    try:

        client = privileged_db()

    except Exception as e:

        st.error('Privileged database connection failed.')
        st.exception(e)
        return

    users_cache = _load_users(client)

    # --------------------------------------------------------------------------
    # LOAD PENDING REQUESTS
    # --------------------------------------------------------------------------

    try:

        response = (
            client.table('warehouse_transfer_requests')
            .select('*')
            .eq('status', 'PENDING')
            .order('id', desc=True)
            .execute()
        )

        requests = response.data or []

    except Exception as e:

        st.error('Failed to load transfer requests.')
        st.exception(e)
        return

    if not requests:

        st.success('✅ No pending warehouse transfer requests.')
        return

    st.warning(f'🟡 Pending Transfers: {len(requests)}')

    # --------------------------------------------------------------------------
    # REQUEST SELECT
    # --------------------------------------------------------------------------

    option_map = {}

    labels = []

    for req in requests:

        maker = _user_name(
            req.get('requested_by'),
            users_cache
        )

        label = (
            f"#{req.get('id')} | "
            f"Product {req.get('product_id')} | "
            f"Qty {req.get('quantity')} | "
            f"Maker: {maker}"
        )

        option_map[label] = req

        labels.append(label)

    selected_label = st.selectbox(
        'Select Transfer Request',
        labels
    )

    req = option_map[selected_label]

    request_id = req.get('id')

    maker_id = req.get('requested_by')

    maker_name = _user_name(
        maker_id,
        users_cache
    )

    # --------------------------------------------------------------------------
    # DETAIL
    # --------------------------------------------------------------------------

    st.markdown('---')

    st.markdown(f'### Transfer Request #{request_id}')

    c1, c2 = st.columns(2)

    with c1:

        st.write(f'**Source Warehouse:** {req.get("source_warehouse_id")}')

        st.write(f'**Destination Warehouse:** {req.get("destination_warehouse_id")}')

        st.write(f'**Product ID:** {req.get("product_id")}')

    with c2:

        st.write(f'**Quantity:** {req.get("quantity")}')

        st.write(f'**Maker:** {maker_name}')

        st.write(f'**Created At:** {req.get("created_at")}')

    notes = req.get('notes')

    if notes:

        st.write(f'**Note:** {notes}')

    # --------------------------------------------------------------------------
    # SELF APPROVAL BLOCK
    # --------------------------------------------------------------------------

    if str(maker_id) == str(current_user_id):

        st.error('🚫 SELF-APPROVAL BLOCKED')

        st.info(
            'Maker cannot approve own transfer request.'
        )

        return

    # --------------------------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------------------------

    st.markdown('---')

    b1, b2 = st.columns(2)

    with b1:

        if st.button(
            '✅ APPROVE TRANSFER',
            type='primary',
            use_container_width=True
        ):

            try:

                response = (
                    client.rpc(
                        'approve_warehouse_transfer_rpc',
                        {
                            'p_request_id': int(request_id),
                            'p_checker_id': str(current_user_id),
                        }
                    ).execute()
                )

                result = response.data

                if isinstance(result, list):

                    result = result[0] if result else None

                if result and result.get('success'):

                    st.success('✅ Transfer approved successfully.')

                    st.info(
                        f'''
Request ID : #{request_id}
Approved By : {current_username}
Quantity : {req.get('quantity')}

Stock movement completed.
'''
                    )

                    time.sleep(1)

                    st.rerun()

                else:

                    st.error(
                        result.get('message', 'Approval failed.')
                    )

            except Exception as e:

                st.exception(e)

    with b2:

        if st.button(
            '❌ REJECT TRANSFER',
            use_container_width=True
        ):

            try:

                response = (
                    client.rpc(
                        'reject_warehouse_transfer_rpc',
                        {
                            'p_request_id': int(request_id),
                            'p_checker_id': str(current_user_id),
                            'p_reason': 'Rejected from approval queue',
                        }
                    ).execute()
                )

                result = response.data

                if isinstance(result, list):

                    result = result[0] if result else None

                if result and result.get('success'):

                    st.success('❌ Transfer rejected.')

                    time.sleep(1)

                    st.rerun()

                else:

                    st.error(
                        result.get('message', 'Reject failed.')
                    )

            except Exception as e:

                st.exception(e)


__all__ = ['render_warehouse_transfer_approval_queue']