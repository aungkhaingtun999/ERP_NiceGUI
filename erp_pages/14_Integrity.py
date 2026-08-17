# ============================================================
# erp_pages/14_Integrity.py
# ERP ENTERPRISE INTEGRITY CHECK DASHBOARD
#
# Checks:
#   1. Double Entry
#   2. Sales <-> Payments
#   3. Stock <-> Inventory Ledger
#   4. FIFO Cost <-> Stock
#   5. Sales <-> Sale Items
#
# READ-ONLY
# This page NEVER modifies ERP data.
# ============================================================

import datetime
import streamlit as st
import pandas as pd

from supabase_client import get_supabase


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ERP Integrity Check",
    page_icon="🔐",
    layout="wide",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding: 0 1rem;
    }

    .check-card {
        padding: 14px 16px;
        margin: 8px 0;
        border-radius: 10px;
        border-left: 5px solid #ccc;
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

    .badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 14px;
        font-size: 12px;
        font-weight: 700;
        white-space: nowrap;
    }

    .badge-passed {
        background-color: #28a745;
        color: white;
    }

    .badge-failed {
        background-color: #dc3545;
        color: white;
    }

    .badge-error {
        background-color: #6c757d;
        color: white;
    }

    .suggestion {
        margin-top: 10px;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 13px;
        background-color: #fff3cd;
        color: #856404;
    }

    .metric-card {
        text-align: center;
        padding: 16px;
        border-radius: 10px;
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

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def money(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def qty(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


# ============================================================
# DATABASE
# ============================================================

@st.cache_data(ttl=60, show_spinner=False)
def execute_query(
    table_name: str,
    select: str = "*",
    filters: dict | None = None,
    limit: int | None = None,
):
    try:
        supabase = get_supabase()

        if not supabase:
            return []

        query = supabase.table(table_name).select(select)

        if filters:
            for key, value in filters.items():

                if isinstance(value, list):
                    query = query.in_(key, value)

                else:
                    query = query.eq(key, value)

        if limit:
            query = query.limit(limit)

        response = query.execute()

        return response.data or []

    except Exception:
        return []


def get_table_count(table_name: str):
    try:
        rows = execute_query(
            table_name,
            select="id",
            limit=1000,
        )
        return len(rows)

    except Exception:
        return 0


# ============================================================
# CHECK 1
# DOUBLE ENTRY
# ============================================================

def check_double_entry():

    try:

        entries = execute_query(
            "journal_entries",
            select="debit,credit",
        )

        debit_total = sum(
            money(x.get("debit"))
            for x in entries
        )

        credit_total = sum(
            money(x.get("credit"))
            for x in entries
        )

        difference = abs(
            debit_total - credit_total
        )

        passed = difference < 0.01

        return {
            "name": "Double Entry",
            "icon": "📊",
            "status": (
                "BALANCED"
                if passed
                else "IMBALANCED"
            ),
            "passed": passed,
            "detail": (
                f"Debit: {debit_total:,.2f} | "
                f"Credit: {credit_total:,.2f}"
            ),
            "suggestion": (
                None
                if passed
                else
                "Check journal_entries for "
                "unbalanced transactions."
            ),
        }

    except Exception as e:

        return {
            "name": "Double Entry",
            "icon": "📊",
            "status": "ERROR",
            "passed": False,
            "detail": str(e)[:100],
            "suggestion": (
                "Check journal_entries table."
            ),
        }


# ============================================================
# CHECK 2
# SALES <-> PAYMENTS
#
# IMPORTANT:
# Reconcile by sale_id, NOT global totals.
# ============================================================

def check_sales_vs_payments():

    try:

        sales = execute_query(
            "sales",
            select=(
                "id,total,total_amount,"
                "sale_status"
            ),
            filters={
                "sale_status": "COMPLETED"
            },
        )

        if not sales:

            return {
                "name": "Sales ↔ Payments",
                "icon": "💰",
                "status": "MATCHED",
                "passed": True,
                "detail": "No completed sales found.",
                "suggestion": None,
            }

        sale_ids = [
            int(x["id"])
            for x in sales
            if x.get("id") is not None
        ]

        payments = execute_query(
            "payment_transactions",
            select=(
                "id,sale_id,amount,status"
            ),
        )

        payment_map = {}

        for payment in payments:

            if payment.get("status") != "COMPLETED":
                continue

            sale_id = payment.get("sale_id")

            if sale_id is None:
                continue

            try:
                sale_id = int(sale_id)
            except Exception:
                continue

            payment_map[sale_id] = (
                payment_map.get(sale_id, 0.0)
                + money(payment.get("amount"))
            )

        mismatches = []

        sales_total = 0.0
        payments_total = 0.0

        for sale in sales:

            sale_id = int(sale["id"])

            sale_amount = money(
                sale.get("total")
            )

            payment_amount = money(
                payment_map.get(sale_id)
            )

            sales_total += sale_amount
            payments_total += payment_amount

            if abs(
                sale_amount - payment_amount
            ) >= 0.01:

                mismatches.append(
                    {
                        "sale_id": sale_id,
                        "sale": sale_amount,
                        "payment": payment_amount,
                        "difference": (
                            sale_amount
                            - payment_amount
                        ),
                    }
                )

        passed = len(mismatches) == 0

        suggestion = None

        if mismatches:

            ids = ", ".join(
                f"#{x['sale_id']}"
                for x in mismatches[:5]
            )

            suggestion = (
                "Payment mismatch sale(s): "
                f"{ids}"
            )

        return {
            "name": "Sales ↔ Payments",
            "icon": "💰",
            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),
            "passed": passed,
            "detail": (
                f"Sales: {sales_total:,.2f} | "
                f"Payments: {payments_total:,.2f}"
            ),
            "suggestion": suggestion,
        }

    except Exception as e:

        return {
            "name": "Sales ↔ Payments",
            "icon": "💰",
            "status": "ERROR",
            "passed": False,
            "detail": str(e)[:100],
            "suggestion": (
                "Verify payment_transactions "
                "schema and sale_id."
            ),
        }


# ============================================================
# CHECK 3
# STOCK <-> INVENTORY LEDGER
# ============================================================

def check_stock_vs_ledger():

    try:

        stock_data = execute_query(
            "warehouse_stock",
            select="qty",
        )

        stock_total = sum(
            qty(x.get("qty"))
            for x in stock_data
        )

        ledger_data = execute_query(
            "inventory_ledger",
            select="qty_in,qty_out",
        )

        ledger_total = sum(
            qty(x.get("qty_in"))
            - qty(x.get("qty_out"))
            for x in ledger_data
        )

        difference = abs(
            stock_total - ledger_total
        )

        passed = difference < 0.01

        return {
            "name": "Stock ↔ Inventory Ledger",
            "icon": "📦",
            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),
            "passed": passed,
            "detail": (
                f"Stock: {stock_total:,.0f} | "
                f"Ledger: {ledger_total:,.0f}"
            ),
            "suggestion": (
                None
                if passed
                else
                "Check inventory ledger for "
                "missing or duplicated movements."
            ),
        }

    except Exception as e:

        return {
            "name": "Stock ↔ Inventory Ledger",
            "icon": "📦",
            "status": "ERROR",
            "passed": False,
            "detail": str(e)[:100],
            "suggestion": (
                "Check warehouse_stock and "
                "inventory_ledger."
            ),
        }


# ============================================================
# CHECK 4
# FIFO QTY + VALUE <-> STOCK
#
# IMPORTANT:
# Do NOT compare fifo_cost against itself.
# ============================================================

def check_fifo_vs_stock():

    try:

        fifo_data = execute_query(
            "inventory_cost_layers",
            select=(
                "qty_remaining,unit_cost"
            ),
        )

        fifo_qty = sum(
            qty(x.get("qty_remaining"))
            for x in fifo_data
        )

        fifo_value = sum(
            qty(x.get("qty_remaining"))
            * money(x.get("unit_cost"))
            for x in fifo_data
        )

        stock_data = execute_query(
            "warehouse_stock",
            select="qty",
        )

        stock_qty = sum(
            qty(x.get("qty"))
            for x in stock_data
        )

        qty_difference = abs(
            fifo_qty - stock_qty
        )

        qty_matched = (
            qty_difference < 0.01
        )

        passed = qty_matched

        return {
            "name": "FIFO Cost ↔ Stock",
            "icon": "📈",
            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),
            "passed": passed,
            "detail": (
                f"FIFO Qty: {fifo_qty:,.0f} | "
                f"Stock Qty: {stock_qty:,.0f} | "
                f"FIFO Value: {fifo_value:,.2f}"
            ),
            "suggestion": (
                None
                if passed
                else
                f"FIFO quantity differs from "
                f"warehouse stock by "
                f"{qty_difference:,.2f}."
            ),
        }

    except Exception as e:

        return {
            "name": "FIFO Cost ↔ Stock",
            "icon": "📈",
            "status": "ERROR",
            "passed": False,
            "detail": str(e)[:100],
            "suggestion": (
                "Check inventory_cost_layers "
                "and warehouse_stock."
            ),
        }


