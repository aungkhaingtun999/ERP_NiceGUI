# ==============================================================================
# erp_pages/pos/product.py
# ERP ENTERPRISE POS PRODUCT MODULE v12.8 FINAL
# TWO SEARCH BOX + CART FIX
# ==============================================================================

from typing import List, Dict, Any

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
# LOAD PRODUCTS
# ==============================================================================

def load_pos_products(
    warehouse_id=None
) -> List[Dict[str, Any]]:

    try:

        return get_pos_products(
            warehouse_id=warehouse_id
        ) or []


    except Exception as e:

        st.error(
            f"Product Load Error : {e}"
        )

        return []



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

def product_label(product):

    price = get_final_price(
        product
    )

    return (

        f"{product.get('sku','NO-SKU')} | "

        f"{product.get('name','')} | "

        f"Stock:{product.get('available_qty',0)} | "

        f"{money(price.get('price',0))}"

    )



# ==============================================================================
# PRODUCT UI
# ==============================================================================

def render_products(
    warehouse_id
):


    # Ensure cart exists

    if "cart" not in st.session_state:

        st.session_state.cart = []



    products = load_pos_products(
        warehouse_id
    )


    if not products:

        st.warning(
            "No products found"
        )

        return []



    # --------------------------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------------------------

    st.subheader(
        "🔍 Product Search"
    )


    col1, col2 = st.columns(2)



    with col1:

        name_search = st.text_input(

            "🔍 Product Name",

            key="pos_name_search_box"

        )



    with col2:

        barcode_search = st.text_input(

            "📦 SKU / Barcode",

            key="pos_barcode_search_box"

        )



    # --------------------------------------------------------------------------
    # FILTER
    # --------------------------------------------------------------------------

    matches = []


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



        name_ok = True

        code_ok = True



        if name_search:

            name_ok = (

                name_search.lower()

                in

                name

            )



        if barcode_search:

            key = barcode_search.lower()


            code_ok = (

                key in sku

                or

                key in barcode

            )



        if name_ok and code_ok:

            matches.append(
                product
            )



    if not matches:

        st.warning(
            "Product not found"
        )

        return products



    # --------------------------------------------------------------------------
    # SELECT
    # --------------------------------------------------------------------------

    selected = st.selectbox(

        "Select Product",

        matches,

        format_func=product_label,

        key="pos_product_selectbox"

    )



    qty = st.number_input(

        "Quantity",

        min_value=1,

        value=1,

        step=1,

        key="pos_product_qty"

    )



    # --------------------------------------------------------------------------
    # INFO
    # --------------------------------------------------------------------------

    if selected:


        price_data = get_final_price(
            selected
        )


        st.info(

            f"""
**Product:** {selected.get('name')}

**Price:** {money(price_data.get('price',0))}

**Price Source:** {price_data.get('source','SYSTEM')}

**Available Stock:** {selected.get('available_qty',0)}
"""

        )



        # ----------------------------------------------------------------------
        # ADD CART
        # ----------------------------------------------------------------------

        if st.button(

            "➕ Add To Cart",

            use_container_width=True,

            key="pos_add_cart_button"

        ):


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

                float(
                    price_data.get(
                        "price",
                        0
                    )
                ),

                price_data.get(
                    "source",
                    "SYSTEM"
                )

            )


            st.session_state.cart = (
                st.session_state.cart
            )


            st.success(
                f"{selected.get('name')} added to cart"
            )


            st.rerun()



    return products
