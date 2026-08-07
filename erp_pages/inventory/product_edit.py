# ==============================================================================
# erp_pages/inventory/product_edit.py
# ERP ENTERPRISE INVENTORY PRODUCT EDIT v1.0
#
# Product Master Update Component
#
# Owner Price Compatible
#
# ==============================================================================


import time

import streamlit as st


from erp_core.context import CacheManager


from database import (
    update_product_rpc
)




# ==============================================================================
# RENDER PRODUCT EDIT
# ==============================================================================


def render_product_edit(

    selected_wh_id

):


    st.subheader(
        "✏️ Edit Product Master"
    )



    try:


        from database import (
            get_inventory_view
        )


        products = get_inventory_view(

            warehouse_id=selected_wh_id,

            search=None

        )


    except Exception as e:


        st.error(

            f"Product Load Error : {e}"

        )

        return




    if not products:


        st.info(
            "No product available"
        )

        return




    product_map = {


        f"{p.get('id')} | {p.get('name')}":

        p


        for p in products


    }




    selected_name = st.selectbox(

        "Select Product",

        list(product_map.keys()),

        key="edit_product_selector"

    )



    selected_product = product_map[

        selected_name

    ]





    with st.form(

        f"edit_product_{selected_product.get('id')}"

    ):



        col1, col2 = st.columns(2)




        with col1:



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

                    or 0

                )

            )




            minimum_stock = st.number_input(

                "Minimum Stock",

                value=int(

                    selected_product.get(

                        "minimum_stock",

                        0

                    )

                    or 0

                )

            )





        with col2:



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

                    or 0

                )

            )





            owner_price = st.number_input(

                "👑 Owner Price (Main)",

                value=float(

                    selected_product.get(

                        "owner_selling_price",

                        0

                    )

                    or 0

                )

            )




            unit = st.selectbox(

                "Unit",

                [

                    "pcs",

                    "kg",

                    "box"

                ],

                index=

                [

                    "pcs",

                    "kg",

                    "box"

                ].index(

                    selected_product.get(

                        "unit",

                        "pcs"

                    )

                )

                if selected_product.get(

                    "unit"

                ) in [

                    "pcs",

                    "kg",

                    "box"

                ]

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





        if selected_product.get(

            "owner_price_locked",

            False

        ):


            st.warning(

                "🔒 Owner Price Locked"

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



                    unit=

                    unit,



                    notes=

                    notes,



                    is_active=True

                )





                if result.get(

                    "success"

                ):


                    st.success(

                        "✅ Product Updated Successfully"

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

                            "Update Failed"

                        )

                    )





            except Exception as e:


                st.error(

                    f"Update Error : {e}"

                )