# ============================================================
# CHECK 5
# SALES <-> SALE ITEMS
# ============================================================

def check_sales_items():
    """
    Check sale calculation:

        SUM(sale_items.total OR qty * unit_price - item_discount)
        - sales.discount
        + sales.tax
        = sales.total

    IMPORTANT:
    Do NOT compare raw item subtotal directly to sales.total
    because sales.total may include header discount and tax.
    """
    try:
        sales_data = execute_query(
            'sales',
            select='id,subtotal,discount,tax,total',
            filters={'sale_status': 'COMPLETED'}
        )

        total_sales = len(sales_data)
        matched = 0
        mismatched = []

        total_discrepancy = 0.0

        for sale in sales_data:
            sale_id = sale.get("id")

            sale_subtotal = float(sale.get("subtotal") or 0)
            sale_discount = float(sale.get("discount") or 0)
            sale_tax = float(sale.get("tax") or 0)
            sale_total = float(sale.get("total") or 0)

            items_data = execute_query(
                'sale_items',
                select='quantity,unit_price,discount,total',
                filters={'sale_id': sale_id}
            )

            item_subtotal = 0.0

            for item in items_data:
                qty = float(item.get("quantity") or 0)
                unit_price = float(item.get("unit_price") or 0)
                item_discount = float(item.get("discount") or 0)

                item_subtotal += (
                    qty * unit_price
                ) - item_discount

            # ------------------------------------------------
            # CHECK 1
            # Items subtotal == sales.subtotal
            # ------------------------------------------------
            subtotal_diff = abs(item_subtotal - sale_subtotal)

            # ------------------------------------------------
            # CHECK 2
            # subtotal - discount + tax == total
            # ------------------------------------------------
            calculated_total = (
                sale_subtotal
                - sale_discount
                + sale_tax
            )

            total_diff = abs(calculated_total - sale_total)

            # ------------------------------------------------
            # Final result
            # ------------------------------------------------
            if subtotal_diff < 0.01 and total_diff < 0.01:
                matched += 1
            else:
                total_discrepancy += max(
                    subtotal_diff,
                    total_diff
                )

                if len(mismatched) < 10:
                    mismatched.append({
                        "sale_id": sale_id,
                        "item_subtotal": item_subtotal,
                        "sale_subtotal": sale_subtotal,
                        "discount": sale_discount,
                        "tax": sale_tax,
                        "calculated_total": calculated_total,
                        "sale_total": sale_total,
                        "difference": total_diff
                    })

        is_matched = len(mismatched) == 0

        mismatch_ids = [
            f"#{x['sale_id']}"
            for x in mismatched
        ]

        return {
            "name": "Sales Total ↔ Items",
            "icon": "🧾",
            "status": "MATCHED" if is_matched else "MISMATCHED",
            "status_icon": "✅" if is_matched else "❌",
            "passed": is_matched,

            "total_sales": total_sales,
            "matched": matched,
            "mismatched": total_sales - matched,

            "discrepancy": total_discrepancy,

            "mismatched_sales": mismatch_ids,

            "details": mismatched,

            "detail": (
                f"Checked {total_sales} sales | "
                f"Matched: {matched} | "
                f"Mismatched: {total_sales - matched}"
            ),

            "suggestion": (
                f"Check sale(s): {', '.join(mismatch_ids)}"
                if mismatch_ids
                else None
            )
        }

    except Exception as e:

        return {
            "name": "Sales Total ↔ Items",
            "icon": "🧾",
            "status": "ERROR",
            "status_icon": "⚠️",
            "passed": False,

            "total_sales": 0,
            "matched": 0,
            "mismatched": 0,

            "discrepancy": 0,
            "mismatched_sales": [],
            "details": [],

            "detail": str(e)[:100],

            "suggestion": (
                "Check sales / sale_items "
                "columns and database connection"
            )
        }


