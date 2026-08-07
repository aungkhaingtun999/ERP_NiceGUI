# ==============================================================================
# erp_pages/inventory/dashboard.py
# ERP ENTERPRISE INVENTORY DASHBOARD v1.0
#
# Responsibilities:
# - Inventory KPI
# - Warehouse KPI
# - FIFO Valuation
# - Inventory Loss Analytics
# - Stock Card
# - Service Health Check
#
# ==============================================================================


import streamlit as st


from database import (
    db,
    get_inventory_view
)


from erp_core.services.inventory_service import (
    InventoryService
)


from utils.ui import show_table





# ==============================================================================
# INVENTORY DASHBOARD
# ==============================================================================


def render_inventory_dashboard(

    warehouse_id

):


    st.subheader(
        '📊 Enterprise Inventory Dashboard'
    )



    try:


        inventory_service = InventoryService(
            db()
        )



    except Exception as e:


        st.error(
            f'Inventory Service Error : {e}'
        )

        return





    # ==========================================================================
    # KPI
    # ==========================================================================


    st.divider()


    st.subheader(
        '🏭 Inventory KPI'
    )



    try:


        kpi = inventory_service.get_inventory_kpi()



        if kpi.get('success') is False:


            st.error(

                kpi.get(

                    'message',

                    'KPI Loading Failed'

                )

            )



        else:


            c1, c2, c3, c4, c5 = st.columns(5)



            c1.metric(

                '📦 Products',

                kpi.get(

                    'total_products',

                    0

                )

            )



            c2.metric(

                '🏭 Warehouses',

                kpi.get(

                    'total_warehouses',

                    0

                )

            )



            c3.metric(

                '📊 Stock Qty',

                kpi.get(

                    'total_stock_qty',

                    0

                )

            )



            c4.metric(

                '💰 Inventory Value',

                f"{float(kpi.get('total_inventory_value',0)):,.0f} MMK"

            )



            c5.metric(

                '⚠ Low Stock',

                kpi.get(

                    'low_stock_items',

                    0

                )

            )



    except Exception as e:


        st.error(
            f'KPI Error : {e}'
        )






    # ==========================================================================
    # WAREHOUSE KPI
    # ==========================================================================


    st.divider()


    st.subheader(
        '🏭 Warehouse Inventory'
    )



    try:


        warehouse_data = inventory_service.get_warehouse_inventory_kpi()



        if warehouse_data:


            show_table(warehouse_data)


        else:


            st.info(
                'No warehouse data'
            )



    except Exception as e:


        st.error(
            f'Warehouse KPI Error : {e}'
        )






    # ==========================================================================
    # FIFO VALUATION
    # ==========================================================================


    st.divider()


    st.subheader(
        '💰 FIFO Inventory Valuation'
    )



    try:


        valuation = inventory_service.get_inventory_valuation()



        if valuation:


            show_table(valuation)


        else:


            st.info(
                'No FIFO layers found'
            )



    except Exception as e:


        st.error(
            f'FIFO Error : {e}'
        )






    # ==========================================================================
    # LOSS REPORT
    # ==========================================================================


    st.divider()


    st.subheader(
        '📉 Inventory Loss Analytics'
    )



    try:


        loss_data = inventory_service.get_inventory_loss_report()



        if loss_data:


            show_table(loss_data)


        else:


            st.success(
                'No inventory loss detected'
            )



    except Exception as e:


        st.error(
            f'Loss Analytics Error : {e}'
        )






    # ==========================================================================
    # STOCK CARD
    # ==========================================================================


    st.divider()


    st.subheader(
        '📜 Stock Card'
    )



    try:


        products = get_inventory_view(

            warehouse_id=warehouse_id,

            search=None

        )



        if products:


            product_map = {


                f"{p.get('id')} | {p.get('name')}":

                p


                for p in products


            }



            selected_name = st.selectbox(

                'Select Product For Stock Card',

                list(product_map.keys()),

                key='stock_card_product'

            )



            selected_product = product_map[selected_name]



            stock_card = inventory_service.get_stock_card(

                product_id=int(

                    selected_product.get('id')

                ),

                warehouse_id=int(warehouse_id)

            )



            if stock_card:


                show_table(stock_card)


            else:


                st.info(
                    'No stock movement history'
                )



        else:


            st.info(
                'No products available'
            )



    except Exception as e:


        st.error(
            f'Stock Card Error : {e}'
        )






    # ==========================================================================
    # HEALTH CHECK
    # ==========================================================================


    st.divider()


    st.subheader(
        '🩺 Inventory Service Health'
    )



    try:


        health = inventory_service.health_check()


        st.json(health)



    except Exception as e:


        st.error(str(e))
