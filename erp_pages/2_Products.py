# ==============================================================================
# erp_pages/2_Products.py
# ERP ENTERPRISE PRODUCT PRICING CONTROL v4.0
#
# OWNER PRICE PRIORITY ENGINE
#
# OWNER MANUAL PRICE
#        ↓
# PRODUCT MARKUP
#        ↓
# CATEGORY MARKUP
#        ↓
# GLOBAL MARKUP
#
# ==============================================================================


import streamlit as st

from decimal import Decimal

from erp_core.base_repo import db



# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(

    page_title="Product Pricing Control",

    page_icon="📦",

    layout="wide"

)



# ==============================================================================
# DATABASE CLIENT
# ==============================================================================

client = db()



# ==============================================================================
# LOAD PRODUCTS
# ==============================================================================


@st.cache_data(ttl=60)

def load_products():


    try:


        result = (

            client

            .table("products")

            .select(

                """
                id,
                name,
                sku,
                barcode,

                purchase_price,

                selling_price,

                owner_selling_price,

                final_selling_price,

                price_source,

                markup_percent,

                category_id

                """

            )

            .order(

                "name"

            )

            .execute()

        )


        return result.data or []



    except Exception as e:


        st.error(

            f"Product Load Error : {e}"

        )


        return []





# ==============================================================================
# LOAD CATEGORY
# ==============================================================================


@st.cache_data(ttl=300)

def get_category(category_id):


    if not category_id:


        return {


            "name":

                "-",

            "markup":

                None


        }




    try:


        result = (

            client

            .table("categories")

            .select(

                """

                name,

                markup_percent

                """

            )

            .eq(

                "id",

                category_id

            )

            .execute()

        )



        if result.data:


            row = result.data[0]


            return {


                "name":

                    row.get(
                        "name",
                        "-"
                    ),


                "markup":

                    row.get(
                        "markup_percent"
                    )


            }



    except Exception:


        pass




    return {


        "name":

            "-",


        "markup":

            None


    }





# ==============================================================================
# GET GLOBAL MARKUP SETTING
# ==============================================================================


def get_global_markup():


    try:


        result = (

            client

            .table("settings")

            .select(

                "value"

            )

            .eq(

                "key",

                "DEFAULT_MARKUP_PERCENT"

            )

            .execute()

        )



        if result.data:


            return Decimal(

                str(

                    result.data[0]

                    .get(
                        "value",
                        0
                    )

                )

            )



    except Exception:


        pass



    # IMPORTANT
    # NO HARD CODE DEFAULT

    return Decimal("0")





# ==============================================================================
# PRICE CALCULATION PREVIEW
# ==============================================================================


def calculate_preview_price(product):


    cost = Decimal(

        str(

            product.get(

                "purchase_price",

                0

            )
            or 0

        )

    )



    # --------------------------------------------------
    # OWNER PRICE FIRST
    # --------------------------------------------------


    owner_price = product.get(

        "owner_selling_price"

    )


    if owner_price is not None:


        return {


            "price":

                Decimal(

                    str(owner_price)

                ),


            "source":

                "OWNER"


        }





    # --------------------------------------------------
    # PRODUCT MARKUP
    # --------------------------------------------------


    product_markup = product.get(

        "markup_percent"

    )



    if product_markup is not None:


        price = (

            cost +

            (

                cost *

                Decimal(

                    str(product_markup)

                )

                /

                Decimal("100")

            )

        )



        return {


            "price":

                price.quantize(
                    Decimal("0.01")
                ),


            "source":

                "PRODUCT_MARKUP"


        }





    # --------------------------------------------------
    # CATEGORY MARKUP
    # --------------------------------------------------


    category = get_category(

        product.get(

            "category_id"

        )

    )


    category_markup = category.get(

        "markup"

    )


    if category_markup is not None:


        price = (

            cost +

            (

                cost *

                Decimal(

                    str(category_markup)

                )

                /

                Decimal("100")

            )

        )


        return {


            "price":

                price.quantize(
                    Decimal("0.01")
                ),


            "source":

                "CATEGORY_MARKUP"


        }





    # --------------------------------------------------
    # GLOBAL MARKUP
    # --------------------------------------------------


    global_markup = get_global_markup()



    if global_markup > 0:


        price = (

            cost +

            (

                cost *

                global_markup

                /

                Decimal("100")

            )

        )


        return {


            "price":

                price.quantize(
                    Decimal("0.01")
                ),


            "source":

                "GLOBAL_MARKUP"


        }





    return {


        "price":

            Decimal(

                str(

                    product.get(

                        "selling_price",

                        0

                    )
                    or 0

                )

            ),


        "source":

            "CURRENT_PRICE"


    }
    # ==============================================================================
# MAIN UI
# ==============================================================================


