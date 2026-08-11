# ==============================================================================
# erp_pages/inventory/product_import.py
#
# ERP ENTERPRISE PRODUCT MASTER IMPORT v1.0
#
# Purpose:
#   Product Master bulk import foundation
#
# Supported:
#   - CSV
#   - Excel (.xlsx / .xls)
#   - Template download
#   - Preview
#   - Basic validation
#   - Duplicate SKU / Barcode detection inside import file
#
# IMPORTANT:
#   This module DOES NOT write directly to products table.
#   Maker-Checker approval will be connected in the next step.
# ==============================================================================

import io
import csv
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
# REQUIRED COLUMNS
# ==============================================================================

REQUIRED_COLUMNS = [
    "sku",
    "name",
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
# NORMALIZE COLUMN NAME
# ==============================================================================

def _normalize_column_name(value):
    """
    Convert uploaded column names into standard ERP column names.
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
# NORMALIZE DATAFRAME
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

    # Keep known columns only
    for column in PRODUCT_IMPORT_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[PRODUCT_IMPORT_COLUMNS]

    return df


# ==============================================================================
# READ CSV
# ==============================================================================

def _read_csv(uploaded_file):
    """
    Read CSV with UTF-8 / UTF-8-SIG fallback.
    """

    if pd is None:
        raise RuntimeError(
            "pandas is not installed. "
            "Please add pandas to requirements.txt."
        )

    raw = uploaded_file.getvalue()

    # UTF-8 BOM
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    return pd.read_csv(
        io.StringIO(text),
        dtype=str,
        keep_default_na=False,
    )


# ==============================================================================
# READ EXCEL
# ==============================================================================

def _read_excel(uploaded_file):
    """
    Read Excel workbook.
    """

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
# LOAD FILE
# ==============================================================================

def _load_uploaded_file(uploaded_file):
    """
    Detect CSV / Excel and return DataFrame.
    """

    if uploaded_file is None:
        return None

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df = _read_csv(uploaded_file)

    elif file_name.endswith(".xlsx"):
        df = _read_excel(uploaded_file)

    elif file_name.endswith(".xls"):
        df = _read_excel(uploaded_file)

    else:
        raise ValueError(
            "Unsupported file format. "
            "Please upload CSV or Excel (.xlsx / .xls)."
        )

    return _normalize_dataframe(df)


# ==============================================================================
# BASIC VALIDATION
# ==============================================================================

def _validate_dataframe(df):
    """
    Validate imported Product Master rows.

    Returns:
        validated_df
        error_count
    """

    if df is None:
        return None, 0

    df = df.copy()

    # Make everything string first
    for column in PRODUCT_IMPORT_COLUMNS:
        if column in df.columns:
            df[column] = (
                df[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    # Validation columns
    df["is_valid"] = True
    df["error_message"] = ""

    # --------------------------------------------------------------------------
    # Required SKU
    # --------------------------------------------------------------------------

    missing_sku = df["sku"] == ""

    df.loc[missing_sku, "is_valid"] = False
    df.loc[missing_sku, "error_message"] = (
        "SKU is required"
    )

    # --------------------------------------------------------------------------
    # Required Product Name
    # --------------------------------------------------------------------------

    missing_name = df["name"] == ""

    df.loc[missing_name, "is_valid"] = False

    df.loc[
        missing_name & (df["error_message"] == ""),
        "error_message"
    ] = "Product name is required"

    # --------------------------------------------------------------------------
    # Duplicate SKU inside import file
    # --------------------------------------------------------------------------

    duplicate_sku = (
        df["sku"] != ""
    ) & df["sku"].duplicated(
        keep=False
    )

    df.loc[duplicate_sku, "is_valid"] = False

    df.loc[
        duplicate_sku & (df["error_message"] == ""),
        "error_message"
    ] = "Duplicate SKU in import file"

    # --------------------------------------------------------------------------
    # Duplicate Barcode inside import file
    # --------------------------------------------------------------------------

    barcode_mask = df["barcode"] != ""

    duplicate_barcode = (
        barcode_mask
        & df.loc[barcode_mask, "barcode"].duplicated(
            keep=False
        )
    )

    duplicate_barcode_index = duplicate_barcode[
        duplicate_barcode
    ].index

    df.loc[
        duplicate_barcode_index,
        "is_valid"
    ] = False

    for index in duplicate_barcode_index:
        if not df.loc[index, "error_message"]:
            df.loc[index, "error_message"] = (
                "Duplicate barcode in import file"
            )

    # --------------------------------------------------------------------------
    # Numeric Validation
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

                df.loc[index, "is_valid"] = False

                if not df.loc[index, "error_message"]:
                    df.loc[index, "error_message"] = (
                        f"Invalid {column}"
                    )

    # --------------------------------------------------------------------------
    # Final error count
    # --------------------------------------------------------------------------

    error_count = int(
        (~df["is_valid"]).sum()
    )

    return df, error_count


# ==============================================================================
# CSV TEMPLATE
# ==============================================================================

def _create_csv_template():
    """
    Create downloadable CSV template.
    """

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=PRODUCT_IMPORT_COLUMNS,
    )

    writer.writeheader()

    for row in TEMPLATE_ROWS:
        writer.writerow(row)

    return output.getvalue().encode("utf-8-sig")


# ==============================================================================
# EXCEL TEMPLATE
# ==============================================================================

def _create_excel_template():
    """
    Create downloadable Excel template.
    """

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
            "Use this template when importing hundreds or "
            "thousands of Product Master items."
        )

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
                label="⬇️ Download CSV Template",
                data=_create_csv_template(),
                file_name="product_master_import_template.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col2:

            excel_data = _create_excel_template()

            if excel_data:

                st.download_button(
                    label="⬇️ Download Excel Template",
                    data=excel_data,
                    file_name="product_master_import_template.xlsx",
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
# IMPORT PREVIEW
# ==============================================================================

def _render_preview(df):

    if df is None or df.empty:

        st.warning(
            "No product records found in the uploaded file."
        )

        return

    validated_df, error_count = _validate_dataframe(df)

    total_count = len(validated_df)

    valid_count = total_count - error_count

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
    # Validation result
    # --------------------------------------------------------------------------

    if error_count == 0:

        st.success(
            "All imported Product Master rows passed basic validation."
        )

    else:

        st.error(
            f"{error_count} row(s) require correction before submission."
        )

    # --------------------------------------------------------------------------
    # Preview tabs
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

    # --------------------------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------------------------

    if error_count > 0:

        st.warning(
            "Please correct the error rows and upload the file again."
        )

    else:

        st.info(
            "Validation passed. Maker-Checker submission will be "
            "connected in the next step."
        )


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render_product_import():

    st.subheader(
        "📦 Product Master Bulk Import"
    )

    st.caption(
        "ERP Enterprise Product Master | CSV / Excel | "
        "Bulk Import | Maker-Checker"
    )

    # --------------------------------------------------------------------------
    # INFORMATION
    # --------------------------------------------------------------------------

    st.info(
        "Import hundreds of Product Master items using CSV or Excel. "
        "This step validates and previews the file before database submission."
    )

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
            "Upload CSV or Excel containing Product Master records."
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
            "The uploaded file contains no data."
        )

        return

    # --------------------------------------------------------------------------
    # PREVIEW
    # --------------------------------------------------------------------------

    _render_preview(df)


# ==============================================================================
# LEGACY / OPTIONAL ENTRY
# ==============================================================================

def render_inventory_import():
    """
    Backward-compatible wrapper.

    IMPORTANT:
    Inventory In and Product Master Import are different workflows.

    This wrapper is kept only so older imports do not immediately break.
    """

    return render_product_import()
