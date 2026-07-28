# ==============================================================================
# erp_pages/pos/product.py
# ERP ENTERPRISE POS PRODUCT MODULE v12.0
#
# RESPONSIBILITY
#
# Product Loading
# Product Search
# Barcode / SKU Search
# Product Selection
# Stock Validation
#
# Flow:
#
# POS
#  ↓
# Product Loader
#  ↓
# Repository
#  ↓
# Database
#
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





# ==============================================================================
# MONEY FORMAT
# ==============================================================================


def money(value):

    try:

        return f"{float(value):,.0f} MMK"


    except Exception:

        return "0 MMK"







# ==============================================================================
# LOAD PRODUCTS
# ==============================================================================


def load_pos_products(
    warehouse_id=None
) -> List[Dict[str, Any]]:

    """
    POS Product Source

    Single Source Of Truth

    """

    try:

        return get_pos_products(

            warehouse_id=warehouse_id

        ) or []


    except Exception as e:


        st.error(

            f"Product Load Error: {e}"

        )


        return []







# ==============================================================================
# SEARCH ENGINE
# ==============================================================================


def search_products(

    products,

    keyword=""

):


    if not keyword:

        return products



    keyword = str(
        keyword
    ).lower().strip()



    result = []



    for product in products:


        name = str(
            product.get(
                "name",
                ""
            )
        ).lower()



        sku = str(
            product.get(
                "sku",
                ""
            )
        ).lower()



        barcode = str(
            product.get(
                "barcode",
                ""
            )
        ).lower()



        if (

            keyword in name

            or

            keyword in sku

            or

            keyword in barcode

        ):

            result.append(product)



    return result







# ==============================================================================
# STOCK CHECK
# ==============================================================================


def check_stock(

    product,

    qty

):


    available = int(

        product.get(

            "available_qty",

            0

        )

    )


    return qty <= available







# ==============================================================================
# PRODUCT LABEL
# ==============================================================================


def product_label(product):


    return (

        f"{product.get('sku','')} | "

        f"{product.get('name','')} | "

        f"Stock: "

        f"{product.get('available_qty',0)} | "

        f"{money(product.get('final_selling_price',0))}"

    )







# ==============================================================================
# FIND PRODUCT
# ==============================================================================


def get_product_by_id(

    products,

    product_id

):


    for product in products:


        if int(product.get("id")) == int(product_id):

            return product



    return None







# ==============================================================================
# PRODUCT UI
# ==============================================================================


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



    col1, col2 = st.columns(2)



    with col1:


        name_search = st.text_input(

            "Product Name"

        )



    with col2:


        code_search = st.text_input(

            "SKU / Barcode"

        )





    keyword = (

        name_search

        or

        code_search

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



        st.info(

            f"""

Product:

{selected.get('name')}



Price:

{money(

selected.get(

'final_selling_price',

selected.get(

'selling_price',

0

)

)

)}



Price Source:

{selected.get(

'price_source',

'SYSTEM'

)}







Available Stock:

{selected.get(

'available_qty',

0

)}

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


            else:


                cart_item = {


                    "id":

                        selected.get("id"),



                    "name":

                        selected.get("name"),



                    "sku":

                        selected.get("sku"),



                    "qty":

                        int(qty),



                    "selling_price":

                        float(

                            selected.get(

                                "final_selling_price",

                                selected.get(

                                    "selling_price",

                                    0

                                )

                            )

                        ),



                    "price_source":

                        selected.get(

                            "price_source",

                            "SYSTEM"

                        )


                }



                st.session_state.cart.append(

                    cart_item

                )


                st.success(

                    "Added to cart"

                )


                st.rerun()





    return products
