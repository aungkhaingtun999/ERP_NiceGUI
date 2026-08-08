# ==============================================================================
# tests/test_fefo.py
# ERP ENTERPRISE FEFO TEST v2.0
#
# CI/CD SAFE UNIT TEST
#
# Tests:
# - Batch tracking
# - Expiry tracking
# - FEFO ordering
# - Partial batch allocation
# - FEFO COGS calculation
# - Insufficient stock
# - Batch disabled
# - Expiry disabled
# - Invalid issue quantity
# - Expiry ordering
#
# IMPORTANT:
# - No Supabase connection
# - No database modification
# - No Streamlit secrets required
# - Uses mocked InventoryService dependencies
# ==============================================================================


from erp_core.services.inventory_service import InventoryService


# ==============================================================================
# MOCK CLIENT
# ==============================================================================


class MockQuery:

    def __init__(self, data):
        self.data = data

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def gt(self, *args, **kwargs):
        return self

    def not_(self):
        return self

    def is_(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        return MockResponse(self.data)


class MockResponse:

    def __init__(self, data):
        self.data = data


class MockClient:

    def table(self, table_name):
        return MockQuery([])


# ==============================================================================
# TEST SERVICE FACTORY
# ==============================================================================


def make_service():

    return InventoryService(
        MockClient()
    )


# ==============================================================================
# MOCK PRODUCT SETTINGS
# ==============================================================================


def enable_fefo(service):

    service.get_product_batch_settings = lambda product_id: {
        "success": True,
        "product_id": product_id,
        "product_name": "Milk Tea",
        "track_batches": True,
        "track_expiry": True,
        "shelf_life_days": 90,
    }


def disable_batches(service):

    service.get_product_batch_settings = lambda product_id: {
        "success": True,
        "product_id": product_id,
        "product_name": "Milk Tea",
        "track_batches": False,
        "track_expiry": False,
        "shelf_life_days": 0,
    }


def disable_expiry(service):

    service.get_product_batch_settings = lambda product_id: {
        "success": True,
        "product_id": product_id,
        "product_name": "Milk Tea",
        "track_batches": True,
        "track_expiry": False,
        "shelf_life_days": 0,
    }


# ==============================================================================
# MOCK BATCHES
# ==============================================================================


def standard_batches():

    return [

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


# ==============================================================================
# FEFO ISSUE PLAN
# ==============================================================================


def test_fefo_issue_plan():

    service = make_service()

    enable_fefo(service)

    service.get_fefo_batches = lambda product_id, warehouse_id: (
        standard_batches()
    )

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

    service.get_fefo_batches = lambda product_id, warehouse_id: (
        standard_batches()
    )

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )

    allocations = result["allocations"]

    assert len(allocations) == 2


# ==============================================================================
# FIRST EXPIRING BATCH
# ==============================================================================


def test_fefo_first_batch():

    service = make_service()

    enable_fefo(service)

    service.get_fefo_batches = lambda product_id, warehouse_id: (
        standard_batches()
    )

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )

    first = result["allocations"][0]

    assert first["batch_no"] == "TEA-BATCH-001"

    assert first["expiry_date"] == "2026-09-01"

    assert first["available_qty"] == 50

    assert first["issue_qty"] == 50

    assert first["remaining_qty"] == 0

    assert first["unit_cost"] == 1000

    assert first["line_cost"] == 50000


# ==============================================================================
# SECOND BATCH PARTIAL ALLOCATION
# ==============================================================================


def test_fefo_second_batch_partial_allocation():

    service = make_service()

    enable_fefo(service)

    service.get_fefo_batches = lambda product_id, warehouse_id: (
        standard_batches()
    )

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )

    second = result["allocations"][1]

    assert second["batch_no"] == "TEA-BATCH-002"

    assert second["expiry_date"] == "2026-10-01"

    assert second["available_qty"] == 80

    assert second["issue_qty"] == 10

    assert second["remaining_qty"] == 70

    assert second["unit_cost"] == 1050

    assert second["line_cost"] == 10500


# ==============================================================================
# FEFO TOTAL COGS
# ==============================================================================


def test_fefo_total_cogs():

    service = make_service()

    enable_fefo(service)

    service.get_fefo_batches = lambda product_id, warehouse_id: (
        standard_batches()
    )

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

    service.get_fefo_batches = lambda product_id, warehouse_id: (
        standard_batches()
    )

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )

    total_issue = sum(
        item["issue_qty"]
        for item in result["allocations"]
    )

    assert total_issue == 60


# ==============================================================================
# FEFO ORDERING
# ==============================================================================


def test_fefo_uses_earliest_expiry_first():

    service = make_service()

    enable_fefo(service)

    # Deliberately provide batches in the WRONG order.
    batches = [

        {
            "id": 2,
            "batch_no": "LATER",
            "expiry_date": "2026-10-01",
            "quantity": 80,
            "unit_cost": 1050,
        },

        {
            "id": 1,
            "batch_no": "EARLIER",
            "expiry_date": "2026-09-01",
            "quantity": 50,
            "unit_cost": 1000,
        },
    ]

    service.get_fefo_batches = lambda product_id, warehouse_id: batches

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=10,
    )

    first = result["allocations"][0]

    assert first["batch_no"] == "EARLIER"

    assert first["issue_qty"] == 10


# ==============================================================================
# INSUFFICIENT STOCK
# ==============================================================================


def test_fefo_insufficient_stock():

    service = make_service()

    enable_fefo(service)

    service.get_fefo_batches = lambda product_id, warehouse_id: (
        standard_batches()
    )

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=200,
    )

    assert result["success"] is False

    assert result["method"] == "FEFO"

    assert result["requested_qty"] == 200

    assert result["allocated_qty"] == 130

    assert result["shortage_qty"] == 70


# ==============================================================================
# BATCH TRACKING DISABLED
# ==============================================================================


def test_fefo_batch_tracking_disabled():

    service = make_service()

    disable_batches(service)

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=10,
    )

    assert result["success"] is False

    assert result["method"] == "SIMPLE_OR_FIFO"

    assert result["allocations"] == []


# ==============================================================================
# EXPIRY TRACKING DISABLED
# ==============================================================================


def test_fefo_expiry_tracking_disabled():

    service = make_service()

    disable_expiry(service)

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=10,
    )

    assert result["success"] is False

    assert result["method"] == "BATCH_FIFO"

    assert result["allocations"] == []


# ==============================================================================
# INVALID ISSUE QUANTITY
# ==============================================================================


def test_fefo_zero_quantity():

    service = make_service()

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=0,
    )

    assert result["success"] is False

    assert "greater than zero" in result["message"]


def test_fefo_negative_quantity():

    service = make_service()

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=-10,
    )

    assert result["success"] is False

    assert "greater than zero" in result["message"]


# ==============================================================================
# NO FEFO BATCHES
# ==============================================================================


def test_fefo_no_batches():

    service = make_service()

    enable_fefo(service)

    service.get_fefo_batches = lambda product_id, warehouse_id: []

    result = service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=10,
    )

    assert result["success"] is False

    assert result["method"] == "FEFO"

    assert result["allocations"] == []


# ==============================================================================
# NO STOCK MODIFICATION TEST
# ==============================================================================


def test_fefo_does_not_modify_batch_data():

    service = make_service()

    enable_fefo(service)

    batches = standard_batches()

    service.get_fefo_batches = lambda product_id, warehouse_id: batches

    before = [
        dict(batch)
        for batch in batches
    ]

    service.get_fefo_issue_plan(
        product_id=4,
        warehouse_id=1,
        issue_quantity=60,
    )

    assert batches == before
