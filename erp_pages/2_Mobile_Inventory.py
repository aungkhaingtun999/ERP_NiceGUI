import streamlit as st

from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():

    st.title("📦 Mobile Inventory")

    st.caption("📷 Barcode Search Test")

    barcode = st.text_input(
        "📷 Scanned Barcode",
        placeholder="Scan barcode and paste here"
    )

    if barcode:

        st.success(
            f"Barcode : {barcode}"
        )

        if st.button(
            "🔍 Search Product",
            use_container_width=True
        ):

            product = search_product(
                barcode
            )

            if product:

                st.subheader(
                    "📦 Product Found"
                )

                st.write(
                    f"Name : {product.get('name','-')}"
                )

                st.write(
                    f"Barcode : {product.get('barcode','-')}"
                )

                st.write(
                    f"SKU : {product.get('sku','-')}"
                )

                st.write(
                    f"Purchase Price : {product.get('purchase_price',0)}"
                )

                st.write(
                    f"Selling Price : {product.get('selling_price',0)}"
                )

                st.write(
                    f"Stock : {product.get('stock',0)}"
                )

            else:

                st.warning(
                    "Barcode not found - Create New Product"
                )

                render_new_product_form(
                    barcode
                )

    else:

        st.info(
            "Enter or scan a barcode"
        )


if __name__ == "__main__":

    run()
