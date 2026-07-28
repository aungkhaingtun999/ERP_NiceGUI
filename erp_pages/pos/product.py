# ==============================================================================
# erp_pages/pos/product.py
# ERP ENTERPRISE POS PRODUCT MODULE v12.2 FINAL
# ==============================================================================


from typing import (
    List,
    Dict,
    Any
)


import streamlit as st



from erp_core.loaders.product_loader import (
    get_pos_products
)


from .cart import (
    add_to_cart,
    check_available_stock
)


from .engine import (
    get_final_price
)





def money(value):

    try:
        return f"{float(value):,.0f} MMK"

    except Exception:
        return "0 MMK"





def load_pos_products(
    warehouse_id=None
):

    try:

        return get_pos_products(
            warehouse_id=warehouse_id
        ) or []


    except Exception as e:

        st.error(
            f"Product Load Error: {e}"
        )

        return []







def search_products(
    products,
    keyword=""
):


    if not keyword:
        return products



    keyword = str(keyword).lower().strip()



    return [

        p

        for p in products

        if (

            keyword in str(
                p.get("name","")
            ).lower()

            or

            keyword in str(
                p.get("sku","")
            ).lower()

            or

            keyword in str(
                p.get("barcode","")
            ).lower()

        )

    ]







def check_stock(
    product,
    qty
):


    return check_available_stock(

        st.session_state.get(
            "cart",
            []
        ),

        product.get("id"),

        product.get(
            "available_qty",
            0
        ),

        qty

    )







def product_label(product):


    price = get_final_price(product)


    return (

        f"{product.get('sku','')} | "

        f"{product.get('name','')} | "

        f"Stock:{product.get('available_qty',0)} | "

        f"{money(price['price'])}"

    )








def render_products(
    warehouse_id
):


    products = load_pos_products(
        warehouse_id
    )



    if not products:

        st.warning(
            "No Products Found"
        )

        return []




    st.subheader(
        "🔍 Product Search"
    )



    keyword = st.text_input(
        "Name / SKU / Barcode"
    )



    filtered = search_products(
        products,
        keyword
    )



    if not filtered:

        st.warning(
            "Product not found"
        )

        return products




    selected = st.selectbox(

        "Select Product",

        filtered,

        format_func=product_label

    )




    qty = st.number_input(

        "Quantity",

        min_value=1,

        value=1,

        step=1

    )




    if selected:


        price_data = get_final_price(
            selected
        )



        st.info(

            f"""

Product:
{selected.get('name')}


Price:
{money(price_data['price'])}


Source:
{price_data['source']}


Stock:
{selected.get('available_qty',0)}

"""

        )





        if st.button(
            "➕ Add To Cart",
            use_container_width=True
        ):



            if not check_stock(
                selected,
                qty
            ):

                st.error(
                    "Insufficient Stock"
                )

                return products




            add_to_cart(

                st.session_state.cart,

                selected,

                qty,

                price_data["price"],

                price_data["source"]

            )



            st.success(
                "Added to cart"
            )



            st.rerun()



    return products
