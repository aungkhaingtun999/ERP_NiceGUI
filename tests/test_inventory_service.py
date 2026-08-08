# ==============================================================================
# tests/test_inventory_service.py
# ERP ENTERPRISE INVENTORY SERVICE UNIT TEST
#
# Version:
# - No real Supabase connection
# - No Streamlit secrets
# - No database mutation
# - FEFO / Batch logic compatible
# - GitHub Actions / CI friendly
# ==============================================================================

from erp_core.services.inventory_service import InventoryService


# ==============================================================================
# FAKE RESPONSE
# ==============================================================================

class FakeResponse:

    def __init__(self, data=None):
        self.data = data


# ==============================================================================
# FAKE QUERY
#
# Minimal Supabase-like query object used only for unit testing.
# ==============================================================================

class FakeQuery:

    def __init__(self, rows):
        self.rows = rows
        self.result = list(rows)

    def select(self, *args, **kwargs):
        return self

    def eq(self, column, value):
        self.result = [
            row for row in self.result
            if row.get(column) == value
        ]
        return self

    def gt(self, column, value):
        self.result = [
            row for row in self.result
            if float(row.get(column, 0) or 0) > float(value)
        ]
        return self

    def not_(self):
        return self

    def is_(self, column, value):
        if value == "null":
            self.result = [
                row for row in self.result
                if row.get(column) is not None
            ]
        return self

    def order(self, column, desc=False):
        self.result.sort(
            key=lambda row: (
                row.get(column) is None,
                row.get(column)
            ),
            reverse=desc
        )
        return self

    def single(self):
        return self

    def limit(self, value):
        self.result = self.result[:value]
        return self

    def execute(self):
        return FakeResponse(self.result)


# ==============================================================================
# FAKE DATABASE CLIENT
# ==============================================================================

class FakeClient:

    def __init__(self):

        self.products = [
            {
                "id": 4,
                "name": "Milk Tea",
                "track_batches": True,
                "track_expiry": True,
                "shelf_life_days": 90,
            }
        ]

        self.inventory_batches = [
            {
                "id": 1,
                "product_id": 4,
                "warehouse_id": 1,
                "batch_no": "TEA-BATCH-001",
                "manufacturing_date": "2026-07-01",
                "expiry_date": "2026-09-01",
                "quantity": 50,
                "unit_cost": 1000,
            },
            {
                "id": 2,
                "product_id": 4,
                "warehouse_id": 1,
                "batch_no": "TEA-BATCH-002",
                "manufacturing_date": "2026-08-01",
                "expiry_date": "2026-10-01",
                "quantity": 80,
                "unit_cost": 1050,
            },
        ]

    def table(self, table_name):

        if table_name == "products":
            return FakeQuery(self.products)

        if table_name == "inventory_batches":
            return FakeQuery(self.inventory_batches)

        return FakeQuery([])


# ==============================================================================
# FAKE SETTINGS SERVICE
#
# InventoryService creates SettingsService(client).
# This test does not need real settings/database access.
# ==============================================================================

class FakeSettings:

    def get_int(self, key, default=10):
        return default


# ==============================================================================
# SERVICE FIXTURE HELPER
# ==============================================================================

def create_service():

    client = FakeClient()

    service = InventoryService(client)

    # Prevent SettingsService from touching real database.
    service.settings = FakeSettings()

    return service


# ==============================================================================
# TEST 1
# PRODUCT BATCH SETTINGS
# ==============================================================================

def test_product_batch_settings():

    service = create_service()

    result = service.get_product_batch_settings(
        product_id=4
    )

    assert result["success"] is True

    assert result["product_id"] == 4

    assert result["product_name"] == "Milk Tea"

    assert result["track_batches"] is True

    assert result["track_expiry"] is True

    assert result["shelf_life_days"] == 90


# ==============================================================================
# TEST 2
# FEFO BATCH ORDER
# ==============================================================================

def test_fefo_batches_are_sorted_by_expiry():

    service = create_service()

    batches = service.get_fefo_batches(
        product_id=4,
        warehouse_id=1
    )

    assert len(batches) == 2

    assert batches[0]["batch_no"] == "TEA-BATCH-001"

    assert batches[0]["expiry_date"] == "2026-09-01"

    assert batches[1]["batch_no"] == "TEA-BATCH-002"

    assert batches[1]["expiry_date"] == "2026-10-01"


