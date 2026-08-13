# ==============================================================================
# erp_pages/inventory/product_import.py
#
# ERP ENTERPRISE PRODUCT MASTER BULK IMPORT v2.0
# ------------------------------------------------------------------------------
# CSV / Excel
# Maker-Checker
# Bulk RPC
# Database-Level Duplicate Check
# File Size Guard
# Row Limit Guard
# CSV Chunking
# Pricing Engine Compatible
#
# IMPORTANT PRICING RULE
# ------------------------------------------------------------------------------
# CSV selling_price
#       ↓
# owner_selling_price
#
# selling_price is OPTIONAL.
#
# If selling_price is supplied:
#       OWNER PRICE
#       ↓
#       request_product_create_rpc()
#       ↓
#       Checker Approval
#       ↓
#       create_product_full()
#
# If selling_price is blank:
#       owner_selling_price = NULL
#       ↓
#       Pricing Settings Engine
#       ↓
#       PRODUCT / CATEGORY / GLOBAL
#
# IMPORTANT SECURITY RULE
# ------------------------------------------------------------------------------
# This module NEVER inserts directly into products.
#
# It only creates Maker requests.
#
# Bulk import:
#
# Python
#    ↓
# Validation
#    ↓
# Bulk RPC
#    ↓
# request_product_create_rpc()
#    ↓
# Pending Approval
#    ↓
# Checker
#    ↓
# Actual Product Creation
#
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
# IMPORT LIMITS
# ==============================================================================

# --------------------------------------------------------------------------
# Maximum uploaded file size.
#
# 25 MB is intentionally conservative for Streamlit memory safety.
# --------------------------------------------------------------------------

MAX_IMPORT_FILE_SIZE_MB = 25
MAX_IMPORT_FILE_SIZE_BYTES = (
    MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024
)

# --------------------------------------------------------------------------
# Maximum rows accepted from one import.
# --------------------------------------------------------------------------

MAX_IMPORT_ROWS = 10_000

# --------------------------------------------------------------------------
# CSV processing chunk size.
#
# Bulk RPC will receive this many rows per request.
# --------------------------------------------------------------------------

IMPORT_CHUNK_SIZE = 500

# --------------------------------------------------------------------------
# Allowed extensions
# --------------------------------------------------------------------------

ALLOWED_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}


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
        "selling_price": "",
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

        # Purchase Price
        "purchase price": "purchase_price",
        "purchase_price": "purchase_price",
        "cost": "purchase_price",
        "cost price": "purchase_price",
        "cost_price": "purchase_price",

        # Selling Price
        #
        # IMPORTANT:
        # selling_price = OWNER PRICE
        #
        "selling price": "selling_price",
        "selling_price": "selling_price",
        "sale price": "selling_price",
        "sale_price": "selling_price",

        # Tax
        "tax": "tax_rate",
        "tax rate": "tax_rate",
        "tax_rate": "tax_rate",

        # Minimum Stock
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
# FILE SIZE VALIDATION
# ==============================================================================

def _validate_file_size(uploaded_file):
    """
    Reject oversized files BEFORE reading them into memory.
    """

    if uploaded_file is None:
        return False, "No file selected."

    size = getattr(
        uploaded_file,
        "size",
        None,
    )

    if size is None:
        return True, ""

    if size > MAX_IMPORT_FILE_SIZE_BYTES:

        size_mb = size / (
            1024 * 1024
        )

        return (
            False,
            (
                f"File is too large: "
                f"{size_mb:.2f} MB. "
                f"Maximum allowed size is "
                f"{MAX_IMPORT_FILE_SIZE_MB} MB."
            ),
        )

    return True, ""


# ==============================================================================
# CSV READER
# ==============================================================================

