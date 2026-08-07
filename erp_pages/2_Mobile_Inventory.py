# ==============================================================================
# 2_Mobile_Inventory.py
# MOBILE INVENTORY ENTERPRISE v1.0
#
# ZXING PRIMARY BARCODE SCANNER
# PRODUCT SEARCH
# PRODUCT REGISTRATION
#
# ==============================================================================


import streamlit as st



# ==============================================================================
# SCANNER
# ==============================================================================


from erp_pages.inventory.zxing_scanner import (
    zxing_scanner
)



# ==============================================================================
# DATABASE
# ==============================================================================


from database import (
    get_warehouses
)


from erp_pages.inventory.warehouse import (
    render_warehouse_selector
)



# ==============================================================================
# PRODUCT MODULES
# ==============================================================================


from erp_pages.inventory.product_search import (
    search_product
)



import erp_pages.inventory.product_form as product_form





# ==============================================================================
# SESSION INITIALIZATION
# ==============================================================================


def initialize_session_state():


    defaults = {


        "mobile_barcode":

        "",


        "mobile_product":

        None,


        "mobile_warehouse_id":

        None,


        "mobile_scanner_active":

        False,


    }



    for key, value in defaults.items():


        if key not in st.session_state:


            st.session_state[key] = value







# --------------------------------------------------------------------------
# Warehouse
# --------------------------------------------------------------------------

warehouses = get_warehouses()


warehouse_id, warehouse_name = render_warehouse_selector(
    warehouses
)


st.session_state.mobile_warehouse_id = warehouse_id
                





# ==============================================================================
# BARCODE SEARCH
# ==============================================================================


def load_product_by_barcode(barcode):


    if not barcode:


        return




    try:


        product = search_product(

            barcode

        )



        st.session_state.mobile_product = product




    except Exception as e:


        st.error(

            f"Product Search Error : {e}"

        )

        st.session_state.mobile_product = None







# ==============================================================================
# SCANNER HANDLER
# ==============================================================================


def handle_zxing_scan():



    barcode = zxing_scanner()



    if barcode:



        if barcode != st.session_state.mobile_barcode:



            st.session_state.mobile_barcode = barcode



            load_product_by_barcode(

                barcode

            )



            st.rerun()

# ==============================================================================
# PRODUCT RESULT VIEW
# ==============================================================================


def render_product_view():


    product = st.session_state.get(
        "mobile_product"
    )


    barcode = st.session_state.get(
        "mobile_barcode",
        ""
    )



    # --------------------------------------------------------------------------
    # PRODUCT FOUND
    # --------------------------------------------------------------------------


    if product:


        st.divider()


        st.subheader(
            "📦 Product Found"
        )



        col1, col2 = st.columns(2)



        with col1:


            st.write(
                f"**Name:** {product.get('name','N/A')}"
            )


            st.write(
                f"**Barcode:** {product.get('barcode','N/A')}"
            )


            st.write(
                f"**SKU:** {product.get('sku','N/A')}"
            )



        with col2:


            st.write(

                f"**Stock:** {product.get('stock',0)}"

            )


            st.write(

                f"**Selling Price:** "
                f"{float(product.get('selling_price',0) or 0):,.2f} MMK"

            )



        st.success(
            "✅ Product loaded successfully"
        )




    # --------------------------------------------------------------------------
    # NOT FOUND
    # --------------------------------------------------------------------------


    elif barcode:


        st.divider()


        st.warning(
            "Product not found"
        )


        st.info(
            "You can register this barcode as a new product."
        )





    else:


        st.info(
            "📷 Scan barcode or enter SKU"
        )








# ==============================================================================
# MANUAL BARCODE INPUT
# ==============================================================================


def render_manual_search():


    barcode = st.text_input(

        "⌨️ Barcode / SKU",

        value=

        st.session_state.get(
            "mobile_barcode",
            ""
        ),

        key="mobile_manual_barcode"

    )



    if barcode != st.session_state.mobile_barcode:


        st.session_state.mobile_barcode = barcode



        if barcode:


            load_product_by_barcode(
                barcode
            )


        else:


            st.session_state.mobile_product = None



        st.rerun()








# ==============================================================================
# CLEAR FUNCTION
# ==============================================================================


def clear_mobile_inventory():


    st.session_state.mobile_barcode = ""

    st.session_state.mobile_product = None

    st.session_state.mobile_scanner_active = False

# ==============================================================================
# NEW PRODUCT REGISTRATION
# ==============================================================================


def render_new_product():


    product = st.session_state.get(
        "mobile_product"
    )


    barcode = st.session_state.get(
        "mobile_barcode",
        ""
    )



    if product:

        return



    if barcode:


        st.divider()


        st.subheader(
            "➕ Register New Product"
        )


        product_form.render_new_product_form(

            barcode

        )






# ==============================================================================
# MAIN MOBILE INVENTORY PAGE
# ==============================================================================


def run():


    st.title(
        "📦 Mobile Inventory Enterprise"
    )


    st.caption(
        "ZXING Primary Scanner | Barcode + SKU Search | Product Registration"
    )



    initialize_session_state()



    # --------------------------------------------------------------------------
    # Warehouse
    # --------------------------------------------------------------------------


    render_mobile_warehouse()



    st.divider()



    # --------------------------------------------------------------------------
    # CONTROL BUTTONS
    # --------------------------------------------------------------------------


    col1, col2 = st.columns(2)



    with col1:


        if st.button(

            "📷 Start Scanner",

            use_container_width=True,

            key="mobile_start_scanner"

        ):


            st.session_state.mobile_scanner_active = True



            st.rerun()




    with col2:


        if st.button(

            "🧹 Clear",

            use_container_width=True,

            key="mobile_clear"

        ):


            clear_mobile_inventory()


            st.rerun()





    st.divider()



    # --------------------------------------------------------------------------
    # ZXING CAMERA
    # --------------------------------------------------------------------------


    if st.session_state.mobile_scanner_active:


        st.success(
            "📷 Scanner Active"
        )


        handle_zxing_scan()



    else:


        st.info(
            "Scanner OFF"
        )





    st.divider()



    # --------------------------------------------------------------------------
    # MANUAL SEARCH
    # --------------------------------------------------------------------------


    render_manual_search()



    st.divider()



    # --------------------------------------------------------------------------
    # RESULT
    # --------------------------------------------------------------------------


    render_product_view()



    # --------------------------------------------------------------------------
    # NEW PRODUCT
    # --------------------------------------------------------------------------


    render_new_product()







# ==============================================================================
# STREAMLIT ENTRY
# ==============================================================================


if __name__ == "__main__":


    run()
