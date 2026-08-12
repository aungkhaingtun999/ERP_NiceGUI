# ==============================================================================
# tests/test_pricing_engine.py
#
# ERP ENTERPRISE - PRICING ENGINE SMOKE TEST
#
# NOTE:
# Temporary placeholder only.
# Full pricing business-rule tests will be rebuilt later.
# ==============================================================================

from erp_core.services.pricing_service import PricingService


def test_pricing_service_import():

    assert PricingService is not None


def test_pricing_method_exists():

    assert hasattr(
        PricingService,
        "calculate_selling_price"
    )
