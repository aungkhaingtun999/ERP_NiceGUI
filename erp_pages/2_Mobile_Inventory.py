# ==============================================================================
# MOBILE INVENTORY v3
# LIVE BARCODE INVENTORY
# ==============================================================================


import streamlit as st


from erp_pages.inventory.zxing_scanner import (
    scan_barcode
)


from erp_pages.inventory.product_search import (
    search_product
)



def run():


    st.title(
        "📦 Mobile Inventory v3"
    )


    st.caption(
        "📷 Live Barcode Scanner • Mobile Optimized"
    )



    if "mobile_product" not in st.session_state:

        st.session_state.mobile_product = None



    barcode = scan_barcode()



    if barcode:


        st.success(
            f"Barcode: {barcode}"
        )



        product = search_product(
            barcode
        )


        if product:

            st.session_state.mobile_product = product


        else:

    st.session_state.new_barcode = barcode

    st.warning(
        "🆕 New Product Barcode"
    )


    product = st.session_state.mobile_product



    if product:


        st.divider()


        st.subheader(
            f"📦 {product.get('name')}"
        )


        st.write(
            f"Barcode : {product.get('barcode')}"
        )


        st.write(
            f"Stock : {product.get('stock')}"
        )


        st.write(
            f"Selling Price : {product.get('selling_price')}"
        )



    else:


        st.info(
            "📷 Point the camera at a barcode"
        )



if __name__ == "__main__":

    run()
