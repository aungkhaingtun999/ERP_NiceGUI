# ==============================================================================
# erp_pages/inventory/product_import.py
#
# ERP ENTERPRISE PRODUCT MASTER BULK IMPORT v2.1
#
# CSV / Excel
# Template Download
# Preview
# Validation
# Duplicate Detection
# Maker-Checker Submission
#
# IMPORTANT
# ------------------------------------------------------------------------------
# This module NEVER writes directly to products table.
#
# Flow:
#
# CSV / Excel
#      ↓
# Validation
#      ↓
# Preview
#      ↓
# request_product_create_rpc()
#      ↓
# product_create_requests
#      ↓
# PENDING
#      ↓
# Checker Approval
#      ↓
# approve_product_create_rpc()
#      ↓
# products + stock + FIFO
# ==============================================================================

import io
import csv
import uuid

import streamlit as st


# ==============================================================================
# OPTIONAL PANDAS
# ==============================================================================

try:
    import pandas as pd
except ImportError:
    pd = None


# ==============================================================================
# IMPORT COLUMNS
# ==============================================================================

PRODUCT_IMPORT_COLUMNS = [
    "sku",
    "barcode",
    "name",
    "category",
    "brand",
    "unit",
    "purchase_price",
    "selling_price",
    "tax_rate",
    "minimum_stock",
]


# ==============================================================================
# TEMPLATE DATA
# ==============================================================================

TEMPLATE_ROWS = [
    {
        "sku": "TEA-001",
        "barcode": "890000000001",
        "name": "Myanmar Tea",
        "category": "Tea",
        "brand": "Example Brand",
        "unit": "PCS",
        "purchase_price": 1000,
        "selling_price": 1200,
        "tax_rate": 0,
        "minimum_stock": 10,
    },
    {
        "sku": "COF-001",
        "barcode": "890000000002",
        "name": "Coffee",
        "category": "Coffee",
        "brand": "Example Brand",
        "unit": "PCS",
        "purchase_price": 2000,
        "selling_price": 2500,
        "tax_rate": 0,
        "minimum_stock": 10,
    },
]


# ==============================================================================
# COLUMN NORMALIZATION
# ==============================================================================

