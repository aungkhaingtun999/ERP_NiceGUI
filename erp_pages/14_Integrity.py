# ==============================================================================
# erp_pages/14_Integrity.py
#
# ERP ENTERPRISE INTEGRITY CHECK DASHBOARD
#
# READ-ONLY
#
# Checks:
#   1. Double Entry
#   2. Sales ↔ Payments
#   3. Stock ↔ Inventory Ledger
#   4. FIFO Cost ↔ Stock
#   5. Sales Total ↔ Sale Items
#
# IMPORTANT
# ------------------------------------------------------------------------------
# This page NEVER modifies:
#   - sales
#   - sale_items
#   - payment_transactions
#   - products
#   - warehouse_stock
#   - inventory_ledger
#   - inventory_cost_layers
#
# ==============================================================================

from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation

import pandas as pd
import streamlit as st

from supabase_client import get_supabase


# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="ERP Integrity Check",
    page_icon="🔐",
    layout="wide",
)


# ==============================================================================
# CONSTANTS
# ==============================================================================

TOLERANCE = Decimal("0.01")
CHECK_LIMIT = 100


# ==============================================================================
# CSS
# ==============================================================================

st.markdown(
    """
<style>

.main {
    padding: 0 1rem;
}

.check-card {
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 8px;
    border-left: 4px solid #ccc;
    background-color: #f8f9fa;
}

.check-passed {
    border-left-color: #28a745;
    background-color: #f0fff4;
}

.check-failed {
    border-left-color: #dc3545;
    background-color: #fff5f5;
}

.check-error {
    border-left-color: #6c757d;
    background-color: #f8f9fa;
}

.metric-card {
    text-align: center;
    padding: 16px;
    border-radius: 8px;
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
}

.metric-value {
    font-size: 28px;
    font-weight: 700;
}

.metric-label {
    font-size: 13px;
    color: #6c757d;
}

.suggestion {
    font-size: 13px;
    color: #856404;
    background-color: #fff3cd;
    padding: 6px 12px;
    border-radius: 4px;
    margin-top: 6px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# HELPERS
# ==============================================================================

def money(value) -> Decimal:
    """Safely convert DB numeric values to Decimal."""

    try:
        if value is None or value == "":
            return Decimal("0")

        return Decimal(str(value))

    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def qty(value) -> Decimal:
    """Safely convert quantity."""

    return money(value)


def money_fmt(value) -> str:
    return f"{float(money(value)):,.2f}"


def qty_fmt(value) -> str:
    value = qty(value)

    if value == value.to_integral_value():
        return f"{int(value):,}"

    return f"{float(value):,.2f}"


# ==============================================================================
# DATABASE
# ==============================================================================

@st.cache_data(
    ttl=60,
    show_spinner=False,
)
def execute_query(
    table_name: str,
    select: str = "*",
    filters: dict | None = None,
    limit: int | None = None,
) -> list:

    try:

        supabase = get_supabase()

        if not supabase:
            return []

        query = (
            supabase
            .table(table_name)
            .select(select)
        )

        if filters:

            for key, value in filters.items():

                if isinstance(value, list):

                    query = query.in_(
                        key,
                        value,
                    )

                else:

                    query = query.eq(
                        key,
                        value,
                    )

        if limit:
            query = query.limit(limit)

        result = query.execute()

        return result.data or []

    except Exception:
        return []


def get_all_rows(
    table_name: str,
    select: str = "*",
) -> list:

    """
    Read-only helper.

    Uses pagination so integrity checks are not silently
    limited to the first 1000 rows.
    """

    try:

        supabase = get_supabase()

        if not supabase:
            return []

        all_rows = []
        page_size = 1000
        offset = 0

        while True:

            response = (
                supabase
                .table(table_name)
                .select(select)
                .range(
                    offset,
                    offset + page_size - 1,
                )
                .execute()
            )

            rows = response.data or []

            all_rows.extend(rows)

            if len(rows) < page_size:
                break

            offset += page_size

        return all_rows

    except Exception:
        return []


def get_table_count(
    table_name: str,
) -> int:

    try:

        rows = get_all_rows(
            table_name,
            "id",
        )

        return len(rows)

    except Exception:
        return 0


# ==============================================================================
# CHECK 1
# DOUBLE ENTRY
# ==============================================================================

def check_double_entry():

    try:

        entries = get_all_rows(
            "journal_entries",
            "debit,credit",
        )

        if not entries:

            return {
                "name": "Double Entry",
                "icon": "📊",
                "status": "ERROR",
                "status_icon": "⚠️",
                "passed": False,
                "detail": "No journal_entries records found.",
                "suggestion": (
                    "Check whether journal_entries is the correct "
                    "accounting source table."
                ),
            }

        debit_total = sum(
            (
                money(row.get("debit"))
                for row in entries
            ),
            Decimal("0"),
        )

        credit_total = sum(
            (
                money(row.get("credit"))
                for row in entries
            ),
            Decimal("0"),
        )

        diff = abs(
            debit_total - credit_total
        )

        passed = diff <= TOLERANCE

        return {
            "name": "Double Entry",
            "icon": "📊",
            "status": (
                "BALANCED"
                if passed
                else "IMBALANCED"
            ),
            "status_icon": (
                "✅"
                if passed
                else "❌"
            ),
            "passed": passed,
            "debit": debit_total,
            "credit": credit_total,
            "diff": diff,
            "detail": (
                f"Debit: {money_fmt(debit_total)} | "
                f"Credit: {money_fmt(credit_total)}"
            ),
            "suggestion": (
                "Check journal_entries for unbalanced "
                "transactions."
                if not passed
                else None
            ),
        }

    except Exception as e:

        return {
            "name": "Double Entry",
            "icon": "📊",
            "status": "ERROR",
            "status_icon": "⚠️",
            "passed": False,
            "detail": str(e)[:200],
            "suggestion": (
                "Check journal_entries schema and database connection."
            ),
        }


# ==============================================================================
# CHECK 2
# SALES ↔ PAYMENTS
# ==============================================================================

def check_sales_vs_payments():

    try:

        sales = get_all_rows(
            "sales",
            """
            id,
            total,
            total_amount,
            paid_amount,
            sale_status
            """,
        )

        completed_sales = [
            row
            for row in sales
            if str(
                row.get("sale_status") or "COMPLETED"
            ).upper()
            == "COMPLETED"
        ]

        # ----------------------------------------------------------------------
        # Canonical sales amount
        # ----------------------------------------------------------------------

        sales_total = sum(
            (
                money(
                    row.get("total")
                    if row.get("total") is not None
                    else row.get("total_amount")
                )
                for row in completed_sales
            ),
            Decimal("0"),
        )

        # ----------------------------------------------------------------------
        # payment_transactions
        # ----------------------------------------------------------------------

        payments = get_all_rows(
            "payment_transactions",
            "amount,status,sale_id",
        )

        completed_payments = [
            row
            for row in payments
            if str(
                row.get("status") or ""
            ).upper()
            == "COMPLETED"
        ]

        payments_total = sum(
            (
                money(row.get("amount"))
                for row in completed_payments
            ),
            Decimal("0"),
        )

        diff = abs(
            sales_total - payments_total
        )

        passed = diff <= TOLERANCE

        return {
            "name": "Sales ↔ Payments",
            "icon": "💰",
            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),
            "status_icon": (
                "✅"
                if passed
                else "❌"
            ),
            "passed": passed,
            "sales": sales_total,
            "payments": payments_total,
            "diff": diff,
            "detail": (
                f"Sales: {money_fmt(sales_total)} | "
                f"Payments: {money_fmt(payments_total)} | "
                f"Difference: {money_fmt(diff)}"
            ),
            "suggestion": (
                "Payment transactions do not reconcile with "
                "completed sales. Check duplicate payments, "
                "unlinked payments, refunds, or unpaid sales."
                if not passed
                else None
            ),
        }

    except Exception as e:

        return {
            "name": "Sales ↔ Payments",
            "icon": "💰",
            "status": "ERROR",
            "status_icon": "⚠️",
            "passed": False,
            "detail": str(e)[:200],
            "suggestion": (
                "Check payment_transactions schema."
            ),
        }


# ==============================================================================
# CHECK 3
# STOCK ↔ INVENTORY LEDGER
# ==============================================================================

def check_stock_vs_ledger():

    try:

        stock_rows = get_all_rows(
            "warehouse_stock",
            "qty",
        )

        ledger_rows = get_all_rows(
            "inventory_ledger",
            "qty_in,qty_out",
        )

        stock_total = sum(
            (
                qty(row.get("qty"))
                for row in stock_rows
            ),
            Decimal("0"),
        )

        ledger_total = sum(
            (
                qty(row.get("qty_in"))
                - qty(row.get("qty_out"))
                for row in ledger_rows
            ),
            Decimal("0"),
        )

        diff = abs(
            stock_total - ledger_total
        )

        passed = diff <= TOLERANCE

        return {
            "name": "Stock ↔ Inventory Ledger",
            "icon": "📦",
            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),
            "status_icon": (
                "✅"
                if passed
                else "❌"
            ),
            "passed": passed,
            "stock": stock_total,
            "ledger": ledger_total,
            "diff": diff,
            "detail": (
                f"Stock: {qty_fmt(stock_total)} | "
                f"Ledger: {qty_fmt(ledger_total)} | "
                f"Difference: {qty_fmt(diff)}"
            ),
            "suggestion": (
                "Check inventory_ledger for missing or "
                "duplicate stock movements."
                if not passed
                else None
            ),
        }

    except Exception as e:

        return {
            "name": "Stock ↔ Inventory Ledger",
            "icon": "📦",
            "status": "ERROR",
            "status_icon": "⚠️",
            "passed": False,
            "detail": str(e)[:200],
            "suggestion": (
                "Check warehouse_stock and inventory_ledger schema."
            ),
        }


# ==============================================================================
# CHECK 4
# FIFO COST ↔ STOCK
# ==============================================================================

def check_fifo_vs_stock():

    """
    IMPORTANT:
    The old implementation was logically invalid:

        stock_value = fifo_cost

    That guarantees PASS.

    This version compares:
        FIFO remaining quantity
        against warehouse_stock quantity

    and separately calculates FIFO inventory value.

    Actual warehouse_stock monetary value is NOT assumed unless
    the table contains a value column.
    """

    try:

        fifo_rows = get_all_rows(
            "inventory_cost_layers",
            "qty_remaining,unit_cost",
        )

        stock_rows = get_all_rows(
            "warehouse_stock",
            "qty",
        )

        fifo_qty = sum(
            (
                qty(row.get("qty_remaining"))
                for row in fifo_rows
            ),
            Decimal("0"),
        )

        stock_qty = sum(
            (
                qty(row.get("qty"))
                for row in stock_rows
            ),
            Decimal("0"),
        )

        fifo_value = sum(
            (
                qty(row.get("qty_remaining"))
                * money(row.get("unit_cost"))
                for row in fifo_rows
            ),
            Decimal("0"),
        )

        qty_diff = abs(
            fifo_qty - stock_qty
        )

        passed = qty_diff <= TOLERANCE

        return {
            "name": "FIFO Cost ↔ Stock",
            "icon": "📈",
            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),
            "status_icon": (
                "✅"
                if passed
                else "❌"
            ),
            "passed": passed,
            "fifo_qty": fifo_qty,
            "stock_qty": stock_qty,
            "fifo_cost": fifo_value,
            "stock_value": fifo_value,
            "diff": qty_diff,
            "detail": (
                f"FIFO Qty: {qty_fmt(fifo_qty)} | "
                f"Stock Qty: {qty_fmt(stock_qty)} | "
                f"FIFO Value: {money_fmt(fifo_value)}"
            ),
            "suggestion": (
                "FIFO remaining quantity does not match "
                "warehouse_stock quantity. Check cost layers."
                if not passed
                else None
            ),
        }

    except Exception as e:

        return {
            "name": "FIFO Cost ↔ Stock",
            "icon": "📈",
            "status": "ERROR",
            "status_icon": "⚠️",
            "passed": False,
            "detail": str(e)[:200],
            "suggestion": (
                "Check inventory_cost_layers and warehouse_stock."
            ),
        }


# ==============================================================================
# CHECK 5
# SALES TOTAL ↔ SALE ITEMS
# ==============================================================================

def check_sales_items():

    """
    Sale total formula:

        item totals
        + tax
        = sale total

    But sale_items.total is treated as the canonical line
    amount after line discount.

    Therefore:

        sum(sale_items.total)
        + sales.tax
        ≈ sales.total

    This correctly handles Sale #312:

        item subtotal after discount = 20,050
        tax                         = 1,620
        sale total                  = 21,670
    """

    try:

        sales = get_all_rows(
            "sales",
            """
            id,
            total,
            total_amount,
            tax,
            sale_status
            """,
        )

        completed_sales = [
            row
            for row in sales
            if str(
                row.get("sale_status") or "COMPLETED"
            ).upper()
            == "COMPLETED"
        ]

        # Keep original behavior: check latest 100.
        completed_sales = completed_sales[
            -CHECK_LIMIT:
        ]

        total_sales = len(
            completed_sales
        )

        matched = 0
        discrepancy = Decimal("0")
        mismatched_sales = []

        for sale in completed_sales:

            sale_id = sale.get("id")

            sale_total = money(
                sale.get("total")
                if sale.get("total") is not None
                else sale.get("total_amount")
            )

            sale_tax = money(
                sale.get("tax")
            )

            items = execute_query(
                "sale_items",
                """
                id,
                sale_id,
                quantity,
                unit_price,
                discount,
                total
                """,
                filters={
                    "sale_id": sale_id,
                },
            )

            # ------------------------------------------------------------------
            # Prefer sale_items.total
            # ------------------------------------------------------------------

            item_total = sum(
                (
                    money(row.get("total"))
                    for row in items
                ),
                Decimal("0"),
            )

            calculated_total = (
                item_total
                + sale_tax
            )

            difference = abs(
                calculated_total
                - sale_total
            )

            if difference <= TOLERANCE:

                matched += 1

            else:

                discrepancy += difference

                if len(mismatched_sales) < 10:

                    mismatched_sales.append(
                        {
                            "sale_id": sale_id,
                            "sale_total": sale_total,
                            "item_total": item_total,
                            "tax": sale_tax,
                            "calculated_total": calculated_total,
                            "difference": difference,
                        }
                    )

        passed = discrepancy <= TOLERANCE

        mismatch_text = ", ".join(
            f"Sale #{x['sale_id']}"
            for x in mismatched_sales
        )

        return {
            "name": "Sales Total ↔ Items",
            "icon": "🧾",
            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),
            "status_icon": (
                "✅"
                if passed
                else "❌"
            ),
            "passed": passed,
            "total_sales": total_sales,
            "matched": matched,
            "discrepancy": discrepancy,
            "mismatched_sales": mismatched_sales,
            "detail": (
                f"Sales checked: {total_sales} | "
                f"Matched: {matched} | "
                f"Discrepancy: {money_fmt(discrepancy)}"
                + (
                    f" | Mismatched: {mismatch_text}"
                    if mismatched_sales
                    else ""
                )
            ),
            "suggestion": (
                "Check sale_items totals and sales.tax for "
                "mismatched sales."
                if not passed
                else None
            ),
        }

    except Exception as e:

        return {
            "name": "Sales Total ↔ Items",
            "icon": "🧾",
            "status": "ERROR",
            "status_icon": "⚠️",
            "passed": False,
            "detail": str(e)[:200],
            "suggestion": (
                "Check sales and sale_items schema."
            ),
        }


# ==============================================================================
# RENDER CHECK CARD
# ==============================================================================

def render_check_card(result):

    status_class = "check-passed" if result["passed"] else (
        "check-failed" if result["status"] != "ERROR" else "check-error"
    )

    with st.container():

        st.markdown(
            f"""
            <div class="check-card {status_class}">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 24px;">{result['icon']}</span>
                    <span style="font-weight: 600; font-size: 16px;">
                        {result['name']}
                    </span>
                    <span style="margin-left: auto; font-weight: 500;">
                        {result['status_icon']} {result['status']}
                    </span>
                </div>
                <div style="margin-top: 6px; font-size: 14px;">
                    {result['detail']}
                </div>
        """,
            unsafe_allow_html=True,
        )

        if result.get("suggestion"):

            st.markdown(
                f"""
                <div class="suggestion">
                    💡 {result['suggestion']}
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# MAIN
# ==============================================================================

def run():

    st.title("🔐 ERP Integrity Check Dashboard")

    st.caption(
        "Read‑only diagnostics verifying internal ERP consistency."
    )

    st.divider()

    # ==========================================================================
    # RUN CHECKS
    # ==========================================================================

    with st.spinner("Running integrity checks..."):

        results = [
            check_double_entry(),
            check_sales_vs_payments(),
            check_stock_vs_ledger(),
            check_fifo_vs_stock(),
            check_sales_items(),
        ]

    # ==========================================================================
    # OVERVIEW METRICS
    # ==========================================================================

    total_checks = len(results)
    passed_checks = sum(
        1
        for r in results
        if r["passed"]
    )
    failed_checks = total_checks - passed_checks

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total_checks}</div>
                <div class="metric-label">Total Checks</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #28a745;">
                    {passed_checks}
                </div>
                <div class="metric-label">✅ Passed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #dc3545;">
                    {failed_checks}
                </div>
                <div class="metric-label">❌ Failed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">
                    {int((passed_checks / total_checks) * 100)}%
                </div>
                <div class="metric-label">Pass Rate</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ==========================================================================
    # DETAILED RESULTS
    # ==========================================================================

    for result in results:

        render_check_card(result)

        st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================================================
    # TIMESTAMP
    # ==========================================================================

    st.caption(
        f"Checked at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
