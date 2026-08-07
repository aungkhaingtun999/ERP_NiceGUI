# ==============================================================================
# erp_pages/inventory/warehouse.py
# ERP ENTERPRISE CENTRAL WAREHOUSE SELECTOR v3.0
# Reusable selector with custom key
# ==============================================================================

import streamlit as st


def render_warehouse_selector(
    warehouses,
    key="erp_global_warehouse_selector"
):

    if not warehouses:
        st.error("No warehouse available")
        return None, None

    warehouse_map = {
        str(w.get("name")): w.get("id")
        for w in warehouses
        if w.get("name")
    }

    if not warehouse_map:
        st.error("Warehouse name missing")
        return None, None

    warehouse_names = list(warehouse_map.keys())

    session_key = f"{key}_selected"

    if session_key not in st.session_state:
        st.session_state[session_key] = warehouse_names[0]

    if st.session_state[session_key] not in warehouse_names:
        st.session_state[session_key] = warehouse_names[0]

    selected_name = st.selectbox(
        "📍 Select Warehouse",
        warehouse_names,
        index=warehouse_names.index(
            st.session_state[session_key]
        ),
        key=key
    )

    st.session_state[session_key] = selected_name

    return warehouse_map[selected_name], selected_name
    
