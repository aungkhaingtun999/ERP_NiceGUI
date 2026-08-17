==============================================================================

erp_pages/3_Reports.py



ERP ENTERPRISE SALES ANALYTICS REPORT v5.0



Sales Summary + Product Sales + Cashier + Payment + Export



PRODUCT NAME SUPPORT

------------------------------------------------------------------------------



sales

↓

sale_items

↓

product_id

↓

products



Product Name Resolution:



1. sale_items.product_name

↓ if NULL / empty

2. products.name

↓ if unavailable

3. "Unknown Product"



IMPORTANT

------------------------------------------------------------------------------

This report is READ-ONLY.



It NEVER:

- modifies sales

- modifies sale_items

- modifies products

- modifies inventory

- modifies warehouse_stock



==============================================================================

from future import annotations

from datetime import date, timedelta

from io import BytesIO

import json

import pandas as pd

import streamlit as st

from erp_core.base_repo import db

from utils.ui import show_table

==============================================================================

CONSTANTS

==============================================================================

UNKNOWN_PRODUCT = "Unknown Product"

==============================================================================

HELPERS

==============================================================================

def safe_number(value):

try:

    return float(value or 0)

except Exception:

    return 0.0

==============================================================================

CASHIER NAME

==============================================================================

def cashier_name(user):

"""

Safely convert Supabase users relation into cashier display name.



Current query provides:

    username

    employee_code

"""



if not isinstance(user, dict):

    return "Unknown"



username = str(

    user.get("username") or ""

).strip()



employee_code = str(

    user.get("employee_code") or ""

).strip()



if username:

    return username



if employee_code:

    return employee_code



return "Unknown"

==============================================================================

PRODUCT NAME

==============================================================================

def resolve_product_name(

item_product_name,

product_name,

):

"""

Product name resolution priority:



1. sale_items.product_name

2. products.name

3. Unknown Product



This protects historical sale reports if

sale_items.product_name was stored as a snapshot.

"""



item_name = str(

    item_product_name or ""

).strip()



if item_name:

    return item_name



master_name = str(

    product_name or ""

).strip()



if master_name:

    return master_name



return UNKNOWN_PRODUCT

==============================================================================

FORMAT NUMBER

==============================================================================

def format_number(value):

try:

    number = float(value or 0)



    if number.is_integer():

        return f"{int(number):,}"



    return f"{number:,.2f}"



except Exception:

    return str(value)

==============================================================================

DATE RANGE

==============================================================================

def get_report_utc_range(

start_date,

end_date,

):

"""

Convert Myanmar local date range into UTC boundaries.



Database created_at is timestamptz / UTC.

"""



try:



    from zoneinfo import ZoneInfo



    myanmar_tz = ZoneInfo(

        "Asia/Yangon"

    )



    start_local = pd.Timestamp(

        start_date,

        tz=myanmar_tz,

    )



    end_local = pd.Timestamp(

        end_date + timedelta(days=1),

        tz=myanmar_tz,

    )



    start_utc = (

        start_local

        .tz_convert("UTC")

        .isoformat()

    )



    end_utc = (

        end_local

        .tz_convert("UTC")

        .isoformat()

    )



    return (

        start_utc,

        end_utc,

    )



except Exception:



    start_utc = (

        f"{start_date.isoformat()}"

        f"T00:00:00+00:00"

    )



    end_utc = (

        f"{(end_date + timedelta(days=1)).isoformat()}"

        f"T00:00:00+00:00"

    )



    return (

        start_utc,

        end_utc,

    )

==============================================================================

LOAD SALES

==============================================================================

@st.cache_data(

ttl=60,

show_spinner=False,

)

def get_sales(

query_start,

query_end,

):

try:



    response = (

        db()

        .table("sales")

        .select(

            """

            id,

            total,

            total_amount,

            discount,

            tax,

            subtotal,

            paid_amount,

            payment_method,

            created_at,

            cashier_id,

            users(

                username,

                employee_code

            )

            """

        )

        .gte(

            "created_at",

            query_start,

        )

        .lt(

            "created_at",

            query_end,

        )

        .order(

            "created_at",

            desc=True,

        )

        .execute()

    )



    return response.data or []



