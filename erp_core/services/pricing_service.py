# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE
# ==============================================================================


from decimal import Decimal


class PricingService:


    def __init__(self, client):

        self.client = client



    def get_setting(
        self,
        key,
        default=None
    ):

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




    def calculate_selling_price(
        self,
        cost
    ):


        markup = Decimal(
            str(
                self.get_setting(
                    "DEFAULT_MARKUP_PERCENT",
                    30
                )
            )
        )


        cost = Decimal(
            str(cost)
        )


        selling = (
            cost +
            (
                cost *
                markup /
                Decimal("100")
            )
        )


        return selling