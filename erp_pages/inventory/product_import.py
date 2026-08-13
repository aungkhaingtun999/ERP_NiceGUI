# ==============================================================================
# erp_pages/inventory/product_import.py
#
# ERP ENTERPRISE PRODUCT MASTER BULK IMPORT
# ------------------------------------------------------------------------------
# CSV / Excel
# Product Master
# Maker-Checker
# Request Product Create RPC
#
# IMPORTANT:
#   This module NEVER directly inserts into products.
#
# FLOW:
#
# CSV / Excel
#      ↓
# Normalize
#      ↓
# Validate
#      ↓
# request_product_create_rpc()
#      ↓
# PENDING
#      ↓
# Product Approval Queue
#      ↓
# approve_product_create_rpc()
#      ↓
# create_product_full()
#
# Compatible with:
#
#     render_product_import(warehouse_id=...)
#
# and:
#
#     render_product_import(
#         db_client=client,
#         warehouse_id=warehouse_id,
#     )
# ==============================================================================

import io
import csv
import uuid
from datetime import datetime

import streamlit as st

from database import db


# ==============================================================================
# OPTIONAL PANDAS
# ==============================================================================

try:
    import pandas as pd
except ImportError:
    pd = None


# ==============================================================================
# IMPORT COLUMNS
# ------------------------------------------------------------------------------
# These are the ERP-supported Product Master import columns.
#
# tax_rate and minimum_stock are OPTIONAL for backward compatibility.
# A CSV containing only the first 8 columns is valid.
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