except Exception as e:



    st.error(

        f"Sales loading error: {e}"

    )



    return []

==============================================================================

LOAD SALE ITEMS

==============================================================================

@st.cache_data(

ttl=60,

show_spinner=False,

)

def get_sale_items(

sale_ids,

):

"""

Load sale_items for the selected sales.



Confirmed columns:



    id

    sale_id

    product_id

    quantity

    unit_price

    discount

    total

    product_name

"""



if not sale_ids:

    return []



try:



    normalized_ids = [

        int(x)

        for x in sale_ids

        if x is not None

    ]



    if not normalized_ids:

        return []



    response = (

        db()

        .table("sale_items")

        .select(

            """

            id,

            sale_id,

            product_id,

            quantity,

            unit_price,

            discount,

            total,

            product_name

            """

        )

        .in_(

            "sale_id",

            normalized_ids,

        )

        .order(

            "sale_id",

        )

        .order(

            "id",

        )

        .execute()

    )



    return response.data or []



except Exception as e:



    st.error(

        f"Sale item loading error: {e}"

    )



    return []

==============================================================================

LOAD PRODUCTS

==============================================================================

@st.cache_data(

ttl=60,

show_spinner=False,

)

def get_products(

product_ids,

):

"""

Load product master data.



Used as fallback when sale_items.product_name

is NULL or empty.

"""



if not product_ids:

    return {}



try:



    normalized_ids = [

        int(x)

        for x in product_ids

        if x is not None

    ]



    if not normalized_ids:

        return {}



    response = (

        db()

        .table("products")

        .select(

            """

            id,

            name,

            sku,

            barcode

            """

        )

        .in_(

            "id",

            normalized_ids,

        )

        .execute()

    )



    rows = response.data or []



    return {

        int(row["id"]): row

        for row in rows

        if row.get("id") is not None

    }



except Exception as e:



    st.error(

        f"Product loading error: {e}"

    )



    return {}

==============================================================================

BUILD PRODUCT SALES DATAFRAME

==============================================================================

def build_product_sales_dataframe(

sales,

sale_items,

products,

):

"""

Build item-level sales dataframe.



Product Name:

    sale_items.product_name

        ↓ fallback

    products.name

"""



if not sale_items:

    return pd.DataFrame()



sales_map = {}



for sale in sales:



    sale_id = sale.get("id")



    if sale_id is None:

        continue



    try:

        sale_id = int(sale_id)

    except Exception:

        continue



    user = sale.get("users")



    sales_map[sale_id] = {

        "created_at": sale.get(

            "created_at"

        ),

        "cashier": cashier_name(

            user

        ),

        "payment_method": sale.get(

            "payment_method"

        ),

    }



rows = []



for item in sale_items:



    sale_id = item.get(

        "sale_id"

    )



    if sale_id is None:

        continue



    try:

        sale_id = int(

            sale_id

        )

    except Exception:

        continue



    sale_info = sales_map.get(

        sale_id,

        {},

    )



    product_id = item.get(

        "product_id"

    )



    try:



        product_id_int = (

            int(product_id)

            if product_id is not None

            else None

        )



    except Exception:



        product_id_int = None



    product = products.get(

        product_id_int,

        {},

    )



    product_name = resolve_product_name(

        item.get("product_name"),

        product.get("name"),

    )



    rows.append(

        {

            "Sale ID": sale_id,



            "Date": sale_info.get(

                "created_at"

            ),



            "Cashier": sale_info.get(

                "cashier",

                "Unknown",

            ),



            "Payment Method": (

                sale_info.get(

                    "payment_method"

                )

                or "Unknown"

            ),



            "Product ID": product_id_int,



            "Product Name": product_name,



            "SKU": (

                product.get("sku")

                or ""

            ),



            "Barcode": (

                product.get("barcode")

                or ""

            ),



            "Quantity": safe_number(

                item.get("quantity")

            ),



            "Unit Price": safe_number(

                item.get("unit_price")

            ),



            "Discount": safe_number(

                item.get("discount")

            ),



            "Sales": safe_number(

                item.get("total")

            ),

        }

    )