st.title(
    "📦 Product Pricing Control"
)


st.caption(
    """
ERP Enterprise Pricing Engine

Owner Manual Price
        ↓
Product Markup
        ↓
Category Markup
        ↓
Global Markup
"""
)



# ==============================================================================
# LOAD PRODUCTS
# ==============================================================================


products = load_products()



if not products:


    st.warning(
        "No Products Found"
    )


    st.stop()





# ==============================================================================
# SEARCH PRODUCT
# ==============================================================================


search = st.text_input(

    "🔍 Search Product"

)




filtered_products = products



if search:


    filtered_products = [

        p

        for p in products

        if search.lower()

        in

        p.get(
            "name",
            ""
        )
        .lower()

    ]




# ==============================================================================
# PRODUCT SELECT
# ==============================================================================


product_map = {


    f"{p['id']} - {p['name']}":

        p


    for p in filtered_products


}




selected_product = st.selectbox(

    "📦 Select Product",

    list(

        product_map.keys()

    )

)




product = product_map[

    selected_product

]




# ==============================================================================
# CATEGORY
# ==============================================================================


category = get_category(

    product.get(

        "category_id"

    )

)





# ==============================================================================
# PRICE ENGINE PREVIEW
# ==============================================================================


preview = calculate_preview_price(

    product

)



final_preview_price = preview["price"]

preview_source = preview["source"]





# ==============================================================================
# PRODUCT INFORMATION
# ==============================================================================


st.divider()


st.subheader(

    "📊 Product Information"

)



c1, c2, c3, c4 = st.columns(4)



with c1:


    st.metric(

        "Purchase Cost",

        f"{float(product.get('purchase_price') or 0):,.0f}"

    )



with c2:


    st.metric(

        "Current Selling",

        f"{float(product.get('selling_price') or 0):,.0f}"

    )



with c3:


    st.metric(

        "Owner Price",

        (

            f"{float(product.get('owner_selling_price')):,.0f}"

            if product.get(
                "owner_selling_price"
            )

            else

            "Not Set"

        )

    )



with c4:


    st.metric(

        "Final Price",

        f"{float(final_preview_price):,.0f}"

    )





# ==============================================================================
# PRICING SOURCE
# ==============================================================================


source_color = {


    "OWNER":

        "🟢 OWNER MANUAL PRICE",


    "PRODUCT_MARKUP":

        "🟡 PRODUCT MARKUP",


    "CATEGORY_MARKUP":

        "🔵 CATEGORY MARKUP",


    "GLOBAL_MARKUP":

        "🟣 GLOBAL MARKUP",


    "CURRENT_PRICE":

        "⚪ CURRENT SELLING PRICE"


}




st.success(

    f"""
### Pricing Decision

Source:

{source_color.get(
    preview_source,
    preview_source
)}


Final Selling Price:

{float(final_preview_price):,.2f}

"""

)





# ==============================================================================
# OWNER PRICE CONTROL
# ==============================================================================


st.divider()


st.subheader(

    "👑 Owner Manual Selling Price"

)



st.caption(

    """
Owner Price has highest priority.

If Owner Price exists:
System will ignore automatic markup calculation.
"""

)




current_owner_price = product.get(

    "owner_selling_price"

)




owner_price = st.number_input(

    "💰 Set Owner Selling Price",

    min_value=0.0,

    value=float(

        current_owner_price or 0

    ),

    step=100.0

)





# ==============================================================================
# MARKUP INFORMATION
# ==============================================================================


st.divider()


st.subheader(

    "⚙ Pricing Rule Preview"

)



col1, col2, col3 = st.columns(3)



with col1:


    st.info(

        f"""
Product Markup

{
    product.get(
        'markup_percent'
    )
    or 0
}%

"""

    )




with col2:


    st.info(

        f"""
Category

{category.get('name')}


Category Markup

{
    category.get(
        'markup'
    )
    or 0
}%

"""

    )




with col3:


    global_markup = get_global_markup()


    st.info(

        f"""
Global Markup

{global_markup}%

"""

    )
    
    # ==============================================================================
# OWNER PRICE SAVE ENGINE
# ==============================================================================


st.divider()

st.subheader(
    "💾 Save Pricing"
)



col_save1, col_save2 = st.columns(2)



# ==============================================================================
# SAVE OWNER PRICE
# ==============================================================================


with col_save1:


    if st.button(
        "👑 Save Owner Price",
        type="primary",
        use_container_width=True
    ):


        try:


            result = client.rpc(

                "save_owner_product_price_rpc",

                {

                    "p_product_id":
                        product["id"],

                    "p_owner_price":
                        owner_price

                }

            ).execute()



            st.success(

                result.data

            )


            st.cache_data.clear()


            st.rerun()



        except Exception as e:


            st.error(

                f"Save Owner Price Failed : {e}"

            )