def _read_csv(uploaded_file):
    """
    Read CSV safely.

    Important:
        No uploaded_file.getvalue().

    Pandas reads the uploaded stream directly.
    """

    if pd is None:

        raise RuntimeError(
            "pandas is not installed. "
            "Please add pandas to requirements.txt."
        )

    # --------------------------------------------------------------------------
    # Reset file pointer
    # --------------------------------------------------------------------------

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    # --------------------------------------------------------------------------
    # Read in chunks so large CSV files don't create one giant DataFrame.
    # --------------------------------------------------------------------------

    chunks = []

    total_rows = 0

    try:

        reader = pd.read_csv(
            uploaded_file,
            dtype=str,
            keep_default_na=False,
            chunksize=IMPORT_CHUNK_SIZE,
        )

        for chunk in reader:

            total_rows += len(chunk)

            # --------------------------------------------------------------
            # Early row-limit protection.
            # --------------------------------------------------------------

            if total_rows > MAX_IMPORT_ROWS:

                raise ValueError(
                    f"Import contains more than "
                    f"{MAX_IMPORT_ROWS:,} rows. "
                    f"Please split the file into smaller files."
                )

            chunks.append(chunk)

    except pd.errors.EmptyDataError:

        return pd.DataFrame()

    except ValueError:

        raise

    except Exception as exc:

        raise RuntimeError(
            f"Unable to read CSV file: {exc}"
        ) from exc

    if not chunks:

        return pd.DataFrame()

    return pd.concat(
        chunks,
        ignore_index=True,
    )


# ==============================================================================
# EXCEL READER
# ==============================================================================

def _read_excel(uploaded_file):
    """
    Excel files are not streamed like CSV.

    Therefore:
        1. File size is checked first.
        2. Pandas is required.
        3. Row count is checked immediately after reading.
    """

    if pd is None:

        raise RuntimeError(
            "pandas is not installed. "
            "Please add pandas to requirements.txt."
        )

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    try:

        df = pd.read_excel(
            uploaded_file,
            dtype=str,
            keep_default_na=False,
        )

    except Exception as exc:

        raise RuntimeError(
            f"Unable to read Excel file: {exc}"
        ) from exc

    if len(df) > MAX_IMPORT_ROWS:

        raise ValueError(
            f"Import contains more than "
            f"{MAX_IMPORT_ROWS:,} rows. "
            f"Please split the Excel file."
        )

    return df


# ==============================================================================
# FILE LOADER
# ==============================================================================

def _load_uploaded_file(uploaded_file):

    if uploaded_file is None:
        return None

    # --------------------------------------------------------------------------
    # File size guard BEFORE reading.
    # --------------------------------------------------------------------------

    ok, message = _validate_file_size(
        uploaded_file
    )

    if not ok:
        raise ValueError(message)

    filename = (
        str(uploaded_file.name)
        .strip()
        .lower()
    )

    if filename.endswith(".csv"):

        df = _read_csv(
            uploaded_file
        )

    elif filename.endswith(
        ".xlsx"
    ):

        df = _read_excel(
            uploaded_file
        )

    elif filename.endswith(
        ".xls"
    ):

        df = _read_excel(
            uploaded_file
        )

    else:

        raise ValueError(
            "Unsupported file format. "
            "Please upload CSV or Excel "
            "(.xlsx / .xls)."
        )

    if df is None:
        return None

    if len(df) > MAX_IMPORT_ROWS:

        raise ValueError(
            f"Import contains more than "
            f"{MAX_IMPORT_ROWS:,} rows."
        )

    return _normalize_dataframe(
        df
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
    # REQUIRED PURCHASE PRICE
    # --------------------------------------------------------------------------

    missing_purchase_price = (
        df["purchase_price"] == ""
    )

    df.loc[
        missing_purchase_price,
        "is_valid",
    ] = False

    df.loc[
        missing_purchase_price
        & (df["error_message"] == ""),
        "error_message",
    ] = "Purchase price is required"

    # --------------------------------------------------------------------------
    # DUPLICATE SKU INSIDE FILE
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
    # DUPLICATE BARCODE INSIDE FILE
    # --------------------------------------------------------------------------

    barcode_mask = (
        df["barcode"] != ""
    )

    duplicate_barcode = (
        barcode_mask
        & df.loc[
            barcode_mask,
            "barcode",
        ].duplicated(
            keep=False
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
            ] = (
                "Duplicate barcode "
                "in import file"
            )

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

        for index, value in df[
            column
        ].items():

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
                    ] = (
                        f"Invalid {column}"
                    )

    # --------------------------------------------------------------------------
    # OWNER PRICE VALIDATION
    # --------------------------------------------------------------------------

    for index, value in df[
        "selling_price"
    ].items():

        if value == "":
            continue

        try:

            owner_price = float(
                value
            )

            if owner_price <= 0:
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
                    "Owner selling price "
                    "must be greater than zero"
                )

    error_count = int(
        (~df["is_valid"]).sum()
    )

    return (
        df,
        error_count,
    )


# ==============================================================================
# DATABASE DUPLICATE CHECK
# ==============================================================================

