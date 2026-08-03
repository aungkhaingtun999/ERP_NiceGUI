import streamlit as st

from erp_pages.inventory.zxing_scanner import scan_barcode


def run():

    st.title("📦 Barcode Test")


    barcode = scan_barcode()


    st.write(
        "VALUE:",
        repr(barcode)
    )


    st.write(
        "TYPE:",
        type(barcode).__name__
    )


    if barcode:

        st.success(
            f"Barcode: {barcode}"
        )


if __name__ == "__main__":
    run()
