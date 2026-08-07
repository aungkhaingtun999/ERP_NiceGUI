# ==============================================================================
# erp_pages/inventory/warehouse.py
# ERP ENTERPRISE INVENTORY WAREHOUSE SELECTOR v1.0
#
# Responsibilities:
# - Warehouse Dropdown
# - Active Warehouse Selection
#
# ==============================================================================


import streamlit as st





# ==============================================================================
# WAREHOUSE SELECTOR
# ==============================================================================


def render_warehouse_selector(

    warehouses

):


    if not warehouses:


        st.error(

            "No warehouse available"

        )


        st.stop()





    # --------------------------------------------------------------------------
    # CREATE MAP
    # --------------------------------------------------------------------------


    warehouse_map = {


        str(

            w.get("name")

        ):

        w.get("id")


        for w in warehouses


    }




    names = list(

        warehouse_map.keys()

    )





    # --------------------------------------------------------------------------
    # SESSION MEMORY
    # --------------------------------------------------------------------------


    if (

        "inventory_selected_warehouse"

        not in st.session_state

    ):


        st.session_state.inventory_selected_warehouse = names[0]






    # --------------------------------------------------------------------------
    # SELECT BOX
    # --------------------------------------------------------------------------


    selected_name = st.selectbox(


        "📍 Select Warehouse",


        names,


        key=

        "inventory_selected_warehouse"



    )





    selected_id = warehouse_map.get(

        selected_name

    )





    return (

        selected_id,

        selected_name

    )