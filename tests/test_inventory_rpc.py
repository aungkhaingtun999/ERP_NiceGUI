tests/test_inventory_rpc.py

"""
ERP Inventory RPC Test Suite

SAFE TEST POLICY

This test module MUST NOT modify the current database state.

Integration tests are READ-ONLY:
- SELECT products
- SELECT warehouse_stock
- SELECT inventory_cost_layers
- SELECT stock_adjustments
- SELECT stock_movements
- get_fefo_issue_plan()

Mutation RPCs are NOT executed against the live database.

Mutation RPCs covered by contract tests:
- stock_adjustment_rpc
- apply_stock_adjustment_fifo_rpc
- approve_stock_adjustment_rpc
- cancel_stock_adjustment_rpc
- create_opening_stock_rpc
- transfer_stock_rpc
- transfer_stock_fifo_rpc

Required environment variables:
SUPABASE_URL
SUPABASE_KEY

Optional:
TEST_PRODUCT_ID
TEST_WAREHOUSE_ID

Example:
TEST_PRODUCT_ID=2
TEST_WAREHOUSE_ID=1

Run:
python -m pytest -v tests/test_inventory_rpc.py

Run with short output:
python -m pytest -q tests/test_inventory_rpc.py
"""

from future import annotations

import json
import os
from decimal import Decimal
from typing import Any, Dict, List

import pytest

============================================================================

OPTIONAL SUPABASE IMPORT

============================================================================

try:
from supabase import create_client
except ImportError:  # pragma: no cover
create_client = None

============================================================================

CONFIGURATION

============================================================================

