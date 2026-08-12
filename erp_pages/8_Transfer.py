# ==============================================================================
# erp_pages/8_Transfer.py
# ERP ENTERPRISE WAREHOUSE TRANSFER v32
# MAKER-CHECKER REQUEST ONLY
# NO DIRECT STOCK UPDATE
# ==============================================================================

import streamlit as st

from erp_core.base_repo import db, log_error
from erp_core.loaders.warehouse_loader import get_warehouses


def run():

    st.title('🔁 Enterprise Warehouse Transfer')
    st.caption('Maker → Pending → Checker Approval → Stock Movement')

    supabase = db()

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

    # ==================================================
    # LOAD WAREHOUSES
    # ==================================================

    warehouses = get_warehouses()

    if not warehouses:
        st.error('No warehouses found.')
        return

    warehouse_options = {}

    for w in warehouses:
        wid = int(w.get('id', 0))
        code = w.get('code', 'N/A')
        name = w.get('name', 'Unknown')
        warehouse_options[wid] = f'[{wid}] {code} - {name}'

    st.subheader('Transfer Details')

    col1, col2 = st.columns(2)

    with col1:

        source_warehouse_id = st.selectbox(
            'Source Warehouse',
            options=list(warehouse_options.keys()),
            index=0,
            format_func=lambda x: warehouse_options[x]
        )

    with col2:

        destination_list = [
            x
            for x in warehouse_options.keys()
            if x != source_warehouse_id
        ]

        if not destination_list:
            st.warning('Need at least two warehouses.')
            return

        dest_warehouse_id = st.selectbox(
            'Destination Warehouse',
            options=destination_list,
            format_func=lambda x: warehouse_options[x]
        )

    # ==================================================
    # LOAD SOURCE STOCK
    # ==================================================

    try:

        stock_rows = (
            supabase
            .table('warehouse_stock')
            .select('product_id,qty,available_qty')
            .eq('warehouse_id', source_warehouse_id)
            .gt('available_qty', 0)
            .execute()
            .data
            or []
        )

    except Exception as e:

        st.error(f'Stock loading error: {e}')
        return

    if not stock_rows:
        st.warning('Source warehouse has no available stock.')
        return

    # ==================================================
    # LOAD PRODUCTS
    # ==================================================

    product_ids = [
        int(x['product_id'])
        for x in stock_rows
    ]

    product_options = {}

    try:

        products = (
            supabase
            .table('products')
            .select('id,name')
            .in_('id', product_ids)
            .execute()
            .data
            or []
        )

        for p in products:
            product_options[int(p['id'])] = p['name']

    except Exception as e:

        st.error(f'Product loading error: {e}')
        return

    if not product_options:
        st.warning('No products found.')
        return

    selected_product_id = st.selectbox(
        'Select Product',
        options=list(product_options.keys()),
        format_func=lambda x: product_options[x]
    )

    # ==================================================
    # SOURCE STOCK
    # ==================================================

    source_stock = next(
        (
            x for x in stock_rows
            if int(x['product_id']) == selected_product_id
        ),
        None
    )

    source_qty = (
        source_stock.get('qty', 0)
        if source_stock
        else 0
    )

    source_available = (
        source_stock.get('available_qty', source_qty)
        if source_stock
        else 0
    )

    # ==================================================
    # DESTINATION STOCK
    # ==================================================

    dest_stock = (
        supabase
        .table('warehouse_stock')
        .select('qty,available_qty')
        .eq('warehouse_id', dest_warehouse_id)
        .eq('product_id', selected_product_id)
        .execute()
        .data
        or []
    )

    if dest_stock:

        dest_qty = dest_stock[0].get('qty', 0)
        dest_available = dest_stock[0].get('available_qty', 0)

    else:

        dest_qty = 0
        dest_available = 0

    # ==================================================
    # DISPLAY
    # ==================================================

    c1, c2 = st.columns(2)

    with c1:

        st.info(
            f'''
📤 SOURCE STOCK

Warehouse:
{warehouse_options[source_warehouse_id]}

Product:
{product_options[selected_product_id]}

Current Qty:
{source_qty}

Available Qty:
{source_available}
'''
        )

    with c2:

        st.success(
            f'''
📥 DESTINATION STOCK

Warehouse:
{warehouse_options[dest_warehouse_id]}

Product:
{product_options[selected_product_id]}

Current Qty:
{dest_qty}

Available Qty:
{dest_available}
'''
        )

    if source_available <= 0:
        st.error('No available stock.')
        return

    # ==================================================
    # TRANSFER QTY
    # ==================================================

    transfer_qty = st.number_input(
        'Transfer Quantity',
        min_value=1,
        max_value=int(source_available),
        value=1
    )

    notes = st.text_area(
        'Transfer Note (Optional)',
        placeholder='Reason / remark for warehouse transfer'
    )

    # ==================================================
    # PREVIEW
    # ==================================================

    st.subheader('📊 Transfer Preview')

    p1, p2 = st.columns(2)

    with p1:

        st.metric(
            'After Source Stock',
            source_qty - transfer_qty,
            delta=f'-{transfer_qty}'
        )

    with p2:

        st.metric(
            'After Destination Stock',
            dest_qty + transfer_qty,
            delta=f'+{transfer_qty}'
        )

    st.warning(
        '⚠️ This action creates a **PENDING transfer request** only. '
        'Stock will move **after Checker approval**.'
    )

    # ==================================================
    # SUBMIT REQUEST
    # ==================================================

    if st.button(
        '📝 Submit Transfer Request',
        type='primary',
        use_container_width=True
    ):

        try:

            response = (
                supabase
                .rpc(
                    'create_warehouse_transfer_request_rpc',
                    {
                        'p_source_warehouse_id': int(source_warehouse_id),
                        'p_destination_warehouse_id': int(dest_warehouse_id),
                        'p_product_id': int(selected_product_id),
                        'p_quantity': float(transfer_qty),
                        'p_requested_by': str(current_user_id),
                        'p_notes': notes,
                    }
                )
                .execute()
            )

            result = response.data

            if isinstance(result, list):
                result = result[0] if result else None

            if not isinstance(result, dict):

                st.error('Invalid RPC response.')
                st.code(str(result))
                return

            if not result.get('success', False):

                st.error(result.get('message', 'Transfer request failed.'))
                return

            st.success('✅ Transfer request submitted successfully.')

            st.info(
                f'''
Request ID : #{result.get('request_id')}
Status : {result.get('status')}
Maker : {current_username}

Stock has NOT moved yet.
Waiting for Checker approval.
'''
            )

            st.rerun()

        except Exception as e:

            log_error(
                message='warehouse transfer request failed',
                exception=e
            )

            st.exception(e)


if __name__ == '__main__':

    run()
