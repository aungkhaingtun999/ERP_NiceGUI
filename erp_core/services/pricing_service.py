# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v2.0
# ==============================================================================

from decimal import Decimal


class PricingService:


    def __init__(self, client):

        self.client = client



    # --------------------------------------------------------------------------
    # GET SETTING
    # --------------------------------------------------------------------------

    def get_setting(self, key, default=None):

        result = (
            self.client
            .table("settings")
            .select("value")
            .eq("key", key)
            .execute()
        )

        if result.data:
            return result.data[0]["value"]

        return default



    # --------------------------------------------------------------------------
    # GET PRODUCT PRICING INFO
    # --------------------------------------------------------------------------

    def get_product_pricing(self, product_id):

        result = (
            self.client
            .table("products")
            .select(
                """
                id,
                markup_percent,
                category_id,
                categories(
                    markup_percent
                )
                """
            )
            .eq("id", product_id)
            .single()
            .execute()
        )

        return result.data



    # --------------------------------------------------------------------------
    # CALCULATE SELLING PRICE
    # --------------------------------------------------------------------------

    def calculate_selling_price(
        self,
        product_id,
        cost
    ):


        cost = Decimal(str(cost))


        product = self.get_product_pricing(
            product_id
        )


        markup = None



        # ==============================================================
        # 1. PRODUCT MARKUP
        # ==============================================================

        if product:

            if product.get("markup_percent") is not None:

                markup = Decimal(
                    str(
                        product["markup_percent"]
                    )
                )



        # ==============================================================
        # 2. CATEGORY MARKUP
        # ==============================================================

        if markup is None and product:

            category = product.get(
                "categories"
            )


            if category:

                if category.get(
                    "markup_percent"
                ) is not None:

                    markup = Decimal(
                        str(
                            category["markup_percent"]
                        )
                    )



        # ==============================================================
        # 3. GLOBAL DEFAULT MARKUP
        # ==============================================================

        if markup is None:

            markup = Decimal(
                str(
                    self.get_setting(
                        "DEFAULT_MARKUP_PERCENT",
                        30
                    )
                )
            )



        # ==============================================================
        # FINAL PRICE
        # ==============================================================

        selling_price = (
            cost +
            (
                cost *
                markup /
                Decimal("100")
            )
        )


        return selling_price
