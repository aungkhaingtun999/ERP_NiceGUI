# ==============================================================================
# erp_pages/inventory/product_approval.py
# ERP ENTERPRISE PRODUCT APPROVAL QUEUE v1.0
# ==============================================================================

import streamlit as st

from erp_core import privileged_db
from erp_core.context import CacheManager


# ==============================================================================
# APPROVAL QUEUE
# ==============================================================================

def render_product_approval_queue():

    st.subheader('🟡 Product Approval Queue')

    current_user = st.session_state.get('user')

    if not current_user:
        st.warning('Login required')
        return

    # --------------------------------------------------------------------------
    # ROLE CHECK
    # --------------------------------------------------------------------------
    role_id = current_user.get('role_id')

    if role_id not in [1, 2]:
        st.info('Approval queue is visible only to Admin or Manager.')
        return

    client = privileged_db()

    try:
        response = (
            client
            .table('product_create_requests')
            .select('*')
            .eq('status', 'PENDING')
            .order('id', desc=True)
            .execute()
        )

        requests = response.data or []

    except Exception as e:
        st.error(f'Failed to load approval queue : {e}')
        return

    if not requests:
        st.success('✅ No pending product requests.')
        return

    st.warning(f'Pending Requests : {len(requests)}')

    st.markdown('---')

    for req in requests:
        product = req.get('product_data', {}) or {}

        with st.container(border=True):
            st.markdown(f'### 📝 Request #{req["id"]}')

            c1, c2 = st.columns(2)

            with c1:
                st.write(f'**Product:** {product.get("name", "-")}')
                st.write(f'**SKU:** {product.get("sku", "-")}')
                st.write(f'**Barcode:** {product.get("barcode", "-")}')
                st.write(f'**Unit:** {product.get("unit", "-")}')

            with c2:
                st.write(f'**Opening Qty:** {req.get("initial_qty", 0)}')
                st.write(f'**Purchase Price:** {product.get("purchase_price", 0)}')
                st.write(f'**Selling Price:** {product.get("selling_price", 0)}')
                st.write(f'**Warehouse:** {req.get("warehouse_id")}')

            st.write(f'**Requested By:** {req.get("requested_by")}')
            st.write(f'**Created At:** {req.get("created_at")}')

            b1, b2 = st.columns(2)

            with b1:
                if st.button(
                    '✅ Approve',
                    key=f'approve_{req["id"]}',
                    use_container_width=True
                ):
                    try:
                        result = (
                            client
                            .rpc(
                                'approve_product_create_rpc',
                                {
                                    'p_request_id': req['id'],
                                    'p_approved_by': current_user['id']
                                }
                            )
                            .execute()
                        )

                        st.success(f'Approved Request #{req["id"]}')

                        CacheManager.bump('product_version')
                        CacheManager.bump('inventory_version')
                        st.cache_data.clear()
                        st.rerun()

                    except Exception as e:
                        st.error(f'Approve failed : {e}')

            with b2:
                if st.button(
                    '❌ Reject',
                    key=f'reject_{req["id"]}',
                    use_container_width=True
                ):
                    try:
                        (
                            client
                            .table('product_create_requests')
                            .update(
                                {
                                    'status': 'REJECTED'
                                }
                            )
                            .eq('id', req['id'])
                            .execute()
                        )

                        st.success(f'Rejected Request #{req["id"]}')
                        st.rerun()

                    except Exception as e:
                        st.error(f'Reject failed : {e}')

            st.markdown('---')