def _check_database_duplicates(
    client,
    validated_df,
):
    """
    Database-level duplicate check.

    This calls ONE RPC for the whole import batch.

    Returns:
        {
            "sku": set(...),
            "barcode": set(...)
        }
    """

    if client is None:
        raise RuntimeError(
            "ERP database client is not available."
        )

    if validated_df is None:
        return {
            "sku": set(),
            "barcode": set(),
        }

    valid_df = validated_df[
        validated_df["is_valid"] == True
    ]

    if valid_df.empty:
        return {
            "sku": set(),
            "barcode": set(),
        }

    skus = [
        str(value).strip()
        for value in valid_df["sku"].tolist()
        if str(value).strip()
    ]

    barcodes = [
        str(value).strip()
        for value in valid_df[
            "barcode"
        ].tolist()
        if str(value).strip()
    ]

    if not skus and not barcodes:
        return {
            "sku": set(),
            "barcode": set(),
        }

    response = client.rpc(
        "check_product_import_duplicates_rpc",
        {
            "p_skus": skus,
            "p_barcodes": barcodes,
        },
    ).execute()

    data = response.data

    if isinstance(data, list):

        if data:
            data = data[0]
        else:
            data = {}

    if not isinstance(data, dict):
        data = {}

    existing_skus = set(
        str(value).strip()
        for value in data.get(
            "existing_skus",
            [],
        )
        if value is not None
    )

    existing_barcodes = set(
        str(value).strip()
        for value in data.get(
            "existing_barcodes",
            [],
        )
        if value is not None
    )

    return {
        "sku": existing_skus,
        "barcode": existing_barcodes,
    }


# ==============================================================================
# APPLY DATABASE DUPLICATE ERRORS
# ==============================================================================

def _apply_database_duplicate_errors(
    validated_df,
    duplicates,
):
    """
    Mark rows that collide with live products table.
    """

    if validated_df is None:
        return validated_df

    df = validated_df.copy()

    existing_skus = duplicates.get(
        "sku",
        set(),
    )

    existing_barcodes = duplicates.get(
        "barcode",
        set(),
    )

    # --------------------------------------------------------------------------
    # Existing SKU
    # --------------------------------------------------------------------------

    for index, row in df.iterrows():

        if not row["is_valid"]:
            continue

        sku = str(
            row["sku"]
        ).strip()

        barcode = str(
            row["barcode"]
        ).strip()

        if (
            sku
            and sku in existing_skus
        ):

            df.loc[
                index,
                "is_valid",
            ] = False

            df.loc[
                index,
                "error_message",
            ] = (
                "SKU already exists "
                "in database"
            )

            continue

        if (
            barcode
            and barcode in existing_barcodes
        ):

            df.loc[
                index,
                "is_valid",
            ] = False

            df.loc[
                index,
                "error_message",
            ] = (
                "Barcode already exists "
                "in database"
            )

    return df


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

    try:

        with pd.ExcelWriter(
            output,
            engine="openpyxl",
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Products",
            )

    except Exception:
        return None

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
            "Use this template to import Product Master items."
        )

        st.info(
            "💡 Selling Price is optional. "
            "If supplied, it is treated as Owner Price. "
            "If blank, ERP Pricing Settings determine "
            "the final selling price."
        )

        st.caption(
            f"Maximum import: "
            f"{MAX_IMPORT_ROWS:,} rows | "
            f"Maximum file size: "
            f"{MAX_IMPORT_FILE_SIZE_MB} MB | "
            f"Bulk RPC size: "
            f"{IMPORT_CHUNK_SIZE} rows"
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
                    "Excel template requires "
                    "pandas and openpyxl."
                )


# ==============================================================================
# IMPORT BATCH HELPERS
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
    ] = _generate_inventory_import_batch_no()


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

    user = st.session_state.get(
        "user"
    )

    if isinstance(
        user,
        dict,
    ):

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
# SAFE VALUE HELPERS
# ==============================================================================

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


# ==============================================================================
# PRODUCT DATA BUILDER
# ==============================================================================

