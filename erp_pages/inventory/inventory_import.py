# ==============================================================================
# erp_pages/inventory/inventory_import.py
#
# ERP ENTERPRISE INVENTORY IN
# BULK EXCEL / CSV IMPORT
#
# Maker Checker Workflow
#
# Excel / CSV
#      ↓
# Local Validation
#      ↓
# Preview
#      ↓
# inventory_import_batches
#      ↓
# inventory_import_lines
#      ↓
# submit_inventory_import_batch
#      ↓
# PENDING
#      ↓
# Checker Approval
#      ↓
# POSTED
#
# IMPORTANT:
# Uploading Excel/CSV NEVER posts stock directly.
#
# IMPORTANT STREAMLIT STATE RULE:
# inventory_import_batch_no_input is the ONLY widget key.
# We NEVER modify that key after its widget has been instantiated
# during the same Streamlit run.
# ==============================================================================

import io
import time

import pandas as pd
import streamlit as st

from database import db


# ==============================================================================
# CONSTANTS
# ==============================================================================

IMPORT_COLUMNS = [
    "SKU",
    "Quantity",
    "Unit Cost",
    "Lot No",
    "MFG Date",
    "Expiry Date",
    "Reference No",
    "Supplier Code",
]


# ==============================================================================
# SESSION STATE
# ==============================================================================

