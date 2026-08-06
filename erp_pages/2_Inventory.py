# ==============================================================================
# pages/2_Inventory.py
# ERP ENTERPRISE PRODUCT MASTER v5.0
# MOBILE INVENTORY EDITION
# ==============================================================================


import time

import streamlit as st
import pandas as pd


# ==============================================================================
# DATABASE BRIDGE
# ==============================================================================

from database import (
    db,
    get_inventory_view,
    get_warehouses,
    update_product_rpc,
)


# ==============================================================================
# ERP CORE SERVICES
# ==============================================================================

from erp_core.context import CacheManager

from erp_core.services.inventory_service import (
    InventoryService
)

from erp_core.services.pricing_service import (
    PricingService
)


# ==============================================================================
# UI
# ==============================================================================

from utils.ui import show_table



# ==============================================================================
# PAGE RUNNER
# ==============================================================================


def run():


    st.title(
        "🏭 Enterprise Product Master v5.0"
    )

    st.caption(
        "ERP Inventory Control Center | Mobile Ready"
    )


    # ==========================================================================
    # SESSION
    # ==========================================================================

    if "inventory_barcode" not in st.session_state:

        st.session_state.inventory_barcode = ""



    # ==========================================================================
    # SERVICE INITIALIZATION
    # ==========================================================================

    try:

        client = db()

        inventory_service = InventoryService(
            client
        )

        pricing_service = PricingService(
            client
        )


    except Exception as e:

        st.error(
            f"ERP Service Connection Failed : {e}"
        )

        st.stop()



    # ==========================================================================
    # WAREHOUSE SELECTOR
    # ==========================================================================


    warehouses = get_warehouses()


    if not warehouses:

        st.error(
            "No active warehouses found"
        )

        st.stop()



    warehouse_map = {

        w.get("name"):
        w.get("id")

        for w in warehouses

    }


    selected_wh_name = st.selectbox(

        "📍 Select Warehouse",

        list(
            warehouse_map.keys()
        )

    )


    selected_wh_id = warehouse_map[
        selected_wh_name
    ]



    # ==========================================================================
    # BARCODE SEARCH AREA
    # ==========================================================================


    st.divider()

    st.subheader(
        "📷 Mobile Barcode Search"
    )


    col1, col2 = st.columns(
        [4,1]
    )


    with col1:

        barcode_input = st.text_input(

            "Barcode / SKU",

            value=
            st.session_state.inventory_barcode,

            placeholder=
            "Scan or type barcode"

        )


    with col2:

        st.write("")

        if st.button(
            "Clear",
            use_container_width=True
        ):

            st.session_state.inventory_barcode = ""

            st.rerun()



    if barcode_input:

        st.session_state.inventory_barcode = barcode_input



    # ==========================================================================
    # PRODUCT LOAD
    # ==========================================================================


    search = barcode_input.strip()



    try:

        products = get_inventory_view(

            warehouse_id=
            selected_wh_id,

            search=
            search

        )


    except Exception as e:

        st.error(
            f"Product loading error : {e}"
        )

        products = []



    # ==========================================================================
    # TABS
    # ==========================================================================


    tab1, tab2, tab3, tab4, tab5 = st.tabs(

        [

            "📋 Product Master",

            "➕ Add Product",

            "✏️ Edit Product",

            "🔧 Stock Adjustment",

            "📊 Dashboard"

        ]

    )

    # ==========================================================================
    # TAB 1 - PRODUCT MASTER
    # ==========================================================================

    with tab1:

        st.subheader(
            "📋 Product Master"
        )


        if products:

            show_table(products)

        else:

            st.info(
                "No products found"
            )



    # ==========================================================================
    # TAB 2 - ADD PRODUCT
    # ==========================================================================

    with tab2:

        st.subheader(
            "➕ Add New Product"
        )


        with st.form(
            "add_product_form",
            clear_on_submit=True
        ):


            c1, c2 = st.columns(2)


            with c1:

                name = st.text_input(
                    "Product Name *"
                )


                sku = st.text_input(
                    "SKU *"
                )


                purchase_price = st.number_input(
                    "Purchase Cost",
                    min_value=0.0,
                    value=0.0
                )


                minimum_stock = st.number_input(
                    "Minimum Stock",
                    min_value=0,
                    value=5
                )



            with c2:

                barcode = st.text_input(
                    "Barcode",
                    value=
                    st.session_state.inventory_barcode
                )


                unit = st.selectbox(

                    "Unit",

                    [
                        "pcs",
                        "kg",
                        "box"
                    ]

                )


                initial_qty = st.number_input(

                    "Initial Stock Qty",

                    min_value=0,

                    value=0

                )



            # ==============================================================
            # PRICING ENGINE PREVIEW
            # ==============================================================


            preview = {}


            if purchase_price > 0:


                try:

                    preview = (
                        pricing_service
                        .calculate_selling_price(

                            cost=
                            purchase_price,

                            product_id=None

                        )
                    )


                    st.info(

f"""
💰 Pricing Preview

Cost:
{purchase_price:,.2f} MMK


Markup:
{preview.get('final_markup_percent',0)} %


Selling Price:
{preview.get('selling_price',0):,.2f} MMK


Source:
{preview.get('markup_source')}
"""

                    )


                except Exception as e:

                    st.warning(
                        f"Pricing Preview Error : {e}"
                    )



            submit = st.form_submit_button(

                "💾 Create Product",

                use_container_width=True

            )



            if submit:


                try:


                    payload = {


                        "name":
                        name,


                        "sku":
                        sku,


                        "barcode":
                        barcode,


                        "purchase_price":
                        purchase_price,


                        "selling_price":

                        preview.get(

                            "selling_price",

                            purchase_price

                        ),


                        "unit":
                        unit,


                        "minimum_stock":
                        minimum_stock,


                        "category_id":
                        1

                    }



                    response = (

                        db()

                        .rpc(

                            "create_product_full",

                            {

                                "p_data":
                                payload,


                                "p_warehouse_id":
                                int(selected_wh_id),


                                "p_initial_qty":
                                int(initial_qty)

                            }

                        )

                        .execute()

                    )



                    result = response.data



                    if isinstance(
                        result,
                        list
                    ):

                        result = result[0]



                    if result.get(
                        "success"
                    ):


                        st.success(

                            "✅ Product Created Successfully"

                        )


                        CacheManager.bump(
                            "inventory_version"
                        )


                        CacheManager.bump(
                            "product_version"
                        )


                        st.cache_data.clear()


                        time.sleep(1)


                        st.rerun()



                    else:


                        st.error(

                            result.get(

                                "message",

                                "Create Failed"

                            )

                        )



                except Exception as e:


                    st.error(

                        f"Create Product Error : {e}"

                    )

    # ==========================================================================
    # TAB 3 - EDIT PRODUCT
    # ==========================================================================

    with tab3:

        st.subheader(
            "✏️ Edit Product Master"
        )


        if not products:

            st.info(
                "No product available"
            )


        else:


            product_map = {

                f"{p.get('id')} | {p.get('name')}":
                p

                for p in products

            }



            selected_product_name = st.selectbox(

                "Select Product",

                list(
                    product_map.keys()
                ),

                key="edit_product_select"

            )


            selected_product = product_map[
                selected_product_name
            ]



            with st.form(

                f"edit_product_{selected_product.get('id')}"

            ):


                c1, c2 = st.columns(2)



                with c1:


                    name = st.text_input(

                        "Product Name",

                        value=
                        selected_product.get(
                            "name",
                            ""
                        )

                    )


                    sku = st.text_input(

                        "SKU",

                        value=
                        selected_product.get(
                            "sku",
                            ""
                        )

                    )


                    purchase_price = st.number_input(

                        "Purchase Cost",

                        value=float(

                            selected_product.get(
                                "purchase_price",
                                0
                            )

                        )

                    )



                    minimum_stock = st.number_input(

                        "Minimum Stock",

                        value=int(

                            selected_product.get(
                                "minimum_stock",
                                0
                            )

                        )

                    )



                with c2:


                    barcode = st.text_input(

                        "Barcode",

                        value=
                        selected_product.get(
                            "barcode",
                            ""
                        )

                    )


                    selling_price = st.number_input(

                        "Selling Price",

                        value=float(

                            selected_product.get(
                                "selling_price",
                                0
                            )

                        )

                    )


                    unit_options = [

                        "pcs",
                        "kg",
                        "box"

                    ]


                    current_unit = (

                        selected_product.get(
                            "unit",
                            "pcs"
                        )

                    )


                    unit = st.selectbox(

                        "Unit",

                        unit_options,

                        index=

                        unit_options.index(
                            current_unit
                        )
                        if current_unit in unit_options
                        else 0

                    )



                notes = st.text_area(

                    "Notes",

                    value=
                    selected_product.get(
                        "notes",
                        ""
                    )

                )



                update = st.form_submit_button(

                    "💾 Update Product",

                    use_container_width=True

                )



                if update:


                    try:


                        result = update_product_rpc(

                            product_id=
                            selected_product.get(
                                "id"
                            ),

                            name=name,

                            sku=sku,

                            barcode=barcode,

                            purchase_price=
                            purchase_price,

                            selling_price=
                            selling_price,

                            minimum_stock=
                            minimum_stock,

                            unit=unit,

                            notes=notes,

                            is_active=True

                        )



                        if result.get(
                            "success"
                        ):


                            st.success(

                                "✅ Product Updated"

                            )


                            CacheManager.bump(
                                "product_version"
                            )


                            time.sleep(1)

                            st.rerun()


                        else:


                            st.error(

                                result.get(

                                    "message",

                                    "Update Failed"

                                )

                            )


                    except Exception as e:


                        st.error(

                            f"Update Error : {e}"

                        )





