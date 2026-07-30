# ==============================================================================
# erp_pages/pos/product.py
# ERP ENTERPRISE POS PRODUCT MODULE v13.0 PERFORMANCE BUILD
#
# PART 1/2
#
# Optimization:
# - Product memory cache
# - Price cache
# - Search index
# - Fast product lookup
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



from .cart import (
    add_to_cart,
    check_available_stock
)



from .engine import (
    get_final_price
)





# ==============================================================================
# MONEY
# ==============================================================================


def money(value):

    try:

        return f"{float(value):,.0f} MMK"

    except Exception:

        return "0 MMK"






# ==============================================================================
# PRODUCT CACHE
# ==============================================================================


@st.cache_data(
    ttl=600,
    show_spinner=False
)
def load_cached_products(

    warehouse_id

):


    try:


        products = get_pos_products(

            warehouse_id

        )



        return products or []



    except Exception as e:


        st.error(

            f"Product Load Error : {e}"

        )


        return []







# ==============================================================================
# PRODUCT PRICE CACHE
# ==============================================================================


@st.cache_data(

    ttl=600,

    show_spinner=False

)
def get_cached_price(

    product_id,

    product_data

):


    try:


        return get_final_price(

            product_data

        )


    except Exception:


        return {


            "price":0,


            "source":"SYSTEM"


        }







# ==============================================================================
# BUILD SEARCH INDEX
# ==============================================================================


@st.cache_data(

    ttl=600,

    show_spinner=False

)
def build_product_index(

    products

):


    index = []



    for p in products:



        index.append(


            {


                "id":

                    p.get("id"),



                "name":

                    str(

                        p.get(

                            "name",

                            ""

                        )

                    ).lower(),



                "sku":

                    str(

                        p.get(

                            "sku",

                            ""

                        )

                    ).lower(),



                "barcode":

                    str(

                        p.get(

                            "barcode",

                            ""

                        )

                    ).lower(),



                "product":

                    p


            }


        )



    return index







# ==============================================================================
# STOCK CHECK
# ==============================================================================


def check_stock(

    product,

    qty

):


    if "cart" not in st.session_state:


        st.session_state.cart = []



    return check_available_stock(


        st.session_state.cart,


        product.get("id"),


        product.get(

            "available_qty",

            0

        ),


        int(qty)

    )







# ==============================================================================
# PRODUCT LABEL
# ==============================================================================


def product_label(

    product

):


    price_data = get_cached_price(


        product.get("id"),


        product


    )



    return (

        f"{product.get('sku','NO-SKU')} | "

        f"{product.get('name','')} | "

        f"Stock:{product.get('available_qty',0)} | "

        f"{money(price_data.get('price',0))}"

    )





# ==============================================================================
# PRODUCT UI
# ==============================================================================


def render_products(

    warehouse_id

):


    # --------------------------------------------------
    # SESSION CART
    # --------------------------------------------------

    if "cart" not in st.session_state:

        st.session_state.cart = []



    # --------------------------------------------------
    # LOAD PRODUCTS
    # --------------------------------------------------

    products = load_cached_products(

        warehouse_id

    )



    if not products:


        st.warning(

            "No products found"

        )

        return []





    # --------------------------------------------------
    # BUILD INDEX
    # --------------------------------------------------

    index = build_product_index(

        products

    )





    # --------------------------------------------------
    # SEARCH UI
    # --------------------------------------------------

    st.subheader(

        "🔍 Product Search"

    )



    col1, col2 = st.columns(2)



    with col1:


        name_search = st.text_input(

            "Product Name",

            key="pos_name_search"

        )



    with col2:


        code_search = st.text_input(

            "SKU / Barcode",

            key="pos_code_search"

        )





    # --------------------------------------------------
    # FAST FILTER
    # --------------------------------------------------

    matches = []



    name_key = name_search.lower().strip()

    code_key = code_search.lower().strip()



    for row in index:


        name_ok = True

        code_ok = True



        if name_key:


            name_ok = (

                name_key

                in

                row["name"]

            )



        if code_key:


            code_ok = (

                code_key

                in

                row["sku"]

                or

                code_key

                in

                row["barcode"]

            )



        if name_ok and code_ok:


            matches.append(

                row["product"]

            )





    if not matches:


        st.warning(

            "Product not found"

        )

        return products






    # --------------------------------------------------
    # PRODUCT SELECT & ADD TO CART (Layout Update)
    # --------------------------------------------------

    col_sel, col_btn_layout = st.columns([3, 1])

    with col_sel:
        selected = st.selectbox(
            "Select Product",
            matches,
            format_func=product_label,
            key="pos_product_select"
        )

    qty = st.number_input(
        "Quantity",
        min_value=1,
        value=1,
        step=1,
        key="pos_qty"
    )

    if selected:

        price_data = get_cached_price(

            selected.get("id"),

            selected

        )



        final_price = float(

            price_data.get(

                "price",

                0

            )

        )

        with col_btn_layout:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            
            add_clicked = st.button(
                "➕ Add",
                type="primary",
                use_container_width=True,
                key="add_cart_btn"
            )

        # --------------------------------------------------
        # PRODUCT INFO CARD (Compact View)
        # --------------------------------------------------

        st.markdown(
            f"""
            <div style="
                padding: 10px 14px;
                background-color: #f8f9fa;
                border-left: 4px solid #ff4b4b;
                border-radius: 4px;
                margin-top: 10px;
                margin-bottom: 10px;
                font-size: 14px;
                color: #31333F;
            ">
                <b>🛍 Product:</b> {selected.get('name')}<br>
                <b>💰 Price:</b> {money(final_price)}<br>
                <b>📦 Stock:</b> {selected.get('available_qty', 0)}
            </div>
            """,
            unsafe_allow_html=True
        )





        # --------------------------------------------------
        # ADD CART
        # --------------------------------------------------

        if add_clicked:



            if not check_stock(

                selected,

                qty

            ):


                st.error(

                    "Insufficient stock"

                )


                return products





            add_to_cart(


                st.session_state.cart,


                selected,


                int(qty),


                final_price,


                price_data.get(

                    "source",

                    "SYSTEM"

                )

            )




            st.session_state.cart = (

                st.session_state.cart

            )



            st.success(

                f"{selected.get('name')} added"

            )



            # No full reload

            st.rerun()





    return products