def _row_to_product_data(
    row,
    batch_no=None,
):
    """
    Convert one validated import row into JSON payload.

    IMPORTANT:

        CSV selling_price
                ↓
        owner_selling_price

    It is NOT a calculated selling price.
    """

    purchase_price = (
        _float_or_none(
            row["purchase_price"]
        )
    )

    owner_selling_price = (
        _float_or_none(
            row["selling_price"]
        )
    )

    return {

        # ----------------------------------------------------------------------
        # MASTER
        # ----------------------------------------------------------------------

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

        # ----------------------------------------------------------------------
        # COST
        # ----------------------------------------------------------------------

        "purchase_price": purchase_price,

        # ----------------------------------------------------------------------
        # OWNER PRICE
        # ----------------------------------------------------------------------

        "owner_selling_price": (
            owner_selling_price
        ),

        # ----------------------------------------------------------------------
        # Backward compatibility.
        #
        # Existing request RPC may still expect selling_price.
        # Canonical owner-price field remains owner_selling_price.
        # ----------------------------------------------------------------------

        "selling_price": (
            owner_selling_price
        ),

        # ----------------------------------------------------------------------
        # OPTIONAL SETTINGS
        # ----------------------------------------------------------------------

        "tax_rate": _float_or_none(
            row["tax_rate"]
        ),

        "minimum_stock": _int_or_zero(
            row["minimum_stock"]
        ),

        # ----------------------------------------------------------------------
        # IMPORT
        # ----------------------------------------------------------------------

        "batch_no": _text_or_none(
            batch_no
        ),

        # ----------------------------------------------------------------------
        # PRICE SOURCE
        # ----------------------------------------------------------------------

        "price_source": (
            "OWNER"
            if owner_selling_price is not None
            else "PRICING_SERVICE"
        ),
    }


# ==============================================================================
# BULK PAYLOAD BUILDER
# ==============================================================================

def _build_bulk_payload(
    valid_df,
    batch_no=None,
):
    """
    Convert valid DataFrame rows into JSON-safe dictionaries.
    """

    payload = []

    if valid_df is None:
        return payload

    for _, row in valid_df.iterrows():

        payload.append(
            _row_to_product_data(
                row,
                batch_no=batch_no,
            )
        )

    return payload


# ==============================================================================
# EXTRACT RPC RESULT
# ==============================================================================

def _extract_rpc_result(result):

    """
    Normalize Supabase RPC JSON result.

    Supported:
        dict
        list[dict]
    """

    if isinstance(
        result,
        dict,
    ):
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
# BULK SUBMIT
# ==============================================================================

