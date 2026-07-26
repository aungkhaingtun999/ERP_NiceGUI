# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v3.0
# Dynamic Markup Priority Engine
# Product → Category → Global
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

                return result.data[0].get(
                    "value"
                )


        except Exception:

            pass


        return default



    # ==========================================================
    # PRODUCT MARKUP
    # ==========================================================

    def get_product_markup(
        self,
        product_id
    ):


        try:

            result = (

                self.client

                .table("products")

                .select(
                    """
                    name,
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


            if result.data:


                product = result.data[0]


                return {


                    "name":
                        product.get(
                            "name"
                        ),


                    "product_markup":
                        product.get(
                            "markup_percent"
                        ),


                    "category_id":
                        product.get(
                            "category_id"
                        )


                }



        except Exception:

            pass



        return {


            "name":"",
            "product_markup":None,
            "category_id":None


        }




    # ==========================================================
    # CATEGORY MARKUP
    # ==========================================================

    def get_category_markup(
        self,
        category_id
    ):


        if not category_id:

            return {


                "name":None,

                "markup":None


            }



        try:


            result = (

                self.client

                .table("categories")

                .select(
                    """
                    name,
                    markup_percent
                    """
                )

                .eq(
                    "id",
                    category_id
                )

                .execute()

            )



            if result.data:


                category = result.data[0]


                return {


                    "name":
                        category.get(
                            "name"
                        ),


                    "markup":
                        category.get(
                            "markup_percent"
                        )


                }



        except Exception:

            pass



        return {


            "name":None,

            "markup":None


        }





    # ==========================================================
    # CALCULATE PRICE
    # ==========================================================

    def calculate_selling_price(

        self,

        cost,

        product_id

    ):



        cost = Decimal(
            str(cost or 0)
        )



        # -----------------------------
        # SETTINGS
        # -----------------------------


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



        global_markup = Decimal(

            str(

                self.get_setting(

                    "DEFAULT_MARKUP_PERCENT",

                    "20"

                )

            )

        )



        # -----------------------------
        # GET MARKUPS
        # -----------------------------


        product = self.get_product_markup(

            product_id

        )


        product_markup = product.get(
            "product_markup"
        )


        category = self.get_category_markup(

            product.get(
                "category_id"
            )

        )


        category_markup = category.get(
            "markup"
        )



        # -----------------------------
        # DEFAULT
        # -----------------------------


        final_markup = global_markup

        source = "GLOBAL_DEFAULT_MARKUP"



        # -----------------------------
        # PRIORITY ENGINE
        # -----------------------------


        if priority == "PRODUCT_FIRST":


            if (

                enable_product

                and product_markup is not None

            ):


                final_markup = Decimal(

                    str(product_markup)

                )

                source = "PRODUCT_MARKUP"



            elif (

                enable_category

                and category_markup is not None

            ):


                final_markup = Decimal(

                    str(category_markup)

                )

                source = "CATEGORY_MARKUP"





        elif priority == "CATEGORY_FIRST":



            if (

                enable_category

                and category_markup is not None

            ):


                final_markup = Decimal(

                    str(category_markup)

                )


                source = "CATEGORY_MARKUP"



            elif (

                enable_product

                and product_markup is not None

            ):


                final_markup = Decimal(

                    str(product_markup)

                )


                source = "PRODUCT_MARKUP"





        elif priority == "GLOBAL_FIRST":


            final_markup = global_markup

            source = "GLOBAL_DEFAULT_MARKUP"





        # -----------------------------
        # PRICE CALCULATION
        # -----------------------------


        selling_price = (

            cost +

            (

                cost *

                final_markup /

                Decimal("100")

            )

        ).quantize(

            Decimal("0.01"),

            rounding=ROUND_HALF_UP

        )





        return {


            "cost":

                float(cost),



            # Product level

            "product_markup":

                float(product_markup)
                if product_markup is not None
                else None,



            # Category level

            "category_markup":

                float(category_markup)
                if category_markup is not None
                else None,



            # Global level

            "global_markup":

                float(global_markup),



            # Final Applied

            "final_markup_percent":

                float(final_markup),



            "markup_source":

                source,



            "selling_price":

                float(selling_price)


        }
