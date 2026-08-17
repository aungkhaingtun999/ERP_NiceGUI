# ============================================================
# erp_pages/14_Integrity.py
# ERP ENTERPRISE INTEGRITY CHECK DASHBOARD
#
# Checks:
#   1. Double Entry
#   2. Sales <-> Payments (with Cash Change support)
#   3. Stock <-> Inventory Ledger
#   4. FIFO Cost <-> Stock (Product-level QTY + Value)
#   5. Sales <-> Sale Items (ONLY subtotal check)
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

    .check-warning {
        border-left-color: #ffc107;
        background-color: #fffcf0;
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

    .badge-warning {
        background-color: #ffc107;
        color: #856404;
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
            "status": "BALANCED" if passed else "IMBALANCED",
            "status_type": "passed" if passed else "failed",
            "passed": passed,
            "detail": (
                f"Debit: {debit_total:,.2f} | "
                f"Credit: {credit_total:,.2f}"
            ),
            "suggestion": (
                None
                if passed
                else "Check journal_entries for unbalanced transactions."
            ),
        }

    except Exception as e:

        return {
            "name": "Double Entry",
            "icon": "📊",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "detail": str(e)[:100],
            "suggestion": "Check journal_entries table.",
        }


# ============================================================
# CHECK 2
# SALES <-> PAYMENTS (with Cash Change support)
# ============================================================

def check_sales_vs_payments():

    try:

        sales = execute_query(
            "sales",
            select=(
                "id,total,total_amount,"
                "sale_status,payment_method"
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
                "status_type": "passed",
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
                "id,sale_id,amount,status,payment_method"
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

        sales_total = 0.0
        payments_total = 0.0
        mismatches = []
        cash_overpayments = []

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

            payment_method = str(
                sale.get("payment_method") or "UNKNOWN"
            ).upper()

            # ------------------------------------------------
            # CASH: Allow overpayment (change)
            # ------------------------------------------------

            if payment_method in ["CASH", "CASH_MMK"]:

                if payment_amount >= sale_amount:

                    change = payment_amount - sale_amount

                    if change > 0.01:

                        cash_overpayments.append({
                            "sale_id": sale_id,
                            "sale_amount": sale_amount,
                            "payment_amount": payment_amount,
                            "change": change,
                            "payment_method": payment_method,
                        })

                    continue

            # ------------------------------------------------
            # NON-CASH: Exact match required
            # ------------------------------------------------

            if abs(sale_amount - payment_amount) >= 0.01:

                mismatches.append({
                    "sale_id": sale_id,
                    "sale": sale_amount,
                    "payment": payment_amount,
                    "difference": sale_amount - payment_amount,
                    "payment_method": payment_method,
                })

        # ------------------------------------------------
        # STATUS
        # ------------------------------------------------

        has_mismatch = len(mismatches) > 0
        has_cash_change = len(cash_overpayments) > 0

        if has_mismatch:

            status = "MISMATCHED"
            status_type = "failed"
            passed = False

            ids = ", ".join(
                f"#{x['sale_id']}"
                for x in mismatches[:5]
            )

            suggestion = f"Payment mismatch sale(s): {ids}"

        elif has_cash_change:

            status = "WARNING"
            status_type = "warning"
            passed = True

            ids = ", ".join(
                f"#{x['sale_id']}"
                for x in cash_overpayments[:5]
            )

            suggestion = f"CASH overpayment/change: {ids}"

        else:

            status = "MATCHED"
            status_type = "passed"
            passed = True
            suggestion = None

        # ------------------------------------------------
        # DETAIL
        # ------------------------------------------------

        detail = (
            f"Sales: {sales_total:,.2f} | "
            f"Applied: {payments_total:,.2f}"
        )

        if has_cash_change:

            change_total = sum(
                x["change"]
                for x in cash_overpayments
            )

            detail += f" | Cash Change: {change_total:,.2f}"

        return {
            "name": "Sales ↔ Payments",
            "icon": "💰",
            "status": status,
            "status_type": status_type,
            "passed": passed,
            "detail": detail,
            "suggestion": suggestion,
            "mismatches": mismatches,
            "cash_overpayments": cash_overpayments,
        }

    except Exception as e:

        return {
            "name": "Sales ↔ Payments",
            "icon": "💰",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "detail": str(e)[:100],
            "suggestion": "Verify payment_transactions schema and sale_id.",
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
            "status": "MATCHED" if passed else "MISMATCHED",
            "status_type": "passed" if passed else "failed",
            "passed": passed,
            "detail": (
                f"Stock: {stock_total:,.0f} | "
                f"Ledger: {ledger_total:,.0f}"
            ),
            "suggestion": (
                None
                if passed
                else "Check inventory ledger for missing or duplicated movements."
            ),
        }

    except Exception as e:

        return {
            "name": "Stock ↔ Inventory Ledger",
            "icon": "📦",
            "status": "ERROR",
            "status_type": "error",
            "passed": False,
            "detail": str(e)[:100],
            "suggestion": "Check warehouse_stock and inventory_ledger.",
        }


# ============================================================
# CHECK 4
# FIFO QTY + VALUE <-> STOCK (Product-level)
# ============================================================

def check_fifo_vs_stock():

    try:

        # ====================================================
        # FIFO COST LAYERS
        # ====================================================

        fifo_data = execute_query(
            "inventory_cost_layers",
            select="product_id,qty_remaining,unit_cost",
        )

        fifo_qty = sum(
            qty(row.get("qty_remaining"))
            for row in fifo_data
        )

        fifo_value = sum(
            qty(row.get("qty_remaining"))
            * money(row.get("unit_cost"))
            for row in fifo_data
        )

        # ====================================================
        # WAREHOUSE STOCK
        # ====================================================

        stock_data = execute_query(
            "warehouse_stock",
            select="product_id,qty",
        )

        stock_qty = sum(
            qty(row.get("qty"))
            for row in stock_data
        )

        # ====================================================
        # PRODUCT-LEVEL DETAILS (for debugging)
        # ====================================================

        # Group FIFO by product
        fifo_by_product = {}

        for row in fifo_data:

            product_id = row.get("product_id")

            if product_id is None:
                continue

            try:
                product_id = int(product_id)
            except Exception:
                continue

            if product_id not in fifo_by_product:

                fifo_by_product[product_id] = {
                    "qty": 0.0,
                    "value": 0.0,
                }

            fifo_by_product[product_id]["qty"] += qty(
                row.get("qty_remaining")
            )

            fifo_by_product[product_id]["value"] += (
                qty(row.get("qty_remaining"))
                * money(row.get("unit_cost"))
            )

        # Group Stock by product
        stock_by_product = {}

        for row in stock_data:

            product_id = row.get("product_id")

            if product_id is None:
                continue

            try:
                product_id = int(product_id)
            except Exception:
                continue

            stock_by_product[product_id] = qty(
                row.get("qty")
            )

        # Find mismatches at product level
        product_mismatches = []

        all_product_ids = set(
            list(fifo_by_product.keys())
            + list(stock_by_product.keys())
        )

        for product_id in all_product_ids:

            fifo_qty_prod = fifo_by_product.get(
                product_id,
                {}
            ).get("qty", 0.0)

            stock_qty_prod = stock_by_product.get(
                product_id,
                0.0
            )

            qty_diff_prod = abs(fifo_qty_prod - stock_qty_prod)

            if qty_diff_prod >= 0.01:

                # Get product name
                product = execute_query(
                    "products",
                    select="id,name,sku",
                    filters={"id": product_id},
                    limit=1,
                )

                product_name = (
                    product[0].get("name", f"ID:{product_id}")
                    if product
                    else f"ID:{product_id}"
                )

                product_mismatches.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "fifo_qty": fifo_qty_prod,
                    "stock_qty": stock_qty_prod,
                    "qty_diff": qty_diff_prod,
                })

        # ====================================================
        # QTY RECONCILIATION
        # ====================================================

        qty_difference = (
            fifo_qty - stock_qty
        )

        qty_matched = (
            abs(qty_difference) < 0.01
        )

        product_level_matched = (
            len(product_mismatches) == 0
        )

        passed = qty_matched and product_level_matched

        # ====================================================
        # IMPORTANT
        #
        # warehouse_stock currently stores QTY only.
        #
        # Therefore we CANNOT claim that
        # FIFO VALUE == STOCK VALUE.
        # ====================================================

        suggestion = None

        if not passed:

            if product_mismatches:

                mismatch_ids = ", ".join(
                    f"{x['product_name']} "
                    f"(diff: {x['qty_diff']:,.0f})"
                    for x in product_mismatches[:5]
                )

                suggestion = (
                    f"Product-level quantity mismatch: {mismatch_ids}"
                )

            else:

                suggestion = (
                    f"FIFO quantity differs from warehouse "
                    f"stock by {abs(qty_difference):,.2f} units."
                )

        else:

            suggestion = (
                "✅ FIFO quantity matches warehouse stock. "
                "FIFO value is calculated from remaining cost layers. "
                "Stock monetary valuation requires a separate stock-value source."
            )

        # ====================================================
        # RETURN
        # ====================================================

        return {

            "name": "FIFO Cost ↔ Stock",

            "icon": "📈",

            "status": (
                "MATCHED"
                if passed
                else "MISMATCHED"
            ),

            "status_type": (
                "passed"
                if passed
                else "failed"
            ),

            "passed": passed,

            "fifo_qty": fifo_qty,

            "stock_qty": stock_qty,

            "qty_difference": qty_difference,

            "fifo_value": fifo_value,

            "product_mismatches": product_mismatches,

            "detail": (
                f"FIFO Qty: {fifo_qty:,.0f} | "
                f"Stock Qty: {stock_qty:,.0f} | "
                f"FIFO Value: {fifo_value:,.2f}"
            ),

            "suggestion": suggestion,
        }

    except Exception as e:

        return {

            "name": "FIFO Cost ↔ Stock",

            "icon": "📈",

            "status": "ERROR",

            "status_type": "error",

            "passed": False,

            "fifo_qty": 0,

            "stock_qty": 0,

            "qty_difference": 0,

            "fifo_value": 0,

            "product_mismatches": [],

            "detail": str(e)[:200],

            "suggestion": (
                "Check inventory_cost_layers "
                "and warehouse_stock schema."
            ),
        }


# ============================================================
# CHECK 5
# SALES <-> SALE ITEMS (ONLY subtotal check)
# =======

##ဘယ်ကာလအတွက် စစ်ဆေးတယ်ဆိုတာ UI. မှာ စာသားနဲ့ဖော်ပြပေးပါ
