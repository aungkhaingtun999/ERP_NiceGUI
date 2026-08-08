# ==============================================================================
# tests/test_pricing_engine.py
# ERP ENTERPRISE PRICING ENGINE TEST v2.0 CLEAN
# ==============================================================================

import sys
import os
import pytest

# ------------------------------------------------------------------------------
# PROJECT ROOT
# ------------------------------------------------------------------------------

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from erp_core.services.pricing_service import PricingService


# ==============================================================================
# MOCK SERVICE
# ==============================================================================

class MockPricingService(PricingService):

    def __init__(self):

        # Do not call super().__init__()

        self.settings = {
            "PRICING_METHOD": "MARKUP",
            "DEFAULT_MARKUP_PERCENT": "40",
        }

        self.product_markups = {
            1: {
                "markup_percent": 50,
                "category_id": 10
            }
        }

        self.category_markups = {
            10: 30
        }

    def get_setting(self, key, default=None):
        return self.settings.get(key, default)

    def get_product_markup(self, product_id):
        return self.product_markups.get(product_id, {})

    def get_category_markup(self, category_id):
        return self.category_markups.get(category_id)

    def get_global_markup(self):
        return 40


# ==============================================================================
# GLOBAL MARKUP
# ==============================================================================

def test_global_markup():

    service = MockPricingService()

    price = service.calculate_selling_price(cost=1000)

    assert price == 1400.0


# ==============================================================================
# PRODUCT PRIORITY
# ==============================================================================

def test_product_markup_priority():

    service = MockPricingService()

    price = service.calculate_selling_price(
        cost=1000,
        product_id=1,
        category_id=10
    )

    # Product markup 50% should win
    assert price == 1500.0


# ==============================================================================
# CATEGORY MARKUP
# ==============================================================================

def test_category_markup():

    service = MockPricingService()

    price = service.calculate_selling_price(
        cost=1000,
        category_id=10
    )

    assert price == 1300.0


# ==============================================================================
# DEFAULT MARKUP
# ==============================================================================

def test_default_markup():

    service = MockPricingService()

    price = service.calculate_selling_price(cost=2000)

    assert price == 2800.0


# ==============================================================================
# ROUNDING
# ==============================================================================

def test_price_rounding():

    service = MockPricingService()

    price = service.calculate_selling_price(cost=1234)

    assert price == pytest.approx(1727.6)
    assert isinstance(price, (int, float))


# ==============================================================================
# ZERO COST
# ==============================================================================

def test_zero_cost():

    service = MockPricingService()

    price = service.calculate_selling_price(cost=0)

    assert price == 0


# ==============================================================================
# NEGATIVE COST
# ==============================================================================

def test_negative_cost():

    service = MockPricingService()

    with pytest.raises(ValueError):
        service.calculate_selling_price(cost=-100)


# ==============================================================================
# OWNER PRICE LOCK
# ==============================================================================

def test_owner_price_lock():

    service = MockPricingService()

    price = service.calculate_selling_price(
        cost=1000,
        product={
            "owner_selling_price": 999,
            "owner_price_locked": True
        }
    )

    assert price == 999.0