# ==============================================================================
# TAB 4 - ENTERPRISE STOCK ADJUSTMENT + MAKER CHECKER WORKFLOW
# ==============================================================================

    with tab4:

    st.subheader("🔧 Enterprise Stock Adjustment")

    if not products:
        st.warning("No products available.")

    else:

        product_map = {
            f"{p.get('id')} | {p.get('name')}": p
            for p in products
        }

        selected_name = st.selectbox(
            "📦 Select Product",
            list(product_map.keys()),
            key="stock_adjust_product"
        )

        selected_product = product_map[selected_name]

        product_id = int(selected_product.get("id"))

        current_qty = (
            selected_product.get("available_qty")
            or selected_product.get("qty")
            or selected_product.get("stock")
            or 0
        )

        st.info(
            f"""
📦 Product: {selected_product.get('name')}

🏭 Warehouse: {selected_wh_name}

📊 Current Stock: {current_qty}
"""
        )

        adjustment_type = st.selectbox(
            "Adjustment Type",
            ["DAMAGE", "COUNT_CORRECTION", "MANUAL_IN", "MANUAL_OUT"]
        )

        qty = st.number_input(
            "Quantity (+/-)",
            value=0,
            step=1
        )

        reason = st.text_input(
            "Reason",
            value="Manual Adjustment"
        )

        if st.button(
            "💾 Submit Adjustment",
            use_container_width=True
        ):

            if qty == 0:
                st.warning("Quantity cannot be zero")
                st.stop()

            try:

                result = inventory_service.adjust_stock(
                    product_id=product_id,
                    warehouse_id=int(selected_wh_id),
                    quantity=int(qty),
                    reason=reason,
                    created_by=st.session_state.get("user_id"),
                    unit_cost=float(selected_product.get("purchase_price", 0))
                )

                if result.get("success"):

                    st.success("✅ Adjustment Submitted (PENDING)")

                    st.cache_data.clear()

                    time.sleep(1)

                    st.rerun()

                else:

                    st.error(result.get("message", "Adjustment Failed"))

            except Exception as e:

                st.error(f"Adjustment Error : {e}")

        st.divider()

        st.subheader("⏳ Pending Approvals")

        try:

            history = inventory_service.get_stock_adjustments(
                warehouse_id=int(selected_wh_id)
            )

            current_user = str(
                st.session_state.get("user_id", "")
            )

            pending_rows = [
                h for h in history
                if str(h.get("status", "")).upper() == "PENDING"
            ]

            if not pending_rows:

                st.success("No pending stock adjustments")

            else:

                for row in pending_rows:

                    with st.container(border=True):

                        st.write(f"**ID:** {row.get('id')}")
                        st.write(f"**Qty:** {row.get('qty')}")
                        st.write(f"**Reason:** {row.get('reason')}")
                        st.write(f"**Requested:** {row.get('created_at')}")
                        st.write(f"**Requested By:** {row.get('requested_by')}")
                        st.write(f"**Status:** {row.get('status')}")
                        st.write("---")

                        maker_user = str(
                            row.get("requested_by", "")
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            if current_user == maker_user:

                                st.caption(
                                    "🚫 Maker cannot approve own request"
                                )

                            else:

                                if st.button(
                                    f"✅ Approve #{row.get('id')}",
                                    key=f"approve_{row.get('id')}",
                                    use_container_width=True
                                ):

                                    res = inventory_service.approve_stock_adjustment(
                                        adjustment_id=int(row.get("id")),
                                        manager_id=current_user
                                    )

                                    if res.get("success"):

                                        st.success(
                                            f"Adjustment #{row.get('id')} approved"
                                        )

                                        st.cache_data.clear()

                                        time.sleep(1)

                                        st.rerun()

                                    else:

                                        st.error(
                                            res.get("message", "Approve failed")
                                        )

                        with col2:

                            if st.button(
                                f"❌ Cancel #{row.get('id')}",
                                key=f"cancel_{row.get('id')}",
                                use_container_width=True
                            ):

                                cancel_res = (
                                    db()
                                    .rpc(
                                        "cancel_stock_adjustment_rpc",
                                        {
                                            "p_adjustment_id": int(row.get("id")),
                                            "p_user_id": current_user
                                        }
                                    )
                                    .execute()
                                )

                                cancel_data = cancel_res.data

                                if isinstance(cancel_data, list):
                                    cancel_data = cancel_data[0]

                                if cancel_data.get("success"):

                                    st.success(
                                        f"Adjustment #{row.get('id')} cancelled"
                                    )

                                    st.cache_data.clear()

                                    time.sleep(1)

                                    st.rerun()

                                else:

                                    st.error(
                                        cancel_data.get("message", "Cancel failed")
                                    )

            st.divider()

            st.subheader("📜 Adjustment History")

            if history:
                show_table(history)
            else:
                st.info("No adjustment history found")

        except Exception as e:

            st.error(f"History Load Error : {e}")
    
    # ==========================================================================
    # TAB 5 - ENTERPRISE INVENTORY DASHBOARD
    # ==========================================================================

    with tab5:


        st.subheader(
            "📊 Enterprise Inventory Dashboard"
        )


        st.caption(
            f"Current Warehouse : {selected_wh_name}"
        )



        # ----------------------------------------------------------------------
        # INVENTORY KPI
        # ----------------------------------------------------------------------

        st.divider()

        st.subheader(
            "🏭 Inventory KPI"
        )


        try:


            kpi = inventory_service.get_inventory_kpi()



            if kpi.get("success") is False:


                st.error(

                    kpi.get(
                        "message",
                        "KPI Loading Failed"
                    )

                )


            else:


                c1, c2, c3, c4, c5 = st.columns(5)



                c1.metric(

                    "📦 Products",

                    kpi.get(
                        "total_products",
                        0
                    )

                )


                c2.metric(

                    "🏭 Warehouses",

                    kpi.get(
                        "total_warehouses",
                        0
                    )

                )


                c3.metric(

                    "📊 Stock Qty",

                    kpi.get(
                        "total_stock_qty",
                        0
                    )

                )


                c4.metric(

                    "💰 Inventory Value",

                    f"{float(kpi.get('total_inventory_value',0)):,.0f} MMK"

                )


                c5.metric(

                    "⚠ Low Stock",

                    kpi.get(
                        "low_stock_items",
                        0
                    )

                )



        except Exception as e:


            st.error(
                f"KPI Error : {e}"
            )




        # ----------------------------------------------------------------------
        # WAREHOUSE INVENTORY
        # ----------------------------------------------------------------------

        st.divider()


        st.subheader(
            "🏭 Warehouse Inventory"
        )


        try:


            warehouse_data = (
                inventory_service
                .get_warehouse_inventory_kpi()
            )



            if warehouse_data:


                show_table(
                    warehouse_data
                )


            else:


                st.info(
                    "No warehouse data"
                )



        except Exception as e:


            st.error(
                f"Warehouse KPI Error : {e}"
            )




        # ----------------------------------------------------------------------
        # FIFO VALUATION
        # ----------------------------------------------------------------------

        st.divider()


        st.subheader(
            "💰 FIFO Inventory Valuation"
        )



        try:


            valuation = (
                inventory_service
                .get_inventory_valuation()
            )


            if valuation:


                show_table(
                    valuation
                )


            else:


                st.info(
                    "No FIFO layers found"
                )



        except Exception as e:


            st.error(
                f"FIFO Error : {e}"
            )




        # ----------------------------------------------------------------------
        # INVENTORY LOSS
        # ----------------------------------------------------------------------

        st.divider()


        st.subheader(
            "📉 Inventory Loss Analytics"
        )



        try:


            loss_data = (
                inventory_service
                .get_inventory_loss_report()
            )



            if loss_data:


                show_table(
                    loss_data
                )


            else:


                st.success(
                    "No inventory loss detected"
                )



        except Exception as e:


            st.error(
                f"Loss Analytics Error : {e}"
            )




        # ----------------------------------------------------------------------
        # STOCK CARD
        # ----------------------------------------------------------------------

        st.divider()


        st.subheader(
            "📜 Stock Card"
        )



        if products:


            product_map = {


                f"{p.get('id')} | {p.get('name')}":
                p


                for p in products

            }



            stock_product_name = st.selectbox(

                "Select Product For Stock Card",

                list(
                    product_map.keys()
                ),

                key="stock_card_product"

            )



            stock_product = product_map[
                stock_product_name
            ]



            stock_card = inventory_service.get_stock_card(

                product_id=int(

                    stock_product.get(
                        "id"
                    )

                ),

                warehouse_id=int(
                    selected_wh_id
                )

            )



            if stock_card:


                show_table(
                    stock_card
                )


            else:


                st.info(
                    "No stock movement history"
                )




        # ----------------------------------------------------------------------
        # HEALTH CHECK
        # ----------------------------------------------------------------------

        st.divider()


        st.subheader(
            "🩺 Inventory Service Health"
        )


        try:


            health = inventory_service.health_check()


            st.json(
                health
            )


        except Exception as e:


            st.error(
                str(e)
            )




# ==============================================================================
# APP ENTRY
# ==============================================================================


if __name__ == "__main__":

    run()