# ==============================================================================
# RESET OWNER PRICE
# ==============================================================================


with col_save2:


    if st.button(

        "♻ Reset Owner Price",

        use_container_width=True

    ):


        try:


            result = client.rpc(

                "save_owner_product_price_rpc",

                {

                    "p_product_id":
                        product["id"],

                    "p_owner_price":
                        None

                }

            ).execute()



            st.success(

                result.data

            )


            st.cache_data.clear()


            st.rerun()



        except Exception as e:


            st.error(

                f"Reset Failed : {e}"

            )





# ==============================================================================
# RECALCULATE FINAL PRICE
# ==============================================================================


st.divider()


st.subheader(

    "🔄 Pricing Engine Test"

)



if st.button(

    "⚙ Calculate Final Selling Price",

    use_container_width=True

):


    try:


        result = client.rpc(

            "calculate_final_product_price_rpc",

            {

                "p_product_id":

                    product["id"]

            }

        ).execute()



        st.success(

            result.data

        )


        st.cache_data.clear()


        st.rerun()



    except Exception as e:


        st.error(

            f"Calculation Failed : {e}"

        )





# ==============================================================================
# FINAL DATABASE STATUS
# ==============================================================================


st.divider()


st.subheader(

    "📌 Database Pricing Status"

)



st.json(

    {

        "Product ID":

            product.get("id"),


        "Owner Price":

            product.get(
                "owner_selling_price"
            ),


        "Final Price":

            product.get(
                "final_selling_price"
            ),


        "Price Source":

            product.get(
                "price_source"
            ),


        "Selling Price":

            product.get(
                "selling_price"
            )

    }

)
# ==============================================================================
# PART 4
# OWNER PRICE CSV BULK UPLOAD
# ==============================================================================


st.divider()

st.subheader(
    "📥 Owner Manual Price CSV Import"
)


st.caption(
    """
Fast Pricing Setup

CSV Format:

product_id,owner_selling_price

Example:

2,1500
37,2000
15,11500

Owner Price has highest priority.
"""
)



# ==============================================================================
# TEMPLATE DOWNLOAD
# ==============================================================================


import pandas as pd
from io import BytesIO



template_df = pd.DataFrame(

    [

        {

            "product_id":
                "",

            "owner_selling_price":
                ""

        }

    ]

)



template_buffer = BytesIO()


template_df.to_csv(

    template_buffer,

    index=False

)


template_buffer.seek(0)



st.download_button(

    label="📄 Download Owner Price CSV Template",

    data=template_buffer,

    file_name="owner_price_template.csv",

    mime="text/csv",

    use_container_width=True

)





# ==============================================================================
# CSV UPLOAD
# ==============================================================================


uploaded_file = st.file_uploader(

    "Upload Owner Price CSV",

    type=["csv"]

)



if uploaded_file:


    try:


        df = pd.read_csv(

            uploaded_file

        )



        required_columns = [

            "product_id",

            "owner_selling_price"

        ]



        missing = [

            c

            for c in required_columns

            if c not in df.columns

        ]



        if missing:


            st.error(

                f"Missing Columns : {missing}"

            )


            st.stop()



        st.dataframe(

            df,

            use_container_width=True

        )



        if st.button(

            "🚀 Import Owner Prices",

            type="primary",

            use_container_width=True

        ):



            success_count = 0

            fail_count = 0

            errors = []



            for _, row in df.iterrows():



                try:



                    product_id = int(

                        row["product_id"]

                    )


                    owner_price = float(

                        row["owner_selling_price"]

                    )



                    result = client.rpc(

                        "save_owner_product_price_rpc",

                        {

                            "p_product_id":

                                product_id,


                            "p_owner_price":

                                owner_price

                        }

                    ).execute()



                    if result.data:


                        success_count += 1


                    else:


                        fail_count += 1



                except Exception as e:


                    fail_count += 1


                    errors.append(

                        {

                            "product_id":

                                row.get(
                                    "product_id"
                                ),


                            "error":

                                str(e)

                        }

                    )





            st.success(

                f"""
✅ Import Completed

Success :
{success_count}

Failed :
{fail_count}
"""

            )



            if errors:


                st.error(

                    "Import Errors"

                )


                st.dataframe(

                    errors,

                    use_container_width=True

                )



            st.cache_data.clear()



            st.rerun()



    except Exception as e:


        st.error(

            f"CSV Error : {e}"

        )





# ==============================================================================
# END STATUS
# ==============================================================================


st.divider()


st.success(

    """
🚀 Owner Pricing System Ready


Priority:

👑 Owner Manual Price

        ↓

🟡 Product Markup

        ↓

🔵 Category Markup

        ↓

🟣 Global Default Markup


ERP Pricing Engine Active

"""

)