def _submit_valid_products(
    client,
    validated_df,
    warehouse_id,
    requested_by,
    batch_no=None,
):
    """
    Submit valid Product requests using BULK RPC.

    IMPORTANT:

    OLD:
        1 row = 1 network RPC

    NEW:
        500 rows = 1 network RPC

    The actual existing request_product_create_rpc()
    is still executed server-side.

    Therefore Maker-Checker is preserved.
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

    total = len(valid_df)

    submitted = 0
    failed = 0

    all_results = []

    reason = (
        "Product Master bulk import request "
        "from Inventory UI"
    )

    # --------------------------------------------------------------------------
    # Split into safe network batches.
    # --------------------------------------------------------------------------

    batches = [
        valid_df.iloc[
            start:start + IMPORT_CHUNK_SIZE
        ]
        for start in range(
            0,
            total,
            IMPORT_CHUNK_SIZE,
        )
    ]

    total_batches = len(
        batches
    )

    progress = st.progress(
        0,
        text=(
            "Preparing bulk Product requests..."
        ),
    )

    for batch_index, batch_df in enumerate(
        batches,
        start=1,
    ):

        batch_payload = (
            _build_bulk_payload(
                batch_df,
                batch_no=batch_no,
            )
        )

        if not batch_payload:
            continue

        try:

            response = client.rpc(
                "request_product_bulk_create_rpc",
                {
                    "p_products": batch_payload,

                    "p_warehouse_id": int(
                        warehouse_id
                    ),

                    "p_initial_qty": int(0),

                    "p_reason": reason,

                    "p_requested_by": requested_by,
                },
            ).execute()

            rpc_result = (
                _extract_rpc_result(
                    response.data
                )
            )

            batch_submitted = int(
                rpc_result.get(
                    "submitted",
                    0,
                )
                or 0
            )

            batch_failed = int(
                rpc_result.get(
                    "failed",
                    0,
                )
                or 0
            )

            submitted += (
                batch_submitted
            )

            failed += (
                batch_failed
            )

            batch_results = (
                rpc_result.get(
                    "results",
                    [],
                )
            )

            if isinstance(
                batch_results,
                list,
            ):

                all_results.extend(
                    batch_results
                )

            else:

                all_results.append(
                    {
                        "success": False,
                        "status": "ERROR",
                        "message": (
                            "Invalid bulk RPC result"
                        ),
                    }
                )

        except Exception as exc:

            # ------------------------------------------------------------------
            # A failed network batch does not crash the whole page.
            # ------------------------------------------------------------------

            failed += len(
                batch_df
            )

            for _, row in batch_df.iterrows():

                all_results.append(
                    {
                        "sku": str(
                            row["sku"]
                        ),
                        "name": str(
                            row["name"]
                        ),
                        "success": False,
                        "status": "ERROR",
                        "message": str(
                            exc
                        ),
                        "request_id": None,
                    }
                )

        progress_value = (
            batch_index
            / total_batches
        )

        progress.progress(
            progress_value,
            text=(
                f"Bulk submitting "
                f"batch {batch_index}/"
                f"{total_batches} "
                f"| {min(batch_index * IMPORT_CHUNK_SIZE, total):,}/"
                f"{total:,} rows"
            ),
        )

    progress.empty()

    return {
        "submitted": submitted,
        "failed": failed,
        "results": all_results,
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

    if df is None or df.empty:

        st.warning(
            "No product records found."
        )

        return

    # --------------------------------------------------------------------------
    # Python validation
    # --------------------------------------------------------------------------

    validated_df, _ = (
        _validate_dataframe(df)
    )

    # --------------------------------------------------------------------------
    # Database duplicate check
    #
    # One RPC for the entire file.
    # --------------------------------------------------------------------------

    db_check_error = None

    try:

        duplicates = (
            _check_database_duplicates(
                client=client,
                validated_df=validated_df,
            )
        )

        validated_df = (
            _apply_database_duplicate_errors(
                validated_df,
                duplicates,
            )
        )

    except Exception as exc:

        db_check_error = str(
            exc
        )

    # --------------------------------------------------------------------------
    # If DB duplicate check failed, DO NOT allow submission.
    # --------------------------------------------------------------------------

    if db_check_error:

        st.error(
            "Database duplicate validation failed."
        )

        st.code(
            db_check_error
        )

        st.warning(
            "Submission is disabled because "
            "live database validation could not be completed."
        )

        return

    # --------------------------------------------------------------------------
    # Final counts
    # --------------------------------------------------------------------------

    error_count = int(
        (~validated_df["is_valid"]).sum()
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
            f"{total_count:,}",
        )

    with col2:

        st.metric(
            "Valid Rows",
            f"{valid_count:,}",
        )

    with col3:

        st.metric(
            "Error Rows",
            f"{error_count:,}",
        )

    st.markdown("---")

    # --------------------------------------------------------------------------
    # PRICING
    # --------------------------------------------------------------------------

    st.info(
        "💰 Pricing Rule: CSV selling_price = Owner Price. "
        "If selling_price is blank, ERP Pricing Settings "
        "will determine the final price."
    )

    # --------------------------------------------------------------------------
    # STATUS
    # --------------------------------------------------------------------------

    if error_count == 0:

        st.success(
            "All Product Master rows passed "
            "file + database validation."
        )

    else:

        st.error(
            f"{error_count:,} row(s) require correction."
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
    # BLOCK IF VALIDATION FAILS
    # --------------------------------------------------------------------------

    if error_count > 0:

        st.warning(
            "❌ Submission is disabled until "
            "all validation errors are corrected."
        )

        return

    # --------------------------------------------------------------------------
    # USER
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
    # DATABASE
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
    # MAKER-CHECKER MESSAGE
    # --------------------------------------------------------------------------

    st.info(
        "⚠️ Bulk submission creates PENDING "
        "Product Master requests only. "
        "Products will NOT be created until "
        "a Checker approves them."
    )

    st.caption(
        f"Network optimization: "
        f"up to {IMPORT_CHUNK_SIZE:,} products per RPC."
    )

    # --------------------------------------------------------------------------
    # SUBMIT
    # --------------------------------------------------------------------------

    if st.button(
        "🚀 Submit All Valid Products for Approval",
        type="primary",
        use_container_width=True,
        key="submit_product_master_import",
    ):

        with st.spinner(
            "Submitting Product Master bulk requests..."
        ):

            try:

                result = (
                    _submit_valid_products(
                        client=client,
                        validated_df=validated_df,
                        warehouse_id=warehouse_id,
                        requested_by=requested_by,
                        batch_no=batch_no,
                    )
                )

            except Exception as exc:

                st.error(
                    f"Bulk submission failed: {exc}"
                )

                return

            submitted = int(
                result.get(
                    "submitted",
                    0,
                )
                or 0
            )

            failed = int(
                result.get(
                    "failed",
                    0,
                )
                or 0
            )

            # ------------------------------------------------------------------
            # RESULT
            # ------------------------------------------------------------------

            if submitted > 0:

                st.success(
                    f"✅ {submitted:,} Product request(s) "
                    "submitted successfully as PENDING."
                )

            if failed > 0:

                st.error(
                    f"❌ {failed:,} Product request(s) failed."
                )

            # ------------------------------------------------------------------
            # RESULT TABLE
            # ------------------------------------------------------------------

            results = result.get(
                "results",
                [],
            )

            if (
                results
                and pd is not None
            ):

                result_df = pd.DataFrame(
                    results
                )

                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True,
                )

            # ------------------------------------------------------------------
            # APPROVAL QUEUE
            # ------------------------------------------------------------------

            if submitted > 0:

                st.info(
                    "Product requests are now waiting "
                    "in Product Approval Queue."
                )


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render_product_import(
    warehouse_id=None,
):

    st.subheader(
        "📦 Product Master Bulk Import"
    )

    st.caption(
        "ERP Enterprise Product Master | "
        "CSV / Excel | Bulk RPC | "
        "Database Duplicate Check | Maker-Checker"
    )

    # --------------------------------------------------------------------------
    # DATABASE CLIENT
    # --------------------------------------------------------------------------

    try:

        client = db()

    except Exception as exc:

        st.error(
            f"Database connection error: {exc}"
        )

        return

    if client is None:

        st.error(
            "ERP database client is not available."
        )

        return

    # --------------------------------------------------------------------------
    # WAREHOUSE
    # --------------------------------------------------------------------------

    if warehouse_id is None:

        st.warning(
            "Please return to Inventory page "
            "and select a warehouse first."
        )

        return

    st.info(
        f"Destination Warehouse ID: {warehouse_id}"
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
        key="product_master_import_uploader",
    )

    if uploaded_file is None:

        st.info(
            "Please upload a CSV or Excel file to continue."
        )

        return

    # --------------------------------------------------------------------------
    # FILE SIZE DISPLAY
    # --------------------------------------------------------------------------

    file_size = getattr(
        uploaded_file,
        "size",
        0,
    )

    file_size_mb = (
        file_size
        / (1024 * 1024)
    )

    st.caption(
        f"File: {uploaded_file.name} | "
        f"Size: {file_size:,} bytes "
        f"({file_size_mb:.2f} MB)"
    )

    # --------------------------------------------------------------------------
    # EARLY FILE SIZE GUARD
    # --------------------------------------------------------------------------

    ok, message = (
        _validate_file_size(
            uploaded_file
        )
    )

    if not ok:

        st.error(
            f"❌ {message}"
        )

        return

    # --------------------------------------------------------------------------
    # PANDAS DEPENDENCY
    # --------------------------------------------------------------------------

    if pd is None:

        st.error(
            "❌ pandas is not installed. "
            "Product Import requires pandas."
        )

        st.code(
            "pandas\nopenpyxl"
        )

        return

    # --------------------------------------------------------------------------
    # LOAD FILE
    # --------------------------------------------------------------------------

    try:

        df = _load_uploaded_file(
            uploaded_file
        )

    except Exception as exc:

        st.error(
            f"Unable to read import file: {exc}"
        )

        return

    if df is None or df.empty:

        st.error(
            "The uploaded file contains no data."
        )

        return

    # --------------------------------------------------------------------------
    # FINAL ROW GUARD
    # --------------------------------------------------------------------------

    if len(df) > MAX_IMPORT_ROWS:

        st.error(
            f"Import contains {len(df):,} rows. "
            f"Maximum allowed is "
            f"{MAX_IMPORT_ROWS:,} rows."
        )

        return

    st.success(
        f"File loaded successfully: "
        f"{len(df):,} row(s)"
    )

    # --------------------------------------------------------------------------
    # PREVIEW + SUBMIT
    # --------------------------------------------------------------------------

    _render_preview(
        client=client,
        df=df,
        warehouse_id=warehouse_id,
        batch_no=batch_no,
    )
