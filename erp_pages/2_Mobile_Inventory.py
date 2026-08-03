import streamlit as st
import streamlit.components.v1 as components

from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():
    st.title("📦 Mobile Inventory")
    st.caption("📷 Barcode Search Test")

    # Session State ထဲမှာ barcode သိမ်းဆည်းရန် စီစဉ်ခြင်း
    if "barcode_input" not in st.session_state:
        st.session_state["barcode_input"] = ""

    # Barcode ထည့်ရန် Input (on_change ဖြင့် Enter ခေါက်တိုင်း အလုပ်လုပ်စေရန်)
    barcode = st.text_input(
        "📷 Scanned Barcode",
        placeholder="Scan barcode and press Enter...",
        key="barcode_input"
    )

    if barcode:
        st.success(f"Barcode : {barcode}")

        # Barcode ဖြင့် ပစ္စည်းရှာမည်
        product = search_product(barcode)

        if product:
            st.subheader("📦 Product Found")
            st.write(f"Name : {product.get('name','-')}")
            st.write(f"Barcode : {product.get('barcode','-')}")
            st.write(f"SKU : {product.get('sku','-')}")
            st.write(f"Purchase Price : {product.get('purchase_price',0)}")
            st.write(f"Selling Price : {product.get('selling_price',0)}")
            st.write(f"Stock : {product.get('stock',0)}")
        else:
            st.warning("Barcode not found - Create New Product")
            render_new_product_form(barcode)
            
    else:
        st.info("Enter or scan a barcode")

    # JavaScript သုံးပြီး Barcode Box ထဲကို ကာဆာ အမြဲတမ်း ဝင်နေစေရန် (Auto-focus)
    components.html(
        """
        <script>
            const doc = window.parent.document;
            setInterval(() => {
                const input = doc.querySelector('input[aria-label="📷 Scanned Barcode"]');
                if (input && doc.activeElement !== input) {
                    input.focus();
                }
            }, 300);
        </script>
        """,
        height=0,
    )


if __name__ == "__main__":
    run()