if not rows:

    return pd.DataFrame()



product_df = pd.DataFrame(

    rows

)



# --------------------------------------------------------------------------

# Date

# --------------------------------------------------------------------------



if "Date" in product_df.columns:



    product_df["Date"] = pd.to_datetime(

        product_df["Date"],

        errors="coerce",

        utc=True,

    )



    product_df = product_df[

        product_df["Date"].notna()

    ].copy()



    if not product_df.empty:



        product_df["Date"] = (

            product_df["Date"]

            .dt.tz_convert(

                "Asia/Yangon"

            )

            .dt.tz_localize(None)

        )



# --------------------------------------------------------------------------

# Numeric columns

# --------------------------------------------------------------------------



for col in [

    "Quantity",

    "Unit Price",

    "Discount",

    "Sales",

]:



    if col in product_df.columns:



        product_df[col] = (

            pd.to_numeric(

                product_df[col],

                errors="coerce",

            )

            .fillna(0.0)

        )



return product_df

==============================================================================

PRODUCT DETAIL REPORT

==============================================================================

def render_product_sales_report(

product_df,

):

st.subheader(

    "📦 Product Sales Report"

)



if product_df.empty:



    st.info(

        "No product sales data found."

    )



    return



# ==========================================================================

# PRODUCT KPI

# ==========================================================================



total_products = (

    product_df["Product Name"]

    .nunique()

)



total_qty = safe_number(

    product_df["Quantity"].sum()

)



total_discount = safe_number(

    product_df["Discount"].sum()

)



total_sales = safe_number(

    product_df["Sales"].sum()

)



c1, c2, c3, c4 = st.columns(4)



c1.metric(

    "📦 Products",

    total_products,

)



c2.metric(

    "🔢 Qty Sold",

    format_number(

        total_qty

    ),

)



c3.metric(

    "🏷 Discount",

    f"{total_discount:,.0f} MMK",

)



c4.metric(

    "💰 Product Sales",

    f"{total_sales:,.0f} MMK",

)



st.divider()



# ==========================================================================

# PRODUCT SUMMARY

# ==========================================================================



st.markdown(

    "### 🏆 Product Sales Summary"

)



product_summary = (

    product_df

    .groupby(

        [

            "Product Name",

            "SKU",

            "Barcode",

        ],

        dropna=False,

    )

    .agg(

        Quantity=(

            "Quantity",

            "sum",

        ),

        Discount=(

            "Discount",

            "sum",

        ),

        Sales=(

            "Sales",

            "sum",

        ),

    )

    .reset_index()

    .sort_values(

        "Sales",

        ascending=False,

    )

)



display_summary = product_summary.copy()



display_summary[

    "Quantity"

] = display_summary[

    "Quantity"

].apply(

    format_number

)



display_summary[

    "Discount"

] = display_summary[

    "Discount"

].apply(

    lambda x: f"{safe_number(x):,.0f}"

)



display_summary[

    "Sales"

] = display_summary[

    "Sales"

].apply(

    lambda x: f"{safe_number(x):,.0f}"

)



show_table(

    display_summary

)



st.divider()



# ==========================================================================

# ITEM-LEVEL DETAIL

# ==========================================================================



st.markdown(

    "### 🧾 Sale Item Detail"

)



detail_columns = [

    "Date",

    "Sale ID",

    "Product Name",

    "SKU",

    "Barcode",

    "Quantity",

    "Unit Price",

    "Discount",

    "Sales",

    "Cashier",

    "Payment Method",

]



detail_df = product_df[

    [

        col

        for col in detail_columns

        if col in product_df.columns

    ]

].copy()



if "Date" in detail_df.columns:



    detail_df["Date"] = (

        detail_df["Date"]

        .dt.strftime(

            "%Y-%m-%d %H:%M:%S"

        )

    )



for col in [

    "Quantity",

    "Unit Price",

    "Discount",

    "Sales",

]:



    if col in detail_df.columns:



        detail_df[col] = detail_df[

            col

        ].apply(

            format_number

        )



