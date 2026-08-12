# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v8.0
#
# SETTINGS CONTROLLED PRICING ENGINE
#
# Canonical Settings Source:
#     public.settings
#
# Supported:
#
#   PRICING_METHOD
#       MARKUP
#       MARGIN
#
#   PRICING_PRIORITY
#       OWNER_FIRST
#       PRODUCT_FIRST
#       CATEGORY_FIRST
#
#   ENABLE_PRODUCT_MARKUP
#   ENABLE_CATEGORY_MARKUP
#   ALLOW_MANUAL_PRICE_OVERRIDE
#
# Pricing Flow:
#
#   OWNER_FIRST
#       Owner Price
#       -> Product Markup
#       -> Category Markup
#       -> Global Markup
#
#   PRODUCT_FIRST
#       Product Markup
#       -> Category Markup
#       -> Global Markup
#
#   CATEGORY_FIRST
#       Category Markup
#       -> Product Markup
#       -> Global Markup
#
# IMPORTANT:
# - This service calculates prices only.
# - It does NOT directly update products.
# - Normal setting changes remain Maker-Checker controlled.
# ==============================================================================


from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional


from ..base_repo import (
    log_error,
)

from .settings_service import (
    SettingsService,
)


# ==============================================================================
# CONSTANTS
# ==============================================================================

PRICE_QUANTUM = Decimal("0.01")

DEFAULT_PRICING_METHOD = "MARKUP"
DEFAULT_PRICING_PRIORITY = "OWNER_FIRST"

DEFAULT_GLOBAL_MARKUP = Decimal("20")

DEFAULT_PRODUCT_MARKUP = Decimal("15")

DEFAULT_CATEGORY_MARKUP = Decimal("20")


# ==============================================================================
# SAFE NUMBER
# ==============================================================================


def safe_decimal(value, default=Decimal("0")):
    """
    Safely convert a value to Decimal.

    Invalid values return the supplied default.
    """

    try:

        if value is None:

            return default

        return Decimal(str(value).strip())

    except Exception:

        return default


# ==============================================================================
# NORMALIZE BOOLEAN
# ==============================================================================


def safe_bool(value, default=False):
    """
    Convert common database/settings values to bool.
    """

    if value is None:

        return default

    if isinstance(value, bool):

        return value

    text = str(value).strip().lower()

    if text in (
        "true",
        "1",
        "yes",
        "y",
        "on",
    ):

        return True

    if text in (
        "false",
        "0",
        "no",
        "n",
        "off",
    ):

        return False

    return default


# ==============================================================================
# ROUND PRICE
# ==============================================================================


def _round_price(value):
    """
    ERP selling price rounding.
    """

    return safe_decimal(value).quantize(
        PRICE_QUANTUM,
        rounding=ROUND_HALF_UP,
    )


# ==============================================================================
# PRICING SERVICE
# ==============================================================================


