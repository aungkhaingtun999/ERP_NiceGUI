# ==============================================================================
# MOBILE INVENTORY v14 ENTERPRISE
# ZXING LIVE BARCODE SCANNER
# CAMERA + SEARCH + PRODUCT REGISTRATION
# ==============================================================================

import streamlit as st
from erp_pages.inventory.zxing_scanner import zxing_scanner
from erp_pages.inventory.product_search import search_product
import erp_pages.inventory.product_form as product_form
from database import get_warehouses

# ------------------------------------------------------------------------------
# INITIALIZATION & STATE MANAGEMENT
# ------------------------------------------------------------------------------

def initialize_session_state():
    """Initialize default session state variables."""
    defaults = {
        "barcode_value": "",
        "product": None,
        "camera_on": False,
        "warehouse_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ------------------------------------------------------------------------------
# PRODUCT SEARCH & CLEAR LOGIC
# ------------------------------------------------------------------------------

def load_product(barcode: str):
    """Search for a product by barcode and update session state."""
    barcode = str(barcode).strip()
    if not barcode:
        return

    try:
        product = search_product(barcode)
        st.session_state.product = product
    except Exception as e:
        st.error(f"Search error: {e}")
        st.session_state.product = None

def clear_inventory():
    """Reset barcode and product details in session state."""
    st.session_state.barcode_value = ""
    st.session_state.product = None
    st.session_state.camera_on = False

# ------------------------------------------------------------------------------
# UI COMPONENTS
# ------------------------------------------------------------------------------

def render_warehouse_selector():
    """Render warehouse selection dropdown and handle errors."""
    st.subheader("🏭 Warehouse")
    try:
        warehouses = get_warehouses()
        if warehouses:
            warehouse_map = {w["name"]: w["id"] for w in warehouses}
            selected = st.selectbox(
                "Select Warehouse",
                options=list(warehouse_map.keys()),
                key="warehouse_selectbox"
            )
            st.session_state.warehouse_id = warehouse_map[selected]
        else:
            st.warning("No warehouses available.")
    except Exception as e:
        st.warning(f"Warehouse error: {e}")

def handle_scanner():
    """Manage the camera barcode scanner state and execution."""
    if st.session_state.camera_on:
        st.success("📷 Scanner Ready")
        scanned = zxing_scanner()
        
        if scanned and scanned != st.session_state.barcode_value:
            st.session_state.barcode_value = scanned
            load_product(scanned)
            st.rerun()
    else:
        st.info("Scanner OFF")

def render_product_view():
    """Display product details or new product registration form."""
    product = st.session_state.product
    barcode = st.session_state.barcode_value

    if product:
        st.divider()
        st.subheader("📦 Product Found")
        st.write(f"**Name:** {product.get('name', 'N/A')}")
        st.write(f"**Barcode:** {product.get('barcode', 'N/A')}")
        st.write(f"**SKU:** {product.get('sku', 'N/A')}")
        st.write(f"**Stock:** {product.get('stock', 0)}")
        
    elif barcode:
        st.divider()
        st.subheader("🆕 New Product Registration")
        product_form.render_new_product_form(barcode)

# ------------------------------------------------------------------------------
# MAIN APPLICATION
# ------------------------------------------------------------------------------

def run():
    st.title("📦 Mobile Inventory")
    st.caption("📷 Live Barcode Scanner + Product Registration")

    # Initialize Session State
    initialize_session_state()

    # Warehouse Selection
    render_warehouse_selector()
    st.divider()

    # Action Buttons (Start Scanner / Clear)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📷 Start Scanner", use_container_width=True):
            st.session_state.camera_on = True
            st.rerun()
    with col2:
        if st.button("🧹 Clear", use_container_width=True):
            clear_inventory()
            st.rerun()

    # Scanner Component
    handle_scanner()
    st.divider()

    # Manual Barcode Text Input
    # Note: Using a callback or checking change avoids redundant reruns
    barcode_input = st.text_input(
        "📷 Barcode / SKU",
        value=st.session_state.barcode_value,
        key="barcode_input_field"
    )

    # Update state if text input changes manually
    if barcode_input != st.session_state.barcode_value:
        st.session_state.barcode_value = barcode_input
        if barcode_input:
            load_product(barcode_input)
        else:
            st.session_state.product = None
        st.rerun()

    # Render Product Details or Registration Form
    render_product_view()

if __name__ == "__main__":
    run()
