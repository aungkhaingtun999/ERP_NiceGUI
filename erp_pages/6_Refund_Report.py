# ==============================================================================
# REFUND REPORT
# ERP ENTERPRISE REFUND REPORT v4.1
#
# Tax-aware Refund Reporting
#
# Compatible with:
#   refund_process_rpc_v4
#
# Uses:
#   refund_net_amount
#   refund_tax_amount
#   refund_total_amount
# ==============================================================================

import io
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database import db
from auth import require_login

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from utils.ui import show_table


# ==============================================================================
# AUTH
# ==============================================================================

user = require_login()

st.set_page_config(
    page_title="Refund Report",
    layout="wide",
)

st.title("📊 Refund Report v4.1")


# ==============================================================================
# SESSION STATE
# ==============================================================================

if "selected_refund_id" not in st.session_state:
    st.session_state.selected_refund_id = None


# ==============================================================================
# LOAD REPORT
# ==============================================================================

@st.cache_data(ttl=60)
def get_refund_report():

    response = (
        db()
        .table("refund_report_view")
        .select("*")
        .order("refund_date", desc=True)
        .execute()
    )

    return pd.DataFrame(
        response.data or []
    )


df = get_refund_report()


# ==============================================================================
# EMPTY DATA
# ==============================================================================

if df.empty:

    st.info("No refund records found.")

    if st.button("🔄 Refresh"):

        st.cache_data.clear()
        st.rerun()

    st.stop()


# ==============================================================================
# SAFE NUMERIC COLUMNS
# ==============================================================================

numeric_columns = [
    "quantity",
    "unit_price",
    "item_total",
    "refund_amount",
    "refund_net_amount",
    "refund_tax_amount",
    "refund_total_amount",
]


for col in numeric_columns:

    if col not in df.columns:

        df[col] = 0

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce",
    ).fillna(0)


# ==============================================================================
# DATE
# ==============================================================================

df["refund_date"] = pd.to_datetime(
    df["refund_date"],
    errors="coerce",
)


# ==============================================================================
# STATUS NORMALIZATION
# ==============================================================================

if "status" not in df.columns:

    df["status"] = "COMPLETED"


