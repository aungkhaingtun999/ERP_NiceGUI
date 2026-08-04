# ==============================================================================
# erp_pages/2_Mobile_Inventory.py
# MOBILE INVENTORY v4
# CAMERA SNAPSHOT + BARCODE SEARCH + NEW PRODUCT
# ==============================================================================

import streamlit as st

from erp_pages.inventory.scanner import get_barcode
from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():

    st.title('📦 Mobile Inventory')

    st.caption('📷 Camera Barcode Scanner')


    if 'barcode_value' not in st.session_state:
        st.session_state.barcode_value = ''


    if 'product' not in st.session_state:
        st.session_state.product = None


    st.info('Tap **Take Photo** and point the camera at the barcode.')


    scanned = get_barcode()


    if scanned and isinstance(scanned, str):

        st.session_state.barcode_value = scanned.strip()


    barcode = st.text_input(
        '📷 Barcode',
        key='barcode_value'
    )


    if st.button(
        '🔍 Search Product',
        use_container_width=True
    ):


        if barcode:


            product = search_product(barcode)


            if product:


                st.session_state.product = product


            else:


                st.session_state.product = None


                st.warning(
                    'Barcode not found - Create New Product'
                )


    if st.session_state.product:


        product = st.session_state.product


        st.success('📦 Product Found')


        st.write('Name:', product.get('name', '-'))

        st.write('Barcode:', product.get('barcode', '-'))

        st.write('SKU:', product.get('sku', '-'))

        st.write('Purchase Price:', product.get('purchase_price', 0))

        st.write('Selling Price:', product.get('selling_price', 0))

        st.write('Stock:', product.get('stock', 0))


    elif barcode:


        st.divider()

        st.subheader('🆕 New Product Registration')

        render_new_product_form(barcode)


if __name__ == '__main__':
    run()
