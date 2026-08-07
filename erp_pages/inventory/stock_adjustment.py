# ==============================================================================
# erp_pages/inventory/stock_adjustment.py
# ERP ENTERPRISE STOCK ADJUSTMENT v1.0
#
# Maker Checker Approval Component
#
# Responsibilities:
# - Stock Adjustment
# - Approval Queue
# - Approve / Cancel
# - Adjustment History
#
# ==============================================================================


import time

import streamlit as st


from database import db


from utils.ui import show_table





# ==============================================================================
# RENDER STOCK ADJUSTMENT
# ==============================================================================


def render_stock_adjustment(

    products,

    warehouse_id,

    warehouse_name,

    inventory_service

):


    st.subheader(
        '🔧 Enterprise Stock Adjustment'
    )



    # ==========================================================================
    # NO PRODUCT
    # ==========================================================================


    if not products:


        st.warning(
            'No products available'
        )

        return




    # ==========================================================================
    # PRODUCT SELECTOR
    # ==========================================================================


    product_map = {


        f"{p.get('id')} | {p.get('name')}":

        p


        for p in products


    }




    selected_name = st.selectbox(

        '📦 Select Product',

        list(product_map.keys()),

        key='stock_adjust_product'

    )



    selected_product = product_map[

        selected_name

    ]




    product_id = int(

        selected_product.get('id')

    )




    current_qty = (

        selected_product.get('available_qty')

        or

        selected_product.get('qty')

        or

        selected_product.get('stock')

        or 0

    )




    st.info(

f'''
📦 Product:
{selected_product.get('name')}


🏭 Warehouse:
{warehouse_name}


📊 Current Stock:
{current_qty}
'''

    )





    # ==========================================================================
    # FORM
    # ==========================================================================


    adjustment_type = st.selectbox(

        'Adjustment Type',

        [

            'DAMAGE',

            'COUNT_CORRECTION',

            'MANUAL_IN',

            'MANUAL_OUT'

        ]

    )



    qty = st.number_input(

        'Quantity (+/-)',

        value=0,

        step=1

    )



    reason = st.text_input(

        'Reason',

        value='Manual Adjustment'

    )





    # ==========================================================================
    # SUBMIT
    # ==========================================================================


    if st.button(

        '💾 Submit Adjustment',

        use_container_width=True

    ):



        if qty == 0:


            st.warning(
                'Quantity cannot be zero'
            )

            st.stop()




        try:


            result = inventory_service.adjust_stock(

                product_id=product_id,

                warehouse_id=int(warehouse_id),

                quantity=int(qty),

                reason=reason,

                created_by=

                st.session_state.get(
                    'user_id'
                ),

                unit_cost=float(

                    selected_product.get(

                        'purchase_price',

                        0

                    )

                )

            )




            if result.get('success'):


                st.success(
                    '✅ Adjustment Submitted (PENDING)'
                )


                st.cache_data.clear()

                time.sleep(1)

                st.rerun()




            else:


                st.error(

                    result.get(

                        'message',

                        'Adjustment Failed'

                    )

                )



        except Exception as e:


            st.error(
                f'Adjustment Error : {e}'
            )






    # ==========================================================================
    # APPROVAL QUEUE
    # ==========================================================================


    st.divider()


    st.subheader(
        '⏳ Pending Approval Queue'
    )




    try:


        history = inventory_service.get_stock_adjustments(

            warehouse_id=int(warehouse_id)

        )



        current_user = str(

            st.session_state.get(

                'user_id',

                ''

            )

        )



        pending_rows = [

            x for x in history

            if str(

                x.get(

                    'status',

                    ''

                )

            ).upper() == 'PENDING'

        ]




        # ----------------------------------------------------------------------
        # NO PENDING
        # ----------------------------------------------------------------------


        if not pending_rows:


            st.success(
                'No pending adjustments'
            )




        # ----------------------------------------------------------------------
        # PENDING LIST
        # ----------------------------------------------------------------------


        else:


            for row in pending_rows:


                with st.container(border=True):


                    st.write(f"ID: {row['id']}")
                    st.write(f"Product: {row['product_name']}")
                    st.write(f"Qty: {row['qty']}")
                    st.write(f"Reason: {row['reason']}")

                    st.write(

                        f"Requested By: {row.get('requested_by')}"

                    )



                    maker = str(

                        row.get(

                            'requested_by',

                            ''

                        )

                    )



                    col1, col2 = st.columns(2)



                    # ----------------------------------------------------------
                    # APPROVE
                    # ----------------------------------------------------------

                    with col1:


                        if current_user == maker:


                            st.caption(
                                '🚫 Maker cannot approve'
                            )



                        else:


                            if st.button(

                                '✅ Approve',

                                key=f"approve_{row.get('id')}"

                            ):


                                result = inventory_service.approve_stock_adjustment(

                                    adjustment_id=int(

                                        row.get('id')

                                    ),

                                    manager_id=current_user

                                )



                                if result.get('success'):


                                    st.success(
                                        'Approved Successfully'
                                    )

                                    st.cache_data.clear()

                                    time.sleep(1)

                                    st.rerun()



                                else:


                                    st.error(

                                        result.get(

                                            'message',

                                            'Approve Failed'

                                        )

                                    )




                    # ----------------------------------------------------------
                    # CANCEL
                    # ----------------------------------------------------------

                    with col2:


                        if st.button(

                            '❌ Cancel',

                            key=f"cancel_{row.get('id')}"

                        ):


                            db().rpc(

                                'cancel_stock_adjustment_rpc',

                                {

                                    'p_adjustment_id':

                                    int(row.get('id')),


                                    'p_user_id':

                                    current_user

                                }

                            ).execute()



                            st.success(
                                'Cancelled'
                            )

                            st.cache_data.clear()

                            time.sleep(1)

                            st.rerun()





        # ==========================================================================
        # HISTORY
        # ==========================================================================


        st.divider()


        st.subheader(
            '📜 Adjustment History'
        )


        show_table(history)




    except Exception as e:


        st.error(
            f'Approval Load Error : {e}'
        )