def _init_state():
    """
    Initialize non-widget application state.

    IMPORTANT:
    inventory_import_batch_no_input is a widget key.
    It is initialized BEFORE st.text_input() is created.
    """

    defaults = {
        "inventory_import_batch_no_input": "",
        "inventory_import_remarks": "",
        "inventory_import_file_name": "",
        "inventory_import_preview": None,
        "inventory_import_validated": False,
        "inventory_import_reset_batch": False,
        "inventory_import_last_submitted_batch": "",
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


# ==============================================================================
# BATCH NUMBER
# ==============================================================================

def _generate_batch_no():
    """
    Generate unique human-readable Inventory In batch number.

    Example:
        INV-IN-20260811-201530
    """

    return (
        "INV-IN-"
        + time.strftime("%Y%m%d-%H%M%S")
    )


# ==============================================================================
# BATCH RESET
# ==============================================================================

def _apply_batch_reset_before_widget():
    """
    Apply batch reset BEFORE the text_input widget is instantiated.

    This is critical.

    We never do:

        st.session_state["inventory_import_batch_no_input"] = ""

    after the text_input has already been rendered.

    Instead, submit sets a reset flag and reruns.
    On the next run this function executes before the widget exists.
    """

    if st.session_state.get(
        "inventory_import_reset_batch",
        False,
    ):

        st.session_state[
            "inventory_import_batch_no_input"
        ] = ""

        st.session_state[
            "inventory_import_reset_batch"
        ] = False


# ==============================================================================
# GENERATE BATCH CALLBACK
# ==============================================================================

def _on_generate_batch():
    """
    Button callback.

    Streamlit executes this callback before the next page run,
    therefore changing the widget key here is safe.
    """

    st.session_state[
        "inventory_import_batch_no_input"
    ] = _generate_batch_no()


# ==============================================================================
# IMPORT BATCH UI
# ==============================================================================

def _render_import_batch():
    """
    Render Import Batch section.

    IMPORTANT:
    Only inventory_import_batch_no_input is used as widget key.

    There is intentionally NO:
        inventory_import_batch_no

    business-state key anymore.
    """

    # --------------------------------------------------------------------------
    # Apply pending reset BEFORE widget instantiation
    # --------------------------------------------------------------------------

    _apply_batch_reset_before_widget()

    # --------------------------------------------------------------------------
    # Safety initialization BEFORE widget instantiation
    # --------------------------------------------------------------------------

    if (
        "inventory_import_batch_no_input"
        not in st.session_state
    ):
        st.session_state[
            "inventory_import_batch_no_input"
        ] = ""

    st.markdown(
        "### 1️⃣ Import Batch"
    )

    col1, col2 = st.columns(
        [3, 1],
        vertical_alignment="bottom",
    )

    # --------------------------------------------------------------------------
    # BATCH INPUT
    # --------------------------------------------------------------------------

    with col1:

        st.text_input(
            "Batch No",
            key="inventory_import_batch_no_input",
            placeholder="INV-IN-YYYYMMDD-HHMMSS",
        )

    # --------------------------------------------------------------------------
    # GENERATE BUTTON
    # --------------------------------------------------------------------------

    with col2:

        st.button(
            "Generate Batch No",
            key="generate_inventory_import_batch_no_btn",
            type="secondary",
            use_container_width=True,
            on_click=_on_generate_batch,
        )

    # --------------------------------------------------------------------------
    # READ CURRENT WIDGET VALUE
    # --------------------------------------------------------------------------

    batch_no = str(
        st.session_state.get(
            "inventory_import_batch_no_input",
            "",
        )
    ).strip()

    # --------------------------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------------------------

    if batch_no:

        st.success(
            f"Import Batch: **{batch_no}**"
        )

    else:

        st.info(
            "Generate a Batch No before uploading Inventory In."
        )

    return batch_no


# ==============================================================================
# CURRENT USER
# ==============================================================================

def _get_current_user_id():

    possible_keys = [
        "user_id",
        "current_user_id",
        "logged_in_user_id",
        "auth_user_id",
        "user_uuid",
    ]

    for key in possible_keys:

        value = st.session_state.get(key)

        if value:
            return value

    user = st.session_state.get(
        "user"
    )

    if isinstance(user, dict):

        for key in [
            "id",
            "user_id",
            "uuid",
        ]:

            value = user.get(key)

            if value:
                return value

    return None


# ==============================================================================
# WAREHOUSES
# ==============================================================================

def _get_warehouses(client):

    response = (
        client
        .table("warehouses")
        .select("id,name")
        .order("id")
        .execute()
    )

    return response.data or []


# ==============================================================================
# TEMPLATE DATA
# ==============================================================================

def _template_dataframe():

    return pd.DataFrame(
        [
            {
                "SKU": "TEA-001",
                "Quantity": 50,
                "Unit Cost": 2500,
                "Lot No": "TEA-LOT-001",
                "MFG Date": "2026-08-01",
                "Expiry Date": "2027-08-01",
                "Reference No": "PO-001",
                "Supplier Code": "SUP-001",
            },
            {
                "SKU": "COFFEE-001",
                "Quantity": 25,
                "Unit Cost": 5000,
                "Lot No": "COF-LOT-001",
                "MFG Date": "2026-08-05",
                "Expiry Date": "2027-08-05",
                "Reference No": "PO-002",
                "Supplier Code": "SUP-002",
            },
        ],
        columns=IMPORT_COLUMNS,
    )


# ==============================================================================
# EXCEL TEMPLATE
# ==============================================================================

def _excel_template_bytes():

    output = io.BytesIO()

    df = _template_dataframe()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Inventory In",
        )

    output.seek(0)

    return output.getvalue()


# ==============================================================================
# CSV TEMPLATE
# ==============================================================================

def _csv_template_bytes():

    df = _template_dataframe()

    return (
        df.to_csv(
            index=False,
        )
        .encode("utf-8-sig")
    )


# ==============================================================================
# READ UPLOAD
# ==============================================================================

def _read_uploaded_file(uploaded_file):

    filename = uploaded_file.name.lower()

    file_bytes = uploaded_file.getvalue()

    if filename.endswith(".xlsx"):

        df = pd.read_excel(
            io.BytesIO(file_bytes)
        )

    elif filename.endswith(".csv"):

        df = pd.read_csv(
            io.BytesIO(file_bytes)
        )

    else:

        raise ValueError(
            "Only .xlsx and .csv files are supported."
        )

    return df


