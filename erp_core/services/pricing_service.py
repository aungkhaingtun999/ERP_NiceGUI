# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v2.0
# ==============================================================================


from decimal import Decimal


class PricingService:


    def __init__(self, client):

        self.client = client



    # ==========================================================
    # GET SYSTEM SETTING
    # ==========================================================

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



    # ==========================================================
    # GET PRODUCT DATA
    # ==========================================================

    def get_product(
        self,
        product_id
    ):

        result = (
            self.client
            .table("products")
            .select(
                """
                id,
                category_id,
                brand_id,
                selling_price
                """
            )
            .eq(
                "id",
                product_id
            )
            .single()
            .execute()
        )


        return result.data



    # ==========================================================
    # PRODUCT MARKUP OVERRIDE
    # ==========================================================

    def get_product_markup(
        self,
        product_id
    ):

        result = (
            self.client
            .table("product_pricing")
            .select("*")
            .eq(
                "product_id",
                product_id
            )
            .execute()
        )


        if result.data:

            return Decimal(
                str(
                    result.data[0]["markup_percent"]
                )
            )


        return None



    # ==========================================================
    # CATEGORY MARKUP
    # ==========================================================

    def get_category_markup(
        self,
        category_id
    ):


        if not category_id:

            return None


        result = (
            self.client
            .table("category_pricing")
            .select("markup_percent")
            .eq(
                "category_id",
                category_id
            )
            .execute()
        )


        if result.data:

            return Decimal(
                str(
                    result.data[0]["markup_percent"]
                )
            )


        return None



    # ==========================================================
    # CALCULATE SELLING PRICE
    # ==========================================================

    def calculate_selling_price(
        self,
        cost,
        product_id=None
    ):


        cost = Decimal(
            str(cost)
        )


        markup = None



        # 1️⃣ Product Override

        if product_id:

            markup = self.get_product_markup(
                product_id
            )



        # 2️⃣ Category Override

        if markup is None and product_id:

            product = self.get_product(
                product_id
            )

            if product:

                markup = self.get_category_markup(
                    product.get("category_id")
                )



        # 3️⃣ Global Default

        if markup is None:

            markup = Decimal(
                str(
                    self.get_setting(
                        "DEFAULT_MARKUP_PERCENT",
                        30
                    )
                )
            )



        selling = (
            cost +
            (
                cost *
                markup /
                Decimal("100")
            )
        )


        return selling.quantize(
            Decimal("0.01")
        )



    # ==========================================================
    # UPDATE PRODUCT SELLING PRICE
    # ==========================================================

    def update_product_price(
        self,
        product_id,
        selling_price
    ):


        auto_update = self.get_setting(
            "AUTO_UPDATE_SELLING_PRICE",
            "true"
        )


        if str(auto_update).lower() != "true":

            return False



        self.client.table(
            "products"
        ).update(

            {
                "selling_price":
                    float(
                        selling_price
                    )
            }

        ).eq(
            "id",
            product_id
        ).execute()



        return True