# ============================================================
# RENDER CHECK CARD
# ============================================================

def render_check_card(result):

    if result.get("status") == "ERROR":
        status_class = "check-error"
        badge_class = "badge-error"
    elif result.get("passed", False):
        status_class = "check-passed"
        badge_class = "badge-passed"
    else:
        status_class = "check-failed"
        badge_class = "badge-failed"

    status_display = result.get("status", "UNKNOWN")

    with st.container():

        st.markdown(
            f"""
            <div class="check-card {status_class}">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 24px;">{result.get('icon', '📋')}</span>
                    <span style="font-weight: 600; font-size: 16px;">
                        {result.get('name', 'Check')}
                    </span>
                    <span style="margin-left: auto;">
                        <span class="badge {badge_class}">
                            {status_display}
                        </span>
                    </span>
                </div>
                <div style="margin-top: 6px; font-size: 14px;">
                    {result.get('detail', '')}
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

        # Show mismatches if any (for check 5)
        if result.get("details") and len(result["details"]) > 0:

            with st.expander(
                f"📋 View {len(result['details'])} mismatch details"
            ):

                mismatch_df = pd.DataFrame(
                    result["details"]
                )

                st.dataframe(
                    mismatch_df,
                    use_container_width=True,
                    hide_index=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# RUN ALL
# ============================================================

def run_all_checks():

    return [
        check_double_entry(),
        check_sales_vs_payments(),
        check_stock_vs_ledger(),
        check_fifo_vs_stock(),
        check_sales_items(),
    ]


# ============================================================
# EXPORT
# ============================================================

def export_to_csv(results):

    rows = []

    for result in results:

        rows.append(
            {
                "Check": result.get("name"),
                "Status": result.get("status"),
                "Detail": result.get("detail"),
                "Passed": result.get(
                    "passed",
                    False,
                ),
                "Suggestion": result.get(
                    "suggestion"
                ) or "",
            }
        )

    return pd.DataFrame(
        rows
    ).to_csv(
        index=False
    )


# ============================================================
# MAIN
# ============================================================

def run():

    st.title(
        "🔐 ERP Integrity Check Dashboard"
    )

    st.caption(
        "Double Entry & FIFO Cost Monitoring"
    )

    # ========================================================
    # SIDEBAR
    # ========================================================

    with st.sidebar:

        st.header("⚙️ Settings")

        supabase = get_supabase()

        if supabase:

            st.success(
                "✅ Database Connected"
            )

        else:

            st.error(
                "❌ Database Disconnected"
            )

            return

        st.divider()

        st.subheader(
            "📊 Database Stats"
        )

        st.metric(
            "Sales",
            get_table_count("sales"),
        )

        st.metric(
            "Products",
            get_table_count("products"),
        )

        st.divider()

        st.subheader("📤 Export")

        if st.button(
            "📥 Export Report",
            use_container_width=True,
        ):

            if (
                "integrity_results"
                in st.session_state
            ):

                csv_data = export_to_csv(
                    st.session_state[
                        "integrity_results"
                    ]
                )

                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=(
                        "integrity_report.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                )

            else:

                st.warning(
                    "Run checks first."
                )

    # ========================================================
    # RUN BUTTON
    # ========================================================

    col1, col2 = st.columns(
        [1, 3]
    )

    with col1:

        if st.button(
            "🔄 Run All Checks",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner("Running integrity checks..."):

                results = run_all_checks()

                st.session_state[
                    "integrity_results"
                ] = results

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    if "integrity_results" in st.session_state:

        results = st.session_state[
            "integrity_results"
        ]

        # Overview Metrics
        total_checks = len(results)
        passed_checks = sum(
            1
            for r in results
            if r.get("passed", False)
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
            pass_rate = int((passed_checks / total_checks) * 100) if total_checks > 0 else 0
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-value">{pass_rate}%</div>
                    <div class="metric-label">Pass Rate</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        # Detailed Results
        for result in results:

            render_check_card(result)

            st.markdown("<br>", unsafe_allow_html=True)

        # Timestamp
        st.caption(
            f"Checked at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    else:

        st.info(
            "👆 Click **Run All Checks** to start integrity verification."
        )
