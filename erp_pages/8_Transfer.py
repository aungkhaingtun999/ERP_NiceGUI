# ==================================================
# WAREHOUSE & PRODUCT SELECTION (Normal State - No Form)
# ==================================================

# Source & Destination Warehouse Selectboxes
source_warehouse_id = st.selectbox(
    "Source Warehouse",
    options=list(warehouse_options.keys()),
    format_func=lambda x: warehouse_options[x]
)

dest_warehouse_id = st.selectbox(
    "Destination Warehouse",
    options=list(warehouse_options.keys()),
    format_func=lambda x: warehouse_options[x]
)

# Product Selectbox
selected_product_id = st.selectbox(
    "Select Product",
    options=list(product_options.keys()),
    format_func=lambda x: product_options[x]
)


# ==================================================
# STOCK INFORMATION (Real-time Fetching)
# ==================================================

source_stock_qty = 0
source_available_qty = 0

dest_stock_qty = 0
dest_available_qty = 0

try:
    supabase = db()

    # Source Stock Query
    source_stock = (
        supabase
        .table("warehouse_stock")
        .select("*")
        .eq("warehouse_id", source_warehouse_id)
        .eq("product_id", selected_product_id)
        .execute()
        .data
        or []
    )

    if source_stock:
        source_stock_qty = source_stock[0].get("qty", 0)
        source_available_qty = source_stock[0].get("available_qty", source_stock_qty)

    # Destination Stock Query
    dest_stock = (
        supabase
        .table("warehouse_stock")
        .select("*")
        .eq("warehouse_id", dest_warehouse_id)
        .eq("product_id", selected_product_id)
        .execute()
        .data
        or []
    )

    if dest_stock:
        dest_stock_qty = dest_stock[0].get("qty", 0)
        dest_available_qty = dest_stock[0].get("available_qty", dest_stock_qty)

except Exception as e:
    st.warning(f"Stock loading error: {e}")


# ==================================================
# DISPLAY STOCK (Live Preview)
# ==================================================

stock_col1, stock_col2 = st.columns(2)

with stock_col1:
    st.info(
        f"""
📤 **Source Stock**

Warehouse:
{warehouse_options[source_warehouse_id]}

Product:
{product_options[selected_product_id]}

Current Qty:
{source_stock_qty}

Available Qty:
{source_available_qty}
"""
    )

with stock_col2:
    st.success(
        f"""
📥 **Destination Stock**

Warehouse:
{warehouse_options[dest_warehouse_id]}

Product:
{product_options[selected_product_id]}

Current Qty:
{dest_stock_qty}

Available Qty:
{dest_available_qty}
"""
    )


# ==================================================
# TRANSFER VALIDATION & EXECUTION
# ==================================================

if source_available_qty <= 0:
    st.error("Source warehouse has no available stock to transfer.")
else:
    # Transfer Quantity Input
    transfer_qty = st.number_input(
        "Transfer Quantity",
        min_value=1,
        max_value=int(source_available_qty),
        value=1,
        step=1
    )

    # Transfer Execute Button (အစားထိုး Form Submit Button)
    if st.button("Confirm & Transfer", type="primary"):
        # ဒီနေရာမှာ Database ထဲကို Stock Move တဲ့ Transaction / Update logic တွေ ဆက်ရေးရပါမယ်
        st.success(f"Successfully transferred {transfer_qty} of {product_options[selected_product_id]} from {warehouse_options[source_warehouse_id]} to {warehouse_options[dest_warehouse_id]}!")
