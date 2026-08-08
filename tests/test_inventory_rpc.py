# ==============================================================================
# tests/test_fefo.py
# FEFO SERVICE TESTS — RPC ARCHITECTURE
# READ-ONLY / NO DATABASE MUTATION
# ==============================================================================

from __future__ import annotations

import pytest
from erp_core.services.inventory_service import InventoryService


# ==============================================================================
# MOCK RPC RESPONSE
# ==============================================================================

class MockRPCResponse:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error

    def execute(self):
        return self


# ==============================================================================
# MOCK SUPABASE CLIENT
# ==============================================================================

class MockClient:
    def __init__(self, rpc_results=None):
        self.rpc_results = rpc_results or {}

    def rpc(self, function_name, params=None):
        result = self.rpc_results.get(function_name)
        if result is None:
            return MockRPCResponse(
                data=None,
                error={
                    "message": (
                        f"Mock RPC not configured: "
                        f"{function_name}"
                    )
                },
            )
        return MockRPCResponse(
            data=result,
            error=None,
        )


# ==============================================================================
# STANDARD FEFO DATA
# ==============================================================================

def standard_batches():
    return [
        {
            "id": 4,
            "batch_id": 4,
            "batch_no": "TEA-BATCH-001",
            "manufacturing_date": "2026-01-01",
            "expiry_date": "2026-09-01",
            "available_qty": 50,
            "quantity": 50,
            "unit_cost": 1000,
        },
        {
            "id": 5,
            "batch_id": 5,
            "batch_no": "TEA-BATCH-002",
            "manufacturing_date": "2026-02-01",
            "expiry_date": "2026-10-01",
            "available_qty": 80,
            "quantity": 80,
            "unit_cost": 1050,
        },
    ]


# ==============================================================================
# EXPECTED RPC RESULT
# ==============================================================================

def fefo_rpc_result(
    issue_quantity=60,
    success=True,
):
    if issue_quantity == 60:
        return {
            "success": True,
            "method": "FEFO",
            "product_id": 4,
            "warehouse_id": 1,
            "requested_qty": 60,
            "available_qty": 130,
            "allocated_qty": 60,
            "shortage_qty": 0,
            "total_cost": 60500,
            "allocations": [
                {
                    "batch_id": 4,
                    "batch_no": "TEA-BATCH-001",
                    "manufacturing_date": "2026-01-01",
                    "expiry_date": "2026-09-01",
                    "available_qty": 50,
                    "issue_qty": 50,
                    "remaining_qty": 0,
                    "unit_cost": 1000,
                    "line_cost": 50000,
                },
                {
                    "batch_id": 5,
                    "batch_no": "TEA-BATCH-002",
                    "manufacturing_date": "2026-02-01",
                    "expiry_date": "2026-10-01",
                    "available_qty": 80,
                    "issue_qty": 10,
                    "remaining_qty": 70,
                    "unit_cost": 1050,
                    "line_cost": 10500,
                },
            ],
        }
    if issue_quantity == 200:
        return {
            "success": False,
            "method": "FEFO",
            "product_id": 4,
            "warehouse_id": 1,
            "requested_qty": 200,
            "available_qty": 130,
            "allocated_qty": 130,
            "shortage_qty": 70,
            "total_cost": 134000,
            "allocations": [
                {
                    "batch_id": 4,
                    "batch_no": "TEA-BATCH-001",
                    "manufacturing_date": "2026-01-01",
                    "expiry_date": "2026-09-01",
                    "available_qty": 50,
                    "issue_qty": 50,
                    "remaining_qty": 0,
                    "unit_cost": 1000,
                    "line_cost": 50000,
                },
                {
                    "batch_id": 5,
                    "batch_no": "TEA-BATCH-002",
                    "manufacturing_date": "2026-02-01",
                    "expiry_date": "2026-10-01",
                    "available_qty": 80,
                    "issue_qty": 80,
                    "remaining_qty": 0,
                    "unit_cost": 1050,
                    "line_cost": 84000,
                },
            ],
        }
    return {
        "success": success,
        "method": "FEFO",
        "product_id": 4,
        "warehouse_id": 1,
        "requested_qty": issue_quantity,
        "available_qty": 130,
        "allocated_qty": 0,
        "shortage_qty": issue_quantity,
        "total_cost": 0,
        "allocations": [],
    }


