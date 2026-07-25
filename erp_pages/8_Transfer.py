# ==============================================================================
# erp_pages/8_Transfer.py
# ERP ENTERPRISE WAREHOUSE TRANSFER v31 STABLE
# ==============================================================================

import streamlit as st

from erp_core.base_repo import db, log_error
from erp_core.loaders.warehouse_loader import get_warehouses



def run():

    st.title("🔁 Enterprise Warehouse Transfer")

    supabase = db()


    # ==================================================
    # LOAD WAREHOUSES
    # ==================================================

    warehouses = get_warehouses()


    if not warehouses:

        st.error("No warehouses found.")
        return



    warehouse_options = {
        int(w["id"]): w["name"]
        for w in warehouses
    }



    st.subheader("Transfer Details")


    col1, col2 = st.columns(2)



    with col1:

        source_warehouse_id = st.selectbox(
            "Source Warehouse",
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

            st.warning(
                "Need at least two warehouses."
            )
            return


        dest_warehouse_id = st.selectbox(
            "Destination Warehouse",
            options=destination_list,
            format_func=lambda x: warehouse_options[x]
        )



    # ==================================================
    # LOAD SOURCE STOCK
    # ==================================================

    try:

        stock_rows = (

            supabase
            .table("warehouse_stock")
            .select(
                """
                product_id,
                qty,
                available_qty
                """
            )
            .eq(
                "warehouse_id",
                source_warehouse_id
            )
            .gt(
                "available_qty",
                0
            )
            .execute()
            .data
            or []

        )


    except Exception as e:

        st.error(
            f"Stock loading error: {e}"
        )
        return



    if not stock_rows:

        st.warning(
            "Source warehouse has no available stock."
        )
        return



    # ==================================================
    # LOAD PRODUCTS
    # ==================================================

    product_ids = [
        int(x["product_id"])
        for x in stock_rows
    ]


    product_options = {}



    try:

        products = (

            supabase
            .table("products")
            .select(
                "id,name"
            )
            .in_(
                "id",
                product_ids
            )
            .execute()
            .data
            or []

        )


        for p in products:

            product_options[
                int(p["id"])
            ] = p["name"]



    except Exception as e:

        st.error(
            f"Product loading error: {e}"
        )
        return



    if not product_options:

        st.warning(
            "No products found."
        )
        return



    # ==================================================
    # PRODUCT SELECT
    # ==================================================

    selected_product_id = st.selectbox(

        "Select Product",

        options=list(product_options.keys()),

        format_func=lambda x:
            product_options[x]

    )



    # ==================================================
    # GET SOURCE STOCK
    # ==================================================

    source_stock = next(

        (
            x for x in stock_rows
            if int(x["product_id"]) == selected_product_id
        ),

        None

    )


    source_qty = (
        source_stock.get("qty",0)
        if source_stock
        else 0
    )


    source_available = (

        source_stock.get(
            "available_qty",
            source_qty
        )

        if source_stock

        else 0

    )



    # ==================================================
    # GET DESTINATION STOCK
    # ==================================================

    dest_stock = (

        supabase
        .table("warehouse_stock")
        .select(
            "qty,available_qty"
        )
        .eq(
            "warehouse_id",
            dest_warehouse_id
        )
        .eq(
            "product_id",
            selected_product_id
        )
        .execute()
        .data
        or []

    )


    if dest_stock:

        dest_qty = dest_stock[0].get(
            "qty",
            0
        )

        dest_available = dest_stock[0].get(
            "available_qty",
            0
        )


    else:

        dest_qty = 0
        dest_available = 0



    # ==================================================
    # STOCK DISPLAY
    # ==================================================

    c1,c2 = st.columns(2)



    with c1:

        st.info(
f"""
📤 SOURCE STOCK

Warehouse:
{warehouse_options[source_warehouse_id]}

Product:
{product_options[selected_product_id]}

Current Qty:
{source_qty}

Available Qty:
{source_available}
"""
        )



    with c2:

        st.success(
f"""
📥 DESTINATION STOCK

Warehouse:
{warehouse_options[dest_warehouse_id]}

Product:
{product_options[selected_product_id]}

Current Qty:
{dest_qty}

Available Qty:
{dest_available}
"""
        )



    if source_available <= 0:

        st.error(
            "No available stock."
        )
        return



    # ==================================================
    # TRANSFER QTY
    # ==================================================

    transfer_qty = st.number_input(

        "Transfer Quantity",

        min_value=1,

        max_value=int(source_available),

        value=1

    )



    # ==================================================
    # PREVIEW
    # ==================================================

    st.subheader(
        "📊 Transfer Preview"
    )


    p1,p2 = st.columns(2)


    with p1:

        st.metric(

            "After Source Stock",

            source_qty - transfer_qty,

            delta=f"-{transfer_qty}"

        )


    with p2:

        st.metric(

            "After Destination Stock",

            dest_qty + transfer_qty,

            delta=f"+{transfer_qty}"

        )



    # ==================================================
    # EXECUTE
    # ==================================================

    if st.button(
        "🚚 Execute Transfer",
        type="primary"
    ):


        try:


            # Reduce Source

            supabase.table(
                "warehouse_stock"
            ).update(

                {
                    "qty":
                    source_qty-transfer_qty,

                    "available_qty":
                    source_available-transfer_qty
                }

            ).eq(
                "warehouse_id",
                source_warehouse_id
            ).eq(
                "product_id",
                selected_product_id
            ).execute()



            # Add Destination

            if dest_stock:


                supabase.table(
                    "warehouse_stock"
                ).update(

                    {
                        "qty":
                        dest_qty+transfer_qty,

                        "available_qty":
                        dest_available+transfer_qty
                    }

                ).eq(
                    "warehouse_id",
                    dest_warehouse_id
                ).eq(
                    "product_id",
                    selected_product_id
                ).execute()



            else:


                supabase.table(
                    "warehouse_stock"
                ).insert(

                    {
                        "warehouse_id":
                        dest_warehouse_id,

                        "product_id":
                        selected_product_id,

                        "qty":
                        transfer_qty,

                        "available_qty":
                        transfer_qty
                    }

                ).execute()



            st.success(
                "✅ Stock transfer completed."
            )


            st.rerun()



        except Exception as e:


            log_error(
                f"warehouse transfer error: {e}"
            )

            st.error(
                str(e)
            )




if __name__ == "__main__":

    run()
