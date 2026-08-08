from erp_core.services.inventory_service import InventoryService
from database import supabase


def test_fefo_issue_plan():

    service = InventoryService(supabase)

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60
    )

    print(result)

    assert result["success"] is True
    assert result["method"] == "FEFO"
    assert result["requested_qty"] == 60
    assert result["allocated_qty"] == 60
    assert result["shortage_qty"] == 0

    assert len(result["allocations"]) == 2

    assert result["allocations"][0]["batch_no"] == "TEA-BATCH-001"
    assert result["allocations"][0]["issue_qty"] == 50

    assert result["allocations"][1]["batch_no"] == "TEA-BATCH-002"
    assert result["allocations"][1]["issue_qty"] == 10

    assert result["total_cost"] == 60500