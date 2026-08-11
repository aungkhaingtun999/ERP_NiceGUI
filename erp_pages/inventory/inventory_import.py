import streamlit as st
from datetime import date

from erp_core.services.inventory_import_service import InventoryImportService

def render_inventory_import():

st.subheader("📥 Inventory In (Stock Import)")

service = InventoryImportService()

current_user = st.session_state.get("user")

if not current_user:
    st.warning("Login required.")
    return

# =========================================================
# Session state
# =========================================================

if "current_import_batch_no" not in st.session_state:
    st.session_state.current_import_batch_no = ""

if "current_import_batch_id" not in st.session_state:
    st.session_state.current_import_batch_id = None

# =========================================================
# Create Batch
# =========================================================

st.markdown("### Create Import Batch")

col1, col2 = st.columns([2, 1])

with col1:
    batch_no = st.text_input(
        "Batch No",
        value=service.generate_batch_no(),
        key="import_batch_no_input"
    )

with col2:
    if st.button("Generate New Batch No"):
        st.rerun()

warehouses = st.session_state.get("warehouses", [])

warehouse_options = {
    w["name"]: w["id"]
    for w in warehouses
}

if not warehouse_options:
    st.error("No warehouses found.")
    return

warehouse_name = st.selectbox(
    "Destination Warehouse",
    options=list(warehouse_options.keys())
)

warehouse_id = warehouse_options[warehouse_name]

remarks = st.text_area(
    "Remarks",
    placeholder="Supplier invoice, opening stock, GRN note..."
)

if st.button("Create Batch", type="primary"):

    result = service.create_batch(
        batch_no=batch_no,
        warehouse_to=warehouse_id,
        requested_by=current_user["id"],
        remarks=remarks
    )

    if result.get("success"):

        st.session_state.current_import_batch_no = result["batch_no"]
        st.session_state.current_import_batch_id = result["id"]

        st.success(f"Batch created: {result['batch_no']}")

        st.rerun()

    else:
        st.error(result.get("message"))

batch_no = st.session_state.current_import_batch_no
batch_id = st.session_state.current_import_batch_id

if not batch_no:
    st.info("Create a batch first.")
    return

st.divider()

st.markdown(f"### Current Batch: `{batch_no}`")

# =========================================================
# Add Line
# =========================================================

st.markdown("#### Add Line")

with st.form("add_import_line_form", clear_on_submit=True):

    c1, c2, c3 = st.columns(3)

    with c1:
        sku = st.text_input("SKU *")

    with c2:
        qty = st.number_input(
            "Quantity *",
            min_value=0.0,
            value=1.0,
            step=1.0
        )

    with c3:
        unit_cost = st.number_input(
            "Unit Cost *",
            min_value=0.0,
            value=0.0,
            step=100.0
        )

    c4, c5, c6 = st.columns(3)

    with c4:
        lot_no = st.text_input("Lot / Batch No")

    with c5:
        mfg_date = st.date_input(
            "MFG Date",
            value=None
        )

    with c6:
        expiry_date = st.date_input(
            "Expiry Date",
            value=None
        )

    submitted = st.form_submit_button("Add Line")

    if submitted:

        lines = service.get_batch_lines(batch_no)
        next_line_no = len(lines) + 1

        result = service.add_line(
            batch_id=batch_id,
            line_no=next_line_no,
            warehouse_id=warehouse_id,
            sku=sku.strip(),
            qty=qty,
            unit_cost=unit_cost,
            lot_no=lot_no.strip() or None,
            mfg_date=str(mfg_date) if mfg_date else None,
            expiry_date=str(expiry_date) if expiry_date else None
        )

        if result.get("success"):
            st.success("Line added.")
            st.rerun()
        else:
            st.error("Failed to add line.")

st.divider()

# =========================================================
# Batch Lines
# =========================================================

st.markdown("### Batch Lines")

lines = service.get_batch_lines(batch_no)

if lines:
    st.dataframe(lines, use_container_width=True)
else:
    st.info("No lines added yet.")

# =========================================================
# Submit Batch
# =========================================================

st.divider()

if st.button("Submit Batch for Approval", type="primary"):

    result = service.submit_batch(batch_no)

    if result.get("success"):

        if result.get("status") == "PENDING":
            st.success(
                f"Batch submitted successfully. Pending approval. Valid lines: {result.get('valid_lines')}"
            )
        else:
            st.warning(
                f"Batch has validation errors. Error lines: {result.get('error_lines')}"
            )

        st.rerun()

    else:
        st.error(result.get("message"))

# =========================================================
# Current Status
# =========================================================

batch = service.get_batch(batch_no)

if batch:

    st.divider()

    st.markdown("### Batch Status")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Status", batch["status"])
    c2.metric("Total Lines", batch["total_lines"])
    c3.metric("Valid", batch["valid_lines"])
    c4.metric("Errors", batch["error_lines"])

    if batch.get("posted_at"):
        st.success(f"Posted at: {batch['posted_at']}")