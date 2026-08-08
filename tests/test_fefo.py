# ==============================================================================
# tests/test_fefo.py
# ERP ENTERPRISE FEFO TEST v1
#
# Test:
# - Batch tracking
# - Expiry tracking
# - FEFO ordering
# - Partial batch allocation
# - FEFO COGS calculation
#
# IMPORTANT:
# This test DOES NOT modify stock.
# ==============================================================================


from database import db

from erp_core.services.inventory_service import (
    InventoryService
)


# ==============================================================================
# FEFO ISSUE PLAN TEST
# ==============================================================================


def test_fefo_issue_plan():

    # --------------------------------------------------------------------------
    # SERVICE
    # --------------------------------------------------------------------------

    service = InventoryService(
        db()
    )


    # --------------------------------------------------------------------------
    # REQUEST 60 PCS
    # --------------------------------------------------------------------------

    result = service.get_fefo_issue_plan(

        product_id=4,

        warehouse_id=1,

        issue_quantity=60

    )


    # --------------------------------------------------------------------------
    # DEBUG OUTPUT
    # --------------------------------------------------------------------------

    print()

    print(
        "========== FEFO TEST RESULT =========="
    )

    print(
        result
    )

    print(
        "======================================="
    )


    # --------------------------------------------------------------------------
    # BASIC RESULT
    # --------------------------------------------------------------------------

    assert result["success"] is True

    assert result["method"] == "FEFO"

    assert result["requested_qty"] == 60

    assert result["allocated_qty"] == 60

    assert result["shortage_qty"] == 0


    # --------------------------------------------------------------------------
    # ALLOCATION COUNT
    # --------------------------------------------------------------------------

    allocations = result["allocations"]

    assert len(
        allocations
    ) == 2


    # --------------------------------------------------------------------------
    # FIRST BATCH
    # --------------------------------------------------------------------------

    first = allocations[0]


    assert first["batch_no"] == (
        "TEA-BATCH-001"
    )

    assert first["expiry_date"] == (
        "2026-09-01"
    )

    assert first["available_qty"] == 50

    assert first["issue_qty"] == 50

    assert first["remaining_qty"] == 0

    assert first["unit_cost"] == 1000

    assert first["line_cost"] == 50000


    # --------------------------------------------------------------------------
    # SECOND BATCH
    # --------------------------------------------------------------------------

    second = allocations[1]


    assert second["batch_no"] == (
        "TEA-BATCH-002"
    )

    assert second["expiry_date"] == (
        "2026-10-01"
    )

    assert second["available_qty"] == 80

    assert second["issue_qty"] == 10

    assert second["remaining_qty"] == 70

    assert second["unit_cost"] == 1050

    assert second["line_cost"] == 10500


    # --------------------------------------------------------------------------
    # TOTAL COGS
    # --------------------------------------------------------------------------

    assert result["total_cost"] == 60500


    # --------------------------------------------------------------------------
    # FINAL TOTAL
    # --------------------------------------------------------------------------

    total_issue = sum(

        item["issue_qty"]

        for item in allocations

    )


    assert total_issue == 60