df["status"] = (
    df["status"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)


# ==============================================================================
# TEXT NORMALIZATION
# ==============================================================================

text_columns = [
    "invoice_no",
    "cashier_name",
    "warehouse_name",
    "product_name",
    "processed_by",
    "reason",
]


for col in text_columns:

    if col not in df.columns:

        df[col] = ""

    df[col] = (
        df[col]
        .fillna("")
        .astype(str)
    )


# ==============================================================================
# V4 REPORT AMOUNTS
# ==============================================================================

# ------------------------------------------------------------------------------
# IMPORTANT
#
# V4 refund amount calculation:
#
#   Net   = refund_net_amount
#   Tax   = refund_tax_amount
#   Total = refund_total_amount
#
# Do NOT use item_total as the primary refund amount.
# ------------------------------------------------------------------------------

df["report_net"] = df["refund_net_amount"]

df["report_tax"] = df["refund_tax_amount"]

df["report_total"] = df["refund_total_amount"]


# ==============================================================================
# LEGACY FALLBACK
# ==============================================================================

# Old refund rows may not have V4 amount columns populated.
#
# For those old rows:
#
#   Net   -> item_total
#   Tax   -> 0
#   Total -> item_total
#
# New V4 rows are NOT affected.

legacy_total_mask = (
    df["report_total"] == 0
) & (
    df["item_total"] != 0
)


df.loc[
    legacy_total_mask,
    "report_total"
] = df.loc[
    legacy_total_mask,
    "item_total"
]


legacy_net_mask = (
    df["report_net"] == 0
) & (
    df["item_total"] != 0
)


df.loc[
    legacy_net_mask,
    "report_net"
] = df.loc[
    legacy_net_mask,
    "item_total"
]


# ==============================================================================
# SIDEBAR FILTER
# ==============================================================================

st.sidebar.header("🔍 Report Filter")


invoice_search = st.sidebar.text_input(
    "Invoice No"
)


cashier_filter = st.sidebar.multiselect(
    "Cashier",
    sorted(
        df["cashier_name"]
        .dropna()
        .unique()
        .tolist()
    ),
)


warehouse_filter = st.sidebar.multiselect(
    "Warehouse",
    sorted(
        df["warehouse_name"]
        .dropna()
        .unique()
        .tolist()
    ),
)


status_filter = st.sidebar.multiselect(
    "Status",
    [
        "PENDING",
        "COMPLETED",
        "REJECTED",
    ],
)


min_date = df["refund_date"].min()


if pd.isna(min_date):

    min_date = pd.Timestamp.today()


from_date = st.sidebar.date_input(
    "From Date",
    min_date.date(),
)


to_date = st.sidebar.date_input(
    "To Date",
    date.today(),
)


# ==============================================================================
# APPLY FILTER
# ==============================================================================

filtered = df.copy()


filtered = filtered[
    (
        filtered["refund_date"].dt.date
        >= from_date
    )
    &
    (
        filtered["refund_date"].dt.date
        <= to_date
    )
]


if invoice_search:

    filtered = filtered[
        filtered["invoice_no"].str.contains(
            invoice_search,
            case=False,
            na=False,
        )
    ]


if cashier_filter:

    filtered = filtered[
        filtered["cashier_name"].isin(
            cashier_filter
        )
    ]


if warehouse_filter:

    filtered = filtered[
        filtered["warehouse_name"].isin(
            warehouse_filter
        )
    ]


if status_filter:

    filtered = filtered[
        filtered["status"].isin(
            status_filter
        )
    ]


# ==============================================================================
# REFRESH
# ==============================================================================

if st.sidebar.button("🔄 Refresh Data"):

    st.cache_data.clear()
    st.rerun()


# ==============================================================================
# KPI
# ==============================================================================

total_refunds = filtered[
    "refund_id"
].nunique()


pending = (
    filtered["status"] == "PENDING"
).sum()


completed = (
    filtered["status"] == "COMPLETED"
).sum()


rejected = (
    filtered["status"] == "REJECTED"
).sum()


total_net = filtered[
    "report_net"
].sum()


total_tax = filtered[
    "report_tax"
].sum()


total_refund = filtered[
    "report_total"
].sum()


# ==============================================================================
# KPI CARDS
# ==============================================================================

c1, c2, c3, c4, c5 = st.columns(5)


with c1:

    st.metric(
        "Total Refunds",
        f"{total_refunds:,}",
    )


with c2:

    st.metric(
        "Pending",
        f"{pending:,}",
    )


with c3:

    st.metric(
        "Completed",
        f"{completed:,}",
    )


with c4:

    st.metric(
        "Rejected",
        f"{rejected:,}",
    )


with c5:

    st.metric(
        "Refund Total",
        f"{total_refund:,.2f} MMK",
    )


# ==============================================================================
# FINANCIAL SUMMARY
# ==============================================================================

st.divider()

st.subheader(
    "💰 Refund Financial Summary"
)


f1, f2, f3 = st.columns(3)


with f1:

    st.metric(
        "Refund Net",
        f"{total_net:,.2f} MMK",
    )


with f2:

    st.metric(
        "Refund Tax",
        f"{total_tax:,.2f} MMK",
    )


with f3:

    st.metric(
        "Refund Total",
        f"{total_refund:,.2f} MMK",
    )


# ==============================================================================
# PDF GENERATOR
# ==============================================================================

def create_refund_pdf(
    header,
    items,
):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "REFUND REPORT",
            styles["Title"],
        )
    )

    content.append(
        Spacer(1, 12)
    )

    header_text = f"""
    <b>Refund ID:</b> {header.get('refund_id', '')}<br/>
    <b>Invoice:</b> {header.get('invoice_no', '')}<br/>
    <b>Status:</b> {header.get('status', '')}<br/>
    <b>Cashier:</b> {header.get('cashier_name', '')}<br/>
    <b>Warehouse:</b> {header.get('warehouse_name', '')}<br/>
    <b>Reason:</b> {header.get('reason', '')}
    """

    content.append(
        Paragraph(
            header_text,
            styles["Normal"],
        )
    )

    content.append(
        Spacer(1, 12)
    )

    table_data = [
        [
            "Product",
            "Qty",
            "Price",
            "Net",
            "Tax",
            "Total",
        ]
    ]

    total_net_val = 0
    total_tax_val = 0
    total_amount_val = 0

    for item in items:

        net = float(
            item.get(
                "refund_net_amount",
                item.get(
                    "item_total",
                    0,
                ),
            )
            or 0
        )

        tax = float(
            item.get(
                "refund_tax_amount",
                0,
            )
            or 0
        )

        total = float(
            item.get(
                "refund_total_amount",
                item.get(
                    "item_total",
                    0,
                ),
            )
            or 0
        )

        total_net_val += net
        total_tax_val += tax
        total_amount_val += total

        table_data.append(
            [
                item.get(
                    "product_name",
                    "",
                ),
                item.get(
                    "quantity",
                    0,
                ),
                f"{float(item.get('unit_price', 0) or 0):,.2f}",
                f"{net:,.2f}",
                f"{tax:,.2f}",
                f"{total:,.2f}",
            ]
        )

    table_data.append(
        [
            "TOTAL",
            "",
            "",
            f"{total_net_val:,.2f}",
            f"{total_tax_val:,.2f}",
            f"{total_amount_val:,.2f}",
        ]
    )

    table = Table(
        table_data,
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold",
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
            ]
        )
    )

    content.append(table)

    doc.build(content)

    buffer.seek(0)

    return buffer