show_table(

    detail_df

)

==============================================================================

MAIN

==============================================================================

def run():

st.title(

    "📊 ERP Executive Analytics & Reports"

)



st.caption(

    "MYANMAR ERP - Sales Performance Analytics"

)



# ==========================================================================

# DATE FILTER

# ==========================================================================



try:



    from utils.timezone import (

        get_myanmar_today

    )



    today = get_myanmar_today()



    if not isinstance(

        today,

        date,

    ):



        today = date.today()



except Exception:



    today = date.today()



c1, c2 = st.columns(2)



start_date = c1.date_input(

    "Start Date",

    value=today,

    key="reports_start_date",

)



end_date = c2.date_input(

    "End Date",

    value=today,

    key="reports_end_date",

)



if start_date > end_date:



    st.error(

        "Start Date cannot be later than End Date."

    )



    return



# ==========================================================================

# UTC RANGE

# ==========================================================================



(

    start_utc,

    end_utc,

) = get_report_utc_range(

    start_date,

    end_date,

)



# ==========================================================================

# LOAD SALES

# ==========================================================================



sales = get_sales(

    start_utc,

    end_utc,

)



if not sales:



    st.warning(

        "No sales data found for the selected date range."

    )



    st.caption(

        f"Checked: {start_date} → {end_date}"

    )



    return



# ==========================================================================

# SALES DATAFRAME

# ==========================================================================



df = pd.DataFrame(

    sales

)



# ==========================================================================

# NORMALIZE TOTAL

# ==========================================================================

#

# sales.total is the canonical sale total.

# total_amount is currently 0 in existing records.

#



if "total" in df.columns:



    df["total"] = (

        pd.to_numeric(

            df["total"],

            errors="coerce",

        )

        .fillna(0.0)

    )



elif "total_amount" in df.columns:



    df["total"] = (

        pd.to_numeric(

            df["total_amount"],

            errors="coerce",

        )

        .fillna(0.0)

    )



else:



    df["total"] = 0.0



# ==========================================================================

# MONEY

# ==========================================================================



for col in [

    "total",

    "total_amount",

    "discount",

    "tax",

    "subtotal",

    "paid_amount",

]:



    if col in df.columns:



        df[col] = (

            pd.to_numeric(

                df[col],

                errors="coerce",

            )

            .fillna(0.0)

        )



# ==========================================================================

# CREATED AT

# ==========================================================================



if "created_at" not in df.columns:



    st.error(

        "Sales data does not contain created_at."

    )



    return



df["created_at"] = pd.to_datetime(

    df["created_at"],

    errors="coerce",

    utc=True,

)



df = df[

    df["created_at"].notna()

].copy()



if df.empty:



    st.warning(

        "Sales records were found, but created_at values are invalid."

    )



    return



# ==========================================================================

# MYANMAR TIME

# ==========================================================================



df["created_at"] = (

    df["created_at"]

    .dt.tz_convert(

        "Asia/Yangon"

    )

    .dt.tz_localize(None)

)



# ==========================================================================

# CASHIER

# ==========================================================================



if "users" in df.columns:



    df["Cashier"] = (

        df["users"]

        .apply(

            cashier_name

        )

    )



else:



    df["Cashier"] = "SYSTEM"



# ==========================================================================

# CASHIER FILTER

# ==========================================================================



st.sidebar.subheader(

    "🔎 Filters"

)



cashier_values = (

    df["Cashier"]

    .fillna("Unknown")

    .astype(str)

    .str.strip()

    .replace(

        "",

        "Unknown",

    )

    .unique()

    .tolist()

)



cashier_options = [

    "All"

] + sorted(

    cashier_values

)



selected_cashier = (

    st.sidebar.selectbox(

        "Cashier",

        cashier_options,

        key="reports_cashier_filter",

    )

)



if selected_cashier != "All":



    df = df[

        df["Cashier"]

        == selected_cashier

    ].copy()



if df.empty:



    st.warning(

        "No data after filter."

    )



    return



# ==========================================================================

# LOAD SALE ITEMS

# ==========================================================================



sale_ids = [

    sale.get("id")

    for sale in sales

    if sale.get("id") is not None

]



