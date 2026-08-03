import streamlit as st
import streamlit.components.v1 as components

from erp_pages.inventory.product_search import search_product
from erp_pages.inventory.product_form import render_new_product_form


def run():
    st.title("📦 Mobile Inventory")
    st.caption("📷 Barcode Scanner Integration Test")

    # Session State ထဲမှာ Barcode သိမ်းရန်
    if "scanned_barcode" not in st.session_state:
        st.session_state["scanned_barcode"] = ""

    # JavaScript သုံးပြီး Scanner ကလာတဲ့ Data ကို ဖမ်းယူပြီး Streamlit query params (သို့) input ထဲထည့်ပေးခြင်း
    # ဒါမှမဟုတ် Streamlit ရဲ့ text_input ကို တိုက်ရိုက် Focus ပေးထားမည့် ကုဒ်
    
    # ပုံမှန် Text Input (Scanner က ဒီဘောက်စ်ထဲကို တိုက်ရိုက်ပစ်ထည့်ပါမယ်)
    barcode = st.text_input(
        "📷 Scanned Barcode",
        value=st.session_state["scanned_barcode"],
        placeholder="Click here and scan barcode...",
        key="barcode_input"
    )

    # အကယ်၍ Barcode Box ထဲ တိုက်ရိုက်ရောက်အောင် JavaScript ဖြင့် အမြဲ Focus လုပ်ပေးခြင်း
    components.html(
        """
        <script>
            // Streamlit ရဲ့ Input Box ကို ရှာပြီး Focus လုပ်ပေးခြင်း
            const doc = window.parent.document;
            const inputField = doc.querySelector('input[aria-label="📷 Scanned Barcode"]');
            
            if (inputField) {
                inputField.focus();
                // Click လိုက်ရင်လည်း Focus မပြုတ်သွားအောင် ထိန်းပေးခြင်း
                inputField.addEventListener('blur', () => {
                    setTimeout(() => inputField.focus(), 100);
                });
            }
        </script>
        """,
        height=0,
    )

    # ဝင်လာတဲ့ Barcode ကို စစ်ဆေးပြီး ရှာဖွေခြင်း
    if barcode:
        st.success(f"Barcode : {barcode}")

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

        # နောက်တစ်ခါ ဆက်ဖတ်ရန် ရှင်းလင်းသည့်ခလုတ်
        if st.button("🔄 Clear / Scan Next"):
            st.session_state["scanned_barcode"] = ""
            st.rerun()
    else:
        st.info("Please scan a barcode...")


if __name__ == "__main__":
    run()