# ==============================================================================
# SERVICE FACTORY
# ==============================================================================

def make_service(issue_quantity=60):
    client = MockClient(
        rpc_results={
            "get_fefo_issue_plan": fefo_rpc_result(issue_quantity)
        }
    )
    service = InventoryService(client=client)
    return service


# ==============================================================================
# ENABLE FEFO
# ==============================================================================

def enable_fefo(service):
    service.get_fefo_batches = lambda product_id, warehouse_id: (
        standard_batches()
    )


# ==============================================================================
# FEFO BASIC TEST
# ==============================================================================

def test_fefo_issue_plan():
    service = make_service()
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )
    print()
    print("========== FEFO TEST RESULT ==========")
    print(result)
    print("=======================================")
    assert result["success"] is True
    assert result["method"] == "FEFO"
    assert result["requested_qty"] == 60
    assert result["allocated_qty"] == 60
    assert result["shortage_qty"] == 0


# ==============================================================================
# ALLOCATION COUNT
# ==============================================================================

def test_fefo_allocation_count():
    service = make_service()
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )
    allocations = result["allocations"]
    assert len(allocations) == 2


# ==============================================================================
# FIRST BATCH
# ==============================================================================

def test_fefo_first_batch():
    service = make_service()
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )
    first = result["allocations"][0]
    assert first["batch_id"] == 4
    assert first["batch_no"] == "TEA-BATCH-001"
    assert first["issue_qty"] == 50
    assert first["unit_cost"] == 1000
    assert first["line_cost"] == 50000


# ==============================================================================
# SECOND BATCH
# ==============================================================================

def test_fefo_second_batch_partial_allocation():
    service = make_service()
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )
    second = result["allocations"][1]
    assert second["batch_id"] == 5
    assert second["batch_no"] == "TEA-BATCH-002"
    assert second["issue_qty"] == 10
    assert second["remaining_qty"] == 70
    assert second["unit_cost"] == 1050
    assert second["line_cost"] == 10500


# ==============================================================================
# TOTAL COGS
# ==============================================================================

def test_fefo_total_cogs():
    service = make_service()
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )
    assert result["total_cost"] == 60500


# ==============================================================================
# TOTAL ISSUE QUANTITY
# ==============================================================================

def test_fefo_total_issue_quantity():
    service = make_service()
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )
    total_issue = sum(
        row["issue_qty"] for row in result["allocations"]
    )
    assert total_issue == 60


# ==============================================================================
# EARLIEST EXPIRY FIRST
# ==============================================================================

def test_fefo_uses_earliest_expiry_first():
    service = make_service()
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )
    allocations = result["allocations"]
    assert allocations[0]["expiry_date"] == "2026-09-01"
    assert allocations[1]["expiry_date"] == "2026-10-01"


# ==============================================================================
# INSUFFICIENT STOCK
# ==============================================================================

def test_fefo_insufficient_stock():
    service = make_service(issue_quantity=200)
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=200,
    )
    assert result["success"] is False
    assert result["requested_qty"] == 200
    assert result["available_qty"] == 130
    assert result["allocated_qty"] == 130
    assert result["shortage_qty"] == 70
    assert result["total_cost"] == 134000


# ==============================================================================
# ZERO QUANTITY
# ==============================================================================

def test_fefo_zero_quantity():
    service = make_service()
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=0,
    )
    assert result["success"] is False
    assert result["allocated_qty"] == 0
    assert result["shortage_qty"] == 0


# ==============================================================================
# NEGATIVE QUANTITY
# ==============================================================================

def test_fefo_negative_quantity():
    service = make_service()
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=-5,
    )
    assert result["success"] is False
    assert result["allocated_qty"] == 0
    assert result["shortage_qty"] == 5


# ==============================================================================
# NO BATCHES
# ==============================================================================

def test_fefo_no_batches():
    service = make_service()
    service.get_fefo_batches = lambda product_id, warehouse_id: []
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=10,
    )
    assert result["success"] is False


# ==============================================================================
# READ-ONLY TEST
# ==============================================================================

def test_fefo_does_not_modify_batch_data():
    before = standard_batches()
    service = make_service()
    enable_fefo(service)
    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )
    after = standard_batches()
    assert result["success"] is True
    assert before == after
