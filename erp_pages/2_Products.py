# ==============================================================================
# erp_pages/2_Products.py
# ERP ENTERPRISE PRODUCT PRICING CONTROL
# ==============================================================================


import streamlit as st

from decimal import Decimal

from erp_core.base_repo import db


st.set_page_config(
    page_title="Products",
    layout="wide"
)



# ==========================================================
# CLIENT
# ==========================================================

client = db()



# ==========================================================
# LOAD PRODUCTS
# ==========================================================

def load_products():

    result = (
        client
        .table("products")
        .select(
            """
            id,
            name,
            sku,
            purchase_price,
            selling_price,
            markup_percent,
            category_id
            """
        )
        .order(
            "id"
        )
        .execute()
    )

    return result.data or []



# ==========================================================
# CATEGORY
# ==========================================================

def get_category(category_id):

    if not category_id:

        return {
            "name": "-",
            "markup": None
        }


    result = (
        client
        .table("categories")
        .select(
            "name,markup_percent"
        )
        .eq(
            "id",
            category_id
        )
        .execute()
    )


    if result.data:

        return {

            "name":
                result.data[0]["name"],

            "markup":
                result.data[0]["markup_percent"]

        }


    return {
        "name":"-",
        "markup":None
    }



# ==========================================================
# TITLE
# ==========================================================


st.title(
    "📦 Product Pricing Control"
)



products = load_products()



if not products:

    st.warning(
        "No Products Found"
    )

    st.stop()



# ==========================================================
# SEARCH
# ==========================================================


search = st.text_input(
    "🔍 Search Product"
)



if search:


    products = [

        p for p in products

        if search.lower()
        in p["name"].lower()

    ]



product_map = {

    f'{p["id"]} - {p["name"]}':
    p

    for p in products

}



selected = st.selectbox(

    "Select Product",

    list(product_map.keys())

)



product = product_map[selected]



category = get_category(

    product.get(
        "category_id"
    )

)



# ==========================================================
# PRICING PANEL
# ==========================================================


st.divider()


col1,col2,col3 = st.columns(3)



with col1:

    st.metric(

        "Purchase Cost",

        f'{product.get("purchase_price",0):,.2f}'

    )



with col2:

    st.metric(

        "Current Selling",

        f'{product.get("selling_price",0):,.2f}'

    )



with col3:

    st.metric(

        "Product Markup",

        f'{product.get("markup_percent") or 0}%'

    )



st.subheader(
    "⚙️ Pricing Engine Preview"
)



c1,c2,c3 = st.columns(3)



with c1:

    st.write(
        "Product Markup"
    )

    st.info(
        f'{product.get("markup_percent") or 0}%'
    )



with c2:

    st.write(
        "Category"
    )

    st.info(
        category["name"]
    )



with c3:

    st.write(
        "Category Markup"
    )

    st.info(
        f'{category["markup"] or 0}%'
    )



# ==========================================================
# AUTO CALCULATION
# ==========================================================


cost = Decimal(

    str(
        product.get(
            "purchase_price",
            0
        )
    )

)


markup = Decimal(

    str(

        product.get(
            "markup_percent"
        )
        or
        category["markup"]
        or
        20

    )

)


auto_price = (

    cost +

    (
        cost *
        markup /
        Decimal("100")
    )

)



st.success(

    f"Auto Selling Price: {auto_price:,.2f}"

)



# ==========================================================
# MANUAL OVERRIDE
# ==========================================================


manual_price = st.number_input(

    "Manual Selling Price Override",

    min_value=0.0,

    value=float(
        product.get(
            "selling_price",
            auto_price
        )
    )

)



# ==========================================================
# SAVE
# ==========================================================


if st.button(
    "💾 Save Pricing",
    type="primary"
):


    result = client.rpc(

        "update_product_pricing_rpc",

        {

            "p_product_id":
                product["id"],

            "p_selling_price":
                manual_price,

            "p_markup_percent":
                product.get(
                    "markup_percent"
                )

        }

    ).execute()



    st.success(
        result.data
    )

    st.cache_data.clear()

    st.rerun()