class PricingService:

    # ==========================================================================
    # INIT
    # ==========================================================================

    def __init__(self, client):

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
        default=None,
    ):
        """
        Read setting from canonical public.settings
        through SettingsService.
        """

        try:

            value = self.settings_service.get_setting(
                key,
                default,
            )

            if value is None:

                return default

            return value

        except Exception as e:

            log_error(
                message="Pricing setting error",
                exception=e,
            )

            return default

    # ==========================================================================
    # BOOLEAN SETTINGS
    # ==========================================================================

    def get_bool_setting(
        self,
        key,
        default=False,
    ):

        return safe_bool(
            self.get_setting(
                key,
                default,
            ),
            default,
        )

    # ==========================================================================
    # MARKUP SETTINGS
    # ==========================================================================

    def get_global_markup(self):

        return max(
            Decimal("0"),
            safe_decimal(
                self.get_setting(
                    "DEFAULT_MARKUP_PERCENT",
                    DEFAULT_GLOBAL_MARKUP,
                ),
                DEFAULT_GLOBAL_MARKUP,
            ),
        )

    # ==========================================================================
    # PRODUCT DEFAULT MARKUP
    # ==========================================================================

    def get_product_default_markup(self):

        return max(
            Decimal("0"),
            safe_decimal(
                self.get_setting(
                    "PRODUCT_MARKUP_PERCENT",
                    DEFAULT_PRODUCT_MARKUP,
                ),
                DEFAULT_PRODUCT_MARKUP,
            ),
        )

    # ==========================================================================
    # CATEGORY DEFAULT MARKUP
    # ==========================================================================

    def get_category_default_markup(self):

        return max(
            Decimal("0"),
            safe_decimal(
                self.get_setting(
                    "CATEGORY_MARKUP_PERCENT",
                    DEFAULT_CATEGORY_MARKUP,
                ),
                DEFAULT_CATEGORY_MARKUP,
            ),
        )

    # ==========================================================================
    # PRODUCT
    # ==========================================================================

    def get_product_markup(
        self,
        product_id,
    ) -> Dict[str, Any]:
        """
        Load product pricing information.

        Expected product fields where available:

            id
            category_id
            markup_percent
            owner_selling_price
            owner_price_locked
        """

        if product_id is None:

            return {}

        cache_key = f"product:{product_id}"

        if cache_key in self.cache:

            return self.cache[cache_key]

        try:

            result = (
                self.client
                .table("products")
                .select("*")
                .eq("id", product_id)
                .limit(1)
                .execute()
            )

            rows = result.data or []

            if not rows:

                return {}

            product = rows[0]

            self.cache[cache_key] = product

            return product

        except Exception as e:

            log_error(
                message="Product pricing load failed",
                exception=e,
            )

            return {}

    # ==========================================================================
    # CATEGORY MARKUP
    # ==========================================================================

    def get_category_markup(
        self,
        category_id,
    ) -> Optional[Decimal]:
        """
        Load category markup_percent.

        If category table or markup column is unavailable,
        return None so pricing can continue to the next rule.
        """

        if category_id is None:

            return None

        cache_key = f"category:{category_id}"

        if cache_key in self.cache:

            return self.cache[cache_key]

        try:

            result = (
                self.client
                .table("categories")
                .select("*")
                .eq("id", category_id)
                .limit(1)
                .execute()
            )

            rows = result.data or []

            if not rows:

                return None

            category = rows[0]

            markup = category.get(
                "markup_percent"
            )

            if markup is None:

                return None

            markup = max(
                Decimal("0"),
                safe_decimal(markup),
            )

            self.cache[cache_key] = markup

            return markup

        except Exception as e:

            # Category markup is optional.
            # Do not break the whole pricing engine.
            log_error(
                message="Category pricing load failed",
                exception=e,
            )

            return None

    # ==========================================================================
    # MARKUP CALCULATION
    # ==========================================================================

    def _calculate_markup_price(
        self,
        cost,
        markup,
    ):

        cost = safe_decimal(cost)

        markup = safe_decimal(markup)

        if cost < 0:

            raise ValueError(
                "Cost cannot be negative."
            )

        if markup < 0:

            markup = Decimal("0")

        return _round_price(
            cost
            * (
                Decimal("1")
                + (
                    markup
                    / Decimal("100")
                )
            )
        )

    # ==========================================================================
    # MARGIN CALCULATION
    # ==========================================================================

    def _calculate_margin_price(
        self,
        cost,
        margin,
    ):
        """
        Calculate selling price from target margin.

        Example:

            Cost = 100
            Margin = 20%

            Selling Price =
                100 / (1 - 0.20)
                = 125
        """

        cost = safe_decimal(cost)

        margin = safe_decimal(margin)

        if cost < 0:

            raise ValueError(
                "Cost cannot be negative."
            )

        if margin < 0:

            margin = Decimal("0")

        if margin >= Decimal("100"):

            raise ValueError(
                "Margin must be below 100%."
            )

        divisor = (
            Decimal("1")
            - (
                margin
                / Decimal("100")
            )
        )

        return _round_price(
            cost / divisor
        )

    # ==========================================================================
    # CALCULATE FROM PERCENT
    # ==========================================================================

    def _calculate_from_percent(
        self,
        cost,
        percent,
    ):
        """
        Apply the configured pricing method.

        MARKUP:
            Cost + percentage

        MARGIN:
            Target margin percentage
        """

        method = str(
            self.get_setting(
                "PRICING_METHOD",
                DEFAULT_PRICING_METHOD,
            )
        ).strip().upper()

        if method == "MARGIN":

            return self._calculate_margin_price(
                cost,
                percent,
            )

        return self._calculate_markup_price(
            cost,
            percent,
        )

    # ==========================================================================
    # OWNER PRICE
    # ==========================================================================

    def _get_owner_price(
        self,
        product,
    ):
        """
        Return owner selling price only when manual override
        is permitted.

        ALLOW_MANUAL_PRICE_OVERRIDE controls whether owner
        selling price can participate in normal pricing.
        """

        if not self.get_bool_setting(
            "ALLOW_MANUAL_PRICE_OVERRIDE",
            True,
        ):

            return None

        owner_price = safe_decimal(
            product.get(
                "owner_selling_price"
            )
        )

        if owner_price <= 0:

            return None

        return _round_price(
            owner_price
        )

    # ==========================================================================
    # PRODUCT MARKUP
    # ==========================================================================

    def _get_product_markup(
        self,
        product,
    ):
        """
        Return product-level markup if enabled.

        If product has no explicit markup_percent,
        use PRODUCT_MARKUP_PERCENT as the product default.
        """

        if not self.get_bool_setting(
            "ENABLE_PRODUCT_MARKUP",
            True,
        ):

            return None

        if product.get(
            "markup_percent"
        ) is not None:

            markup = safe_decimal(
                product.get(
                    "markup_percent"
                )
            )

            if markup >= 0:

                return markup

        return self.get_product_default_markup()

    # ==========================================================================
    # CATEGORY MARKUP
    # ==========================================================================

    def _get_category_markup(
        self,
        product,
    ):
        """
        Return category-level markup if enabled.
        """

        if not self.get_bool_setting(
            "ENABLE_CATEGORY_MARKUP",
            True,
        ):

            return None

        category_id = product.get(
            "category_id"
        )

        category_markup = (
            self.get_category_markup(
                category_id
            )
        )

        if category_markup is not None:

            return category_markup

        return self.get_category_default_markup()

    # ==========================================================================
    # FINAL PRICE CALCULATION
    # ==========================================================================

    def calculate_price(
        self,
        product_id,
        base_price,
        product=None,
    ) -> Dict[str, Any]:
        """
        Calculate final selling price.

        Returns:

            {
                "price": Decimal,
                "markup": Decimal,
                "source": str
            }
        """

        try:

            cost = safe_decimal(
                base_price
            )

            if cost < 0:

                raise ValueError(
                    "Cost cannot be negative."
                )

            if product is None and product_id:

                product = self.get_product_markup(
                    product_id
                )

            product = dict(
                product or {}
            )

            # ------------------------------------------------------------------
            # ZERO COST
            # ------------------------------------------------------------------

            if cost == 0:

                return {
                    "price": Decimal("0.00"),
                    "markup": Decimal("0"),
                    "source": "ZERO_COST",
                }

            # ------------------------------------------------------------------
            # SETTINGS
            # ------------------------------------------------------------------

            priority = str(
                self.get_setting(
                    "PRICING_PRIORITY",
                    DEFAULT_PRICING_PRIORITY,
                )
            ).strip().upper()

            if priority not in (
                "OWNER_FIRST",
                "PRODUCT_FIRST",
                "CATEGORY_FIRST",
            ):

                priority = DEFAULT_PRICING_PRIORITY

            # ------------------------------------------------------------------
            # OWNER FIRST
            # ------------------------------------------------------------------

            owner_price = self._get_owner_price(
                product
            )

            if (
                priority == "OWNER_FIRST"
                and owner_price is not None
            ):

                return {
                    "price": owner_price,
                    "markup": Decimal("0"),
                    "source": "OWNER_PRICE",
                }

            # ------------------------------------------------------------------
            # BUILD MARKUP ORDER
            # ------------------------------------------------------------------

            if priority == "CATEGORY_FIRST":

                rules = [
                    (
                        "CATEGORY_MARKUP",
                        self._get_category_markup(product),
                    ),
                    (
                        "PRODUCT_MARKUP",
                        self._get_product_markup(product),
                    ),
                ]

            else:

                rules = [
                    (
                        "PRODUCT_MARKUP",
                        self._get_product_markup(product),
                    ),
                    (
                        "CATEGORY_MARKUP",
                        self._get_category_markup(product),
                    ),
                ]

            # ------------------------------------------------------------------
            # PRODUCT / CATEGORY
            # ------------------------------------------------------------------

            for source, markup in rules:

                if markup is None:

                    continue

                price = self._calculate_from_percent(
                    cost,
                    markup,
                )

                return {
                    "price": price,
                    "markup": markup,
                    "source": source,
                }

            # ------------------------------------------------------------------
            # GLOBAL MARKUP
            # ------------------------------------------------------------------

            global_markup = (
                self.get_global_markup()
            )

            price = self._calculate_from_percent(
                cost,
                global_markup,
            )

            return {
                "price": price,
                "markup": global_markup,
                "source": "GLOBAL_MARKUP",
            }

        except Exception as e:

            log_error(
                message="Final price calculation failed",
                exception=e,
            )

            return {
                "price": _round_price(
                    safe_decimal(base_price)
                ),
                "markup": Decimal("0"),
                "source": "ERROR",
            }

    # ==========================================================================
    # SIMPLE COMPATIBILITY METHOD
    # ==========================================================================

    def calculate_selling_price(
        self,
        cost,
        product_id=None,
        category_id=None,
        product=None,
    ) -> float:
        """
        Compatibility API.

        Returns only the final selling price as float.

        Supports:

            calculate_selling_price(cost)

            calculate_selling_price(
                cost,
                product_id=123
            )

            calculate_selling_price(
                cost,
                category_id=5
            )

            calculate_selling_price(
                cost,
                product={...}
            )
        """

        cost_decimal = safe_decimal(
            cost
        )

        if cost_decimal < 0:

            raise ValueError(
                "Cost cannot be negative."
            )

        if cost_decimal == 0:

            return 0.0

        # ----------------------------------------------------------------------
        # LOAD PRODUCT
        # ----------------------------------------------------------------------

        if product is None and product_id is not None:

            product = self.get_product_markup(
                product_id
            )

        product = dict(
            product or {}
        )

        # ----------------------------------------------------------------------
        # EXPLICIT CATEGORY
        # ----------------------------------------------------------------------

        if category_id is not None:

            product["category_id"] = (
                category_id
            )

        result = self.calculate_price(
            product_id=product_id,
            base_price=cost_decimal,
            product=product,
        )

        return float(
            result["price"]
        )

    # ==========================================================================
    # PRICE DETAILS
    # ==========================================================================

    def calculate_price_details(
        self,
        cost,
        product_id=None,
        category_id=None,
        product=None,
    ) -> Dict[str, Any]:
        """
        Detailed pricing API.

        Useful for:
            - Inventory
            - Product Create
            - Product Edit
            - POS
            - Reports
            - Debugging
        """

        cost_decimal = safe_decimal(
            cost
        )

        if cost_decimal < 0:

            raise ValueError(
                "Cost cannot be negative."
            )

        if product is None and product_id is not None:

            product = self.get_product_markup(
                product_id
            )

        product = dict(
            product or {}
        )

        if category_id is not None:

            product["category_id"] = (
                category_id
            )

        result = self.calculate_price(
            product_id=product_id,
            base_price=cost_decimal,
            product=product,
        )

        return {
            "cost": cost_decimal,
            "price": result["price"],
            "markup": result["markup"],
            "source": result["source"],
            "pricing_method": str(
                self.get_setting(
                    "PRICING_METHOD",
                    DEFAULT_PRICING_METHOD,
                )
            ).upper(),
            "pricing_priority": str(
                self.get_setting(
                    "PRICING_PRIORITY",
                    DEFAULT_PRICING_PRIORITY,
                )
            ).upper(),
        }

    # ==========================================================================
    # CACHE CLEAR
    # ==========================================================================

    def clear_cache(self):

        self.cache.clear()


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "PricingService",
    "safe_decimal",
]