sale_items = get_sale_items(

    sale_ids

)



# ==========================================================================

# LOAD PRODUCT MASTER

# ==========================================================================



product_ids = [

    item.get("product_id")

    for item in sale_items

    if item.get("product_id") is not None

]



products = get_products(

    product_ids

)



# ==========================================================================

# BUILD PRODUCT DATA

# ==========================================================================



product_df = (

    build_product_sales_dataframe(

        sales=sales,

        sale_items=sale_items,

        products=products,

    )

)



# ==========================================================================

# IMPORTANT:

# Apply cashier filter to product report too.

# ==========================================================================



if (

    not product_df.empty

    and selected_cashier != "All"

):



    product_df = product_df[

        product_df["Cashier"]

        == selected_cashier

    ].copy()



# ==========================================================================

# KPI

# ==========================================================================



revenue = safe_number(

    df["total"].sum()

)



discount = safe_number(

    df["discount"].sum()

    if "discount" in df.columns

    else 0

)



tax = safe_number(

    df["tax"].sum()

    if "tax" in df.columns

    else 0

)



bills = len(df)



c1, c2, c3, c4 = st.columns(4)



c1.metric(

    "💰 Revenue",

    f"{revenue:,.0f} MMK",

)



c2.metric(

    "🧾 Bills",

    bills,

)



c3.metric(

    "🏷 Discount",

    f"{discount:,.0f} MMK",

)



c4.metric(

    "🧮 Tax",

    f"{tax:,.0f} MMK",

)



st.divider()



# ==========================================================================

# TABS

# ==========================================================================



tab1, tab2, tab3, tab4, tab5 = st.tabs(

    [

        "📈 Sales Summary",

        "📦 Product Sales",

        "👨‍💼 Cashier",

        "💳 Payment",

        "📥 Export",

    ]

)



# ==========================================================================

# TAB 1 - SALES SUMMARY

# ==========================================================================



with tab1:



    st.subheader(

        "Daily Sales"

    )



    daily = (

        df.groupby(

            df["created_at"].dt.date

        )["total"]

        .sum()

        .reset_index()

    )



    daily.columns = [

        "Date",

        "Sales",

    ]



    show_table(

        daily

    )



    st.subheader(

        "Monthly Sales"

    )



    monthly = (

        df.groupby(

            df["created_at"]

            .dt.to_period("M")

            .astype(str)

        )["total"]

        .sum()

        .reset_index()

    )



    monthly.columns = [

        "Month",

        "Sales",

    ]



    show_table(

        monthly

    )



# ==========================================================================

# TAB 2 - PRODUCT SALES

# ==========================================================================



with tab2:



    render_product_sales_report(

        product_df

    )



# ==========================================================================

# TAB 3 - CASHIER

# ==========================================================================



with tab3:



    st.subheader(

        "Cashier Performance"

    )



    cashier = (

        df.groupby(

            "Cashier"

        )

        .agg(

            Bills=(

                "id",

                "count",

            ),

            Sales=(

                "total",

                "sum",

            ),

        )

        .reset_index()

        .sort_values(

            "Sales",

            ascending=False,

        )

    )



    show_table(

        cashier

    )



# ==========================================================================

# TAB 4 - PAYMENT

# ==========================================================================



with tab4:



    st.subheader(

        "Payment Method"

    )



    if "payment_method" in df.columns:



        payment = (

            df.assign(

                payment_method=(

                    df[

                        "payment_method"

                    ]

                    .fillna(

                        "Unknown"

                    )

                    .astype(str)

                    .replace(

                        "",

                        "Unknown",

                    )

                )

            )

            .groupby(

                "payment_method"

            )

            .agg(

                Bills=(

                    "id",

                    "count",

                ),

                Amount=(

                    "total",

                    "sum",

                ),

            )

            .reset_index()

            .sort_values(

                "Amount",

                ascending=False,

            )

        )



        show_table(

            payment

        )



    else:



        st.info(

            "Payment method data is not available."

        )



# ==========================================================================

# TAB 5 - EXPORT

# ==========================================================================