# ==============================================================================
# NORMALIZE COLUMNS
# ==============================================================================

def _normalize_columns(df):

    rename_map = {}

    for column in df.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace("_", " ")
        )

        if normalized == "sku":

            rename_map[column] = "SKU"

        elif normalized in (
            "quantity",
            "qty",
        ):

            rename_map[column] = "Quantity"

        elif normalized in (
            "unit cost",
            "cost",
            "purchase price",
        ):

            rename_map[column] = "Unit Cost"

        elif normalized in (
            "lot no",
            "lot number",
            "lot",
        ):

            rename_map[column] = "Lot No"

        elif normalized in (
            "mfg date",
            "manufacturing date",
        ):

            rename_map[column] = "MFG Date"

        elif normalized in (
            "expiry date",
            "expiration date",
            "expire date",
        ):

            rename_map[column] = "Expiry Date"

        elif normalized in (
            "reference no",
            "reference number",
            "ref no",
        ):

            rename_map[column] = "Reference No"

        elif normalized in (
            "supplier code",
            "supplier",
        ):

            rename_map[column] = "Supplier Code"

    return df.rename(
        columns=rename_map
    )


# ==============================================================================
# CLEAN DATAFRAME
# ==============================================================================

def _clean_dataframe(df):

    df = _normalize_columns(
        df
    )

    mandatory_columns = [
        "SKU",
        "Quantity",
        "Unit Cost",
    ]

    missing_mandatory = [
        column
        for column in mandatory_columns
        if column not in df.columns
    ]

    if missing_mandatory:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                missing_mandatory
            )
        )

    # --------------------------------------------------------------------------
    # Add optional columns
    # --------------------------------------------------------------------------

    for column in IMPORT_COLUMNS:

        if column not in df.columns:

            df[column] = None

    df = df[
        IMPORT_COLUMNS
    ].copy()

    # --------------------------------------------------------------------------
    # Remove completely empty rows
    # --------------------------------------------------------------------------

    df = (
        df
        .dropna(
            how="all"
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------------------------
    # SKU
    # --------------------------------------------------------------------------

    df["SKU"] = (
        df["SKU"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------------------------
    # Numeric
    # --------------------------------------------------------------------------

    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="coerce",
    )

    df["Unit Cost"] = pd.to_numeric(
        df["Unit Cost"],
        errors="coerce",
    )

    # --------------------------------------------------------------------------
    # Text
    # --------------------------------------------------------------------------

    text_columns = [
        "Lot No",
        "Reference No",
        "Supplier Code",
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # --------------------------------------------------------------------------
    # Dates
    # --------------------------------------------------------------------------

    df["MFG Date"] = pd.to_datetime(
        df["MFG Date"],
        errors="coerce",
    )

    df["Expiry Date"] = pd.to_datetime(
        df["Expiry Date"],
        errors="coerce",
    )

    return df


# ==============================================================================
# LOAD PRODUCTS BY SKU
# ==============================================================================

def _load_products_by_sku(
    client,
    skus,
):

    clean_skus = sorted(
        {
            str(sku).strip()
            for sku in skus
            if sku is not None
            and str(sku).strip()
        }
    )

    if not clean_skus:

        return {}

    products = []

    chunk_size = 100

    for start in range(
        0,
        len(clean_skus),
        chunk_size,
    ):

        chunk = clean_skus[
            start:start + chunk_size
        ]

        response = (
            client
            .table("products")
            .select(
                "id,sku,name"
            )
            .in_(
                "sku",
                chunk,
            )
            .execute()
        )

        products.extend(
            response.data or []
        )

    return {
        str(product["sku"]).strip(): product
        for product in products
        if product.get("sku") is not None
    }


# ==============================================================================
# VALIDATE DATA
# ==============================================================================

def _validate_dataframe(
    client,
    df,
    warehouse_id,
):

    df = df.copy()

    df["Product ID"] = None
    df["Product Name"] = ""
    df["Status"] = "VALID"
    df["Error"] = ""

    # --------------------------------------------------------------------------
    # Product lookup
    # --------------------------------------------------------------------------

    product_map = _load_products_by_sku(
        client,
        df["SKU"].tolist(),
    )

    # --------------------------------------------------------------------------
    # Duplicate detection
    # --------------------------------------------------------------------------

    seen_keys = set()

    for index, row in df.iterrows():

        errors = []

        sku = str(
            row["SKU"] or ""
        ).strip()

        lot_no = str(
            row["Lot No"] or ""
        ).strip()

        qty = row["Quantity"]

        unit_cost = row["Unit Cost"]

        # ----------------------------------------------------------------------
        # SKU
        # ----------------------------------------------------------------------

        if not sku:

            errors.append(
                "SKU is required."
            )

        elif sku not in product_map:

            errors.append(
                f"Product SKU not found: {sku}"
            )

        else:

            product = product_map[
                sku
            ]

            df.at[
                index,
                "Product ID",
            ] = product["id"]

            df.at[
                index,
                "Product Name",
            ] = product.get(
                "name",
                "",
            )

        # ----------------------------------------------------------------------
        # Quantity
        # ----------------------------------------------------------------------

        if pd.isna(qty):

            errors.append(
                "Quantity is required."
            )

        else:

            try:

                qty_value = float(qty)

                if qty_value <= 0:

                    errors.append(
                        "Quantity must be greater than zero."
                    )

            except Exception:

                errors.append(
                    "Invalid quantity."
                )

        # ----------------------------------------------------------------------
        # Unit Cost
        # ----------------------------------------------------------------------

        if pd.isna(unit_cost):

            errors.append(
                "Unit Cost is required."
            )

        else:

            try:

                cost_value = float(
                    unit_cost
                )

                if cost_value < 0:

                    errors.append(
                        "Unit Cost cannot be negative."
                    )

            except Exception:

                errors.append(
                    "Invalid Unit Cost."
                )

        # ----------------------------------------------------------------------
        # Lot
        # ----------------------------------------------------------------------

        if not lot_no:

            errors.append(
                "Lot No is required."
            )

        # ----------------------------------------------------------------------
        # Duplicate PRODUCT / WAREHOUSE / LOT
        # ----------------------------------------------------------------------

        duplicate_key = (
            str(
                df.at[
                    index,
                    "Product ID",
                ]
                or ""
            ),
            int(warehouse_id),
            lot_no,
        )

        if duplicate_key in seen_keys:

            errors.append(
                "Duplicate PRODUCT / WAREHOUSE / LOT "
                "in import file."
            )

        else:

            seen_keys.add(
                duplicate_key
            )

        # ----------------------------------------------------------------------
        # Date validation
        # ----------------------------------------------------------------------

        mfg_date = row["MFG Date"]

        expiry_date = row["Expiry Date"]

        if (
            not pd.isna(mfg_date)
            and not pd.isna(expiry_date)
            and expiry_date < mfg_date
        ):

            errors.append(
                "Expiry Date cannot be earlier "
                "than MFG Date."
            )

        # ----------------------------------------------------------------------
        # Result
        # ----------------------------------------------------------------------

        if errors:

            df.at[
                index,
                "Status",
            ] = "ERROR"

            df.at[
                index,
                "Error",
            ] = " | ".join(
                errors
            )

        else:

            df.at[
                index,
                "Status",
            ] = "VALID"

    return df


# ==============================================================================
# CREATE BATCH
# ==============================================================================

def _create_batch(
    client,
    batch_no,
    warehouse_id,
    remarks,
    user_id,
):

    payload = {
        "batch_no": batch_no,
        "transaction_type": "STOCK_IN",
        "status": "DRAFT",
        "warehouse_to": warehouse_id,
        "requested_by": user_id,
        "remarks": remarks,
        "total_lines": 0,
        "valid_lines": 0,
        "error_lines": 0,
    }

    response = (
        client
        .table(
            "inventory_import_batches"
        )
        .insert(
            payload
        )
        .execute()
    )

    data = response.data or []

    if not data:

        raise RuntimeError(
            "Unable to create inventory import batch."
        )

    return data[0]


# ==============================================================================
# INSERT IMPORT LINES
# ==============================================================================

def _insert_import_lines(
    client,
    batch_id,
    warehouse_id,
    valid_df,
):

    payloads = []

    for index, row in valid_df.iterrows():

        def _date_value(value):

            if pd.isna(value):

                return None

            return value.strftime(
                "%Y-%m-%d"
            )

        payloads.append(
            {
                "batch_id": batch_id,
                "line_no": int(
                    index + 1
                ),
                "warehouse_id": warehouse_id,
                "sku": str(
                    row["SKU"]
                ).strip(),
                "product_id": int(
                    row["Product ID"]
                ),
                "qty": float(
                    row["Quantity"]
                ),
                "unit_cost": float(
                    row["Unit Cost"]
                ),
                "lot_no": str(
                    row["Lot No"]
                ).strip() or None,
                "mfg_date": _date_value(
                    row["MFG Date"]
                ),
                "expiry_date": _date_value(
                    row["Expiry Date"]
                ),
                "reference_no": str(
                    row["Reference No"]
                ).strip() or None,
                "supplier_code": str(
                    row["Supplier Code"]
                ).strip() or None,

                # ----------------------------------------------------------------
                # Keep line unposted.
                #
                # RPC / approval workflow will handle posting later.
                # ----------------------------------------------------------------

                "is_valid": False,
                "error_message": None,
            }
        )

    if not payloads:

        raise RuntimeError(
            "No valid import lines found."
        )

    # --------------------------------------------------------------------------
    # Chunk insert
    # --------------------------------------------------------------------------

    chunk_size = 100

    for start in range(
        0,
        len(payloads),
        chunk_size,
    ):

        chunk = payloads[
            start:start + chunk_size
        ]

        (
            client
            .table(
                "inventory_import_lines"
            )
            .insert(
                chunk
            )
            .execute()
        )


# ==============================================================================
# SUBMIT RPC
# ==============================================================================

def _submit_batch(
    client,
    batch_no,
):

    response = client.rpc(
        "submit_inventory_import_batch",
        {
            "p_batch_no": batch_no,
        },
    ).execute()

    result = response.data

    if isinstance(
        result,
        list,
    ):

        return (
            result[0]
            if result
            else {}
        )

    return result or {}


# ==============================================================================
# FORMAT PREVIEW
# ==============================================================================

def _preview_dataframe(df):

    preview_columns = [
        "SKU",
        "Product Name",
        "Quantity",
        "Unit Cost",
        "Lot No",
        "MFG Date",
        "Expiry Date",
        "Reference No",
        "Supplier Code",
        "Status",
        "Error",
    ]

    return df[
        preview_columns
    ].copy()


# ==============================================================================
# MAIN
# ==============================================================================

def render_inventory_import():

    # ==========================================================================
    # INITIALIZE STATE
    # ==========================================================================

    _init_state()

    # ==========================================================================
    # PAGE HEADER
    # ==========================================================================

    st.subheader(
        "📥 Inventory In"
    )

    st.caption(
        "ERP Enterprise Inventory In | "
        "Excel / CSV Bulk Import | "
        "Maker-Checker Enabled"
    )

    # ==========================================================================
    # DATABASE
    # ==========================================================================

    try:

        client = db()

    except Exception as e:

        st.error(
            f"Database connection failed: {e}"
        )

        return

    if client is None:

        st.error(
            "ERP database client is not available."
        )

        return

    # ==========================================================================
    # CURRENT USER
    # ==========================================================================

    current_user = _get_current_user_id()

    if not current_user:

        st.warning(
            "Current user session ID was not found. "
            "Please log in again."
        )

    # ==========================================================================
    # WAREHOUSE
    # ==========================================================================

    try:

        warehouses = _get_warehouses(
            client
        )

    except Exception as e:

        st.error(
            f"Warehouse loading failed: {e}"
        )

        return

    if not warehouses:

        st.warning(
            "No warehouses found."
        )

        return

    warehouse_options = {
        f"{warehouse['id']} - "
        f"{warehouse.get('name', '')}":
            warehouse["id"]
        for warehouse in warehouses
    }

    selected_warehouse_label = st.selectbox(
        "Destination Warehouse",
        list(
            warehouse_options.keys()
        ),
        key="inventory_import_warehouse",
    )

    selected_warehouse_id = (
        warehouse_options[
            selected_warehouse_label
        ]
    )

    st.info(
        f"Destination Warehouse ID: "
        f"{selected_warehouse_id}"
    )

    # ==========================================================================
    # BATCH
    # ==========================================================================

    batch_no = _render_import_batch()

    if not batch_no:

        st.warning(
            "Please generate an Import Batch No "
            "before uploading."
        )

        return

    # ==========================================================================
    # REMARKS
    # ==========================================================================

    remarks = st.text_input(
        "Remarks",
        key="inventory_import_remarks",
        placeholder="August stock receiving",
    )

    # ==========================================================================
    # TEMPLATE
    # ==========================================================================

    st.markdown(
        "### 2️⃣ Excel / CSV Bulk Import"
    )

    st.info(
        "ရာချီ / ထောင်ချီသော ပစ္စည်းများကို "
        "Excel သို့မဟုတ် CSV ဖြင့် တစ်ကြိမ်တည်း သွင်းနိုင်ပါတယ်။ "
        "Upload လုပ်ရုံနဲ့ stock မတက်ပါ။ "
        "Checker approval ပြီးမှသာ POSTED ဖြစ်ပါမယ်။"
    )

    col1, col2 = st.columns(
        2
    )

    # --------------------------------------------------------------------------
    # Excel Template
    # --------------------------------------------------------------------------

    with col1:

        st.download_button(
            label="📥 Download Excel Template",
            data=_excel_template_bytes(),
            file_name="inventory_in_template.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            key="inventory_import_excel_template",
            use_container_width=True,
        )

    # --------------------------------------------------------------------------
    # CSV Template
    # --------------------------------------------------------------------------

    with col2:

        st.download_button(
            label="📥 Download CSV Template",
            data=_csv_template_bytes(),
            file_name="inventory_in_template.csv",
            mime="text/csv",
            key="inventory_import_csv_template",
            use_container_width=True,
        )

    # ==========================================================================
    # FILE UPLOAD
    # ==========================================================================

    uploaded_file = st.file_uploader(
        "Upload Excel / CSV",
        type=[
            "xlsx",
            "csv",
        ],
        key="inventory_import_uploader",
    )

    if uploaded_file:

        uploaded_name = uploaded_file.name

        previous_name = st.session_state.get(
            "inventory_import_file_name",
            "",
        )

        # ----------------------------------------------------------------------
        # Validate only when file changes
        # ----------------------------------------------------------------------

        if previous_name != uploaded_name:

            try:

                raw_df = _read_uploaded_file(
                    uploaded_file
                )

                clean_df = _clean_dataframe(
                    raw_df
                )

                validated_df = _validate_dataframe(
                    client=client,
                    df=clean_df,
                    warehouse_id=selected_warehouse_id,
                )

                st.session_state[
                    "inventory_import_preview"
                ] = validated_df

                st.session_state[
                    "inventory_import_file_name"
                ] = uploaded_name

                st.session_state[
                    "inventory_import_validated"
                ] = True

            except Exception as e:

                st.session_state[
                    "inventory_import_preview"
                ] = None

                st.session_state[
                    "inventory_import_validated"
                ] = False

                st.session_state[
                    "inventory_import_file_name"
                ] = ""

                st.error(
                    f"File validation failed: {e}"
                )

    # ==========================================================================
    # PREVIEW
    # ==========================================================================

    preview_df = st.session_state.get(
        "inventory_import_preview"
    )

    if preview_df is not None:

        st.markdown(
            "### 3️⃣ Import Preview"
        )

        total_lines = len(
            preview_df
        )

        valid_lines = int(
            (
                preview_df["Status"]
                == "VALID"
            ).sum()
        )

        error_lines = int(
            (
                preview_df["Status"]
                == "ERROR"
            ).sum()
        )

        c1, c2, c3 = st.columns(
            3
        )

        c1.metric(
            "Total Lines",
            total_lines,
        )

        c2.metric(
            "Valid Lines",
            valid_lines,
        )

        c3.metric(
            "Error Lines",
            error_lines,
        )

        # ----------------------------------------------------------------------
        # Validation result
        # ----------------------------------------------------------------------

        if error_lines > 0:

            st.error(
                f"{error_lines} line(s) contain errors. "
                "Correct the Excel/CSV file and upload again."
            )

        else:

            st.success(
                f"All {valid_lines} lines passed local validation."
            )

        # ----------------------------------------------------------------------
        # Preview table
        # ----------------------------------------------------------------------

        st.dataframe(
            _preview_dataframe(
                preview_df
            ),
            use_container_width=True,
            hide_index=True,
        )

        # ----------------------------------------------------------------------
        # Download validation result
        # ----------------------------------------------------------------------

        validation_csv = (
            preview_df
            .to_csv(
                index=False
            )
            .encode("utf-8-sig")
        )

        st.download_button(
            "📥 Download Validation Result",
            data=validation_csv,
            file_name=(
                "inventory_import_validation.csv"
            ),
            mime="text/csv",
            key="inventory_import_validation_download",
            use_container_width=True,
        )

    # ==========================================================================
    # SUBMIT
    # ==========================================================================

    st.markdown(
        "### 4️⃣ Submit for Checker Approval"
    )

    can_submit = (
        preview_df is not None
        and len(preview_df) > 0
        and int(
            (
                preview_df["Status"]
                == "ERROR"
            ).sum()
        ) == 0
        and bool(
            batch_no.strip()
        )
        and bool(
            current_user
        )
    )

    if not can_submit:

        if preview_df is None:

            st.info(
                "Upload an Excel/CSV file first."
            )

        elif not batch_no.strip():

            st.warning(
                "Batch No is required."
            )

        elif not current_user:

            st.warning(
                "Current user is not available."
            )

    # ==========================================================================
    # SUBMIT BUTTON
    # ==========================================================================

    if st.button(
        "📤 Submit Inventory In for Approval",
        type="primary",
        disabled=not can_submit,
        key="inventory_import_submit",
        use_container_width=True,
    ):

        try:

            # ------------------------------------------------------------------
            # Safety re-read
            # ------------------------------------------------------------------

            submit_batch_no = str(
                st.session_state.get(
                    "inventory_import_batch_no_input",
                    "",
                )
            ).strip()

            if not submit_batch_no:

                st.error(
                    "Batch No is empty."
                )

                return

            if not current_user:

                st.error(
                    "Current user is not available."
                )

                return

            # ------------------------------------------------------------------
            # CREATE DRAFT
            # ------------------------------------------------------------------

            with st.spinner(
                "Creating Inventory In draft..."
            ):

                batch = _create_batch(
                    client=client,
                    batch_no=submit_batch_no,
                    warehouse_id=selected_warehouse_id,
                    remarks=remarks.strip()
                    or None,
                    user_id=current_user,
                )

            batch_id = batch.get(
                "id"
            )

            if not batch_id:

                raise RuntimeError(
                    "Inventory import batch ID was not returned."
                )

            # ------------------------------------------------------------------
            # VALID LINES
            # ------------------------------------------------------------------

            valid_df = preview_df[
                preview_df["Status"]
                == "VALID"
            ].copy()

            if valid_df.empty:

                raise RuntimeError(
                    "No valid import lines found."
                )

            # ------------------------------------------------------------------
            # INSERT LINES
            # ------------------------------------------------------------------

            with st.spinner(
                "Saving Inventory In lines..."
            ):

                _insert_import_lines(
                    client=client,
                    batch_id=batch_id,
                    warehouse_id=selected_warehouse_id,
                    valid_df=valid_df,
                )

            # ------------------------------------------------------------------
            # SUBMIT RPC
            #
            # IMPORTANT:
            # This only changes workflow state to PENDING.
            # It does NOT directly post stock.
            # ------------------------------------------------------------------

            with st.spinner(
                "Submitting for Checker approval..."
            ):

                result = _submit_batch(
                    client=client,
                    batch_no=submit_batch_no,
                )

            # ------------------------------------------------------------------
            # RESULT
            # ------------------------------------------------------------------

            success = bool(
                result.get(
                    "success",
                    False,
                )
                if isinstance(
                    result,
                    dict,
                )
                else False
            )

            if success:

                st.success(
                    "✅ Inventory In submitted successfully."
                )

                st.info(
                    "Maker-Checker: "
                    "DRAFT → PENDING → Checker Approval → POSTED"
                )

                if isinstance(
                    result,
                    dict,
                ):

                    st.json(
                        result
                    )

                # --------------------------------------------------------------
                # Clear preview state
                #
                # IMPORTANT:
                # We DO NOT modify the widget key here.
                # --------------------------------------------------------------

                st.session_state[
                    "inventory_import_preview"
                ] = None

                st.session_state[
                    "inventory_import_file_name"
                ] = ""

                st.session_state[
                    "inventory_import_validated"
                ] = False

                st.session_state[
                    "inventory_import_last_submitted_batch"
                ] = submit_batch_no

                # --------------------------------------------------------------
                # Request widget reset on NEXT rerun.
                #
                # This is the critical fix for:
                #
                # StreamlitAPIException:
                # st.session_state.inventory_import_batch_no_input
                # cannot be modified after the widget ...
                # --------------------------------------------------------------

                st.session_state[
                    "inventory_import_reset_batch"
                ] = True

                # --------------------------------------------------------------
                # Rerun.
                #
                # On next run:
                # _init_state()
                #      ↓
                # _render_import_batch()
                #      ↓
                # _apply_batch_reset_before_widget()
                #      ↓
                # widget is created with ""
                # --------------------------------------------------------------

                st.rerun()

            else:

                message = (
                    result.get(
                        "message",
                        "Inventory submission failed.",
                    )
                    if isinstance(
                        result,
                        dict,
                    )
                    else str(result)
                )

                st.error(
                    message
                )

                if isinstance(
                    result,
                    dict,
                ):

                    st.json(
                        result
                    )

        except Exception as e:

            st.error(
                f"Inventory In submission failed: {e}"
            )

    # ==========================================================================
    # LAST SUBMITTED BATCH
    # ==========================================================================

    last_submitted_batch = st.session_state.get(
        "inventory_import_last_submitted_batch",
        "",
    )

    if last_submitted_batch:

        st.success(
            f"Last submitted batch: "
            f"**{last_submitted_batch}**"
        )

    # ==========================================================================
    # WORKFLOW
    # ==========================================================================

    st.markdown("---")

    st.markdown(
        """
        **Inventory In Workflow**

        `Excel / CSV`
        → `Validate`
        → `Preview`
        → `DRAFT`
        → `Submit`
        → `PENDING`
        → `Checker Approval`
        → `POSTED`
        → `warehouse_stock`
        → `inventory_cost_layers`
        → `stock_movements`
        """
    )

    st.caption(
        "Maker cannot approve his own Inventory In batch."
    )
