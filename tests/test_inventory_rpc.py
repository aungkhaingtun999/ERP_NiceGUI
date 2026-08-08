"""Inventory RPC Architecture Tests

Purpose

Validate the inventory RPC architecture without changing the current database state.

IMPORTANT

These tests are intentionally READ-ONLY.

They DO NOT:

create stock
approve adjustments
apply adjustments
transfer stock
modify products
modify warehouse stock
modify FIFO layers
insert movement records

The tests verify:

Required RPC functions exist.
RPC signatures match the current architecture.
FEFO RPC can be called in read-only mode.
FEFO allocation results are internally consistent.
Current inventory reconciliation is consistent.
No pending stock adjustments remain.

Environment

Required: SUPABASE_URL SUPABASE_KEY

Run: pytest -q tests/test_inventory_rpc.py

Run with verbose output: pytest -v tests/test_inventory_rpc.py
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import pytest

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = Any

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

REQUIRED_RPC_FUNCTIONS = {
    "apply_stock_adjustment_fifo_rpc",
    "approve_stock_adjustment_rpc",
    "approve_stock_count_rpc",
    "cancel_stock_adjustment_rpc",
    "create_opening_stock_rpc",
    "get_fefo_issue_plan",
    "stock_adjustment_rpc",
    "transfer_stock_fifo_rpc",
    "transfer_stock_rpc",
}

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def supabase():
    """Create one Supabase client for the entire test session.

    This fixture does not modify the database.
    """
    if create_client is None:
        pytest.skip("supabase package is not installed")
    if not SUPABASE_URL or not SUPABASE_KEY:
        pytest.skip("SUPABASE_URL / SUPABASE_KEY are not configured")
    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )


# ============================================================================
# HELPERS
# ============================================================================

def rpc_call(
    supabase,
    function_name: str,
    params: dict[str, Any],
):
    """Execute an RPC.

    This helper is only used with READ-ONLY RPCs in this test file.
    """
    return supabase.rpc(
        function_name,
        params,
    ).execute()


def to_decimal(value: Any) -> Decimal:
    """Safely convert database numeric values to Decimal."""
    if value is None:
        return Decimal("0")

    return Decimal(str(value))


def get_rows(response) -> list[dict[str, Any]]:
    """Normalize Supabase response data."""
    data = getattr(response, "data", None)

    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


# ============================================================================
# TEST 01 — ENVIRONMENT
# ============================================================================

def test_supabase_environment(supabase):
    """Verify Supabase connection is available."""
    assert supabase is not None


# ============================================================================
# TEST 02 — RPC EXISTENCE
# ============================================================================

def test_required_rpc_functions_exist(supabase):
    """Verify that all required inventory RPC functions exist.

    This is a read-only catalog query.
    """
    response = (
        supabase
        .table("pg_proc")
        .select("proname")
        .in_("proname", list(REQUIRED_RPC_FUNCTIONS))
        .execute()
    )
    rows = get_rows(response)
    found = {row["proname"] for row in rows if row.get("proname")}
    missing = REQUIRED_RPC_FUNCTIONS - found
    assert not missing, (
        "Missing inventory RPC functions: " + ", ".join(sorted(missing))
    )


# ============================================================================
# TEST 03 — FEFO CONTRACT
# ============================================================================

def test_get_fefo_issue_plan_contract(supabase):
    """Verify get_fefo_issue_plan returns the expected contract.

    This RPC is read-only and does not consume stock.
    """
    product_id = 4
    warehouse_id = 1
    issue_quantity = Decimal("60")
    response = rpc_call(
        supabase,
        "get_fefo_issue_plan",
        {
            "p_product_id": product_id,
            "p_warehouse_id": warehouse_id,
            "p_issue_quantity": float(issue_quantity),
        },
    )
    result = response.data
    assert isinstance(result, dict), (
        f"Expected JSON object, got: {type(result)}"
    )
    required_keys = {
        "success",
        "method",
        "product_id",
        "warehouse_id",
        "requested_qty",
        "available_qty",
        "allocated_qty",
        "shortage_qty",
        "total_cost",
        "allocations",
    }
    missing = required_keys - set(result.keys())
    assert not missing, (
        "FEFO result missing keys: " + ", ".join(sorted(missing))
    )
    assert result["method"] == "FEFO"
    assert result["product_id"] == product_id
    assert result["warehouse_id"] == warehouse_id


# ============================================================================
# TEST 04 — FEFO SUCCESS CASE
# ============================================================================

def test_fefo_success_allocation(supabase):
    """Verify a valid FEFO request can be completely allocated.

    Current known test data:
    Product 4
    Warehouse 1
    Batch 4 = 50
    Batch 5 = 80
    Request: 60
    Expected:
    Batch 4 -> 50
    Batch 5 -> 10
    """
    response = rpc_call(
        supabase,
        "get_fefo_issue_plan",
        {
            "p_product_id": 4,
            "p_warehouse_id": 1,
            "p_issue_quantity": 60,
        },
    )
    result = response.data
    assert result["success"] is True
    assert result["method"] == "FEFO"
    requested = to_decimal(result["requested_qty"])
    allocated = to_decimal(result["allocated_qty"])
    shortage = to_decimal(result["shortage_qty"])
    assert requested == Decimal("60")
    assert allocated == Decimal("60")
    assert shortage == Decimal("0")
    allocations = result["allocations"]
    assert isinstance(allocations, list)
    assert len(allocations) >= 1
    total_issue = sum(
        to_decimal(row["issue_qty"]) for row in allocations
    )
    assert total_issue == Decimal("60")


# ============================================================================
# TEST 05 — FEFO COST CONSISTENCY
# ============================================================================

def test_fefo_total_cost_consistency(supabase):
    """Verify total_cost equals the sum of allocation line costs."""
    response = rpc_call(
        supabase,
        "get_fefo_issue_plan",
        {
            "p_product_id": 4,
            "p_warehouse_id": 1,
            "p_issue_quantity": 60,
        },
    )
    result = response.data
    allocations = result["allocations"]
    calculated_cost = sum(
        to_decimal(row["issue_qty"]) * to_decimal(row["unit_cost"]) for row in allocations
    )
    reported_cost = to_decimal(result["total_cost"])
    assert calculated_cost == reported_cost


# ============================================================================
# TEST 06 — FEFO ORDER
# ============================================================================

def test_fefo_expiry_order(supabase):
    """Verify FEFO allocations are ordered by earliest expiry first."""
    response = rpc_call(
        supabase,
        "get_fefo_issue_plan",
        {
            "p_product_id": 4,
            "p_warehouse_id": 1,
            "p_issue_quantity": 60,
        },
    )
    result = response.data
    allocations = result["allocations"]
    expiry_dates = [
        row["expiry_date"] for row in allocations if row.get("expiry_date") is not None
    ]
    assert expiry_dates == sorted(expiry_dates)


# ============================================================================
# TEST 07 — FEFO SHORTAGE
# ============================================================================

def test_fefo_shortage_contract(supabase):
    """Verify FEFO correctly reports shortage when requested quantity exceeds available quantity.

    This test is READ-ONLY.
    """
    response = rpc_call(
        supabase,
        "get_fefo_issue_plan",
        {
            "p_product_id": 4,
            "p_warehouse_id": 1,
            "p_issue_quantity": 200,
        },
    )
    result = response.data
    assert result["success"] is False
    requested = to_decimal(result["requested_qty"])
    allocated = to_decimal(result["allocated_qty"])
    shortage = to_decimal(result["shortage_qty"])
    assert requested == Decimal("200")
    assert allocated <= requested
    assert shortage == requested - allocated
    assert shortage > 0


# ============================================================================
# TEST 08 — FEFO DOES NOT CHANGE STOCK
# ============================================================================

def test_fefo_is_read_only(supabase):
    """Verify calling FEFO does not change warehouse stock.

    The same quantity is read before and after the RPC call.
    """
    before_response = (
        supabase
        .table("warehouse_stock")
        .select("qty, available_qty, reserved_qty")
        .eq("product_id", 4)
        .eq("warehouse_id", 1)
        .limit(1)
        .execute()
    )
    before_rows = get_rows(before_response)
    if not before_rows:
        pytest.skip("Product 4 / warehouse 1 stock row does not exist")
    before = before_rows[0]
    rpc_call(
        supabase,
        "get_fefo_issue_plan",
        {
            "p_product_id": 4,
            "p_warehouse_id": 1,
            "p_issue_quantity": 1,
        },
    )
    after_response = (
        supabase
        .table("warehouse_stock")
        .select("qty, available_qty, reserved_qty")
        .eq("product_id", 4)
        .eq("warehouse_id", 1)
        .limit(1)
        .execute()
    )
    after_rows = get_rows(after_response)
    assert after_rows, "Warehouse stock row disappeared"
    after = after_rows[0]
    assert to_decimal(after["qty"]) == to_decimal(before["qty"])
    assert to_decimal(after["available_qty"]) == to_decimal(
        before["available_qty"]
    )
    assert to_decimal(after["reserved_qty"]) == to_decimal(
        before["reserved_qty"]
    )


# ============================================================================
# TEST 09 — CURRENT INVENTORY RECONCILIATION
# ============================================================================

def test_inventory_reconciliation(supabase):
    """Verify product stock and warehouse stock are reconciled.

    This test does not modify anything.
    """
    product_response = (
        supabase
        .table("products")
        .select("id, stock")
        .eq("id", 2)
        .limit(1)
        .execute()
    )
    product_rows = get_rows(product_response)
    if not product_rows:
        pytest.skip("Product 2 does not exist")
    product_stock = to_decimal(
        product_rows[0]["stock"]
    )
    warehouse_response = (
        supabase
        .table("warehouse_stock")
        .select("qty")
        .eq("product_id", 2)
        .eq("warehouse_id", 1)
        .limit(1)
        .execute()
    )
    warehouse_rows = get_rows(warehouse_response)
    if not warehouse_rows:
        pytest.skip("Product 2 / warehouse 1 stock row does not exist")
    warehouse_stock = to_decimal(
        warehouse_rows[0]["qty"]
    )
    assert product_stock == warehouse_stock, (
        f"Product stock mismatch: "
        f"products.stock={product_stock}, "
        f"warehouse_stock.qty={warehouse_stock}"
    )


# ============================================================================
# TEST 10 — FIFO RECONCILIATION
# ============================================================================

def test_fifo_reconciliation(supabase):
    """Verify FIFO remaining quantity equals warehouse stock.

    Current known product: Product 2 / Warehouse 1
    """
    warehouse_response = (
        supabase
        .table("warehouse_stock")
        .select("qty")
        .eq("product_id", 2)
        .eq("warehouse_id", 1)
        .limit(1)
        .execute()
    )
    warehouse_rows = get_rows(warehouse_response)
    if not warehouse_rows:
        pytest.skip("Warehouse stock row not found")
    warehouse_qty = to_decimal(
        warehouse_rows[0]["qty"]
    )
    fifo_response = (
        supabase
        .table("inventory_cost_layers")
        .select("qty_remaining")
        .eq("product_id", 2)
        .eq("warehouse_id", 1)
    ).execute()
    fifo_rows = get_rows(fifo_response)
    fifo_qty = sum(
        to_decimal(row["qty_remaining"]) for row in fifo_rows
    )
    assert fifo_qty == warehouse_qty, (
        f"FIFO mismatch: "
        f"warehouse={warehouse_qty}, "
        f"fifo={fifo_qty}"
    )


# ============================================================================
# TEST 11 — NO PENDING ADJUSTMENTS
# ============================================================================

def test_no_pending_adjustments(supabase):
    """Current production/test database should have no pending adjustments.

    This is a read-only check.
    """
    response = (
        supabase
        .table("stock_adjustments")
        .select("id")
        .eq("status", "PENDING")
        .execute()
    )
    rows = get_rows(response)
    assert rows == [], (
        f"Pending stock adjustments still exist: {rows}"
    )


# ============================================================================
# TEST 12 — APPLIED ADJUSTMENT STATE
# ============================================================================

def test_applied_adjustment_21(supabase):
    """Verify the known applied negative adjustment remains APPLIED.

    This does not execute the APPLY RPC.
    """
    response = (
        supabase
        .table("stock_adjustments")
        .select(
            "id, product_id, warehouse_id, qty, status"
        )
        .eq("id", 21)
        .limit(1)
        .execute()
    )
    rows = get_rows(response)
    if not rows:
        pytest.skip("Adjustment 21 does not exist")
    row = rows[0]
    assert row["status"] == "APPLIED"
    assert int(row["product_id"]) == 2
    assert int(row["warehouse_id"]) == 1
    assert to_decimal(row["qty"]) == Decimal("-5")


# ============================================================================
# TEST 13 — NO INVENTORY SIDE EFFECT FROM TEST SUITE
# ============================================================================

def test_current_tea_stock_is_reconciled(supabase):
    """Final read-only safety check for the current Tea inventory.

    Expected current state:
    products.stock = 11
    warehouse_stock.qty = 11
    FIFO remaining = 11
    """
    product_response = (
        supabase
        .table("products")
        .select("stock")
        .eq("id", 2)
        .limit(1)
        .execute()
    )
    product_rows = get_rows(product_response)
    if not product_rows:
        pytest.skip("Tea product does not exist")
    product_stock = to_decimal(
        product_rows[0]["stock"]
    )
    warehouse_response = (
        supabase
        .table("warehouse_stock")
        .select("qty")
        .eq("product_id", 2)
        .eq("warehouse_id", 1)
        .limit(1)
        .execute()
    )
    warehouse_rows = get_rows(warehouse_response)
    assert warehouse_rows
    warehouse_stock = to_decimal(
        warehouse_rows[0]["qty"]
    )
    fifo_response = (
        supabase
        .table("inventory_cost_layers")
        .select("qty_remaining")
        .eq("product_id", 2)
        .eq("warehouse_id", 1)
    ).execute()
    fifo_rows = get_rows(fifo_response)
    fifo_stock = sum(
        to_decimal(row["qty_remaining"]) for row in fifo_rows
    )
    assert product_stock == Decimal("11")
    assert warehouse_stock == Decimal("11")
    assert fifo_stock == Decimal("11")
    assert product_stock == warehouse_stock
    assert warehouse_stock == fifo_stock


# ============================================================================
# END
# ============================================================================

if __name__ == "__main__":
    raise SystemExit(
        pytest.main(
            [
                "-v",
                __file__,
            ]
        )
    )
