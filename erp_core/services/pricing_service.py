# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v6.0 FINAL
#
# Settings Controlled Pricing Engine
#
# Flow:
#
# Product Markup
#        ↓
# Category Markup
#        ↓
# Global Markup
#
# ==============================================================================

from decimal import Decimal, ROUND_HALF_UP
import time

from ..base_repo import log_error
from ..config import Tables
from .settings_service import SettingsService


# ==============================================================================
# PRICING SERVICE
# ==============================================================================


class PricingService:

    # ==========================================================================
    # INIT
    # ==========================================================================

    def __init__(self, client):
        self.client = client
        self.settings_service = SettingsService(client)
        self.cache = {}
        self.cache_time = 0
        self.cache_ttl = 300

    # ==========================================================================
    # SAFE QUERY
    # ==========================================================================

    def query(self, table, select="*", filters=None):
        try:
            q = self.client.table(table).select(select)

            if filters:
                for key, value in filters.items():
                    q = q.eq(key, value)

            result = q.execute()
            return result.data or []

        except Exception as e:
            log_error(message=f"Pricing query failed {table}", exception=e)
            return []

    # ==========================================================================
    # SETTINGS
    # ==========================================================================

    def get_setting(self, key):
        return self.settings_service.get_setting(key)

    # ==========================================================================
    # PRODUCT MARKUP
    # ==========================================================================

    def get_product_markup(self, product_id):
        try:
            rows = self.query(
                Tables.PRODUCTS,
                """
                id,
                name,
                markup_percent,
                category_id,
                owner_price
                """,
                {"id": product_id},
            )

            if rows:
                return rows[0]

        except Exception as e:
            log_error(message="Product markup load failed", exception=e)

        return {
            "id": product_id,
            "name": "",
            "markup_percent": None,
            "category_id": None,
            "owner_price": None,
        }

    # ==========================================================================
    # CATEGORY MARKUP
    # ==========================================================================

    def get_category_markup(self, category_id):
        if not category_id:
            return {"name": None, "markup_percent": None}

        try:
            rows = self.query(
                Tables.CATEGORIES,
                """
                name,
                markup_percent
                """,
                {"id": category_id},
            )

            if rows:
                return rows[0]

        except Exception as e:
            log_error(message="Category markup load failed", exception=e)

        return {"name": None, "markup_percent": None}

    # ==========================================================================
    # GLOBAL MARKUP & FINAL PRICE CALCULATION
    # ==========================================================================

    def get_global_markup(self):
        try:
            global_markup = self.get_setting("global_markup_percent")
            if global_markup is not None:
                return Decimal(str(global_markup))
        except Exception as e:
            log_error(message="Global markup load failed", exception=e)
        return Decimal("0.00")

    def calculate_price(self, product_id, base_price):
        try:
            base_decimal = Decimal(str(base_price))

            # 1. Product Markup
            product_data = self.get_product_markup(product_id)
            markup = product_data.get("markup_percent")

            # 2. Category Markup (if product markup is not set)
            if markup is None and product_data.get("category_id"):
                category_data = self.get_category_markup(product_data["category_id"])
                markup = category_data.get("markup_percent")

            # 3. Global Markup (if both product and category markups are not set)
            if markup is None:
                markup = self.get_global_markup()

            markup_decimal = Decimal(str(markup))

            # Final Price Calculation using ROUND_HALF_UP
            final_price = base_decimal * (
                Decimal("1") + (markup_decimal / Decimal("100"))
            )
            return final_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        except Exception as e:
            log_error(
                message=f"Price calculation failed for product {product_id}",
                exception=e,
            )
            return Decimal(str(base_price))

    # ==========================================================================
    # SIMPLE PRICE CALCULATION (COMPATIBILITY METHOD)
    # ==========================================================================

    def calculate_selling_price(
        self,
        cost,
        product_id=None
    ):

        cost = Decimal(str(cost or 0))

        method = str(
            self.get_setting(
                "PRICING_METHOD"
            )
            or "MARKUP"
        ).upper()

        # ==================================================
        # OWNER PRICE FIRST
        # ==================================================

        if method == "OWNER_FIRST" and product_id:

            product = self.get_product_markup(
                product_id
            )

            owner_price = product.get(
                "owner_price"
            )

            if owner_price not in (
                None,
                "",
                0
            ):

                return {

                    "selling_price":
                    float(owner_price),

                    "final_markup_percent":
                    0,

                    "markup_source":
                    "OWNER_PRICE"

                }

        # ==================================================
        # PRODUCT / CATEGORY / GLOBAL MARKUP
        # ==================================================

        result = self.calculate_price(
            product_id,
            cost
        )

        final_price = float(result)

        markup = round(
            (
                (final_price - float(cost))
                /
                float(cost)
                *
                100
            ),
            2
        ) if cost else 0

        return {

            "selling_price":
            final_price,

            "final_markup_percent":
            markup,

            "markup_source":
            "MARKUP"

        }
