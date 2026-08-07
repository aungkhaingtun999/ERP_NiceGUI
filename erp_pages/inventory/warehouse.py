# ==============================================================================
# erp_pages/inventory/warehouse.py
# ERP ENTERPRISE WAREHOUSE SELECTOR CLEAN v2.0
# ==============================================================================

import streamlit as st



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



    current = st.session_state.get(
        "inventory_selected_warehouse",
        warehouse_names[0]
    )



    if current not in warehouse_names:

        current = warehouse_names[0]



    selected_name = st.selectbox(

        "📍 Select Warehouse",

        warehouse_names,

        index=warehouse_names.index(current),

        key="erp_inventory_warehouse_selector"

    )



    st.session_state.inventory_selected_warehouse = selected_name



    return (

        warehouse_map[selected_name],

        selected_name

    )
