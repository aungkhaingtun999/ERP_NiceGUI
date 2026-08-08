# ==============================================================================
# erp_pages/inventory/product_create.py
# ERP ENTERPRISE INVENTORY PRODUCT CREATE v1.2
#
# Owner First Pricing Compatible
#
# ==============================================================================


import time
import streamlit as st


from erp_core.context import CacheManager



# ==============================================================================
# PRODUCT CREATE
# ==============================================================================


def render_product_create(
    db_client,
    pricing_service,
    warehouse_id,
):


    st.subheader(
        "➕ Add New Product"
    )



    with st.form(
        "add_product_form",
        clear_on_submit=True
    ):


        c1, c2 = st.columns(2)



        # ----------------------------------------------------------------------
        # LEFT
        # ----------------------------------------------------------------------

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



        # ----------------------------------------------------------------------
        # RIGHT
        # ----------------------------------------------------------------------

        with c2:


            barcode = st.text_input(
                "Barcode"
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


            owner_price = st.number_input(
                "Owner Selling Price (Main)",
                min_value=0.0,
                value=0.0
            )




        # ======================================================================
        # PRICING ENGINE
        # ======================================================================


        preview = {

            "selling_price":
            purchase_price,

            "final_markup_percent":
            0,

            "markup_source":
            "PURCHASE_COST"

        }




        if purchase_price > 0:


            try:


                # --------------------------------------------------------------
                # OWNER FIRST
                # --------------------------------------------------------------

                if owner_price > 0:


                    preview = {

                        "selling_price":
                        owner_price,


                        "final_markup_percent":
                        0,


                        "markup_source":
                        "OWNER_PRICE"

                    }



                else:


                    result = (
                        pricing_service
                        .calculate_selling_price(
                        cost=purchase_price,
                        product_id=None
                        )
                )

# ------------------------------------------------------------------
# PRICING SERVICE RESPONSE NORMALIZATION
#
# PricingService may return:
#   1. dict
#   2. numeric selling price
# ------------------------------------------------------------------

if isinstance(result, dict):

    preview = result

elif isinstance(result, (int, float)):

    calculated_price = float(result)

    markup_percent = (
        ((calculated_price - purchase_price)
         / purchase_price) * 100
        if purchase_price > 0
        else 0
    )

    preview = {
        "selling_price":
            calculated_price,

        "final_markup_percent":
            markup_percent,

        "markup_source":
            "PRICING_SERVICE"
    }

else:

    raise ValueError(
        "Invalid pricing service response."
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




        # ======================================================================
        # SUBMIT
        # ======================================================================


        submit = st.form_submit_button(

            "💾 Create Product",

            use_container_width=True

        )



        if submit:


            try:


                final_price = preview.get(

                    "selling_price",

                    purchase_price

                )



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
                    final_price,



                    "owner_selling_price":

                    owner_price
                    if owner_price > 0
                    else None,



                    "final_selling_price":
                    final_price,



                    "price_source":

                    preview.get(
                        "markup_source",
                        "DEFAULT"
                    ),



                    "unit":
                    unit,



                    "minimum_stock":
                    minimum_stock,



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
