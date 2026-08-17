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

    try:

        sales = execute_query(
            "sales",
            select=(
                "id,total,subtotal,"
                "discount,tax,sale_status"
            ),
            filters={
                "sale_status": "COMPLETED"
            },
        )

        mismatches = []

        checked = 0
        matched = 0

        for sale in sales:

            sale_id = sale.get("id")

            if sale_id is None:
                continue

            checked += 1

            items = execute_query(
                "sale_items",
                select=(
                    "quantity,"
                    "unit_price,"
                    "discount,"
                    "total"
                ),
                filters={
                    "sale_id": sale_id
                },
            )

            item_gross = sum(
                qty(x.get("quantity"))
                * money(x.get("unit_price"))
                for x in items
            )

            item_discount = sum(
                money(x.get("discount"))
                for x in items
            )

            item_net = (
                item_gross
                - item_discount
            )

            sale_subtotal = money(
                sale.get("subtotal")
            )

            sale_discount = money(
                sale.get("discount")
            )

            sale_tax = money(
                sale.get("tax")
            )

            sale_total = money(
                sale.get("total")
            )

            calculated_total = (
                sale_subtotal
                - sale_discount
                + sale_tax
            )

            subtotal_diff = abs(
                item_net
                - sale_subtotal
            )

            final_diff = abs(
                calculated_total
                - sale_total
            )

            discount_diff = abs(
                item_discount
                - sale_discount
            )

            sale_ok = (
                subtotal_diff < 0.01
                and final_diff < 0.01
            )

            if sale_ok:

                matched += 1

            else:

                mismatches.append(
                    {
                        "sale_id": sale_id,
                        "item_net": item_net,
                        "sale_subtotal": sale_subtotal,
                        "sale_discount": sale_discount,
                        "sale_tax": sale_tax,
                        "sale_total": sale_total,
                        "calculated_total": calculated_total,
                        "subtotal_diff": subtotal_diff,
                        "final_diff": final_diff,
                        "discount_diff": discount_diff,
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
                f"Check sale(s): {ids}"
            )

        return {
            "name": "Sales Total ↔ Items",
            "icon": "🧾",
            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),
            "passed": passed,
            "detail": (
                f"Checked {checked} sales | "
                f"Matched: {matched}"
            ),
            "suggestion": suggestion,
            "mismatches": mismatches,
        }

    except Exception as e:

        return {
            "name": "Sales Total ↔ Items",
            "icon": "🧾",
            "status": "ERROR",
            "passed": False,
            "detail": str(e)[:100],
            "suggestion": (
                "Check sales and sale_items schema."
            ),
        }


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

            execute_query.clear()

            with st.spinner(
                "Running integrity checks..."
            ):

                results = run_all_checks()

                st.session_state[
                    "integrity_results"
                ] = results

                st.session_state[
                    "last_integrity_run"
                ] = (
                    datetime.datetime.now()
                    .strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

    with col2:

        if (
            "last_integrity_run"
            in st.session_state
        ):

            st.caption(
                "🕐 Last Check: "
                + st.session_state[
                    "last_integrity_run"
                ]
            )

    st.divider()

    # ========================================================
    # RESULTS
    # ========================================================

    if (
        "integrity_results"
        not in st.session_state
    ):

        st.info(
            "🔍 Click 'Run All Checks' "
            "to start the integrity audit."
        )

        return

    results = st.session_state[
        "integrity_results"
    ]

    total = len(results)

    errors = sum(
        1
        for r in results
        if r.get("status") == "ERROR"
    )

    passed = sum(
        1
        for r in results
        if r.get("passed", False)
    )

    failed = total - passed - errors

    # ========================================================
    # SUMMARY
    # ========================================================

    st.markdown(
        "### 📊 Summary"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:32px;">
                    ✅
                </div>
                <div class="metric-value">
                    {passed}/{total}
                </div>
                <div class="metric-label">
                    Passed
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:32px;">
                    ❌
                </div>
                <div class="metric-value">
                    {failed}
                </div>
                <div class="metric-label">
                    Failed
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:32px;">
                    ⚠️
                </div>
                <div class="metric-value">
                    {errors}
                </div>
                <div class="metric-label">
                    Errors
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:

        if errors > 0:

            icon = "⚠️"
            label = "ERROR"

        elif failed > 0:

            icon = "🚨"
            label = "CRITICAL"

        else:

            icon = "🎉"
            label = "ALL GOOD"

        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size:32px;">
                    {icon}
                </div>
                <div class="metric-value">
                    {label}
                </div>
                <div class="metric-label">
                    Status
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ========================================================
    # DISPLAY DETAILED RESULTS
    # ========================================================

    st.markdown("### 📋 Detailed Results")

    for check in results:

        # --------------------------------------------------------
        # STATUS
        # --------------------------------------------------------

        if check.get("passed", False):

            card_class = "check-passed"
            badge_class = "badge-passed"
            badge_text = "✅ PASSED"

        elif check.get("status") == "ERROR":

            card_class = "check-error"
            badge_class = "badge-error"
            badge_text = "⚠️ ERROR"

        else:

            card_class = "check-failed"
            badge_class = "badge-failed"
            badge_text = "❌ FAILED"

        # --------------------------------------------------------
        # SUGGESTION
        # --------------------------------------------------------

        suggestion_html = ""

        suggestion = check.get("suggestion")

        if suggestion:

            suggestion_html = f"""
            <div class="suggestion">
                💡 {suggestion}
            </div>
            """

        # --------------------------------------------------------
        # CARD
        # --------------------------------------------------------

        card_html = f"""
        <div class="check-card {card_class}">

            <div style="
                display:flex;
                align-items:center;
                gap:14px;
                width:100%;
            ">

                <div style="
                    width:40px;
                    font-size:28px;
                    text-align:center;
                    flex-shrink:0;
                ">
                    {check.get("icon", "🔍")}
                </div>

                <div style="
                    flex:1;
                    font-weight:600;
                    font-size:16px;
                ">
                    {check.get("name", "Unknown Check")}
                </div>

                <div style="
                    width:110px;
                    text-align:center;
                    flex-shrink:0;
                ">
                    <span class="badge {badge_class}">
                        {badge_text}
                    </span>
                </div>

                <div style="
                    flex:2;
                    font-size:14px;
                ">
                    {check.get("detail", "")}
                </div>

            </div>

            {suggestion_html}

        </div>
        """

        # IMPORTANT:
        # unsafe_allow_html=True is required
        st.markdown(
            card_html,
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # Detailed mismatch information
        # ----------------------------------------------------

        if (
            check.get("name")
            == "Sales Total ↔ Items"
            and check.get("mismatches")
        ):

            with st.expander(
                "🔎 View Sales ↔ Items discrepancies"
            ):

                mismatch_df = pd.DataFrame(
                    check["mismatches"]
                )

                st.dataframe(
                    mismatch_df,
                    use_container_width=True,
                    hide_index=True,
                )

    # ========================================================
    # FINAL STATUS
    # ========================================================

    st.divider()

    if errors > 0:

        st.error(
            f"⚠️ {errors} integrity check(s) "
            "could not be completed. "
            "Database/schema requires attention."
        )

    elif failed > 0:

        st.error(
            f"🚨 {failed} integrity check(s) "
            "failed. Review the detailed results above."
        )

    else:

        st.success(
            "🎉 All integrity checks passed successfully. "
            "System integrity is healthy."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run()
