# ==============================================================================
# tests/test_inventory_service.py
#
# ERP ENTERPRISE - INVENTORY SERVICE SMOKE TEST
#
# NOTE:
# This is a temporary placeholder test.
# Full Inventory / FEFO / FIFO tests will be rebuilt
# after the ERP core architecture is stable.
# ==============================================================================

from erp_core.services.inventory_service import InventoryService


def test_inventory_service_import():

    assert InventoryService is not None


def test_inventory_service_can_be_created():

    class FakeClient:
        pass

    service = InventoryService(FakeClient())

    assert service is not None
