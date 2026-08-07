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
# erp_pages/inventory/warehouse.py
# ERP ENTERPRISE WAREHOUSE SELECTOR v1.1
# ==============================================================================


import streamlit as st



def render_warehouse_selector(
    warehouses
):


    if not warehouses:

        st.error(
            "No warehouse available"
        )

        return None, None



    # --------------------------------------------------
    # CREATE NAME LIST
    # --------------------------------------------------

    warehouse_names = [

        w.get("name")

        for w in warehouses

        if w.get("name")

    ]



    if not warehouse_names:

        st.error(
            "Warehouse name missing"
        )

        return None, None



    # --------------------------------------------------
    # SELECT BOX
    # --------------------------------------------------

    selected_name = st.selectbox(

        "📍 Select Warehouse",

        warehouse_names,

        key="inventory_main_warehouse_selector"

    )



    # --------------------------------------------------
    # FIND ID
    # --------------------------------------------------

    warehouse_map = {

        w.get("name"):
        w.get("id")

        for w in warehouses

    }



    selected_id = warehouse_map.get(
        selected_name
    )


    return (
        selected_id,
        selected_name
    )




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
    warehouse_names,
    key="inventory_main_warehouse_selector"
    )





    selected_id = warehouse_map.get(

        selected_name

    )





    return (

        selected_id,

        selected_name

    )
