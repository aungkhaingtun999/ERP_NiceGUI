# ==============================================================================
# tests/test_fefo.py
#
# ERP ENTERPRISE - FEFO SMOKE TEST
#
# NOTE:
# Temporary placeholder only.
# Full FEFO tests will be rebuilt after Inventory / RPC architecture freezes.
# ==============================================================================

from erp_core.services.inventory_service import InventoryService


def test_fefo_service_import():

    assert InventoryService is not None


def test_fefo_method_exists():

    assert hasattr(
        InventoryService,
        "get_fefo_issue_plan"
    )