def _normalize_column_name(value):
    """
    Convert common CSV / Excel column names
    into ERP standard column names.
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    replacements = {
        "product sku": "sku",
        "product_sku": "sku",
        "item sku": "sku",
        "item_sku": "sku",

        "product barcode": "barcode",
        "product_barcode": "barcode",
        "item barcode": "barcode",
        "item_barcode": "barcode",

        "product name": "name",
        "product_name": "name",
        "item name": "name",
        "item_name": "name",

        "category name": "category",
        "category_name": "category",

        "brand name": "brand",
        "brand_name": "brand",

        "unit name": "unit",
        "unit_name": "unit",

        "purchase price": "purchase_price",
        "purchase_price": "purchase_price",
        "cost": "purchase_price",
        "cost price": "purchase_price",

        "selling price": "selling_price",
        "selling_price": "selling_price",
        "sale price": "selling_price",

        "tax": "tax_rate",
        "tax rate": "tax_rate",
        "tax_rate": "tax_rate",

        "minimum stock": "minimum_stock",
        "minimum_stock": "minimum_stock",
        "min stock": "minimum_stock",
        "min_stock": "minimum_stock",
    }

    return replacements.get(value, value)


# ==============================================================================
# DATAFRAME NORMALIZATION
# ==============================================================================

def _normalize_dataframe(df):
    """
    Normalize uploaded DataFrame.
    """

    if df is None:
        return None

    df = df.copy()

    df.columns = [
        _normalize_column_name(column)
        for column in df.columns
    ]

    for column in PRODUCT_IMPORT_COLUMNS:

        if column not in df.columns:
            df[column] = ""

    return df[PRODUCT_IMPORT_COLUMNS]


# ==============================================================================
# CSV READER
# ==============================================================================

def _read_csv(uploaded_file):

    if pd is None:
        raise RuntimeError(
            "pandas is not installed. "
            "Please add pandas to requirements.txt."
        )

    raw = uploaded_file.getvalue()

    try:
        text = raw.decode("utf-8-sig")

    except UnicodeDecodeError:

        text = raw.decode(
            "utf-8",
            errors="replace",
        )

    return pd.read_csv(
        io.StringIO(text),
        dtype=str,
        keep_default_na=False,
    )


# ==============================================================================
# EXCEL READER
# ==============================================================================

def _read_excel(uploaded_file):

    if pd is None:
        raise RuntimeError(
            "pandas is not installed. "
            "Please add pandas to requirements.txt."
        )

    return pd.read_excel(
        uploaded_file,
        dtype=str,
        keep_default_na=False,
    )


# ==============================================================================
# FILE LOADER
# ==============================================================================

def _load_uploaded_file(uploaded_file):

    if uploaded_file is None:
        return None

    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):

        df = _read_csv(uploaded_file)

    elif filename.endswith(".xlsx"):

        df = _read_excel(uploaded_file)

    elif filename.endswith(".xls"):

        df = _read_excel(uploaded_file)

    else:

        raise ValueError(
            "Unsupported file format. "
            "Please upload CSV or Excel (.xlsx / .xls)."
        )

    return _normalize_dataframe(df)


# ==============================================================================
# VALIDATION
# ==============================================================================

def _validate_dataframe(df):

    if df is None:
        return None, 0

    df = df.copy()

    # --------------------------------------------------------------------------
    # STRING CLEANUP
    # --------------------------------------------------------------------------

    for column in PRODUCT_IMPORT_COLUMNS:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # --------------------------------------------------------------------------
    # VALIDATION COLUMNS
    # --------------------------------------------------------------------------

    df["is_valid"] = True
    df["error_message"] = ""

    # --------------------------------------------------------------------------
    # REQUIRED SKU
    # --------------------------------------------------------------------------

    missing_sku = df["sku"] == ""

    df.loc[
        missing_sku,
        "is_valid",
    ] = False

    df.loc[
        missing_sku,
        "error_message",
    ] = "SKU is required"

    # --------------------------------------------------------------------------
    # REQUIRED NAME
    # --------------------------------------------------------------------------

    missing_name = df["name"] == ""

    df.loc[
        missing_name,
        "is_valid",
    ] = False

    df.loc[
        missing_name
        & (df["error_message"] == ""),
        "error_message",
    ] = "Product name is required"

    # --------------------------------------------------------------------------
    # DUPLICATE SKU
    # --------------------------------------------------------------------------

    duplicate_sku = (
        (df["sku"] != "")
        & df["sku"].duplicated(
            keep=False
        )
    )

    df.loc[
        duplicate_sku,
        "is_valid",
    ] = False

    df.loc[
        duplicate_sku
        & (df["error_message"] == ""),
        "error_message",
    ] = "Duplicate SKU in import file"

    # --------------------------------------------------------------------------
    # DUPLICATE BARCODE
    # --------------------------------------------------------------------------

    barcode_mask = df["barcode"] != ""

    duplicate_barcode = (
        barcode_mask
        & df.loc[
            barcode_mask,
            "barcode",
        ].duplicated(
            keep=False,
        )
    )

    duplicate_barcode_indexes = (
        duplicate_barcode[
            duplicate_barcode
        ].index
    )

    df.loc[
        duplicate_barcode_indexes,
        "is_valid",
    ] = False

    for index in duplicate_barcode_indexes:

        if not df.loc[
            index,
            "error_message",
        ]:

            df.loc[
                index,
                "error_message",
            ] = "Duplicate barcode in import file"

    # --------------------------------------------------------------------------
    # NUMERIC VALIDATION
    # --------------------------------------------------------------------------

    numeric_columns = [
        "purchase_price",
        "selling_price",
        "tax_rate",
        "minimum_stock",
    ]

    for column in numeric_columns:

        for index, value in df[column].items():

            if value == "":
                continue

            try:

                number = float(value)

                if number < 0:
                    raise ValueError

            except Exception:

                df.loc[
                    index,
                    "is_valid",
                ] = False

                if not df.loc[
                    index,
                    "error_message",
                ]:

                    df.loc[
                        index,
                        "error_message",
                    ] = f"Invalid {column}"

    # --------------------------------------------------------------------------
    # FINAL COUNT
    # --------------------------------------------------------------------------

    error_count = int(
        (~df["is_valid"]).sum()
    )

    return df, error_count


# ==============================================================================
# CSV TEMPLATE
# ==============================================================================

def _create_csv_template():

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=PRODUCT_IMPORT_COLUMNS,
    )

    writer.writeheader()

    for row in TEMPLATE_ROWS:
        writer.writerow(row)

    return output.getvalue().encode(
        "utf-8-sig"
    )


# ==============================================================================
# EXCEL TEMPLATE
# ==============================================================================

def _create_excel_template():

    if pd is None:
        return None

    df = pd.DataFrame(
        TEMPLATE_ROWS,
        columns=PRODUCT_IMPORT_COLUMNS,
    )

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Products",
        )

    output.seek(0)

    return output.getvalue()


# ==============================================================================
# TEMPLATE UI
# ==============================================================================

def _render_template_section():

    with st.expander(
        "📄 Product Import Template",
        expanded=False,
    ):

        st.write(
            "Use this template to import hundreds or "
            "thousands of Product Master items."
        )

        if pd is not None:

            st.dataframe(
                pd.DataFrame(
                    TEMPLATE_ROWS,
                    columns=PRODUCT_IMPORT_COLUMNS,
                ),
                use_container_width=True,
                hide_index=True,
            )

        col1, col2 = st.columns(2)

        with col1:

            st.download_button(
                "⬇️ Download CSV Template",
                data=_create_csv_template(),
                file_name=(
                    "product_master_import_template.csv"
                ),
                mime="text/csv",
                use_container_width=True,
            )

        with col2:

            excel_data = _create_excel_template()

            if excel_data:

                st.download_button(
                    "⬇️ Download Excel Template",
                    data=excel_data,
                    file_name=(
                        "product_master_import_template.xlsx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.spreadsheetml.sheet"
                    ),
                    use_container_width=True,
                )

            else:

                st.warning(
                    "Excel template requires pandas/openpyxl."
                )


# ==============================================================================
# USER ID RESOLUTION
# ==============================================================================

def _get_current_user_id():

    """
    Try common ERP session-state user ID keys.

    Never invent a user ID.
    """

    candidate_keys = [
        "user_id",
        "current_user_id",
        "logged_in_user_id",
        "auth_user_id",
        "user_uuid",
    ]

    for key in candidate_keys:

        value = st.session_state.get(key)

        if not value:
            continue

        try:

            return str(
                uuid.UUID(str(value))
            )

        except Exception:

            continue

    user = st.session_state.get("user")

    if isinstance(user, dict):

        for key in [
            "id",
            "user_id",
            "uuid",
        ]:

            value = user.get(key)

            if not value:
                continue

            try:

                return str(
                    uuid.UUID(str(value))
                )

            except Exception:

                continue

    return None

# ==============================================================================
# PRODUCT DATA BUILDER
# ==============================================================================

def _row_to_product_data(row):
    """
    Convert one validated import row into the JSON payload
    expected by request_product_create_rpc().
    """

    def _text_or_none(value):
        if value is None:
            return None

        value = str(value).strip()

        return value if value else None

    def _float_or_none(value):
        value = _text_or_none(value)

        if value is None:
            return None

        return float(value)

    def _int_or_zero(value):
        value = _text_or_none(value)

        if value is None:
            return 0

        return int(float(value))

    return {
        "sku": _text_or_none(row["sku"]),
        "barcode": _text_or_none(row["barcode"]),
        "name": _text_or_none(row["name"]),
        "category": _text_or_none(row["category"]),
        "brand": _text_or_none(row["brand"]),
        "unit": _text_or_none(row["unit"]),

        "purchase_price": _float_or_none(
            row["purchase_price"]
        ),

        "selling_price": _float_or_none(
            row["selling_price"]
        ),

        "tax_rate": _float_or_none(
            row["tax_rate"]
        ),

        "minimum_stock": _int_or_zero(
            row["minimum_stock"]
        ),

        # Keep current ERP pricing architecture.
        "price_source": "PRICING_SERVICE",
    }


# ==============================================================================
# SUBMIT ONE PRODUCT REQUEST
# ==============================================================================

def _submit_product_request(
    client,
    row,
    warehouse_id,
    requested_by,
    reason,
):
    """
    Submit exactly ONE product creation request.

    IMPORTANT:
    This calls request_product_create_rpc().
    It does NOT insert into products directly.
    """

    if client is None:
        raise RuntimeError(
            "ERP database client is not available."
        )

    if warehouse_id is None:
        raise RuntimeError(
            "Warehouse ID is required."
        )

    if requested_by is None:
        raise RuntimeError(
            "Current user ID could not be resolved."
        )

    product_data = _row_to_product_data(row)

    response = client.rpc(
        "request_product_create_rpc",
        {
            "p_product_data": product_data,
            "p_warehouse_id": int(warehouse_id),
            "p_initial_qty": 0,
            "p_reason": reason,
            "p_requested_by": requested_by,
        },
    ).execute()

    return response.data


# ==============================================================================
# SUBMIT VALID PRODUCTS
# ==============================================================================

def _submit_valid_products(
    client,
    validated_df,
    warehouse_id,
    requested_by,
):
    """
    Submit all valid rows as separate Maker requests.

    Example:
        300 valid products
        ↓
        300 request_product_create_rpc() calls
        ↓
        300 PENDING requests

    No direct product INSERT happens here.
    """

    if validated_df is None:
        return {
            "submitted": 0,
            "failed": 0,
            "results": [],
        }

    valid_df = validated_df[
        validated_df["is_valid"] == True
    ].copy()

    if valid_df.empty:
        return {
            "submitted": 0,
            "failed": 0,
            "results": [],
        }

    results = []

    submitted = 0
    failed = 0

    reason = (
        "Product Master bulk import request "
        "from Inventory UI"
    )

    total = len(valid_df)

    progress = st.progress(
        0,
        text="Submitting Product requests...",
    )

    for position, (_, row) in enumerate(
        valid_df.iterrows(),
        start=1,
    ):

        sku = str(row["sku"]).strip()
        name = str(row["name"]).strip()

        try:

            result = _submit_product_request(
                client=client,
                row=row,
                warehouse_id=warehouse_id,
                requested_by=requested_by,
                reason=reason,
            )

            success = False

            if isinstance(result, dict):

                success = bool(
                    result.get(
                        "success",
                        False,
                    )
                )

            elif isinstance(result, list) and result:

                first_result = result[0]

                if isinstance(first_result, dict):

                    success = bool(
                        first_result.get(
                            "success",
                            False,
                        )
                    )

            if success:

                submitted += 1

            else:

                failed += 1

            if isinstance(result, dict):

                message = result.get(
                    "message",
                    "",
                )

                request_id = result.get(
                    "request_id"
                )

            elif isinstance(result, list) and result:

                first_result = result[0]

                if isinstance(first_result, dict):

                    message = first_result.get(
                        "message",
                        "",
                    )

                    request_id = first_result.get(
                        "request_id"
                    )

                else:

                    message = str(
                        first_result
                    )

                    request_id = None

            else:

                message = str(result)

                request_id = None

            results.append(
                {
                    "sku": sku,
                    "name": name,
                    "success": success,
                    "message": message,
                    "request_id": request_id,
                }
            )

        except Exception as e:

            failed += 1

            results.append(
                {
                    "sku": sku,
                    "name": name,
                    "success": False,
                    "message": str(e),
                    "request_id": None,
                }
            )

        progress.progress(
            position / total,
            text=(
                f"Submitting {position}/{total} "
                f"| SKU: {sku}"
            ),
        )

    progress.empty()

    return {
        "submitted": submitted,
        "failed": failed,
        "results": results,
    }


# ==============================================================================
# PREVIEW
# ==============================================================================

def _render_preview(
    client,
    df,
    warehouse_id,
):
    """
    Display validation preview and Maker-Checker submission button.
    """

    if df is None or df.empty:

        st.warning(
            "No product records found."
        )

        return

    validated_df, error_count = (
        _validate_dataframe(df)
    )

    total_count = len(
        validated_df
    )

    valid_count = (
        total_count - error_count
    )

    # --------------------------------------------------------------------------
    # KPI
    # --------------------------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Rows",
            total_count,
        )

    with col2:

        st.metric(
            "Valid Rows",
            valid_count,
        )

    with col3:

        st.metric(
            "Error Rows",
            error_count,
        )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # VALIDATION STATUS
    # --------------------------------------------------------------------------

    if error_count == 0:

        st.success(
            "All Product Master rows passed basic validation."
        )

    else:

        st.error(
            f"{error_count} row(s) require correction."
        )

    # --------------------------------------------------------------------------
    # PREVIEW TABS
    # --------------------------------------------------------------------------

    tab_all, tab_valid, tab_errors = st.tabs(
        [
            "📋 All",
            "✅ Valid",
            "❌ Errors",
        ]
    )

    with tab_all:

        st.dataframe(
            validated_df,
            use_container_width=True,
            hide_index=True,
        )

    with tab_valid:

        valid_df = validated_df[
            validated_df["is_valid"] == True
        ]

        st.dataframe(
            valid_df,
            use_container_width=True,
            hide_index=True,
        )

    with tab_errors:

        error_df = validated_df[
            validated_df["is_valid"] == False
        ]

        if error_df.empty:

            st.success(
                "No validation errors."
            )

        else:

            st.dataframe(
                error_df,
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # BLOCK SUBMISSION IF VALIDATION FAILS
    # --------------------------------------------------------------------------

    if error_count > 0:

        st.warning(
            "❌ Submission is disabled until all error rows "
            "are corrected."
        )

        return

    # --------------------------------------------------------------------------
    # USER ID
    # --------------------------------------------------------------------------

    requested_by = (
        _get_current_user_id()
    )

    if not requested_by:

        st.error(
            "Current ERP user ID could not be resolved. "
            "Please log in again."
        )

        return

    # --------------------------------------------------------------------------
    # DATABASE CLIENT
    # --------------------------------------------------------------------------

    if client is None:

        st.error(
            "ERP database client is not available."
        )

        return

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    if warehouse_id is None:

        st.error(
            "Destination warehouse is required."
        )

        return

    # --------------------------------------------------------------------------
    # MAKER-CHECKER INFORMATION
    # --------------------------------------------------------------------------

    st.info(
        "⚠️ Submission creates PENDING Product Master requests only. "
        "Products will NOT be created until a Checker approves them."
    )

    # --------------------------------------------------------------------------
    # SUBMIT BUTTON
    # --------------------------------------------------------------------------

    submit_key = (
        "submit_product_master_import"
    )

    if st.button(
        "🚀 Submit All Valid Products for Approval",
        type="primary",
        use_container_width=True,
        key=submit_key,
    ):

        with st.spinner(
            "Submitting Product Master requests..."
        ):

            result = _submit_valid_products(
                client=client,
                validated_df=validated_df,
                warehouse_id=warehouse_id,
                requested_by=requested_by,
            )

        submitted = result.get(
            "submitted",
            0,
        )

        failed = result.get(
            "failed",
            0,
        )

        # ----------------------------------------------------------------------
        # RESULT
        # ----------------------------------------------------------------------

        if submitted > 0:

            st.success(
                f"✅ {submitted} Product request(s) "
                f"submitted successfully as PENDING."
            )

        if failed > 0:

            st.error(
                f"❌ {failed} Product request(s) failed."
            )

        # ----------------------------------------------------------------------
        # RESULT TABLE
        # ----------------------------------------------------------------------

        results = result.get(
            "results",
            [],
        )

        if results:

            result_df = pd.DataFrame(
                results
            )

            st.dataframe(
                result_df,
                use_container_width=True,
                hide_index=True,
            )

        # ----------------------------------------------------------------------
        # REFRESH APPROVAL QUEUE
        # ----------------------------------------------------------------------

        if submitted > 0:

            st.info(
                "Product requests are now waiting in "
                "Product Approval Queue."
            )


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render_product_import(
    db_client=None,
    warehouse_id=None,
):
    """
    Main Product Master Bulk Import UI.

    Parameters:
        db_client:
            Supabase / ERP database client.

        warehouse_id:
            Selected destination warehouse.

    IMPORTANT:
        This function never directly inserts products.
    """

    st.subheader(
        "📦 Product Master Bulk Import"
    )

    st.caption(
        "ERP Enterprise Product Master | "
        "CSV / Excel | Bulk Import | Maker-Checker"
    )

    # --------------------------------------------------------------------------
    # INFORMATION
    # --------------------------------------------------------------------------

    st.info(
        "Import hundreds or thousands of Product Master items "
        "using CSV or Excel. The file is validated first, then "
        "submitted as Maker-Checker requests."
    )

    # --------------------------------------------------------------------------
    # DESTINATION WAREHOUSE
    # --------------------------------------------------------------------------

    if warehouse_id is not None:

        st.success(
            f"Destination Warehouse ID: {warehouse_id}"
        )

    else:

        st.warning(
            "No destination warehouse selected."
        )

    # --------------------------------------------------------------------------
    # DATABASE STATUS
    # --------------------------------------------------------------------------

    if db_client is None:

        st.error(
            "ERP database client is not available."
        )

        st.info(
            "Please return to the Inventory page and "
            "select a warehouse before using Product Import."
        )

        return

    # --------------------------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------------------------

    _render_template_section()

    st.markdown("---")

    # --------------------------------------------------------------------------
    # FILE UPLOAD
    # --------------------------------------------------------------------------

    uploaded_file = st.file_uploader(
        "📤 Upload Product Master CSV / Excel",
        type=[
            "csv",
            "xlsx",
            "xls",
        ],
        key="product_master_import_uploader",
        help=(
            "Upload a CSV or Excel file containing "
            "Product Master records."
        ),
    )

    if uploaded_file is None:

        st.info(
            "Please upload a CSV or Excel file to continue."
        )

        return

    # --------------------------------------------------------------------------
    # FILE INFORMATION
    # --------------------------------------------------------------------------

    st.caption(
        f"File: {uploaded_file.name} | "
        f"Size: {uploaded_file.size:,} bytes"
    )

    # --------------------------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------------------------

    try:

        df = _load_uploaded_file(
            uploaded_file
        )

    except Exception as e:

        st.error(
            f"Unable to read import file: {e}"
        )

        return

    # --------------------------------------------------------------------------
    # EMPTY FILE
    # --------------------------------------------------------------------------

    if df is None or df.empty:

        st.error(
            "The uploaded file contains no product data."
        )

        return

    # --------------------------------------------------------------------------
    # PREVIEW + SUBMISSION
    # --------------------------------------------------------------------------

    _render_preview(
        client=db_client,
        df=df,
        warehouse_id=warehouse_id,
    )
