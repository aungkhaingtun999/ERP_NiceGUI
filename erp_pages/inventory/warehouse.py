# ==============================================================================
# erp_pages/inventory/warehouse.py
# ERP ENTERPRISE CENTRAL WAREHOUSE SELECTOR v2.0
#
# Single Source Warehouse Selector
# ==============================================================================

import streamlit as st


WAREHOUSE_KEY = "erp_global_warehouse_selector"


def render_warehouse_selector(warehouses):


    if not warehouses:

        st.error(
            "No warehouse available"
        )

        return None, None



    warehouse_map = {

        str(w.get("name")):
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



    if (
        "erp_selected_warehouse"
        not in st.session_state
    ):

        st.session_state.erp_selected_warehouse = warehouse_names[0]



    if (
        st.session_state.erp_selected_warehouse
        not in warehouse_names
    ):

        st.session_state.erp_selected_warehouse = warehouse_names[0]



    selected_name = st.selectbox(

        "📍 Select Warehouse",

        warehouse_names,

        index=warehouse_names.index(
            st.session_state.erp_selected_warehouse
        ),

        key=WAREHOUSE_KEY

    )



    st.session_state.erp_selected_warehouse = selected_name



    return (

        warehouse_map[selected_name],

        selected_name

    )
