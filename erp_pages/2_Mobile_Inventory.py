# ==============================================================================
# MOBILE INVENTORY v12 STABLE
# CAMERA ON/OFF + AUTO SEARCH + MANUAL BARCODE
# ==============================================================================

import io
import streamlit as st
from PIL import Image

# Barcode decoder
try:
    from pyzbar.pyzbar import decode
    PYZBAR_OK = True
except Exception:
    PYZBAR_OK = False

from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


# ------------------------------------------------------------------------------
# CAMERA SCAN
# ------------------------------------------------------------------------------

def scan_barcode_from_camera():
    if not PYZBAR_OK:
        st.error(
            'pyzbar / zbar library မရှိပါ။ packages.txt တွင် libzbar0 ထည့်ပါ။'
        )
        return None

    photo = st.camera_input('📷 Scan barcode')

    if photo is None:
        return None

    image = Image.open(io.BytesIO(photo.getvalue()))
    codes = decode(image)

    if codes:
        return codes[0].data.decode('utf-8')

    st.warning('❌ Barcode not detected. Try again.')
    return None


# ------------------------------------------------------------------------------
# LOAD PRODUCT
# ------------------------------------------------------------------------------

def load_product(barcode):
    if not barcode:
        return

    barcode = str(barcode).strip()
    product = search_product(barcode)

    st.session_state.barcode_value = barcode
    st.session_state.product = product


# ------------------------------------------------------------------------------
# MAIN PAGE
# ------------------------------------------------------------------------------

def run():

    st.title('📦 Mobile Inventory')
    st.caption('📷 Camera Scan + Manual Barcode')

    # Session state
    if 'camera_on' not in st.session_state:
        st.session_state.camera_on = False

    if 'barcode_value' not in st.session_state:
        st.session_state.barcode_value = ''

    if 'product' not in st.session_state:
        st.session_state.product = None

    # --------------------------------------------------------------------------
    # CAMERA CONTROL
    # --------------------------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        if st.button('📷 Camera ON', use_container_width=True):
            st.session_state.camera_on = True
            st.rerun()

    with col2:
        if st.button('🛑 Camera OFF', use_container_width=True):
            st.session_state.camera_on = False
            st.rerun()

    # --------------------------------------------------------------------------
    # CAMERA SCAN AUTO SEARCH
    # --------------------------------------------------------------------------

    if st.session_state.camera_on:

        st.success('📷 Camera ON - point to barcode')

        scanned = scan_barcode_from_camera()

        if scanned:

            st.success(f'✅ Scanned: {scanned}')

            # AUTO SEARCH
            load_product(scanned)

    else:

        st.info('Camera OFF')

    st.divider()

    # --------------------------------------------------------------------------
    # MANUAL BARCODE
    # --------------------------------------------------------------------------

    barcode = st.text_input(
        '📷 Manual Barcode / SKU',
        value=st.session_state.barcode_value,
        placeholder='Type barcode manually'
    )

    # AUTO SEARCH WHEN MANUAL INPUT CHANGES
    if barcode and barcode != st.session_state.barcode_value:
        load_product(barcode)

    # Use session value after auto search
    barcode = st.session_state.barcode_value
    product = st.session_state.product

    # --------------------------------------------------------------------------
    # PRODUCT DISPLAY
    # --------------------------------------------------------------------------

    if product:

        st.divider()
        st.subheader('📦 Product Found')

        st.write('**Name:**', product.get('name', '-'))
        st.write('**Barcode:**', product.get('barcode', '-'))
        st.write('**SKU:**', product.get('sku', '-'))
        st.write('**Purchase Price:**', product.get('purchase_price', 0))
        st.write('**Selling Price:**', product.get('selling_price', 0))
        st.write('**Stock:**', product.get('stock', 0))

    # --------------------------------------------------------------------------
    # NEW PRODUCT
    # --------------------------------------------------------------------------

    elif barcode:

        st.divider()
        st.subheader('🆕 New Product Registration')

        render_new_product_form(barcode)


if __name__ == '__main__':
    run()
