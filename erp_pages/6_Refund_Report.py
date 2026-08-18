# ==============================================================================
# ERP ENTERPRISE REFUND REPORT v5.2
# TAX-AWARE + FROM/TO DATE + REJECTED SEPARATION
#
# IMPORTANT ACCOUNTING RULE
# ------------------------------------------------------------------------------
# ACTUAL REFUND REGISTER:
#     COMPLETED
#     APPROVED
#
# REJECTED:
#     Completely separated from Refund Register
#
# PENDING:
#     Completely separated from Refund Register
#
# REFUND TOTAL:
#     COMPLETED + APPROVED ONLY
#
# REJECTED TOTAL:
#     REJECTED ONLY
#
# PENDING TOTAL:
#     PENDING ONLY
# ==============================================================================

import io
from datetime import date, timedelta

import pandas as pd
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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="Refund Report",
    page_icon="↩️",
    layout="wide",
)


# ==============================================================================
# AUTH
# ==============================================================================

user = require_login()


# ==============================================================================
# BUSINESS STATUS RULE
# ==============================================================================

ACTUAL_REFUND_STATUSES = [
    "COMPLETED",
    "APPROVED",
]

REJECTED_STATUS = "REJECTED"

PENDING_STATUS = "PENDING"


# ==============================================================================
# COLUMN DEFINITIONS
# ==============================================================================

NUMERIC_COLUMNS = [
    "quantity",
    "unit_price",
    "item_total",
    "refund_amount",
    "refund_net_amount",
    "refund_tax_amount",
    "refund_total_amount",
]

TEXT_COLUMNS = [
    "invoice_no",
    "cashier_name",
    "warehouse_name",
    "product_name",
    "processed_by",
    "reason",
]


# ==============================================================================
# SAFE HELPERS
# ==============================================================================

def safe_float(value):
    try:
        if value is None:
            return 0.0

        if pd.isna(value):
            return 0.0

        return float(value)

    except Exception:
        return 0.0


def safe_text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value)


def money(value):
    return f"{safe_float(value):,.2f} MMK"


# ==============================================================================
# NORMALIZE REPORT DATAFRAME
# ==============================================================================

