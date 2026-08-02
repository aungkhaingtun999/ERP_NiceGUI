# ==============================================================================
# pages/2_Mobile_Inventory.py
# ERP MOBILE INVENTORY v4.1 (Refactored)
# ==============================================================================

import streamlit as st
from database import db, money 
from auth import is_authenticated
from utils.ui import show_table
def run():
    st.set_page_config(page_title="Mobile Inventory", layout="centered", page_icon="📦")

    if not is_authenticated():
        st.error("ကျေးဇူးပြု၍ စနစ်ထဲသို့ အရင်ဝင်ရောက် (Login) ပါ။")
        st.stop()

    st.title("📦 Mobile Inventory")

    # ===============================
    # FORM
    # ===============================
    with st.form("inventory_form", clear_on_submit=True):
        barcode = st.text_input("📷 Barcode / SKU")
        name = st.text_input("📝 Product Name")
        
        col1, col2 = st.columns(2)
        purchase_price = col1.number_input("💰 Purchase Price", min_value=0.0, step=100.0)
        selling_price = col2.number_input("💵 Selling Price", min_value=0.0, step=100.0)
        
        stock = st.number_input("📦 Opening Stock", min_value=0, step=1)
        
        category = st.text_input("🏷️ Category")
        supplier = st.text_input("🏭 Supplier")
        unit = st.selectbox("Unit", ["pcs", "box", "kg", "pack"])

        submitted = st.form_submit_button("➕ Save Product")

        if submitted:
            if not name or not barcode:
                st.error("Barcode နှင့် ပစ္စည်းအမည် (Name) တို့ကို မဖြစ်မနေ ထည့်သွင်းပေးရပါမည်။")
            else:
                try:
                    client = db()
                    
                    # 1. Barcode ရှိပြီးသားလား စစ်ဆေးခြင်း
                    existing = client.table("products").select("id").eq("barcode", barcode).execute()
                    
                    if existing.data:
                        st.warning("⚠️ ဤ Barcode နံပါတ်ဖြင့် ပစ္စည်းရှိနှင့်ပြီး ဖြစ်ပါသည်။ အချက်အလက်ပြင်ဆင်ရန် (Update) လိုအပ်ပါသလား။")
                    else:
                        # 2. Insert လုပ်ခြင်း
                        data = {
                            "barcode": barcode,
                            "sku": barcode,
                            "name": name,
                            "purchase_price": money(purchase_price),
                            "selling_price": money(selling_price),
                            "unit": unit,
                            "category": category,
                            "is_active": True
                        }
                        
                        client.table("products").insert(data).execute()
                        st.success(f"✅ {name} ပစ္စည်းအချက်အလက်များကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # ===============================
    # FEATURES NOTE
    # ===============================
    st.divider()
    st.info("""
    💡 **Mobile အသုံးပြုသူများအတွက် အကြံပြုချက်:**
    - **Camera Scan:** ဖုန်း Browser ရှိ 'Text Input' ကွက်လပ်ကို နှိပ်လိုက်ပါက Keyboard ပေါ်လာမည်ဖြစ်ပြီး၊ ထိုနေရာတွင် Camera icon (သို့) Barcode scanning tool ကို အသုံးပြုနိုင်ပါသည်။
    """)

if __name__ == "__main__":
    run()

