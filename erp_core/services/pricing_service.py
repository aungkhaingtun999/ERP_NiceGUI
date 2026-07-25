# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v2.0
# Dynamic Markup Priority Engine
# ==============================================================================


from decimal import Decimal, ROUND_HALF_UP



class PricingService:


    def __init__(
        self,
        client
    ):

        self.client = client



    # ==========================================================
    # GET SETTING
    # ==========================================================

    def get_setting(
        self,
        key,
        default=None
    ):

        try:

            result = (
                self.client
                .table("settings")
                .select("value")
                .eq(
                    "key",
                    key
                )
                .execute()
            )


            if result.data:

                return result.data[0]["value"]


        except Exception:

            pass


        return default



    # ==========================================================
    # GET PRODUCT MARKUP
    # ==========================================================

    def get_product_markup(
        self,
        product_id
    ):

        result = (
            self.client
            .table("products")
            .select(
                """
                markup_percent,
                category_id
                """
            )
            .eq(
                "id",
                product_id
            )
            .execute()
        )


        if not result.data:

            return {
                "markup": None,
                "category_id": None
            }


        product = result.data[0]


        return {

            "markup":
                product.get(
                    "markup_percent"
                ),

            "category_id":
                product.get(
                    "category_id"
                )
        }



    # ==========================================================
    # GET CATEGORY MARKUP
    # ==========================================================

    def get_category_markup(
        self,
        category_id
    ):


        if not category_id:

            return None


        result = (
            self.client
            .table("categories")
            .select(
                "markup_percent"
            )
            .eq(
                "id",
                category_id
            )
            .execute()
        )


        if result.data:

            return result.data[0].get(
                "markup_percent"
            )


        return None



    # ==========================================================
    # PRICING ENGINE
    # ==========================================================

    def calculate_selling_price(

        self,

        cost,

        product_id

    ):


        cost = Decimal(
            str(cost)
        )



        # SETTINGS

        priority = self.get_setting(

            "PRICING_PRIORITY",

            "PRODUCT_FIRST"

        )



        enable_product = (

            str(
                self.get_setting(
                    "ENABLE_PRODUCT_MARKUP",
                    "true"
                )
            ).lower()
            ==
            "true"

        )



        enable_category = (

            str(
                self.get_setting(
                    "ENABLE_CATEGORY_MARKUP",
                    "true"
                )
            ).lower()
            ==
            "true"

        )



        default_markup = Decimal(

            str(

                self.get_setting(

                    "DEFAULT_MARKUP_PERCENT",

                    "20"

                )

            )

        )



        # PRODUCT DATA

        product_data = self.get_product_markup(

            product_id

        )


        product_markup = product_data["markup"]

        category_id = product_data["category_id"]



        category_markup = None


        if enable_category:

            category_markup = self.get_category_markup(

                category_id

            )



        selected_markup = default_markup

        source = "GLOBAL_SETTING"



        # ======================================================
        # PRIORITY ENGINE
        # ======================================================


        if priority == "PRODUCT_FIRST":


            if (
                enable_product
                and product_markup is not None
            ):

                selected_markup = Decimal(
                    str(product_markup)
                )

                source = "PRODUCT_MARKUP"



            elif (
                enable_category
                and category_markup is not None
            ):

                selected_markup = Decimal(
                    str(category_markup)
                )

                source = "CATEGORY_MARKUP"



        elif priority == "CATEGORY_FIRST":


            if category_markup is not None:


                selected_markup = Decimal(
                    str(category_markup)
                )

                source = "CATEGORY_MARKUP"



            elif (
                enable_product
                and product_markup is not None
            ):


                selected_markup = Decimal(
                    str(product_markup)
                )

                source = "PRODUCT_MARKUP"



        elif priority == "GLOBAL_FIRST":


            selected_markup = default_markup

            source = "GLOBAL_SETTING"



        # ======================================================
        # CALCULATE
        # ======================================================


        selling_price = (

            cost +

            (
                cost *
                selected_markup /
                Decimal("100")
            )

        ).quantize(

            Decimal("0.01"),

            rounding=ROUND_HALF_UP

        )



        return {


            "cost":
                float(cost),


            "markup":
                float(selected_markup),


            "selling_price":
                float(selling_price),


            "source":
                source

        }
