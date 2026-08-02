# ==============================================================================
# erp_pages/inventory/product_form.py
# MOBILE INVENTORY v3
# ERP ENTERPRISE PRODUCT REGISTRATION
# ==============================================================================


import streamlit as st


from database import (
    get_inventory_service,
    get_categories,
    get_suppliers,
    get_warehouses
)



# ==============================================================================
# LOAD OPTIONS
# ==============================================================================


def load_options():


    categories = get_categories()

    suppliers = get_suppliers()

    warehouses = get_warehouses()


    return (
        categories or [],
        suppliers or [],
        warehouses or []
    )



# ==============================================================================
# NEW PRODUCT FORM
# ==============================================================================


def render_new_product_form(barcode):


    st.divider()


    st.subheader(
        "🆕 New Product Registration"
    )


    categories, suppliers, warehouses = load_options()



    category_map = {

        c["id"]: c["name"]

        for c in categories

    }


    supplier_map = {

        s["id"]: s["name"]

        for s in suppliers

    }


    warehouse_map = {

        w["id"]: w["name"]

        for w in warehouses

    }



    with st.form(
        "mobile_product_form"
    ):



        st.text_input(
            "📷 Barcode",
            value=barcode,
            disabled=True
        )


        name = st.text_input(
            "📝 Product Name"
        )


        sku = st.text_input(
            "🏷 SKU"
        )



        col1, col2 = st.columns(2)



        with col1:

            purchase_price = st.number_input(
                "💰 Purchase Price",
                min_value=0.0
            )


            markup = st.number_input(
                "📈 Markup %",
                min_value=0.0,
                value=20.0
            )


        with col2:


            selling_price = st.number_input(
                "💵 Selling Price",
                min_value=0.0
            )


            stock = st.number_input(
                "📦 Opening Stock",
                min_value=0,
                step=1
            )



        category_id = st.selectbox(

            "📂 Category",

            options=list(category_map.keys()),

            format_func=lambda x:
                category_map[x]

        ) if category_map else None




        supplier_id = st.selectbox(

            "🏭 Supplier",

            options=list(supplier_map.keys()),

            format_func=lambda x:
                supplier_map[x]

        ) if supplier_map else None



        warehouse_id = st.selectbox(

            "🏬 Warehouse",

            options=list(warehouse_map.keys()),

            format_func=lambda x:
                warehouse_map[x]

        ) if warehouse_map else None




        unit = st.selectbox(

            "Unit",

            [
                "pcs",
                "box",
                "kg",
                "liter"
            ]

        )



        save = st.form_submit_button(
            "💾 Save Product"
        )



        if save:


            if not name:

                st.error(
                    "Product name required"
                )

                return



            product_data = {


                "name":
                    name,


                "barcode":
                    barcode,


                "sku":
                    sku,


                "purchase_price":
                    purchase_price,


                "selling_price":
                    selling_price,


                "final_selling_price":
                    selling_price,


                "markup_percent":
                    markup,


                "category_id":
                    category_id,


                "supplier_id":
                    supplier_id,


                "unit":
                    unit,


                "stock":
                    stock

            }



            try:


                service = (
                    get_inventory_service()
                )


                result = (

                    service
                    .create_product_with_stock(

                        product_data,

                        opening_stock=stock,

                        warehouse_id=warehouse_id

                    )

                )



                if result.get("success"):


                    st.success(
                        "✅ Product Saved Successfully"
                    )


                    st.session_state.mobile_product = (
                        result["data"]
                    )


                    st.rerun()



                else:


                    st.error(
                        result.get(
                            "message",
                            "Save failed"
                        )
                    )



            except Exception as e:


                st.error(
                    f"Error: {e}"
                )
