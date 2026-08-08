# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v7.0 FINAL
#
# SETTINGS CONTROLLED OWNER FIRST PRICING
#
# Priority:
#
# Owner Selling Price
#        ↓
# Product Markup
#        ↓
# Category Markup
#        ↓
# Global / Default Markup
#
# ==============================================================================


from decimal import (
    Decimal,
    ROUND_HALF_UP
)


from ..base_repo import (
    log_error
)


from ..config import (
    Tables
)


from .settings_service import (
    SettingsService
)



# ==============================================================================
# SAFE NUMBER
# ==============================================================================


def safe_decimal(value):

    try:

        return Decimal(
            str(value)
        )

    except Exception:

        return Decimal("0")





# ==============================================================================
# PRICING SERVICE
# ==============================================================================


class PricingService:



    # ==========================================================================
    # INIT
    # ==========================================================================


    def __init__(

        self,

        client

    ):


        self.client = client


        self.settings_service = SettingsService(
            client
        )


        self.cache = {}




    # ==========================================================================
    # SETTINGS
    # ==========================================================================


    def get_setting(

        self,

        key,

        default=None

    ):


        try:

            value = self.settings_service.get_setting(
                key
            )


            if value is None:

                return default


            return value



        except Exception as e:


            log_error(

                message="Pricing setting error",

                exception=e

            )


            return default


    # ==========================================================================
    # SIMPLE COMPATIBILITY METHOD
    #
    # Used by:
    # - pages/2_Inventory.py
    # - tests/test_pricing_engine.py
    #
    # Contract:
    # - Returns float selling price
    # - Supports product_id
    # - Supports category_id
    # - Rejects negative cost
    # - Zero cost returns 0
    # ==========================================================================

    def calculate_selling_price(
        self,
        cost,
        product_id=None,
        category_id=None,
        product=None
    ):

        # ----------------------------------------------------------------------
        # VALIDATE COST
        # ----------------------------------------------------------------------

        cost_decimal = safe_decimal(cost)

        if cost_decimal < 0:

            raise ValueError(
                "Cost cannot be negative."
            )

        # ----------------------------------------------------------------------
        # LOAD PRODUCT
        # ----------------------------------------------------------------------

        if product is None and product_id is not None:

            product = self.get_product_markup(
                product_id
            )

        product = product or {}

        # ----------------------------------------------------------------------
        # CATEGORY ID
        #
        # If product already contains category_id, use it.
        # Explicit category_id has priority when supplied.
        # ----------------------------------------------------------------------

        if category_id is not None:

            product = dict(product)

            product["category_id"] = category_id

        # ----------------------------------------------------------------------
        # ZERO COST
        # ----------------------------------------------------------------------

        if cost_decimal == 0:

            return 0.0

        # ----------------------------------------------------------------------
        # CALCULATE
        # ----------------------------------------------------------------------

        result = self.calculate_price(
            product_id=product_id,
            base_price=cost_decimal,
            product=product
        )

        # ----------------------------------------------------------------------
        # RETURN ONLY SELLING PRICE
        #
        # calculate_price() internally keeps:
        # - price
        # - markup
        # - source
        #
        # Compatibility method returns only float.
        # ----------------------------------------------------------------------

        return float(
            result["price"]
        )

    # ==========================================================================
    # FINAL PRICE CALCULATION
    #
    # OWNER FIRST ENGINE
    # ==========================================================================

    def calculate_price(
        self,
        product_id,
        base_price,
        product=None
    ):

        try:

            cost = safe_decimal(base_price)

            if product is None and product_id:
                product = self.get_product_markup(product_id)

            product = product or {}

            # 1. Owner price
            pricing_method = self.get_setting(
                "PRICING_METHOD",
                "OWNER_FIRST"
            )

            if pricing_method == "OWNER_FIRST":

                owner_price = safe_decimal(
                    product.get("owner_selling_price")
                )

                owner_locked = product.get(
                    "owner_price_locked",
                    False
                )

                if owner_price > 0 or owner_locked:

                    return {
                        "price": owner_price.quantize(
                            Decimal("0.01"),
                            rounding=ROUND_HALF_UP
                        ),
                        "markup": Decimal("0"),
                        "source": "OWNER_PRICE"
                    }

            # 2. Product markup
            markup = product.get("markup_percent")

            if markup is not None:

                markup = safe_decimal(markup)

                final_price = cost * (
                    Decimal("1") + (markup / Decimal("100"))
                )

                return {
                    "price": final_price.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    ),
                    "markup": markup,
                    "source": "PRODUCT_MARKUP"
                }

            # 3. Category markup
            category_markup = self.get_category_markup(
                product.get("category_id")
            )

            if category_markup is not None:

                markup = safe_decimal(category_markup)

                final_price = cost * (
                    Decimal("1") + (markup / Decimal("100"))
                )

                return {
                    "price": final_price.quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP
                    ),
                    "markup": markup,
                    "source": "CATEGORY_MARKUP"
                }

            # 4. Default markup
            markup = self.get_global_markup()

            final_price = cost * (
                Decimal("1") + (markup / Decimal("100"))
            )

            return {
                "price": final_price.quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP
                ),
                "markup": markup,
                "source": "DEFAULT"
            }

        except Exception as e:

            log_error(
                message="Final price calculation failed",
                exception=e
            )

            return {
                "price": safe_decimal(base_price),
                "markup": Decimal("0"),
                "source": "ERROR"
        }

# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "PricingService"

]
