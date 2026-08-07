# ==============================================================================
# erp_pages/inventory/warehouse.py
# ERP ENTERPRISE WAREHOUSE SELECTOR v2.0 FINAL
#
# Responsibilities:
# - Warehouse Dropdown
# - Session Memory
# - Active Warehouse Selection
#
# ==============================================================================


import streamlit as st




# ==============================================================================
# RENDER WAREHOUSE SELECTOR
# ==============================================================================


def render_warehouse_selector(
    warehouses
):


    if not warehouses:


        st.error(
            "No warehouse available"
        )


        return None, None





    # --------------------------------------------------------------------------
    # MAP
    # --------------------------------------------------------------------------


    warehouse_map = {


        str(
            w.get("name")
        ):

        w.get("id")


        for w in warehouses

        if w.get("name")

    }



    if not warehouse_map:


        st.error(
            "Warehouse name missing"
        )


        return None, None





    warehouse_names = list(

        warehouse_map.keys()

    )





    # --------------------------------------------------------------------------
    # SESSION DEFAULT
    # --------------------------------------------------------------------------


    if (

        "inventory_selected_warehouse"

        not in st.session_state

    ):


        st.session_state.inventory_selected_warehouse = (
            warehouse_names[0]
        )






    # --------------------------------------------------------------------------
    # SELECT BOX
    # --------------------------------------------------------------------------


    selected_name = st.selectbox(

        "📍 Select Warehouse",

        warehouse_names,

        index=

        warehouse_names.index(

            st.session_state.inventory_selected_warehouse

        )

        if st.session_state.inventory_selected_warehouse in warehouse_names

        else 0,


        key="inventory_main_warehouse_selector"

    )





    # --------------------------------------------------------------------------
    # SAVE SESSION
    # --------------------------------------------------------------------------


    st.session_state.inventory_selected_warehouse = selected_name





    selected_id = warehouse_map.get(

        selected_name

    )





    return (

        selected_id,

        selected_name

    )
