import streamlit as st

# ===========================
# SOURCE & DESTINATION STOCK
# ===========================

warehouse_ids = [
    warehouse_map[from_name]["id"],
    warehouse_map[to_name]["id"]
]

# Database ခေါ်ဆိုမှုကို တစ်ခါတည်းဖြင့် အကောင်းဆုံးဖြစ်အောင် ပေါင်းထုတ်ထားသည်
stocks_response = (
    supabase
    .table("warehouse_stock")
    .select("*")
    .eq("product_id", product["id"])
    .in_("warehouse_id", warehouse_ids)
    .execute()
    .data
)

stock_map = {item["warehouse_id"]: item for item in stocks_response}

# Source stock
source_record = stock_map.get(warehouse_map[from_name]["id"], {})
source_qty = source_record.get("qty", 0)
source_available = source_record.get("available_qty", source_qty)

# Destination stock
dest_record = stock_map.get(warehouse_map[to_name]["id"], {})
dest_qty = dest_record.get("qty", 0)
dest_available = dest_record.get("available_qty", dest_qty)


# ===========================
# DISPLAY STOCK STATUS
# ===========================

c1, c2 = st.columns(2)

with c1:
    st.info(
        f"""
        📤 **Source Warehouse**
        
        {from_name}
        
        Product: 
        {product['name']}
        
        Current Stock: 
        {source_qty}
        
        Available: 
        {source_available}
        """
    )

with c2:
    st.success(
        f"""
        📥 **Destination Warehouse**
        
        {to_name}
        
        Product: 
        {product['name']}
        
        Current Stock: 
        {dest_qty}
        
        Available: 
        {dest_available}
        """
    )


# ===========================
# VALIDATION & TRANSFER INPUT
# ===========================

available = source_available

if available <= 0:
    st.error("Source warehouse has no available stock.")
    st.stop()

st.markdown("---")

# Transfer Quantity Input
transfer_qty = st.number_input(
    "Transfer Quantity",
    min_value=1,
    max_value=int(available),
    value=1,
    step=1
)


# ===========================
# AFTER TRANSFER PREVIEW
# ===========================

st.subheader("📊 After Transfer Preview")

col_p1, col_p2 = st.columns(2)

new_source_qty = source_qty - transfer_qty
new_dest_qty = dest_qty + transfer_qty

with col_p1:
    st.markdown(f"**{from_name}**")
    st.metric(
        label="Stock Change",
        value=new_source_qty,
        delta=f"-{transfer_qty}"
    )

with col_p2:
    st.markdown(f"**{to_name}**")
    st.metric(
        label="Stock Change",
        value=new_dest_qty,
        delta=f"+{transfer_qty}"
    )