with tab5:



    st.subheader(

        "📥 Export Sales Report"

    )



    # ----------------------------------------------------------------------

    # Sales Export

    # ----------------------------------------------------------------------



    export_sales_df = df.copy()



    export_sales_df.drop(

        columns=[

            "cashier_id",

            "users",

        ],

        errors="ignore",

        inplace=True,

    )



    if "created_at" in export_sales_df.columns:



        export_sales_df[

            "created_at"

        ] = pd.to_datetime(

            export_sales_df[

                "created_at"

            ],

            errors="coerce",

        )



    for col in export_sales_df.columns:



        if (

            export_sales_df[

                col

            ].dtype

            == "object"

        ):



            export_sales_df[

                col

            ] = export_sales_df[

                col

            ].apply(

                lambda x:

                json.dumps(

                    x,

                    ensure_ascii=False,

                )

                if isinstance(

                    x,

                    (

                        dict,

                        list,

                    ),

                )

                else x

            )



    export_sales_df = (

        export_sales_df

        .fillna("")

    )



    # ----------------------------------------------------------------------

    # Product Export

    # ----------------------------------------------------------------------



    export_product_df = (

        product_df.copy()

    )



    if (

        not export_product_df.empty

        and "Date"

        in export_product_df.columns

    ):



        export_product_df[

            "Date"

        ] = pd.to_datetime(

            export_product_df[

                "Date"

            ],

            errors="coerce",

        )



    export_product_df = (

        export_product_df

        .fillna("")

    )



    # ----------------------------------------------------------------------

    # CSV - Sales

    # ----------------------------------------------------------------------



    csv_sales = (

        export_sales_df

        .to_csv(

            index=False

        )

        .encode(

            "utf-8-sig"

        )

    )



    st.download_button(

        "⬇ Download Sales CSV",

        data=csv_sales,

        file_name=(

            "ERP_Sales_Report.csv"

        ),

        mime="text/csv",

        key=(

            "reports_download_sales_csv"

        ),

    )



    # ----------------------------------------------------------------------

    # CSV - Product

    # ----------------------------------------------------------------------



    if not export_product_df.empty:



        csv_products = (

            export_product_df

            .to_csv(

                index=False

            )

            .encode(

                "utf-8-sig"

            )

        )



        st.download_button(

            "⬇ Download Product Sales CSV",

            data=csv_products,

            file_name=(

                "ERP_Product_Sales_Report.csv"

            ),

            mime="text/csv",

            key=(

                "reports_download_product_csv"

            ),

        )



    # ----------------------------------------------------------------------

    # Excel

    # ----------------------------------------------------------------------



    output = BytesIO()



    with pd.ExcelWriter(

        output,

        engine="openpyxl",

    ) as writer:



        export_sales_df.to_excel(

            writer,

            index=False,

            sheet_name="Sales",

        )



        if not export_product_df.empty:



            export_product_df.to_excel(

                writer,

                index=False,

                sheet_name="Product Sales",

            )



            # --------------------------------------------------------------

            # Product Summary Sheet

            # --------------------------------------------------------------



            product_summary_export = (

                product_df

                .groupby(

                    [

                        "Product Name",

                        "SKU",

                        "Barcode",

                    ],

                    dropna=False,

                )

                .agg(

                    Quantity=(

                        "Quantity",

                        "sum",

                    ),

                    Discount=(

                        "Discount",

                        "sum",

                    ),

                    Sales=(

                        "Sales",

                        "sum",

                    ),

                )

                .reset_index()

                .sort_values(

                    "Sales",

                    ascending=False,

                )

            )



            product_summary_export.to_excel(

                writer,

                index=False,

                sheet_name="Product Summary",

            )



    st.download_button(

        "⬇ Download Excel",

        data=output.getvalue(),

        file_name=(

            "ERP_Sales_Report.xlsx"

        ),

        mime=(

            "application/vnd.openxmlformats-officedocument."

            "spreadsheetml.sheet"

        ),

        key=(

            "reports_download_excel"

        ),

    )

==============================================================================

DIRECT ENTRY

==============================================================================

if name == "main":

run()
