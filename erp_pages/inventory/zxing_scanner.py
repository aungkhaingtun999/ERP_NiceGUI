import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import io


def zxing_scanner():

    photo = st.camera_input("📷 Take barcode photo")

    if photo is None:
        return None

    image = Image.open(io.BytesIO(photo.getvalue()))

    codes = decode(image)

    if codes:
        return codes[0].data.decode("utf-8")

    st.warning("❌ Barcode not detected. Try again.")
    return None