# ==============================================================================
# REFUND SELECTOR
# ==============================================================================
#
# UI DESIGN
#
# Refund Report
#      ↓
# Select Refund ▼
#      ↓
# Selected Refund Detail
#
# Only the selected refund is displayed.
# ==============================================================================

st.divider()

st.subheader(
    "🔎 Refund Details"
)


if filtered.empty:

    st.warning(
        "No refund records match the selected filters."
    )

else:

    # --------------------------------------------------------------------------
    # BUILD REFUND SELECTOR
    # --------------------------------------------------------------------------

    selector_options = []

    for _, row in filtered.iterrows():

        refund_id = row["refund_id"]

        invoice_no = row["invoice_no"]

        status = row["status"]

        total = float(
            row["report_total"] or 0
        )

        selector_options.append(
            (
                refund_id,
                (
                    f"#{refund_id} | "
                    f"{invoice_no} | "
                    f"{total:,.2f} MMK | "
                    f"{status}"
                ),
            )
        )


    # --------------------------------------------------------------------------
    # SELECT REFUND
    # --------------------------------------------------------------------------

    selected_refund_id = st.selectbox(
        "Select Refund",
        options=[
            item[0]
            for item in selector_options
        ],
        format_func=lambda refund_id: next(
            (
                item[1]
                for item in selector_options
                if item[0] == refund_id
            ),
            str(refund_id),
        ),
        key="refund_selector",
    )


    # --------------------------------------------------------------------------
    # SELECTED REFUND ROW
    # --------------------------------------------------------------------------

    selected_rows = filtered[
        filtered["refund_id"]
        == selected_refund_id
    ]


    if selected_rows.empty:

        st.warning(
            "Selected refund record was not found."
        )

    else:

        selected_row = selected_rows.iloc[0]


        # ======================================================================
        # REFUND HEADER SUMMARY
        # ======================================================================

        st.markdown(
            f"### Refund #{selected_refund_id}"
        )


        h1, h2, h3, h4 = st.columns(4)


        with h1:

            st.write(
                "**Invoice**"
            )

            st.write(
                selected_row["invoice_no"]
            )


        with h2:

            st.write(
                "**Status**"
            )

            st.write(
                selected_row["status"]
            )


        with h3:

            st.write(
                "**Cashier**"
            )

            st.write(
                selected_row["cashier_name"]
            )


        with h4:

            st.write(
                "**Warehouse**"
            )

            st.write(
                selected_row["warehouse_name"]
            )


        # ======================================================================
        # DATE / REASON
        # ======================================================================

        d1, d2 = st.columns(2)


        with d1:

            refund_date_value = selected_row[
                "refund_date"
            ]

            if pd.notna(
                refund_date_value
            ):

                st.write(
                    "**Refund Date**"
                )

                st.write(
                    refund_date_value.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                )

            else:

                st.write(
                    "**Refund Date:** -"
                )


        with d2:

            st.write(
                "**Reason**"
            )

            reason_value = selected_row[
                "reason"
            ]

            st.write(
                reason_value
                if reason_value
                else "-"
            )


        st.divider()


        # ======================================================================
        # SELECTED REFUND AMOUNTS
        # ======================================================================

        selected_net = float(
            selected_row["report_net"]
            or 0
        )

        selected_tax = float(
            selected_row["report_tax"]
            or 0
        )

        selected_total = float(
            selected_row["report_total"]
            or 0
        )


        a1, a2, a3 = st.columns(3)


        with a1:

            st.metric(
                "Refund Net",
                f"{selected_net:,.2f} MMK",
            )


        with a2:

            st.metric(
                "Refund Tax",
                f"{selected_tax:,.2f} MMK",
            )


        with a3:

            st.metric(
                "Refund Total",
                f"{selected_total:,.2f} MMK",
            )


        st.divider()


        # ======================================================================
        # LOAD SELECTED REFUND ITEMS
        # ======================================================================

        try:

            items_response = (
                db()
                .table("refund_detail_view")
                .select("*")
                .eq(
                    "refund_id",
                    selected_refund_id,
                )
                .execute()
            )

            selected_items = (
                items_response.data
                or []
            )

        except Exception as e:

            selected_items = []

            st.error(
                f"Unable to load refund details: {e}"
            )


        # ======================================================================
        # DETAIL ITEMS
        # ======================================================================

        if selected_items:

            detail_df = pd.DataFrame(
                selected_items
            )


            # ------------------------------------------------------------------
            # SAFE NUMERIC COLUMNS
            # ------------------------------------------------------------------

            detail_numeric_columns = [
                "quantity",
                "unit_price",
                "item_total",
                "refund_net_amount",
                "refund_tax_amount",
                "refund_total_amount",
            ]


            for col in detail_numeric_columns:

                if col not in detail_df.columns:

                    detail_df[col] = 0

                detail_df[col] = pd.to_numeric(
                    detail_df[col],
                    errors="coerce",
                ).fillna(0)


            # ------------------------------------------------------------------
            # LEGACY FALLBACK
            # ------------------------------------------------------------------

            detail_df["display_net"] = (
                detail_df[
                    "refund_net_amount"
                ]
            )


            legacy_detail_net = (
                detail_df["display_net"].isna()
                |
                (
                    detail_df[
                        "display_net"
                    ] == 0
                )
            ) & (
                detail_df[
                    "item_total"
                ] != 0
            )


            detail_df.loc[
                legacy_detail_net,
                "display_net",
            ] = detail_df.loc[
                legacy_detail_net,
                "item_total",
            ]


            detail_df["display_tax"] = (
                detail_df[
                    "refund_tax_amount"
                ]
                .fillna(0)
            )


            detail_df["display_total"] = (
                detail_df[
                    "refund_total_amount"
                ]
            )


            legacy_detail_total = (
                detail_df[
                    "display_total"
                ].isna()
                |
                (
                    detail_df[
                        "display_total"
                    ] == 0
                )
            ) & (
                detail_df[
                    "item_total"
                ] != 0
            )


            detail_df.loc[
                legacy_detail_total,
                "display_total",
            ] = detail_df.loc[
                legacy_detail_total,
                "item_total",
            ]


            # ------------------------------------------------------------------
            # DISPLAY TABLE
            # ------------------------------------------------------------------

            selected_detail_display = pd.DataFrame(
                {
                    "Product":
                        detail_df[
                            "product_name"
                        ],

                    "Qty":
                        detail_df[
                            "quantity"
                        ],

                    "Unit Price":
                        detail_df[
                            "unit_price"
                        ],

                    "Refund Net":
                        detail_df[
                            "display_net"
                        ],

                    "Refund Tax":
                        detail_df[
                            "display_tax"
                        ],

                    "Refund Total":
                        detail_df[
                            "display_total"
                        ],
                }
            )


            st.subheader(
                "📦 Refund Items"
            )


            st.dataframe(
                selected_detail_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Qty":
                        st.column_config.NumberColumn(
                            "Qty",
                            format="%.2f",
                        ),

                    "Unit Price":
                        st.column_config.NumberColumn(
                            "Unit Price",
                            format="%,.2f MMK",
                        ),

                    "Refund Net":
                        st.column_config.NumberColumn(
                            "Refund Net",
                            format="%,.2f MMK",
                        ),

                    "Refund Tax":
                        st.column_config.NumberColumn(
                            "Refund Tax",
                            format="%,.2f MMK",
                        ),

                    "Refund Total":
                        st.column_config.NumberColumn(
                            "Refund Total",
                            format="%,.2f MMK",
                        ),
                },
            )


            # ------------------------------------------------------------------
            # DETAIL TOTALS
            # ------------------------------------------------------------------

            detail_net = detail_df[
                "display_net"
            ].sum()

            detail_tax = detail_df[
                "display_tax"
            ].sum()

            detail_total = detail_df[
                "display_total"
            ].sum()


            t1, t2, t3 = st.columns(3)


            with t1:

                st.metric(
                    "Net",
                    f"{detail_net:,.2f} MMK",
                )


            with t2:

                st.metric(
                    "Tax",
                    f"{detail_tax:,.2f} MMK",
                )


            with t3:

                st.metric(
                    "Total",
                    f"{detail_total:,.2f} MMK",
                )


            # ------------------------------------------------------------------
            # PDF / HTML
            # ------------------------------------------------------------------

            pdf_file = create_refund_pdf(
                selected_row.to_dict(),
                selected_items,
            )


            e1, e2 = st.columns(2)


            with e1:

                st.download_button(
                    "📄 PDF",
                    pdf_file,
                    (
                        f"refund_"
                        f"{selected_refund_id}.pdf"
                    ),
                    "application/pdf",
                    key=(
                        f"pdf_"
                        f"{selected_refund_id}"
                    ),
                )


            html_table = (
                selected_detail_display
                .to_html(
                    index=False,
                )
            )


            html_content = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <title>
                    Refund {selected_refund_id}
                </title>
            </head>

            <body>

                <h2>Refund Report</h2>

                <p>
                    <b>Refund ID:</b>
                    {selected_refund_id}<br>

                    <b>Invoice:</b>
                    {selected_row["invoice_no"]}<br>

                    <b>Status:</b>
                    {selected_row["status"]}
                </p>

                {html_table}

                <h3>
                    Net:
                    {detail_net:,.2f} MMK
                </h3>

                <h3>
                    Tax:
                    {detail_tax:,.2f} MMK
                </h3>

                <h3>
                    Total:
                    {detail_total:,.2f} MMK
                </h3>

            </body>
            </html>
            """


            with e2:

                st.download_button(
                    "🖨️ HTML",
                    html_content,
                    (
                        f"refund_"
                        f"{selected_refund_id}.html"
                    ),
                    "text/html",
                    key=(
                        f"html_"
                        f"{selected_refund_id}"
                    ),
                )


        else:

            st.warning(
                "No refund item records found."
            )


# ==============================================================================
# ANALYTICS
# ==============================================================================

st.divider()

st.subheader(
    "📊 Refund Analytics"
)


if not filtered.empty:

    # --------------------------------------------------------------------------
    # Daily Refund Total
    # --------------------------------------------------------------------------

    daily = (
        filtered
        .groupby(
            filtered[
                "refund_date"
            ].dt.date
        )["report_total"]
        .sum()
    )

    st.line_chart(
        daily
    )

    col1, col2 = st.columns(2)

    # --------------------------------------------------------------------------
    # Top Products
    # --------------------------------------------------------------------------

    with col1:

        st.subheader(
            "🏆 Top 10 Products"
        )

        top_products = (
            filtered
            .groupby(
                "product_name"
            )["quantity"]
            .sum()
            .sort_values(
                ascending=False
            )
            .head(10)
        )

        st.bar_chart(
            top_products
        )

    # --------------------------------------------------------------------------
    # Status
    # --------------------------------------------------------------------------

    with col2:

        st.subheader(
            "📊 Status"
        )

        status_data = (
            filtered
            .groupby(
                "status"
            )["refund_id"]
            .nunique()
        )

        if not status_data.empty:

            st.plotly_chart(
                px.pie(
                    values=status_data.values,
                    names=status_data.index,
                    title="Refund Status",
                ),
                use_container_width=True,
            )

    # --------------------------------------------------------------------------
    # Cashier Ranking
    # --------------------------------------------------------------------------

    st.subheader(
        "👤 Cashier Ranking (Top 5)"
    )

    cashier_ranking = (
        filtered
        .groupby(
            "cashier_name"
        )["report_total"]
        .sum()
        .sort_values(
            ascending=False
        )
        .head(5)
    )

    st.bar_chart(
        cashier_ranking
    )

else:

    st.warning(
        "No data for analytics."
    )


# ==============================================================================
# EXPORT
# ==============================================================================

st.divider()

st.subheader(
    "📥 Export"
)


export_columns = [
    "refund_id",
    "sale_id",
    "invoice_no",
    "refund_date",
    "status",
    "reason",
    "product_id",
    "product_name",
    "quantity",
    "unit_price",
    "item_total",
    "refund_net_amount",
    "refund_tax_amount",
    "refund_total_amount",
    "cashier_name",
    "processed_by",
    "approved_at",
    "warehouse_name",
]


for col in export_columns:

    if col not in filtered.columns:

        filtered[col] = ""


export_df = filtered[
    export_columns
].copy()


export_df = export_df.rename(
    columns={
        "refund_id":
            "Refund ID",

        "sale_id":
            "Sale ID",

        "invoice_no":
            "Invoice",

        "refund_date":
            "Refund Date",

        "status":
            "Status",

        "reason":
            "Reason",

        "product_id":
            "Product ID",

        "product_name":
            "Product",

        "quantity":
            "Quantity",

        "unit_price":
            "Unit Price",

        "item_total":
            "Item Price Total",

        "refund_net_amount":
            "Refund Net",

        "refund_tax_amount":
            "Refund Tax",

        "refund_total_amount":
            "Refund Total",

        "cashier_name":
            "Cashier",

        "processed_by":
            "Processed By",

        "approved_at":
            "Approved At",

        "warehouse_name":
            "Warehouse",
    }
)


# ==============================================================================
# EXCEL
# ==============================================================================

excel_buffer = io.BytesIO()


with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl",
) as writer:

    export_df.to_excel(
        writer,
        index=False,
        sheet_name="Refund Report",
    )


excel_buffer.seek(0)


st.download_button(
    "📥 Excel",
    excel_buffer.getvalue(),
    "refund_report_v4.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
