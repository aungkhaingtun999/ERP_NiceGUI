# ==============================================================================
# MOBILE INVENTORY v11 STABLE
# BUILT-IN CAMERA SCAN + MANUAL BARCODE INPUT
# ==============================================================================

import io
import streamlit as st
from PIL import Image

# pyzbar ကို optional လုပ်ထားတယ်
try:
    from pyzbar.pyzbar import decode
    PYZBAR_OK = True
except Exception:
    PYZBAR_OK = False

from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def scan_barcode_from_camera():

    if not PYZBAR_OK:
        st.error(
            'pyzbar / zbar library မရှိသေးပါ။ '
            'Streamlit Cloud မှာ packages.txt ထည့်ဖို့လိုပါတယ်။'
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


def load_product(barcode):

    if not barcode:
        return

    barcode = str(barcode).strip()

    product = search_product(barcode)

    if product:

        st.session_state.product = product
        st.session_state.barcode_value = barcode

    else:

        st.session_state.product = None

        st.warning(f'❌ Barcode not found: {barcode}')


def run():

    st.title('📦 Mobile Inventory')
    st.caption('📷 Camera Scan + Manual Barcode')

    if 'barcode_value' not in st.session_state:
        st.session_state.barcode_value = ''

    if 'product' not in st.session_state:
        st.session_state.product = None

    # --------------------------------------------------
    # CAMERA SCAN
    # --------------------------------------------------

    scanned_code = scan_barcode_from_camera()

    if scanned_code:

        st.success(f'✅ Scanned: {scanned_code}')

        load_product(scanned_code)

    st.divider()

    # --------------------------------------------------
    # MANUAL BARCODE
    # --------------------------------------------------

    barcode = st.text_input(
        '📷 Manual Barcode / SKU',
        value=st.session_state.barcode_value,
        placeholder='Type barcode manually'
    )

    if st.button('🔍 Search Product', use_container_width=True):

        if barcode:
            load_product(barcode)
        else:
            st.warning('Enter barcode first')

    # --------------------------------------------------
    # PRODUCT DISPLAY
    # --------------------------------------------------

    product = st.session_state.product

    if product:

        st.divider()
        st.subheader('📦 Product Found')

        st.write('Name:', product.get('name', '-'))
        st.write('Barcode:', product.get('barcode', '-'))
        st.write('SKU:', product.get('sku', '-'))
        st.write('Purchase:', product.get('purchase_price', 0))
        st.write('Selling:', product.get('selling_price', 0))
        st.write('Stock:', product.get('stock', 0))

    elif barcode:

        st.divider()
        st.subheader('🆕 New Product Registration')

        render_new_product_form(barcode)


if __name__ == '__main__':
    run()
