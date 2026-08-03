# ==============================================================================
# MOBILE INVENTORY v3
# FORM TEST MODE
# ==============================================================================

import streamlit as st

from erp_pages.inventory.product_form import (
    render_new_product_form
)


def run():

    st.title(
        "📦 Mobile Inventory"
    )

    st.caption(
        "🆕 Product Registration Test"
    )


    test_barcode = "TEST123456"


    st.success(
        f"Barcode : {test_barcode}"
    )


    render_new_product_form(
        test_barcode
    )


if __name__ == "__main__":

    run()
