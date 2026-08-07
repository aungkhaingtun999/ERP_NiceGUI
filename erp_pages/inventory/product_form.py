# ==============================================================================
# ERP ENTERPRISE PRODUCT FORM v13
#
# Compatible:
# - create_product_full RPC
# - Owner First Pricing
# - Warehouse Stock
# ==============================================================================


import streamlit as st


from erp_core.context import CacheManager



# ------------------------------------------------------------------------------
# SAVE MESSAGE
# ------------------------------------------------------------------------------


def show_saved_message():

    if "product_saved_message" in st.session_state:

        st.success(
            st.session_state.product_saved_message
        )

        del st.session_state.product_saved_message





# ------------------------------------------------------------------------------
# NEW PRODUCT FORM
# ------------------------------------------------------------------------------


def render_new_product_form(
    db_client,
    pricing_service,
    warehouse_id,
    barcode=None
):


    show_saved_message()


    st.subheader(
        "🆕 New Product Registration"
    )



    name = st.text_input(
        "Product Name"
    )


    barcode_value = st.text_input(
        "Barcode",
        value=barcode or ""
    )


    sku = st.text_input(
        "SKU"
    )



    purchase_price = st.number_input(
        "Purchase Price",
        min_value=0.0,
        step=100.0
    )



    owner_price = st.number_input(
        "👑 Owner Selling Price",
        min_value=0.0,
        step=100.0
    )



    opening_stock = st.number_input(
        "Opening Stock",
        min_value=0,
        step=1
    )



    unit = st.selectbox(
        "Unit",
        [
            "pcs",
            "kg",
            "box"
        ]
    )




    if st.button(
        "💾 Save Product",
        use_container_width=True
    ):



        if not name:


            st.warning(
                "Please enter product name"
            )

            return



        try:



            # --------------------------------------------------
            # PRICE ENGINE
            # --------------------------------------------------


            if owner_price > 0:


                final_price = owner_price

                price_source = "OWNER_PRICE"


            else:


                preview = (
                    pricing_service
                    .calculate_selling_price(
                        cost=purchase_price,
                        product_id=None
                    )
                )


                final_price = preview.get(
                    "selling_price",
                    purchase_price
                )


                price_source = preview.get(
                    "markup_source",
                    "DEFAULT"
                )





            payload = {


                "name":
                name,


                "barcode":
                barcode_value,


                "sku":
                sku,


                "purchase_price":
                purchase_price,


                "selling_price":
                final_price,


                "owner_selling_price":
                owner_price if owner_price > 0 else None,


                "final_selling_price":
                final_price,


                "price_source":
                price_source,


                "unit":
                unit,


                "category_id":
                1


            }




            response = (

                db_client

                .rpc(

                    "create_product_full",

                    {


                        "p_data":
                        payload,


                        "p_warehouse_id":
                        int(warehouse_id),


                        "p_initial_qty":
                        int(opening_stock)

                    }

                )

                .execute()

            )




            result = response.data



            if isinstance(
                result,
                list
            ):

                result=result[0]




            if result.get(
                "success"
            ):


                st.session_state.product_saved_message = (

                    "✅ Product saved successfully!"

                )


                CacheManager.bump(
                    "inventory_version"
                )


                CacheManager.bump(
                    "product_version"
                )


                st.cache_data.clear()


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
                f"❌ Error: {e}"
            )