PRODUCT_REQUIRED_COLUMNS = [
    "sku",
    "barcode",
    "name",
    "unit",
    "purchase_price",
    "selling_price",
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
        "brand": "Premium Food",
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
        "brand": "Premium Food",
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
    Normalize common CSV / Excel column names
    into ERP standard column names.
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    replacements = {
        # SKU
        "product sku": "sku",
        "product_sku": "sku",
        "item sku": "sku",
        "item_sku": "sku",

        # Barcode
        "product barcode": "barcode",
        "product_barcode": "barcode",
        "item barcode": "barcode",
        "item_barcode": "barcode",

        # Name
        "product name": "name",
        "product_name": "name",
        "item name": "name",
        "item_name": "name",

        # Category
        "category name": "category",
        "category_name": "category",

        # Brand
        "brand name": "brand",
        "brand_name": "brand",

        # Unit
        "unit name": "unit",
        "unit_name": "unit",

        # Purchase
        "purchase price": "purchase_price",
        "purchase_price": "purchase_price",
        "cost": "purchase_price",
        "cost price": "purchase_price",
        "cost_price": "purchase_price",

        # Selling
        "selling price": "selling_price",
        "selling_price": "selling_price",
        "sale price": "selling_price",
        "sale_price": "selling_price",

        # Tax
        "tax": "tax_rate",
        "tax rate": "tax_rate",
        "tax_rate": "tax_rate",

        # Minimum stock
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

    Missing OPTIONAL columns are automatically added.

    The user's original 8-column format is therefore accepted:

        sku
        barcode
        name
        category
        brand
        unit
        purchase_price
        selling_price
    """

    if df is None:
        return None

    df = df.copy()

    # Normalize headers
    df.columns = [
        _normalize_column_name(column)
        for column in df.columns
    ]

    # Remove completely unnamed Excel columns
    valid_columns = []

    for column in df.columns:
        column_name = str(column).strip()

        if not column_name:
            continue

        if column_name.startswith("Unnamed:"):
            continue

        valid_columns.append(column)

    df = df[valid_columns]

    # Add missing ERP columns
    for column in PRODUCT_IMPORT_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    # Keep only ERP columns
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

    # UTF-8 BOM
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode(
            "utf-8",
            errors="replace",
        )

    # First attempt: normal CSV
    try:
        return pd.read_csv(
            io.StringIO(text),
            dtype=str,
            keep_default_na=False,
        )
    except Exception:

        # Fallback for unusual delimiter
        return pd.read_csv(
            io.StringIO(text),
            dtype=str,
            keep_default_na=False,
            sep=None,
            engine="python",
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

    filename = str(
        uploaded_file.name
    ).lower()

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
# VALIDATION HELPERS
# ==============================================================================


def _is_blank(value):

    if value is None:
        return True

    return str(value).strip() == ""


def _safe_float(value):

    if _is_blank(value):
        return None

    return float(
        str(value).strip()
    )


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

        if column not in df.columns:
            df[column] = ""

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

    missing_sku = (
        df["sku"] == ""
    )

    df.loc[
        missing_sku,
        "is_valid",
    ] = False

    df.loc[
        missing_sku
        & (df["error_message"] == ""),
        "error_message",
    ] = "SKU is required"

    # --------------------------------------------------------------------------
    # REQUIRED BARCODE
    # --------------------------------------------------------------------------

    missing_barcode = (
        df["barcode"] == ""
    )

    df.loc[
        missing_barcode,
        "is_valid",
    ] = False

    df.loc[
        missing_barcode
        & (df["error_message"] == ""),
        "error_message",
    ] = "Barcode is required"

    # --------------------------------------------------------------------------
    # REQUIRED NAME
    # --------------------------------------------------------------------------

    missing_name = (
        df["name"] == ""
    )

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
    # REQUIRED UNIT
    # --------------------------------------------------------------------------

    missing_unit = (
        df["unit"] == ""
    )

    df.loc[
        missing_unit,
        "is_valid",
    ] = False

    df.loc[
        missing_unit
        & (df["error_message"] == ""),
        "error_message",
    ] = "Unit is required"

    # --------------------------------------------------------------------------
    # PURCHASE PRICE
    # --------------------------------------------------------------------------

    for index, value in df["purchase_price"].items():

        if _is_blank(value):

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
                ] = "Purchase price is required"

            continue

        try:

            number = float(
                str(value).strip()
            )

            if number <= 0:
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
                ] = "Invalid purchase_price"

    # --------------------------------------------------------------------------
    # SELLING PRICE
    #
    # The CSV selling_price is required as Product Master data.
    #
    # NOTE:
    # Current create_product_full() pricing engine remains the DB
    # source of truth for final_selling_price.
    # --------------------------------------------------------------------------

    for index, value in df["selling_price"].items():

        if _is_blank(value):

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
                ] = "Selling price is required"

            continue

        try:

            number = float(
                str(value).strip()
            )

            if number <= 0:
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
                ] = "Invalid selling_price"

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

    barcode_mask = (
        df["barcode"] != ""
    )

    duplicate_barcode = pd.Series(
        False,
        index=df.index,
    )

    if barcode_mask.any():

        duplicate_values = (
            df.loc[
                barcode_mask,
                "barcode",
            ]
            .duplicated(
                keep=False
            )
        )

        duplicate_barcode.loc[
            duplicate_values.index
        ] = duplicate_values.values

    df.loc[
        duplicate_barcode,
        "is_valid",
    ] = False

    for index in duplicate_barcode[
        duplicate_barcode
    ].index:

        if not df.loc[
            index,
            "error_message",
        ]:

            df.loc[
                index,
                "error_message",
            ] = "Duplicate barcode in import file"

    # --------------------------------------------------------------------------
    # OPTIONAL NUMERIC COLUMNS
    # --------------------------------------------------------------------------

    optional_numeric_columns = [
        "tax_rate",
        "minimum_stock",
    ]

    for column in optional_numeric_columns:

        for index, value in df[column].items():

            if _is_blank(value):
                continue

            try:

                number = float(
                    str(value).strip()
                )

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
                    ] = (
                        f"Invalid {column}"
                    )

    # --------------------------------------------------------------------------
    # FINAL COUNT
    # --------------------------------------------------------------------------

    error_count = int(
        (
            ~df["is_valid"]
        ).sum()
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
            "Use this template to import hundreds "
            "or thousands of Product Master items."
        )

        st.caption(
            "The first 8 columns are supported. "
            "tax_rate and minimum_stock are optional."
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

            excel_data = (
                _create_excel_template()
            )

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
# IMPORT BATCH NUMBER
# ==============================================================================


def _generate_inventory_import_batch_no():

    today = datetime.now().strftime(
        "%Y%m%d"
    )

    prefix = (
        f"INV-IN-{today}-"
    )

    sequence_key = (
        "inventory_import_batch_sequence"
    )

    current_sequence = (
        st.session_state.get(
            sequence_key,
            0,
        )
    )

    current_sequence += 1

    st.session_state[
        sequence_key
    ] = current_sequence

    return (
        f"{prefix}"
        f"{current_sequence:03d}"
    )


def _on_click_generate_batch():

    st.session_state[
        "inventory_import_batch_no"
    ] = (
        _generate_inventory_import_batch_no()
    )


# ==============================================================================
# IMPORT BATCH UI
# ==============================================================================


def _render_import_batch():

    if (
        "inventory_import_batch_no"
        not in st.session_state
    ):

        st.session_state[
            "inventory_import_batch_no"
        ] = ""

    st.markdown(
        "### 📦 Import Batch"
    )

    col1, col2 = st.columns(
        [4, 1],
        vertical_alignment="bottom",
    )

    with col1:

        st.text_input(
            "Batch No",
            key="inventory_import_batch_no",
            placeholder=(
                "INV-IN-YYYYMMDD-001"
            ),
        )

    with col2:

        st.button(
            "Generate Batch No",
            key=(
                "generate_inventory_import_batch_no_btn"
            ),
            type="secondary",
            use_container_width=True,
            on_click=_on_click_generate_batch,
        )

    batch_no = (
        st.session_state.get(
            "inventory_import_batch_no",
            "",
        )
        .strip()
    )

    if batch_no:

        st.success(
            f"Import Batch: **{batch_no}**"
        )

    return batch_no


# ==============================================================================
# USER ID RESOLUTION
# ==============================================================================


def _get_current_user_id():

    """
    Resolve current ERP user UUID.

    Never invents a UUID.
    """

    candidate_keys = [
        "user_id",
        "current_user_id",
        "logged_in_user_id",
        "auth_user_id",
        "user_uuid",
    ]

    for key in candidate_keys:

        value = st.session_state.get(
            key
        )

        if not value:
            continue

        try:

            return str(
                uuid.UUID(
                    str(value)
                )
            )

        except Exception:
            continue

    # --------------------------------------------------------------------------
    # USER OBJECT
    # --------------------------------------------------------------------------

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

            if not value:
                continue

            try:

                return str(
                    uuid.UUID(
                        str(value)
                    )
                )

            except Exception:
                continue

    return None


# ==============================================================================
# RPC RESULT NORMALIZER
# ==============================================================================


def _normalize_rpc_result(result):

    """
    Supabase RPC may return:

        dict

    or:

        [dict]
    """

    if isinstance(result, dict):

        return result

    if (
        isinstance(result, list)
        and result
        and isinstance(
            result[0],
            dict,
        )
    ):

        return result[0]

    return {
        "success": False,
        "status": "ERROR",
        "message": str(result),
    }


# ==============================================================================
# PRODUCT DATA BUILDER
# ==============================================================================


def _row_to_product_data(
    row,
    batch_no=None,
):
    """
    Convert one validated import row into the JSON payload
    expected by request_product_create_rpc().
    """

    def _text_or_none(value):

        if value is None:
            return None

        value = str(
            value
        ).strip()

        return (
            value
            if value
            else None
        )

    def _float_or_none(value):

        value = _text_or_none(
            value
        )

        if value is None:
            return None

        return float(value)

    def _int_or_zero(value):

        value = _text_or_none(
            value
        )

        if value is None:
            return 0

        return int(
            float(value)
        )

    purchase_price = (
        _float_or_none(
            row["purchase_price"]
        )
    )

    selling_price = (
        _float_or_none(
            row["selling_price"]
        )
    )

    tax_rate = (
        _float_or_none(
            row["tax_rate"]
        )
    )

    minimum_stock = (
        _int_or_zero(
            row["minimum_stock"]
        )
    )

    # --------------------------------------------------------------------------
    # IMPORTANT
    #
    # Keep BOTH:
    #
    # selling_price
    #
    # and:
    #
    # owner_selling_price
    #
    # for compatibility with the current pricing architecture.
    #
    # We do NOT change the DB pricing engine here.
    # --------------------------------------------------------------------------

    return {

        "sku": _text_or_none(
            row["sku"]
        ),

        "barcode": _text_or_none(
            row["barcode"]
        ),

        "name": _text_or_none(
            row["name"]
        ),

        "category": _text_or_none(
            row["category"]
        ),

        "brand": _text_or_none(
            row["brand"]
        ),

        "unit": _text_or_none(
            row["unit"]
        ),

        "purchase_price": (
            purchase_price
        ),

        "selling_price": (
            selling_price
        ),

        "owner_selling_price": (
            selling_price
        ),

        "tax_rate": tax_rate,

        "minimum_stock": (
            minimum_stock
        ),

        "batch_no": _text_or_none(
            batch_no
        ),

        "price_source": (
            "PRODUCT_IMPORT"
        ),
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
    batch_no=None,
):
    """
    Submit exactly ONE product creation request.

    IMPORTANT:
        No direct INSERT into products.
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

    product_data = (
        _row_to_product_data(
            row,
            batch_no=batch_no,
        )
    )

    response = client.rpc(
        "request_product_create_rpc",
        {
            "p_product_data": product_data,
            "p_warehouse_id": int(
                warehouse_id
            ),
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
    batch_no=None,
):

    """
    Submit all valid rows as separate Maker requests.
    """

    if validated_df is None:

        return {
            "submitted": 0,
            "failed": 0,
            "results": [],
        }

    valid_df = (
        validated_df[
            validated_df["is_valid"] == True
        ]
        .copy()
    )

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
        "Product Master bulk import request"
    )

    if batch_no:

        reason += (
            f" | Batch: {batch_no}"
        )

    total = len(valid_df)

    progress = st.progress(
        0,
        text=(
            "Submitting Product requests..."
        ),
    )

    for position, (_, row) in enumerate(
        valid_df.iterrows(),
        start=1,
    ):

        sku = str(
            row["sku"]
        ).strip()

        name = str(
            row["name"]
        ).strip()

        try:

            raw_result = (
                _submit_product_request(
                    client=client,
                    row=row,
                    warehouse_id=warehouse_id,
                    requested_by=requested_by,
                    reason=reason,
                    batch_no=batch_no,
                )
            )

            result = (
                _normalize_rpc_result(
                    raw_result
                )
            )

            success = bool(
                result.get(
                    "success",
                    False,
                )
            )

            message = result.get(
                "message",
                "",
            )

            request_id = result.get(
                "request_id"
            )

            status = result.get(
                "status",
                "",
            )

            if success:

                submitted += 1

            else:

                failed += 1

            results.append(
                {
                    "sku": sku,
                    "name": name,
                    "success": success,
                    "status": status,
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
                    "status": "ERROR",
                    "message": str(e),
                    "request_id": None,
                }
            )

        progress.progress(
            position / total,
            text=(
                f"Submitting "
                f"{position}/{total} "
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
    batch_no=None,
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
        total_count
        - error_count
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
            "All Product Master rows "
            "passed validation."
        )

    else:

        st.error(
            f"{error_count} row(s) "
            "require correction."
        )

    # --------------------------------------------------------------------------
    # PREVIEW TABS
    # --------------------------------------------------------------------------

    tab_all, tab_valid, tab_errors = (
        st.tabs(
            [
                "📋 All",
                "✅ Valid",
                "❌ Errors",
            ]
        )
    )

    with tab_all:

        st.dataframe(
            validated_df,
            use_container_width=True,
            hide_index=True,
        )

    with tab_valid:

        valid_df = (
            validated_df[
                validated_df["is_valid"]
                == True
            ]
        )

        st.dataframe(
            valid_df,
            use_container_width=True,
            hide_index=True,
        )

    with tab_errors:

        error_df = (
            validated_df[
                validated_df["is_valid"]
                == False
            ]
        )

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
    # BLOCK SUBMISSION
    # --------------------------------------------------------------------------

    if error_count > 0:

        st.warning(
            "❌ Submission is disabled "
            "until all error rows are corrected."
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
            "Current ERP user ID could not "
            "be resolved. Please log in again."
        )

        return

    st.caption(
        f"Maker User ID: `{requested_by}`"
    )

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
    # MAKER CHECKER INFORMATION
    # --------------------------------------------------------------------------

    st.info(
        "⚠️ Submission creates PENDING "
        "Product Master requests only. "
        "Products will NOT be created until "
        "a Checker approves them."
    )

    if batch_no:

        st.caption(
            f"Import Batch: `{batch_no}`"
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

            result = (
                _submit_valid_products(
                    client=client,
                    validated_df=validated_df,
                    warehouse_id=warehouse_id,
                    requested_by=requested_by,
                    batch_no=batch_no,
                )
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
                f"✅ {submitted} Product "
                "request(s) submitted "
                "successfully as PENDING."
            )

        if failed > 0:

            st.error(
                f"❌ {failed} Product "
                "request(s) failed."
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
        # APPROVAL QUEUE
        # ----------------------------------------------------------------------

        if submitted > 0:

            st.info(
                "Product requests are now "
                "waiting in Product Approval Queue."
            )


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================


def render_product_import(
    warehouse_id=None,
    db_client=None,
):
    """
    Main Product Import page.

    Supports BOTH:

        render_product_import(
            warehouse_id=1
        )

    and:

        render_product_import(
            db_client=client,
            warehouse_id=1
        )
    """

    st.subheader(
        "📦 Product Master Bulk Import"
    )

    st.caption(
        "ERP Enterprise Product Master "
        "| CSV / Excel "
        "| Bulk Import "
        "| Maker-Checker"
    )

    # --------------------------------------------------------------------------
    # DATABASE CLIENT
    #
    # IMPORTANT:
    # db_client is optional for backward compatibility.
    # --------------------------------------------------------------------------

    client = db_client

    if client is None:

        try:

            client = db()

        except Exception as e:

            st.error(
                f"Database connection error: {e}"
            )

            return

    if client is None:

        st.error(
            "ERP database client is not available."
        )

        return

    # --------------------------------------------------------------------------
    # WAREHOUSE CHECK
    # --------------------------------------------------------------------------

    if warehouse_id is None:

        st.warning(
            "Please return to Inventory page "
            "and select a warehouse first."
        )

        return

    st.info(
        f"Destination Warehouse ID: "
        f"{warehouse_id}"
    )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # IMPORT BATCH
    # --------------------------------------------------------------------------

    batch_no = (
        _render_import_batch()
    )

    if not batch_no:

        st.warning(
            "Please generate an Import Batch No "
            "before uploading products."
        )

        return

    st.markdown("---")

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
        key=(
            "product_master_import_uploader"
        ),
    )

    if uploaded_file is None:

        st.info(
            "Please upload a CSV or Excel "
            "file to continue."
        )

        return

    st.caption(
        f"File: {uploaded_file.name} "
        f"| Size: "
        f"{uploaded_file.size:,} bytes"
    )

    # --------------------------------------------------------------------------
    # LOAD FILE
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
    # PREVIEW + SUBMIT
    # --------------------------------------------------------------------------

    _render_preview(
        client=client,
        df=df,
        warehouse_id=warehouse_id,
        batch_no=batch_no,
    )