# ==============================================================================
# TEST 3
# FEFO ISSUE PLAN
#
# Request:
#     60 pcs
#
# Batch 001:
#     50 pcs
#
# Batch 002:
#     80 pcs
#
# Expected:
#     50 from Batch 001
#     10 from Batch 002
# ==============================================================================

def test_fefo_issue_plan():

    service = create_service()

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60
    )

    assert result["success"] is True

    assert result["method"] == "FEFO"

    assert result["requested_qty"] == 60

    assert result["allocated_qty"] == 60

    assert result["shortage_qty"] == 0

    allocations = result["allocations"]

    assert len(allocations) == 2


    # --------------------------------------------------------------------------
    # FIRST BATCH
    # --------------------------------------------------------------------------

    first = allocations[0]

    assert first["batch_no"] == "TEA-BATCH-001"

    assert first["expiry_date"] == "2026-09-01"

    assert first["available_qty"] == 50

    assert first["issue_qty"] == 50

    assert first["remaining_qty"] == 0

    assert first["unit_cost"] == 1000

    assert first["line_cost"] == 50000


    # --------------------------------------------------------------------------
    # SECOND BATCH
    # --------------------------------------------------------------------------

    second = allocations[1]

    assert second["batch_no"] == "TEA-BATCH-002"

    assert second["expiry_date"] == "2026-10-01"

    assert second["available_qty"] == 80

    assert second["issue_qty"] == 10

    assert second["remaining_qty"] == 70

    assert second["unit_cost"] == 1050

    assert second["line_cost"] == 10500


    # --------------------------------------------------------------------------
    # TOTAL COGS
    # --------------------------------------------------------------------------

    assert result["total_cost"] == 60500


# ==============================================================================
# TEST 4
# FEFO INSUFFICIENT STOCK
# ==============================================================================

def test_fefo_insufficient_stock():

    service = create_service()

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=200
    )

    assert result["success"] is False

    assert result["method"] == "FEFO"

    assert result["requested_qty"] == 200

    assert result["allocated_qty"] == 130

    assert result["shortage_qty"] == 70

    assert len(result["allocations"]) == 2


# ==============================================================================
# TEST 5
# ZERO ISSUE QUANTITY
# ==============================================================================

def test_fefo_zero_quantity():

    service = create_service()

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=0
    )

    assert result["success"] is False

    assert "greater than zero" in result["message"]


# ==============================================================================
# TEST 6
# NEGATIVE ISSUE QUANTITY
# ==============================================================================

def test_fefo_negative_quantity():

    service = create_service()

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=-10
    )

    assert result["success"] is False

    assert "greater than zero" in result["message"]


# ==============================================================================
# TEST 7
# BATCH TRACKING DISABLED
# ==============================================================================

def test_fefo_rejected_when_batch_tracking_disabled():

    service = create_service()

    service.client.products[0]["track_batches"] = False

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=10
    )

    assert result["success"] is False

    assert result["method"] == "SIMPLE_OR_FIFO"

    assert result["allocations"] == []


# ==============================================================================
# TEST 8
# EXPIRY TRACKING DISABLED
# ==============================================================================

def test_fefo_rejected_when_expiry_tracking_disabled():

    service = create_service()

    service.client.products[0]["track_expiry"] = False

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=10
    )

    assert result["success"] is False

    assert result["method"] == "BATCH_FIFO"

    assert result["allocations"] == []


# ==============================================================================
# TEST 9
# NO AVAILABLE BATCH
# ==============================================================================

def test_fefo_no_available_batch():

    service = create_service()

    service.client.inventory_batches = []

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=10
    )

    assert result["success"] is False

    assert result["method"] == "FEFO"

    assert result["allocations"] == []


# ==============================================================================
# TEST 10
# FEFO DOES NOT MODIFY STOCK
#
# This is important because FEFO v1 is only an allocation planner.
# ==============================================================================

def test_fefo_does_not_modify_stock():

    service = create_service()

    before = [
        dict(batch)
        for batch in service.client.inventory_batches
    ]

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60
    )

    assert result["success"] is True

    after = service.client.inventory_batches

    assert after == before


# ==============================================================================
# END
# ==============================================================================