def normalize_report_dataframe(df):

    if df is None:
        df = pd.DataFrame()

    df = df.copy()

    # --------------------------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------------------------

    for col in NUMERIC_COLUMNS:

        if col not in df.columns:
            df[col] = 0.0

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        ).fillna(0.0)

    # --------------------------------------------------------------------------
    # Text columns
    # --------------------------------------------------------------------------

    for col in TEXT_COLUMNS:

        if col not in df.columns:
            df[col] = ""

        df[col] = (
            df[col]
            .fillna("")
            .astype(str)
        )

    # --------------------------------------------------------------------------
    # IDs
    # --------------------------------------------------------------------------

    for col in [
        "refund_id",
        "sale_id",
        "product_id",
    ]:

        if col not in df.columns:
            df[col] = ""

    # --------------------------------------------------------------------------
    # Status
    # --------------------------------------------------------------------------

    if "status" not in df.columns:
        df["status"] = "COMPLETED"

    df["status"] = (
        df["status"]
        .fillna("COMPLETED")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------------------------
    # Refund date
    # --------------------------------------------------------------------------

    if "refund_date" not in df.columns:
        df["refund_date"] = pd.NaT

    df["refund_date"] = pd.to_datetime(
        df["refund_date"],
        errors="coerce",
    )

    # --------------------------------------------------------------------------
    # Approved at
    # --------------------------------------------------------------------------

    if "approved_at" not in df.columns:
        df["approved_at"] = ""

    # --------------------------------------------------------------------------
    # Accounting amounts
    # --------------------------------------------------------------------------

    df["report_net"] = (
        pd.to_numeric(
            df["refund_net_amount"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    df["report_tax"] = (
        pd.to_numeric(
            df["refund_tax_amount"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    df["report_total"] = (
        pd.to_numeric(
            df["refund_total_amount"],
            errors="coerce",
        )
        .fillna(0.0)
    )

    # --------------------------------------------------------------------------
    # Legacy compatibility
    #
    # If old records do not contain tax-aware refund values,
    # use item_total as fallback.
    # --------------------------------------------------------------------------

    legacy_total_mask = (
        (df["report_total"] == 0)
        & (df["item_total"] != 0)
    )

    df.loc[
        legacy_total_mask,
        "report_total"
    ] = df.loc[
        legacy_total_mask,
        "item_total"
    ]

    legacy_net_mask = (
        (df["report_net"] == 0)
        & (df["item_total"] != 0)
    )

    df.loc[
        legacy_net_mask,
        "report_net"
    ] = df.loc[
        legacy_net_mask,
        "item_total"
    ]

    # --------------------------------------------------------------------------
    # Sort
    # --------------------------------------------------------------------------

    if "refund_date" in df.columns:

        df = df.sort_values(
            by="refund_date",
            ascending=False,
            na_position="last",
        )

    return df.reset_index(drop=True)


# ==============================================================================
# LOAD REFUND REPORT
# ==============================================================================

@st.cache_data(ttl=60)
def load_refund_report():

    try:

        response = (
            db()
            .table("refund_report_view")
            .select("*")
            .order(
                "refund_date",
                desc=True,
            )
            .execute()
        )

        return normalize_report_dataframe(
            pd.DataFrame(
                response.data or []
            )
        )

    except Exception as e:

        st.error(
            f"Failed to load refund report: {e}"
        )

        return pd.DataFrame()


# ==============================================================================
# FILTER BY DATE
# ==============================================================================

def filter_by_date(
    df,
    from_date,
    to_date,
):

    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    if "refund_date" not in result.columns:
        return result.iloc[0:0].copy()

    result["refund_date"] = pd.to_datetime(
        result["refund_date"],
        errors="coerce",
    )

    start_datetime = pd.Timestamp(
        from_date
    )

    end_datetime = (
        pd.Timestamp(to_date)
        + pd.Timedelta(days=1)
        - pd.Timedelta(microseconds=1)
    )

    mask = (
        result["refund_date"].notna()
        & (result["refund_date"] >= start_datetime)
        & (result["refund_date"] <= end_datetime)
    )

    return result.loc[
        mask
    ].copy().reset_index(drop=True)


# ==============================================================================
# SPLIT REPORT BY BUSINESS STATUS
#
# THIS IS THE MOST IMPORTANT PART
#
# actual_df:
#     COMPLETED + APPROVED ONLY
#
# rejected_df:
#     REJECTED ONLY
#
# pending_df:
#     PENDING ONLY
#
# Therefore REJECTED records can NEVER enter the Refund Register.
# ==============================================================================

def split_report_by_status(df):

    if df is None or df.empty:

        empty = pd.DataFrame()

        return (
            empty.copy(),
            empty.copy(),
            empty.copy(),
        )

    normalized = normalize_report_dataframe(
        df
    )

    actual_df = normalized[
        normalized["status"].isin(
            ACTUAL_REFUND_STATUSES
        )
    ].copy()

    rejected_df = normalized[
        normalized["status"] == REJECTED_STATUS
    ].copy()

    pending_df = normalized[
        normalized["status"] == PENDING_STATUS
    ].copy()

    return (
        actual_df.reset_index(drop=True),
        rejected_df.reset_index(drop=True),
        pending_df.reset_index(drop=True),
    )


# ==============================================================================
# CALCULATE SUMMARY
# ==============================================================================

def calculate_summary(
    actual_df,
    rejected_df,
    pending_df,
):

    actual_net = (
        actual_df["report_net"].sum()
        if not actual_df.empty
        else 0.0
    )

    actual_tax = (
        actual_df["report_tax"].sum()
        if not actual_df.empty
        else 0.0
    )

    actual_total = (
        actual_df["report_total"].sum()
        if not actual_df.empty
        else 0.0
    )

    rejected_total = (
        rejected_df["report_total"].sum()
        if not rejected_df.empty
        else 0.0
    )

    pending_total = (
        pending_df["report_total"].sum()
        if not pending_df.empty
        else 0.0
    )

    actual_count = (
        actual_df["refund_id"].nunique()
        if not actual_df.empty
        else 0
    )

    rejected_count = (
        rejected_df["refund_id"].nunique()
        if not rejected_df.empty
        else 0
    )

    pending_count = (
        pending_df["refund_id"].nunique()
        if not pending_df.empty
        else 0
    )

    return {
        "actual_net": safe_float(actual_net),
        "actual_tax": safe_float(actual_tax),
        "actual_total": safe_float(actual_total),

        "rejected_total": safe_float(
            rejected_total
        ),

        "pending_total": safe_float(
            pending_total
        ),

        "actual_count": int(actual_count),
        "rejected_count": int(rejected_count),
        "pending_count": int(pending_count),
    }


# ==============================================================================
# PDF HEADER / FOOTER
# ==============================================================================

def pdf_header_footer(
    canvas,
    doc,
):

    canvas.saveState()

    width, height = A4

    canvas.setFont(
        "Helvetica-Bold",
        9,
    )

    canvas.drawString(
        40,
        height - 28,
        "ERP ENTERPRISE",
    )

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.drawRightString(
        width - 40,
        height - 28,
        "REFUND REPORT",
    )

    canvas.drawString(
        40,
        22,
        "ERP Refund Report",
    )

    canvas.drawRightString(
        width - 40,
        22,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ==============================================================================
# CREATE PDF REPORT
# ==============================================================================

def create_refund_report_pdf(
    actual_df,
    rejected_df,
    pending_df,
    report_from,
    report_to,
):

    buffer = io.BytesIO()

    summary = calculate_summary(
        actual_df,
        rejected_df,
        pending_df,
    )

    actual_net = summary["actual_net"]
    actual_tax = summary["actual_tax"]
    actual_total = summary["actual_total"]

    rejected_total = summary[
        "rejected_total"
    ]

    pending_total = summary[
        "pending_total"
    ]

    actual_count = summary[
        "actual_count"
    ]

    rejected_count = summary[
        "rejected_count"
    ]

    pending_count = summary[
        "pending_count"
    ]

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=48,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RefundTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "RefundSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        spaceAfter=14,
    )

    small_style = ParagraphStyle(
        "RefundSmall",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=TA_LEFT,
    )

    section_style = ParagraphStyle(
        "RefundSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        spaceBefore=8,
        spaceAfter=8,
    )

    content = []

    # --------------------------------------------------------------------------
    # TITLE
    # --------------------------------------------------------------------------

    content.append(
        Paragraph(
            "REFUND REPORT",
            title_style,
        )
    )

    period_text = (
        "Report Period: <b>{}</b> to <b>{}</b>"
        .format(
            report_from.strftime(
                "%Y-%m-%d"
            ),
            report_to.strftime(
                "%Y-%m-%d"
            ),
        )
    )

    content.append(
        Paragraph(
            period_text,
            subtitle_style,
        )
    )

    # --------------------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------------------

    summary_data = [
        [
            "Actual Refunds",
            "Refund Net",
            "Refund Tax",
            "Refund Total",
        ],
        [
            str(actual_count),
            f"{actual_net:,.2f}",
            f"{actual_tax:,.2f}",
            f"{actual_total:,.2f}",
        ],
        [
            "Rejected",
            "Rejected Total",
            "Pending",
            "Pending Total",
        ],
        [
            str(rejected_count),
            f"{rejected_total:,.2f}",
            str(pending_count),
            f"{pending_total:,.2f}",
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            125,
            125,
            125,
            125,
        ],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#343A40"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    colors.HexColor(
                        "#E9ECEF"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 2),
                    (-1, 2),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 3),
                    (-1, 3),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor(
                        "#BFC3C7"
                    ),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    content.append(
        summary_table
    )

    content.append(
        Spacer(1, 16)
    )

    # --------------------------------------------------------------------------
    # ACTUAL REFUND REGISTER
    # --------------------------------------------------------------------------

    content.append(
        Paragraph(
            "ACTUAL REFUND REGISTER",
            section_style,
        )
    )

    content.append(
        Paragraph(
            "Only COMPLETED and APPROVED refunds are included in this section.",
            small_style,
        )
    )

    content.append(
        Spacer(1, 8)
    )

    table_data = [
        [
            "ID",
            "Invoice",
            "Date",
            "Status",
            "Product",
            "Qty",
            "Net",
            "Tax",
            "Total",
        ]
    ]

    for _, row in actual_df.iterrows():

        refund_date = row[
            "refund_date"
        ]

        if pd.notna(refund_date):

            date_text = (
                refund_date.strftime(
                    "%Y-%m-%d"
                )
            )

        else:

            date_text = ""

        table_data.append(
            [
                safe_text(
                    row["refund_id"]
                ),
                safe_text(
                    row["invoice_no"]
                ),
                date_text,
                safe_text(
                    row["status"]
                ),
                safe_text(
                    row["product_name"]
                ),
                f"{safe_float(row['quantity']):,.2f}",
                f"{safe_float(row['report_net']):,.2f}",
                f"{safe_float(row['report_tax']):,.2f}",
                f"{safe_float(row['report_total']):,.2f}",
            ]
        )

    table_data.append(
        [
            "",
            "",
            "",
            "",
            "REFUND TOTAL",
            "",
            f"{actual_net:,.2f}",
            f"{actual_tax:,.2f}",
            f"{actual_total:,.2f}",
        ]
    )

    detail_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            35,
            60,
            58,
            55,
            105,
            35,
            58,
            48,
            61,
        ],
    )

    detail_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#343A40"
                    ),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, 0),
                    7,
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -2),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 1),
                    (-1, -1),
                    6.8,
                ),
                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.HexColor(
                        "#E9ECEF"
                    ),
                ),
                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor(
                        "#BFC3C7"
                    ),
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "LEFT",
                ),
                (
                    "ALIGN",
                    (5, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "ALIGN",
                    (5, 0),
                    (-1, 0),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    content.append(
        detail_table
    )

    # --------------------------------------------------------------------------
    # REJECTED SECTION
    # --------------------------------------------------------------------------

    if not rejected_df.empty:

        content.append(
            Spacer(1, 18)
        )

        content.append(
            Paragraph(
                "REJECTED REFUNDS — SEPARATE",
                section_style,
            )
        )

        rejected_table_data = [
            [
                "ID",
                "Invoice",
                "Date",
                "Status",
                "Product",
                "Qty",
                "Amount",
            ]
        ]

        for _, row in rejected_df.iterrows():

            refund_date = row[
                "refund_date"
            ]

            date_text = (
                refund_date.strftime(
                    "%Y-%m-%d"
                )
                if pd.notna(
                    refund_date
                )
                else ""
            )

            rejected_table_data.append(
                [
                    safe_text(
                        row["refund_id"]
                    ),
                    safe_text(
                        row["invoice_no"]
                    ),
                    date_text,
                    "REJECTED",
                    safe_text(
                        row["product_name"]
                    ),
                    f"{safe_float(row['quantity']):,.2f}",
                    f"{safe_float(row['report_total']):,.2f}",
                ]
            )

        rejected_table_data.append(
            [
                "",
                "",
                "",
                "",
                "REJECTED TOTAL",
                "",
                f"{rejected_total:,.2f}",
            ]
        )

        rejected_table = Table(
            rejected_table_data,
            repeatRows=1,
            colWidths=[
                45,
                75,
                65,
                65,
                130,
                45,
                80,
            ],
        )

        rejected_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#842029"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BACKGROUND",
                        (0, -1),
                        (-1, -1),
                        colors.HexColor(
                            "#F8D7DA"
                        ),
                    ),
                    (
                        "FONTNAME",
                        (0, -1),
                        (-1, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor(
                            "#BFC3C7"
                        ),
                    ),
                    (
                        "ALIGN",
                        (5, 1),
                        (-1, -1),
                        "RIGHT",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        content.append(
            rejected_table
        )

    # --------------------------------------------------------------------------
    # PENDING SECTION
    # --------------------------------------------------------------------------

    if not pending_df.empty:

        content.append(
            Spacer(1, 18)
        )

        content.append(
            Paragraph(
                "PENDING REFUNDS — SEPARATE",
                section_style,
            )
        )

        pending_table_data = [
            [
                "ID",
                "Invoice",
                "Date",
                "Status",
                "Product",
                "Qty",
                "Amount",
            ]
        ]

        for _, row in pending_df.iterrows():

            refund_date = row[
                "refund_date"
            ]

            date_text = (
                refund_date.strftime(
                    "%Y-%m-%d"
                )
                if pd.notna(
                    refund_date
                )
                else ""
            )

            pending_table_data.append(
                [
                    safe_text(
                        row["refund_id"]
                    ),
                    safe_text(
                        row["invoice_no"]
                    ),
                    date_text,
                    "PENDING",
                    safe_text(
                        row["product_name"]
                    ),
                    f"{safe_float(row['quantity']):,.2f}",
                    f"{safe_float(row['report_total']):,.2f}",
                ]
            )

        pending_table_data.append(
            [
                "",
                "",
                "",
                "",
                "PENDING TOTAL",
                "",
                f"{pending_total:,.2f}",
            ]
        )

        pending_table = Table(
            pending_table_data,
            repeatRows=1,
            colWidths=[
                45,
                75,
                65,
                65,
                130,
                45,
                80,
            ],
        )

        pending_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#856404"
                        ),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BACKGROUND",
                        (0, -1),
                        (-1, -1),
                        colors.HexColor(
                            "#FFF3CD"
                        ),
                    ),
                    (
                        "FONTNAME",
                        (0, -1),
                        (-1, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor(
                            "#BFC3C7"
                        ),
                    ),
                    (
                        "ALIGN",
                        (5, 1),
                        (-1, -1),
                        "RIGHT",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        content.append(
            pending_table
        )

    # --------------------------------------------------------------------------
    # ACCOUNTING RULE
    # --------------------------------------------------------------------------

    content.append(
        Spacer(1, 14)
    )

    content.append(
        Paragraph(
            "<b>Accounting Rule:</b> "
            "Refund Total includes only COMPLETED and APPROVED refunds. "
            "REJECTED and PENDING amounts are never included in Actual Refund Total "
            "and are reported separately.",
            small_style,
        )
    )

    doc.build(
        content,
        onFirstPage=pdf_header_footer,
        onLaterPages=pdf_header_footer,
    )

    buffer.seek(0)

    return buffer.getvalue()


# ==============================================================================
# CREATE HTML REPORT
# ==============================================================================

def create_html_report(
    actual_df,
    rejected_df,
    pending_df,
    report_from,
    report_to,
):

    summary = calculate_summary(
        actual_df,
        rejected_df,
        pending_df,
    )

    actual_net = summary["actual_net"]
    actual_tax = summary["actual_tax"]
    actual_total = summary["actual_total"]

    rejected_total = summary[
        "rejected_total"
    ]

    pending_total = summary[
        "pending_total"
    ]

    actual_count = summary[
        "actual_count"
    ]

    rejected_count = summary[
        "rejected_count"
    ]

    pending_count = summary[
        "pending_count"
    ]

    # --------------------------------------------------------------------------
    # ACTUAL REFUND TABLE ONLY
    # --------------------------------------------------------------------------

    html_df = actual_df.copy()

    if not html_df.empty:

        html_df["Refund Date"] = (
            html_df["refund_date"]
            .dt.strftime(
                "%Y-%m-%d %H:%M"
            )
        )

    display_df = pd.DataFrame(
        {
            "Refund ID": html_df.get(
                "refund_id",
                pd.Series(
                    dtype="object"
                ),
            ),
            "Invoice": html_df.get(
                "invoice_no",
                pd.Series(
                    dtype="object"
                ),
            ),
            "Refund Date": html_df.get(
                "Refund Date",
                pd.Series(
                    dtype="object"
                ),
            ),
            "Status": html_df.get(
                "status",
                pd.Series(
                    dtype="object"
                ),
            ),
            "Product": html_df.get(
                "product_name",
                pd.Series(
                    dtype="object"
                ),
            ),
            "Qty": html_df.get(
                "quantity",
                pd.Series(
                    dtype="float"
                ),
            ),
            "Refund Net": html_df.get(
                "report_net",
                pd.Series(
                    dtype="float"
                ),
            ),
            "Refund Tax": html_df.get(
                "report_tax",
                pd.Series(
                    dtype="float"
                ),
            ),
            "Refund Total": html_df.get(
                "report_total",
                pd.Series(
                    dtype="float"
                ),
            ),
            "Cashier": html_df.get(
                "cashier_name",
                pd.Series(
                    dtype="object"
                ),
            ),
            "Warehouse": html_df.get(
                "warehouse_name",
                pd.Series(
                    dtype="object"
                ),
            ),
        }
    )

    table_html = display_df.to_html(
        index=False,
        classes="refund-table",
        border=0,
    )

    # --------------------------------------------------------------------------
    # HTML
    # --------------------------------------------------------------------------

    html_parts = []

    html_parts.append(
        "<!DOCTYPE html>"
    )

    html_parts.append(
        "<html>"
    )

    html_parts.append(
        "<head>"
    )

    html_parts.append(
        '<meta charset="utf-8">'
    )

    html_parts.append(
        "<title>Refund Report</title>"
    )

    html_parts.append(
        "<style>"
    )

    html_parts.append(
        "body { font-family: Arial, sans-serif; margin: 40px; color: #222; }"
    )

    html_parts.append(
        "h1 { text-align: center; margin-bottom: 5px; }"
    )

    html_parts.append(
        ".period { text-align: center; color: #666; margin-bottom: 25px; }"
    )

    html_parts.append(
        ".summary { width: 100%; border-collapse: collapse; margin-bottom: 25px; }"
    )

    html_parts.append(
        ".summary td { border: 1px solid #ddd; padding: 12px; text-align: center; }"
    )

    html_parts.append(
        ".summary-title { font-weight: bold; background: #343a40; color: white; }"
    )

    html_parts.append(
        ".reject-title { font-weight: bold; background: #f8d7da; }"
    )

    html_parts.append(
        ".pending-title { font-weight: bold; background: #fff3cd; }"
    )

    html_parts.append(
        ".refund-table { width: 100%; border-collapse: collapse; margin-top: 20px; }"
    )

    html_parts.append(
        ".refund-table th { background: #343a40; color: white; padding: 9px; text-align: left; }"
    )

    html_parts.append(
        ".refund-table td { border: 1px solid #ddd; padding: 8px; }"
    )

    html_parts.append(
        ".refund-table tr:nth-child(even) { background: #f8f9fa; }"
    )

    html_parts.append(
        ".footer { margin-top: 25px; font-weight: bold; }"
    )

    html_parts.append(
        ".separate { margin-top: 30px; padding: 15px; border: 1px solid #ddd; }"
    )

    html_parts.append(
        "</style>"
    )

    html_parts.append(
        "</head>"
    )

    html_parts.append(
        "<body>"
    )

    html_parts.append(
        "<h1>REFUND REPORT</h1>"
    )

    html_parts.append(
        '<div class="period">'
    )

    html_parts.append(
        "Report Period: <b>"
        + report_from.strftime(
            "%Y-%m-%d"
        )
        + "</b> to <b>"
        + report_to.strftime(
            "%Y-%m-%d"
        )
        + "</b>"
    )

    html_parts.append(
        "</div>"
    )

    # --------------------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------------------

    html_parts.append(
        '<table class="summary">'
    )

    html_parts.append(
        "<tr>"
    )

    html_parts.append(
        '<td class="summary-title">Actual Refunds</td>'
    )

    html_parts.append(
        '<td class="summary-title">Refund Net</td>'
    )

    html_parts.append(
        '<td class="summary-title">Refund Tax</td>'
    )

    html_parts.append(
        '<td class="summary-title">Refund Total</td>'
    )

    html_parts.append(
        "</tr>"
    )

    html_parts.append(
        "<tr>"
    )

    html_parts.append(
        "<td>"
        + str(actual_count)
        + "</td>"
    )

    html_parts.append(
        "<td>"
        + f"{actual_net:,.2f}"
        + " MMK</td>"
    )

    html_parts.append(
        "<td>"
        + f"{actual_tax:,.2f}"
        + " MMK</td>"
    )

    html_parts.append(
        "<td>"
        + f"{actual_total:,.2f}"
        + " MMK</td>"
    )

    html_parts.append(
        "</tr>"
    )

    html_parts.append(
        "<tr>"
    )

    html_parts.append(
        '<td class="reject-title">Rejected</td>'
    )

    html_parts.append(
        '<td class="reject-title">Rejected Total</td>'
    )

    html_parts.append(
        '<td class="pending-title">Pending</td>'
    )

    html_parts.append(
        '<td class="pending-title">Pending Total</td>'
    )

    html_parts.append(
        "</tr>"
    )

    html_parts.append(
        "<tr>"
    )

    html_parts.append(
        "<td>"
        + str(rejected_count)
        + "</td>"
    )

    html_parts.append(
        "<td>"
        + f"{rejected_total:,.2f}"
        + " MMK</td>"
    )

    html_parts.append(
        "<td>"
        + str(pending_count)
        + "</td>"
    )

    html_parts.append(
        "<td>"
        + f"{pending_total:,.2f}"
        + " MMK</td>"
    )

    html_parts.append(
        "</tr>"
    )

    html_parts.append(
        "</table>"
    )

    # --------------------------------------------------------------------------
    # ACTUAL REFUND REGISTER
    # --------------------------------------------------------------------------

    html_parts.append(
        "<h2>ACTUAL REFUND REGISTER</h2>"
    )

    html_parts.append(
        "<p>"
        "Only COMPLETED and APPROVED refunds are shown in this register."
        "</p>"
    )

    html_parts.append(
        table_html
    )

    # --------------------------------------------------------------------------
    # REJECTED SEPARATE
    # --------------------------------------------------------------------------

    if not rejected_df.empty:

        html_parts.append(
            '<div class="separate">'
        )

        html_parts.append(
            "<h2>REJECTED REFUNDS — SEPARATE</h2>"
        )

        html_parts.append(
            "<p>"
            + f"Rejected Total: {rejected_total:,.2f} MMK"
            + "</p>"
        )

        html_parts.append(
            "</div>"
        )

    # --------------------------------------------------------------------------
    # PENDING SEPARATE
    # --------------------------------------------------------------------------

    if not pending_df.empty:

        html_parts.append(
            '<div class="separate">'
        )

        html_parts.append(
            "<h2>PENDING REFUNDS — SEPARATE</h2>"
        )

        html_parts.append(
            "<p>"
            + f"Pending Total: {pending_total:,.2f} MMK"
            + "</p>"
        )

        html_parts.append(
            "</div>"
        )

    # --------------------------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------------------------

    html_parts.append(
        '<div class="footer">'
    )

    html_parts.append(
        "Actual Refund Total: "
        + f"{actual_total:,.2f}"
        + " MMK"
    )

    html_parts.append(
        "<br><br>"
    )

    html_parts.append(
        "Rejected Total: "
        + f"{rejected_total:,.2f}"
        + " MMK"
    )

    html_parts.append(
        "<br><br>"
    )

    html_parts.append(
        "Pending Total: "
        + f"{pending_total:,.2f}"
        + " MMK"
    )

    html_parts.append(
        "</div>"
    )

    html_parts.append(
        "</body>"
    )

    html_parts.append(
        "</html>"
    )

    return "\n".join(
        html_parts
    )


# ==============================================================================
# BUILD EXPORT DATAFRAME
#
# IMPORTANT:
# This function receives ACTUAL REFUND dataframe only.
# Therefore REJECTED records cannot enter the normal Refund CSV.
# ==============================================================================

def build_export_dataframe(
    report_df
):

    if report_df is None:
        report_df = pd.DataFrame()

    export_df = report_df.copy()

    if (
        "refund_date" in export_df.columns
    ):

        export_df["refund_date"] = (
            pd.to_datetime(
                export_df["refund_date"],
                errors="coerce",
            )
            .dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
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

        if col not in export_df.columns:
            export_df[col] = ""

    export_df = export_df[
        export_columns
    ].copy()

    export_df = export_df.rename(
        columns={
            "refund_id": "Refund ID",
            "sale_id": "Sale ID",
            "invoice_no": "Invoice",
            "refund_date": "Refund Date",
            "status": "Status",
            "reason": "Reason",
            "product_id": "Product ID",
            "product_name": "Product",
            "quantity": "Quantity",
            "unit_price": "Unit Price",
            "item_total": "Item Price Total",
            "refund_net_amount": "Refund Net",
            "refund_tax_amount": "Refund Tax",
            "refund_total_amount": "Refund Total",
            "cashier_name": "Cashier",
            "processed_by": "Processed By",
            "approved_at": "Approved At",
            "warehouse_name": "Warehouse",
        }
    )

    return export_df


# ==============================================================================
# MAIN UI
# ==============================================================================

st.title(
    "↩️ ERP ENTERPRISE REFUND REPORT"
)

st.caption(
    "Tax-Aware Refund Reporting | "
    "Date Range | "
    "Rejected Separation"
)


# ==============================================================================
# LOAD DATA
# ==============================================================================

all_refunds_df = load_refund_report()

all_refunds_df = normalize_report_dataframe(
    all_refunds_df
)


# ==============================================================================
# DATE RANGE
# ==============================================================================

today = date.today()

if "refund_report_from_date" not in st.session_state:

    if not all_refunds_df.empty:

        valid_dates = (
            all_refunds_df[
                "refund_date"
            ]
            .dropna()
        )

        if not valid_dates.empty:

            st.session_state[
                "refund_report_from_date"
            ] = valid_dates.min().date()

        else:

            st.session_state[
                "refund_report_from_date"
            ] = today

    else:

        st.session_state[
            "refund_report_from_date"
        ] = today


if "refund_report_to_date" not in st.session_state:

    st.session_state[
        "refund_report_to_date"
    ] = today


col1, col2, col3 = st.columns(
    [1, 1, 1]
)


with col1:

    report_from = st.date_input(
        "From Date",
        value=st.session_state[
            "refund_report_from_date"
        ],
        key="refund_report_from_picker",
    )


with col2:

    report_to = st.date_input(
        "To Date",
        value=st.session_state[
            "refund_report_to_date"
        ],
        key="refund_report_to_picker",
    )


with col3:

    st.write("")
    st.write("")

    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):

        load_refund_report.clear()

        st.rerun()


# ==============================================================================
# VALIDATE DATE
# ==============================================================================

if report_from > report_to:

    st.error(
        "From Date cannot be later than To Date."
    )

    st.stop()


# ==============================================================================
# APPLY DATE FILTER FIRST
# ==============================================================================

date_filtered_df = filter_by_date(
    all_refunds_df,
    report_from,
    report_to,
)


# ==============================================================================
# SPLIT BY STATUS
#
# CRITICAL:
# REJECTED IS REMOVED FROM ACTUAL REFUND REGISTER HERE.
# ==============================================================================

actual_df, rejected_df, pending_df = (
    split_report_by_status(
        date_filtered_df
    )
)


# ==============================================================================
# SUMMARY
# ==============================================================================

summary = calculate_summary(
    actual_df,
    rejected_df,
    pending_df,
)


# ==============================================================================
# KPI CARDS
# ==============================================================================

k1, k2, k3, k4, k5 = st.columns(
    5
)


with k1:

    st.metric(
        "Actual Refunds",
        f"{summary['actual_count']:,}",
    )


with k2:

    st.metric(
        "Refund Net",
        money(
            summary["actual_net"]
        ),
    )


with k3:

    st.metric(
        "Refund Tax",
        money(
            summary["actual_tax"]
        ),
    )


with k4:

    st.metric(
        "Refund Total",
        money(
            summary["actual_total"]
        ),
    )


with k5:

    st.metric(
        "Rejected Total",
        money(
            summary["rejected_total"]
        ),
    )


# ==============================================================================
# ACCOUNTING NOTICE
# ==============================================================================

st.info(
    "Accounting Rule: Refund Total includes ONLY COMPLETED and APPROVED refunds. "
    "REJECTED and PENDING amounts are excluded and reported separately."
)


# ==============================================================================
# STATUS SUMMARY
# ==============================================================================

s1, s2, s3 = st.columns(
    3
)


with s1:

    st.metric(
        "✅ Actual Refund Records",
        f"{summary['actual_count']:,}",
    )


with s2:

    st.metric(
        "❌ Rejected Records",
        f"{summary['rejected_count']:,}",
    )


with s3:

    st.metric(
        "⏳ Pending Records",
        f"{summary['pending_count']:,}",
    )


# ==============================================================================
# TABS
# ==============================================================================

tab_refund, tab_rejected, tab_pending, tab_export = st.tabs(
    [
        "↩️ Refund Register",
        "❌ Rejected",
        "⏳ Pending",
        "📤 Export",
    ]
)


# ==============================================================================
# TAB 1
# ACTUAL REFUND REGISTER
# ==============================================================================

with tab_refund:

    st.subheader(
        "↩️ Actual Refund Register"
    )

    st.caption(
        "Only COMPLETED and APPROVED refunds are shown here."
    )

    if actual_df.empty:

        st.success(
            "No actual refund records found for the selected date range."
        )

    else:

        display_actual = actual_df.copy()

        display_actual["Refund Date"] = (
            display_actual[
                "refund_date"
            ]
            .dt.strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        display_actual = display_actual[
            [
                "refund_id",
                "sale_id",
                "invoice_no",
                "refund_date",
                "status",
                "product_name",
                "quantity",
                "report_net",
                "report_tax",
                "report_total",
                "cashier_name",
                "warehouse_name",
            ]
        ].copy()

        display_actual = display_actual.rename(
            columns={
                "refund_id": "Refund ID",
                "sale_id": "Sale ID",
                "invoice_no": "Invoice",
                "refund_date": "Refund Date",
                "status": "Status",
                "product_name": "Product",
                "quantity": "Qty",
                "report_net": "Refund Net",
                "report_tax": "Refund Tax",
                "report_total": "Refund Total",
                "cashier_name": "Cashier",
                "warehouse_name": "Warehouse",
            }
        )

        st.dataframe(
            display_actual,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        r1, r2, r3 = st.columns(
            3
        )

        with r1:

            st.metric(
                "Refund Net",
                money(
                    summary["actual_net"]
                ),
            )

        with r2:

            st.metric(
                "Refund Tax",
                money(
                    summary["actual_tax"]
                ),
            )

        with r3:

            st.metric(
                "Refund Total",
                money(
                    summary["actual_total"]
                ),
            )


# ==============================================================================
# TAB 2
# REJECTED
# ==============================================================================

with tab_rejected:

    st.subheader(
        "❌ Rejected Refunds"
    )

    st.caption(
        "Rejected refunds are NOT part of the Actual Refund Register."
    )

    if rejected_df.empty:

        st.success(
            "No rejected refunds found for the selected date range."
        )

    else:

        display_rejected = rejected_df.copy()

        display_rejected["Refund Date"] = (
            display_rejected[
                "refund_date"
            ]
            .dt.strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        display_rejected = display_rejected[
            [
                "refund_id",
                "sale_id",
                "invoice_no",
                "refund_date",
                "status",
                "product_name",
                "quantity",
                "report_total",
                "reason",
                "cashier_name",
                "processed_by",
            ]
        ].copy()

        display_rejected = display_rejected.rename(
            columns={
                "refund_id": "Refund ID",
                "sale_id": "Sale ID",
                "invoice_no": "Invoice",
                "refund_date": "Refund Date",
                "status": "Status",
                "product_name": "Product",
                "quantity": "Qty",
                "report_total": "Rejected Amount",
                "reason": "Reason",
                "cashier_name": "Cashier",
                "processed_by": "Processed By",
            }
        )

        st.dataframe(
            display_rejected,
            use_container_width=True,
            hide_index=True,
        )

        st.error(
            "Rejected Total: "
            + money(
                summary[
                    "rejected_total"
                ]
            )
            + " — NOT INCLUDED in Refund Total."
        )


# ==============================================================================
# TAB 3
# PENDING
# ==============================================================================

with tab_pending:

    st.subheader(
        "⏳ Pending Refunds"
    )

    st.caption(
        "Pending refunds are NOT part of the Actual Refund Register."
    )

    if pending_df.empty:

        st.success(
            "No pending refunds found for the selected date range."
        )

    else:

        display_pending = pending_df.copy()

        display_pending["Refund Date"] = (
            display_pending[
                "refund_date"
            ]
            .dt.strftime(
                "%Y-%m-%d %H:%M"
            )
        )

        display_pending = display_pending[
            [
                "refund_id",
                "sale_id",
                "invoice_no",
                "refund_date",
                "status",
                "product_name",
                "quantity",
                "report_total",
                "reason",
                "cashier_name",
                "processed_by",
            ]
        ].copy()

        display_pending = display_pending.rename(
            columns={
                "refund_id": "Refund ID",
                "sale_id": "Sale ID",
                "invoice_no": "Invoice",
                "refund_date": "Refund Date",
                "status": "Status",
                "product_name": "Product",
                "quantity": "Qty",
                "report_total": "Pending Amount",
                "reason": "Reason",
                "cashier_name": "Cashier",
                "processed_by": "Processed By",
            }
        )

        st.dataframe(
            display_pending,
            use_container_width=True,
            hide_index=True,
        )

        st.warning(
            "Pending Total: "
            + money(
                summary[
                    "pending_total"
                ]
            )
            + " — NOT INCLUDED in Refund Total."
        )


# ==============================================================================
# TAB 4
# EXPORT
# ==============================================================================

with tab_export:

    st.subheader(
        "📤 Refund Report Export"
    )

    st.write(
        "Selected Period: "
        f"{report_from.strftime('%Y-%m-%d')}"
        " → "
        f"{report_to.strftime('%Y-%m-%d')}"
    )

    st.divider()

    # --------------------------------------------------------------------------
    # PDF
    # --------------------------------------------------------------------------

    st.markdown(
        "### 📄 PDF Report"
    )

    pdf_bytes = create_refund_report_pdf(
        actual_df=actual_df,
        rejected_df=rejected_df,
        pending_df=pending_df,
        report_from=report_from,
        report_to=report_to,
    )

    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name=(
            "refund_report_"
            f"{report_from.strftime('%Y%m%d')}_"
            f"{report_to.strftime('%Y%m%d')}.pdf"
        ),
        mime="application/pdf",
        use_container_width=True,
    )

    # --------------------------------------------------------------------------
    # HTML
    # --------------------------------------------------------------------------

    st.markdown(
        "### 🌐 HTML Report"
    )

    html_bytes = create_html_report(
        actual_df=actual_df,
        rejected_df=rejected_df,
        pending_df=pending_df,
        report_from=report_from,
        report_to=report_to,
    ).encode(
        "utf-8"
    )

    st.download_button(
        label="🌐 Download HTML Report",
        data=html_bytes,
        file_name=(
            "refund_report_"
            f"{report_from.strftime('%Y%m%d')}_"
            f"{report_to.strftime('%Y%m%d')}.html"
        ),
        mime="text/html",
        use_container_width=True,
    )

    st.divider()

    # --------------------------------------------------------------------------
    # ACTUAL REFUND CSV
    # --------------------------------------------------------------------------

    st.markdown(
        "### ↩️ Actual Refund CSV"
    )

    actual_export_df = (
        build_export_dataframe(
            actual_df
        )
    )

    actual_csv = (
        actual_export_df
        .to_csv(
            index=False,
            encoding="utf-8-sig",
        )
        .encode(
            "utf-8-sig"
        )
    )

    st.download_button(
        label="⬇️ Download Actual Refund CSV",
        data=actual_csv,
        file_name=(
            "actual_refund_register_"
            f"{report_from.strftime('%Y%m%d')}_"
            f"{report_to.strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )

    # --------------------------------------------------------------------------
    # REJECTED CSV
    # --------------------------------------------------------------------------

    st.markdown(
        "### ❌ Rejected CSV"
    )

    rejected_export_df = (
        build_export_dataframe(
            rejected_df
        )
    )

    rejected_csv = (
        rejected_export_df
        .to_csv(
            index=False,
            encoding="utf-8-sig",
        )
        .encode(
            "utf-8-sig"
        )
    )

    st.download_button(
        label="⬇️ Download Rejected CSV",
        data=rejected_csv,
        file_name=(
            "rejected_refund_register_"
            f"{report_from.strftime('%Y%m%d')}_"
            f"{report_to.strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )

    # --------------------------------------------------------------------------
    # PENDING CSV
    # --------------------------------------------------------------------------

    st.markdown(
        "### ⏳ Pending CSV"
    )

    pending_export_df = (
        build_export_dataframe(
            pending_df
        )
    )

    pending_csv = (
        pending_export_df
        .to_csv(
            index=False,
            encoding="utf-8-sig",
        )
        .encode(
            "utf-8-sig"
        )
    )

    st.download_button(
        label="⬇️ Download Pending CSV",
        data=pending_csv,
        file_name=(
            "pending_refund_register_"
            f"{report_from.strftime('%Y%m%d')}_"
            f"{report_to.strftime('%Y%m%d')}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )




# ==============================================================================
# RUN MAIN
# ==============================================================================

if __name__ == "__main__":
    main()