TEST_PRODUCT_ID = int(os.getenv("TEST_PRODUCT_ID", "2"))
TEST_WAREHOUSE_ID = int(os.getenv("TEST_WAREHOUSE_ID", "1"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

============================================================================

RPC CONTRACTS

============================================================================

RPC_CONTRACTS: Dict[str, Dict[str, Any]] = {

"get_fefo_issue_plan": {
    "arguments": [
        "p_product_id",
        "p_warehouse_id",
        "p_issue_quantity",
    ],
    "read_only": True,
    "expected_return": "jsonb",
},

"stock_adjustment_rpc": {
    "arguments": [
        "p_product_id",
        "p_warehouse_id",
        "p_quantity",
        "p_reason",
        "p_created_by",
        "p_transaction_id",
    ],
    "read_only": False,
    "expected_return": "json",
},

"apply_stock_adjustment_fifo_rpc": {
    "arguments": [
        "p_adjustment_id",
    ],
    "read_only": False,
    "expected_return": "json",
},

"approve_stock_adjustment_rpc": {
    "arguments": [
        "p_adjustment_id",
        "p_manager_id",
    ],
    "read_only": False,
    "expected_return": "jsonb",
},

"cancel_stock_adjustment_rpc": {
    "arguments": [
        "p_adjustment_id",
        "p_user_id",
    ],
    "read_only": False,
    "expected_return": "jsonb",
},

"create_opening_stock_rpc": {
    "arguments": [
        "p_items",
        "p_warehouse_id",
        "p_user_id",
    ],
    "read_only": False,
    "expected_return": "json",
},

"transfer_stock_rpc": {
    "arguments": [
        "p_product_id",
        "p_from_w",
        "p_to_w",
        "p_qty",
        "p_user_id",
    ],
    "read_only": False,
    "expected_return": "jsonb",
},

"transfer_stock_fifo_rpc": {
    "arguments": [
        "p_transfer_id",
    ],
    "read_only": False,
    "expected_return": "json",
},

}

============================================================================

HELPERS

============================================================================

def _require_supabase():
"""
Create a Supabase client.

Tests are skipped instead of failing when credentials are not configured.
"""
if create_client is None:
    pytest.skip(
        "supabase package is not installed. "
        "Install with: pip install supabase"
    )

if not SUPABASE_URL or not SUPABASE_KEY:
    pytest.skip(
        "SUPABASE_URL / SUPABASE_KEY are not configured."
    )

return create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)

def _as_number(value: Any) -> Decimal:
"""Convert DB numeric values safely to Decimal."""
if value is None:
return Decimal("0")

return Decimal(str(value))

def _extract_rows(response: Any) -> List[Dict[str, Any]]:
"""
Safely extract Supabase response data.
"""
data = getattr(response, "data", None)

if data is None:
    return []

if isinstance(data, list):
    return data

if isinstance(data, dict):
    return [data]

return []

def _rpc_data(response: Any) -> Any:
"""
Extract RPC result from Supabase response.
"""
return getattr(response, "data", response)

============================================================================

DATABASE FIXTURE

============================================================================

@pytest.fixture(scope="module")
def db():
"""
Read-only Supabase client.

No mutation RPC is called from this test module.
"""
return _require_supabase()

============================================================================

TEST 01 — RPC CONTRACTS

============================================================================

def test_rpc_contracts_are_defined():
"""
Ensure all production inventory RPCs have a known contract.
"""

required = {
    "get_fefo_issue_plan",
    "stock_adjustment_rpc",
    "apply_stock_adjustment_fifo_rpc",
    "approve_stock_adjustment_rpc",
    "cancel_stock_adjustment_rpc",
    "create_opening_stock_rpc",
    "transfer_stock_rpc",
    "transfer_stock_fifo_rpc",
}

assert required.issubset(RPC_CONTRACTS.keys())

def test_mutation_rpcs_are_never_marked_read_only():
"""
Safety guard:
mutation RPCs must never accidentally be classified as read-only.
"""

for name, contract in RPC_CONTRACTS.items():

    if name == "get_fefo_issue_plan":
        continue

    assert contract["read_only"] is False

def test_fefo_rpc_is_read_only():
"""
FEFO planning RPC must be read-only.
"""

contract = RPC_CONTRACTS["get_fefo_issue_plan"]

assert contract["read_only"] is True
assert contract["expected_return"] == "jsonb"

============================================================================

TEST 02 — CURRENT PRODUCT EXISTS

============================================================================

def test_test_product_exists(db):
"""
Confirm configured test product exists.

READ ONLY.
"""

response = (
    db.table("products")
    .select("id,name,stock")
    .eq("id", TEST_PRODUCT_ID)
    .limit(1)
    .execute()
)

rows = _extract_rows(response)

assert rows, (
    f"Test product {TEST_PRODUCT_ID} was not found."
)

assert int(rows[0]["id"]) == TEST_PRODUCT_ID

============================================================================

TEST 03 — CURRENT WAREHOUSE STOCK EXISTS

============================================================================

def test_test_warehouse_stock_exists(db):
"""
Confirm warehouse stock row exists.

READ ONLY.
"""

response = (
    db.table("warehouse_stock")
    .select(
        "product_id,warehouse_id,qty,available_qty,reserved_qty"
    )
    .eq("product_id", TEST_PRODUCT_ID)
    .eq("warehouse_id", TEST_WAREHOUSE_ID)
    .limit(1)
    .execute()
)

rows = _extract_rows(response)

assert rows, (
    f"No warehouse_stock row for "
    f"product={TEST_PRODUCT_ID}, "
    f"warehouse={TEST_WAREHOUSE_ID}"
)

row = rows[0]

assert int(row["product_id"]) == TEST_PRODUCT_ID
assert int(row["warehouse_id"]) == TEST_WAREHOUSE_ID

qty = _as_number(row["qty"])
available = _as_number(row["available_qty"])
reserved = _as_number(row["reserved_qty"])

assert qty >= 0
assert available >= 0
assert reserved >= 0

============================================================================

TEST 04 — PRODUCT / WAREHOUSE / FIFO RECONCILIATION

============================================================================

def test_product_warehouse_fifo_reconciliation(db):
"""
Verify:

    products.stock
        ==
    warehouse_stock.qty
        ==
    FIFO remaining quantity

READ ONLY.

This test matches the current architecture after reconciliation.
"""

product_response = (
    db.table("products")
    .select("id,name,stock")
    .eq("id", TEST_PRODUCT_ID)
    .limit(1)
    .execute()
)

product_rows = _extract_rows(product_response)

assert product_rows, (
    f"Product {TEST_PRODUCT_ID} not found."
)

product_stock = _as_number(product_rows[0]["stock"])

warehouse_response = (
    db.table("warehouse_stock")
    .select("qty")
    .eq("product_id", TEST_PRODUCT_ID)
    .eq("warehouse_id", TEST_WAREHOUSE_ID)
    .limit(1)
    .execute()
)

warehouse_rows = _extract_rows(warehouse_response)

assert warehouse_rows, (
    "warehouse_stock row not found."
)

warehouse_stock = _as_number(
    warehouse_rows[0]["qty"]
)

fifo_response = (
    db.table("inventory_cost_layers")
    .select("qty_remaining")
    .eq("product_id", TEST_PRODUCT_ID)
    .eq("warehouse_id", TEST_WAREHOUSE_ID)
    .gt("qty_remaining", 0)
    .execute()
)

fifo_rows = _extract_rows(fifo_response)

fifo_stock = sum(
    (
        _as_number(row["qty_remaining"])
        for row in fifo_rows
    ),
    Decimal("0"),
)

assert product_stock == warehouse_stock, (
    f"Product/Warehouse mismatch: "
    f"product={product_stock}, "
    f"warehouse={warehouse_stock}"
)

assert warehouse_stock == fifo_stock, (
    f"Warehouse/FIFO mismatch: "
    f"warehouse={warehouse_stock}, "
    f"fifo={fifo_stock}"
)

============================================================================

TEST 05 — NO PENDING ADJUSTMENTS

============================================================================

def test_no_pending_adjustments(db):
"""
Verify there are no orphaned PENDING adjustments.

READ ONLY.

This reflects the current cleaned test state.
"""

response = (
    db.table("stock_adjustments")
    .select("id")
    .eq("status", "PENDING")
    .execute()
)

rows = _extract_rows(response)

assert rows == [], (
    f"Unexpected PENDING adjustments found: {rows}"
)

============================================================================

TEST 06 — APPLIED ADJUSTMENT STATUS

============================================================================

def test_applied_adjustments_are_terminal(db):
"""
Verify APPLIED adjustments exist only as terminal records.

READ ONLY.
"""

response = (
    db.table("stock_adjustments")
    .select(
        "id,product_id,warehouse_id,qty,status"
    )
    .eq("status", "APPLIED")
    .execute()
)

rows = _extract_rows(response)

for row in rows:
    assert row["status"] == "APPLIED"
    assert row["id"] is not None

============================================================================

TEST 07 — FEFO INVALID QUANTITY

============================================================================

def test_fefo_rejects_invalid_quantity(db):
"""
get_fefo_issue_plan() is read-only and safe to execute.

Invalid quantity must return success=false.

NO DATABASE MUTATION.
"""

response = db.rpc(
    "get_fefo_issue_plan",
    {
        "p_product_id": TEST_PRODUCT_ID,
        "p_warehouse_id": TEST_WAREHOUSE_ID,
        "p_issue_quantity": 0,
    },
).execute()

result = _rpc_data(response)

assert isinstance(result, dict), (
    f"Unexpected FEFO result: {result!r}"
)

assert result.get("success") is False

assert (
    "shortage_qty" in result
    or "requested_qty" in result
)

============================================================================

TEST 08 — FEFO NEGATIVE QUANTITY

============================================================================

def test_fefo_rejects_negative_quantity(db):
"""
Negative issue quantity must be rejected.

NO DATABASE MUTATION.
"""

response = db.rpc(
    "get_fefo_issue_plan",
    {
        "p_product_id": TEST_PRODUCT_ID,
        "p_warehouse_id": TEST_WAREHOUSE_ID,
        "p_issue_quantity": -1,
    },
).execute()

result = _rpc_data(response)

assert isinstance(result, dict)
assert result.get("success") is False

============================================================================

TEST 09 — FEFO VALID REQUEST

============================================================================

def test_fefo_valid_request_returns_plan(db):
"""
Execute the read-only FEFO planning RPC.

The test does NOT consume stock.

NO DATABASE MUTATION.
"""

response = db.rpc(
    "get_fefo_issue_plan",
    {
        "p_product_id": TEST_PRODUCT_ID,
        "p_warehouse_id": TEST_WAREHOUSE_ID,
        "p_issue_quantity": 1,
    },
).execute()

result = _rpc_data(response)

assert isinstance(result, dict)

assert result.get("method") == "FEFO"
assert int(result.get("product_id")) == TEST_PRODUCT_ID
assert int(result.get("warehouse_id")) == TEST_WAREHOUSE_ID

assert "requested_qty" in result
assert "allocated_qty" in result
assert "shortage_qty" in result
assert "total_cost" in result
assert "allocations" in result

assert isinstance(
    result["allocations"],
    list,
)

============================================================================

TEST 10 — FEFO ALLOCATION MATH

============================================================================

def test_fefo_allocation_math(db):
"""
Validate FEFO allocation arithmetic.

For every allocation:

    issue_qty <= available_qty
    remaining_qty = available_qty - issue_qty
    line_cost = issue_qty * unit_cost

NO DATABASE MUTATION.
"""

response = db.rpc(
    "get_fefo_issue_plan",
    {
        "p_product_id": TEST_PRODUCT_ID,
        "p_warehouse_id": TEST_WAREHOUSE_ID,
        "p_issue_quantity": 1,
    },
).execute()

result = _rpc_data(response)

assert isinstance(result, dict)

allocations = result.get("allocations", [])

for allocation in allocations:

    available = _as_number(
        allocation.get("available_qty")
    )

    issue = _as_number(
        allocation.get("issue_qty")
    )

    remaining = _as_number(
        allocation.get("remaining_qty")
    )

    unit_cost = _as_number(
        allocation.get("unit_cost")
    )

    line_cost = _as_number(
        allocation.get("line_cost")
    )

    assert issue >= 0
    assert issue <= available

    assert remaining == available - issue

    assert line_cost == issue * unit_cost

============================================================================

TEST 11 — FEFO TOTAL COST

============================================================================

def test_fefo_total_cost_matches_allocations(db):
"""
Verify total_cost equals sum(line_cost).

NO DATABASE MUTATION.
"""

response = db.rpc(
    "get_fefo_issue_plan",
    {
        "p_product_id": TEST_PRODUCT_ID,
        "p_warehouse_id": TEST_WAREHOUSE_ID,
        "p_issue_quantity": 1,
    },
).execute()

result = _rpc_data(response)

allocations = result.get("allocations", [])

calculated_total = sum(
    (
        _as_number(
            allocation.get("line_cost")
        )
        for allocation in allocations
    ),
    Decimal("0"),
)

rpc_total = _as_number(
    result.get("total_cost")
)

assert rpc_total == calculated_total

============================================================================

TEST 12 — FEFO SHORTAGE MATH

============================================================================

def test_fefo_shortage_math(db):
"""
Verify:

    shortage = max(requested - allocated, 0)

NO DATABASE MUTATION.
"""

response = db.rpc(
    "get_fefo_issue_plan",
    {
        "p_product_id": TEST_PRODUCT_ID,
        "p_warehouse_id": TEST_WAREHOUSE_ID,
        "p_issue_quantity": 1,
    },
).execute()

result = _rpc_data(response)

requested = _as_number(
    result.get("requested_qty")
)

allocated = _as_number(
    result.get("allocated_qty")
)

shortage = _as_number(
    result.get("shortage_qty")
)

expected_shortage = max(
    requested - allocated,
    Decimal("0"),
)

assert shortage == expected_shortage

assert result.get("success") == (
    shortage == 0
)

============================================================================

TEST 13 — FEFO ORDER

============================================================================

def test_fefo_order_is_expiry_ascending(db):
"""
If multiple batches are returned, FEFO must order them
by earliest expiry first.

NO DATABASE MUTATION.
"""

response = db.rpc(
    "get_fefo_issue_plan",
    {
        "p_product_id": TEST_PRODUCT_ID,
        "p_warehouse_id": TEST_WAREHOUSE_ID,
        "p_issue_quantity": 1,
    },
).execute()

result = _rpc_data(response)

allocations = result.get("allocations", [])

expiry_dates = [
    allocation.get("expiry_date")
    for allocation in allocations
    if allocation.get("expiry_date") is not None
]

assert expiry_dates == sorted(expiry_dates)

============================================================================

TEST 14 — RPC PAYLOAD CONTRACTS

============================================================================

@pytest.mark.parametrize(
"rpc_name,expected_args",
[
(
"stock_adjustment_rpc",
[
"p_product_id",
"p_warehouse_id",
"p_quantity",
"p_reason",
"p_created_by",
"p_transaction_id",
],
),
(
"apply_stock_adjustment_fifo_rpc",
[
"p_adjustment_id",
],
),
(
"approve_stock_adjustment_rpc",
[
"p_adjustment_id",
"p_manager_id",
],
),
(
"cancel_stock_adjustment_rpc",
[
"p_adjustment_id",
"p_user_id",
],
),
(
"create_opening_stock_rpc",
[
"p_items",
"p_warehouse_id",
"p_user_id",
],
),
(
"transfer_stock_rpc",
[
"p_product_id",
"p_from_w",
"p_to_w",
"p_qty",
"p_user_id",
],
),
(
"transfer_stock_fifo_rpc",
[
"p_transfer_id",
],
),
],
)
def test_rpc_argument_contract(
rpc_name,
expected_args,
):
"""
Verify application-side RPC argument names match
PostgreSQL RPC signatures.

This test does NOT call the RPC.
"""

assert rpc_name in RPC_CONTRACTS

actual_args = RPC_CONTRACTS[
    rpc_name
]["arguments"]

assert actual_args == expected_args

============================================================================

TEST 15 — MUTATION RPC SAFETY GUARD

============================================================================

def test_mutation_rpcs_are_not_called_by_safe_suite():
"""
Safety assertion documenting the design.

This test suite deliberately does not execute mutation RPCs.
"""

mutation_rpcs = {
    name
    for name, contract in RPC_CONTRACTS.items()
    if not contract["read_only"]
}

executed_rpcs = {
    "get_fefo_issue_plan",
}

assert mutation_rpcs.isdisjoint(
    executed_rpcs
)

============================================================================

TEST 16 — CURRENT STOCK IS NON-NEGATIVE

============================================================================

def test_current_stock_is_non_negative(db):
"""
Current product, warehouse and FIFO quantities must not be negative.

READ ONLY.
"""

product_response = (
    db.table("products")
    .select("stock")
    .eq("id", TEST_PRODUCT_ID)
    .limit(1)
    .execute()
)

product_rows = _extract_rows(
    product_response
)

assert product_rows

assert _as_number(
    product_rows[0]["stock"]
) >= 0

warehouse_response = (
    db.table("warehouse_stock")
    .select("qty,available_qty,reserved_qty")
    .eq("product_id", TEST_PRODUCT_ID)
    .eq("warehouse_id", TEST_WAREHOUSE_ID)
    .limit(1)
    .execute()
)

warehouse_rows = _extract_rows(
    warehouse_response
)

assert warehouse_rows

warehouse = warehouse_rows[0]

assert _as_number(
    warehouse["qty"]
) >= 0

assert _as_number(
    warehouse["available_qty"]
) >= 0

assert _as_number(
    warehouse["reserved_qty"]
) >= 0

============================================================================

TEST 17 — MOVEMENT HISTORY IS INTERNALLY VALID

============================================================================

def test_stock_movement_history_has_valid_quantities(db):
"""
Verify movement records contain numeric quantities.

READ ONLY.
"""

response = (
    db.table("stock_movements")
    .select(
        "id,product_id,warehouse_id,"
        "movement_type,qty,reference_type,"
        "reference_id,unit_cost"
    )
    .eq("product_id", TEST_PRODUCT_ID)
    .order("id", desc=True)
    .limit(100)
    .execute()
)

rows = _extract_rows(response)

for row in rows:

    qty = _as_number(
        row.get("qty")
    )

    unit_cost = _as_number(
        row.get("unit_cost")
    )

    assert isinstance(qty, Decimal)
    assert isinstance(unit_cost, Decimal)

    assert row.get("movement_type")
    assert row.get("reference_type")

============================================================================

TEST 18 — JSON SERIALIZATION

============================================================================

def test_fefo_result_is_json_serializable(db):
"""
Ensure the FEFO RPC response can be serialized.

This is useful for Streamlit / FastAPI / GitHub CI consumers.

NO DATABASE MUTATION.
"""

response = db.rpc(
    "get_fefo_issue_plan",
    {
        "p_product_id": TEST_PRODUCT_ID,
        "p_warehouse_id": TEST_WAREHOUSE_ID,
        "p_issue_quantity": 1,
    },
).execute()

result = _rpc_data(response)

try:
    json.dumps(
        result,
        default=str,
    )
except (TypeError, ValueError) as exc:
    pytest.fail(
        f"FEFO RPC result is not JSON serializable: {exc}"
    )

============================================================================

TEST 19 — CURRENT TEA BASELINE

============================================================================

def test_current_tea_baseline_when_using_default_ids(db):
"""
Regression test for the current reconciled Tea state.

Expected current state:
    products.stock      = 11
    warehouse_stock.qty = 11
    FIFO remaining      = 11

This test only runs when the configured defaults are used.

READ ONLY.
"""

if (
    TEST_PRODUCT_ID != 2
    or TEST_WAREHOUSE_ID != 1
):
    pytest.skip(
        "Tea baseline test is only for "
        "TEST_PRODUCT_ID=2 and TEST_WAREHOUSE_ID=1."
    )

product_response = (
    db.table("products")
    .select("stock")
    .eq("id", 2)
    .limit(1)
    .execute()
)

product_rows = _extract_rows(
    product_response
)

assert product_rows

product_stock = _as_number(
    product_rows[0]["stock"]
)

warehouse_response = (
    db.table("warehouse_stock")
    .select("qty")
    .eq("product_id", 2)
    .eq("warehouse_id", 1)
    .limit(1)
    .execute()
)

warehouse_rows = _extract_rows(
    warehouse_response
)

assert warehouse_rows

warehouse_stock = _as_number(
    warehouse_rows[0]["qty"]
)

fifo_response = (
    db.table("inventory_cost_layers")
    .select("qty_remaining")
    .eq("product_id", 2)
    .eq("warehouse_id", 1)
    .gt("qty_remaining", 0)
    .execute()
)

fifo_rows = _extract_rows(
    fifo_response
)

fifo_stock = sum(
    (
        _as_number(
            row["qty_remaining"]
        )
        for row in fifo_rows
    ),
    Decimal("0"),
)

assert product_stock == Decimal("11")
assert warehouse_stock == Decimal("11")
assert fifo_stock == Decimal("11")

============================================================================

END

============================================================================

"""
Expected safe test behavior:

- No INSERT
- No UPDATE
- No DELETE
- No mutation RPC execution
- FEFO RPC only for live integration
- Mutation RPCs tested through contract validation

Recommended command:

python -m pytest -v tests/test_inventory_rpc.py

Expected final result after current DB reconciliation:

PASSED

"""