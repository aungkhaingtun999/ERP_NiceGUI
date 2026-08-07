import streamlit as st

def render_warehouse_selector(warehouses):
    if not warehouses:
        st.error('No warehouse available')
        return None, None
        
    warehouse_map = {str(w.get('name')): w.get('id') for w in warehouses if w.get('name')}
    
    if not warehouse_map:
        st.error('Warehouse name missing')
        return None, None
        
    warehouse_names = list(warehouse_map.keys())
    
    if 'inventory_selected_warehouse' not in st.session_state:
        st.session_state.inventory_selected_warehouse = warehouse_names[0]
        
    default_index = (
        warehouse_names.index(st.session_state.inventory_selected_warehouse)
        if st.session_state.inventory_selected_warehouse in warehouse_names
        else 0
    )
    
    selected_name = st.selectbox(
        '📍 Select Warehouse',
        warehouse_names,
        index=default_index,
        key='inventory_main_warehouse_selector'
    )
    
    st.session_state.inventory_selected_warehouse = selected_name
    selected_id = warehouse_map[selected_name]
    
    return selected_id, selected_name
