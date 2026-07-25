# ==============================================================================
# pages/2_Products.py
# ERP ENTERPRISE PRODUCT MANAGEMENT v1.0
# Pricing Control + Markup Engine UI
# ==============================================================================


import streamlit as st

from decimal import Decimal


from erp_core import (
    get_products
)


from erp_core.base_repo import (
    db
)


from erp_core.context import (
    CacheManager
)



# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="Products Management",
    page_icon="📦",
    layout="wide"
)



# ==============================================================================
# HELPERS
# ==============================================================================

def money(value):

    try:

        return f"{Decimal(str(value)):,.2f} MMK"

    except:

        return "0.00 MMK"



def calculate_preview(
    cost,
    markup
):

    try:

        cost = Decimal(str(cost))

        markup = Decimal(str(markup))


        return (
            cost +
            (
                cost *
                markup /
                Decimal("100")
            )
        )


    except:

        return Decimal("0")



# ==============================================================================
# UPDATE PRODUCT
# ==============================================================================

def update_product_price(
    product_id,
    purchase_price,
    selling_price,
    markup_percent
):

    try:

        result = (
            db()
            .table("products")
            .update(
                {

                    "purchase_price":
                        float(purchase_price),


                    "selling_price":
                        float(selling_price),


                    "markup_percent":
                        float(markup_percent)

                }
            )
            .eq(
                "id",
                product_id
            )
            .execute()
        )


        CacheManager.bump_version(
            "inventory_version"
        )


        return True


    except Exception as e:

        st.error(
            f"Update failed: {e}"
        )

        return False



# ==============================================================================
# MAIN
# ==============================================================================

def run():


    st.title(
        "📦 Product Management"
    )


    st.caption(
        "Pricing Control | Markup Engine | Manual Override"
    )



    # --------------------------------------------------------------------------
    # LOAD PRODUCTS
    # --------------------------------------------------------------------------

    products = get_products(
        limit=500
    )


    if not products:

        st.warning(
            "No products found"
        )

        return



    # --------------------------------------------------------------------------
    # SELECT PRODUCT
    # --------------------------------------------------------------------------

    product_names = {

        f"{p.get('name')} (ID:{p.get('id')})":
            p

        for p in products

    }


    selected = st.selectbox(

        "Select Product",

        options=list(product_names.keys())

    )


    product = product_names[selected]



    st.divider()



    # --------------------------------------------------------------------------
    # PRODUCT INFO
    # --------------------------------------------------------------------------

    st.subheader(
        "📋 Product Information"
    )


    col1,col2,col3 = st.columns(3)


    with col1:

        st.metric(
            "Product",
            product.get("name")
        )


    with col2:

        st.metric(
            "Current Cost",
            money(
                product.get(
                    "purchase_price",
                    0
                )
            )
        )


    with col3:

        st.metric(
            "Current Selling",
            money(
                product.get(
                    "selling_price",
                    0
                )
            )
        )



    st.divider()



    # --------------------------------------------------------------------------
    # PRICING CONTROL
    # --------------------------------------------------------------------------

    st.subheader(
        "💰 Pricing Control"
    )


    purchase_price = st.number_input(

        "Purchase Price",

        value=float(
            product.get(
                "purchase_price",
                0
            )
        ),

        step=100.0

    )



    markup = st.number_input(

        "Markup %",

        value=float(
            product.get(
                "markup_percent",
                0
            )
            or 0
        ),

        min_value=0.0,

        step=1.0

    )



    preview = calculate_preview(

        purchase_price,

        markup

    )



    st.info(
        f"🔍 Selling Price Preview : {money(preview)}"
    )



    manual_override = st.checkbox(

        "✏️ Manual Override Selling Price",

        value=False

    )



    if manual_override:


        selling_price = st.number_input(

            "Manual Selling Price",

            value=float(
                product.get(
                    "selling_price",
                    preview
                )
            ),

            step=100.0

        )


    else:

        selling_price = preview



    st.divider()



    # --------------------------------------------------------------------------
    # SAVE
    # --------------------------------------------------------------------------

    if st.button(

        "💾 Save Product Pricing",

        type="primary",

        use_container_width=True

    ):


        success = update_product_price(

            product["id"],

            purchase_price,

            selling_price,

            markup

        )


        if success:

            st.success(
                "✅ Product pricing updated successfully"
            )

            st.rerun()



# ==============================================================================
# RUN
# ==============================================================================

if __name__ == "__main__":

    run()