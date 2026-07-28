# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v4.0
#
# Dynamic Markup Priority Engine
#
# Priority:
#       Product
#          ↓
#       Category
#          ↓
#       Global
#
# Features:
#   - Safe Supabase Handling
#   - Pricing Trace
#   - Health Check
#   - ERP Test Center Ready
#
# ==============================================================================


from decimal import (
    Decimal,
    ROUND_HALF_UP
)

from typing import (
    Any,
    Dict
)


try:
    from supabase import Client
except Exception:
    Client = Any


from ..base_repo import (
    log_error
)



# ==============================================================================
# Pricing Service
# ==============================================================================


class PricingService:


    # ==========================================================================
    # Constructor
    # ==========================================================================

    def __init__(
        self,
        client: Client
    ):

        self.client = client



    # ==========================================================================
    # Safe Query Helper
    # ==========================================================================

    def safe_query(
        self,
        table_name,
        select="*",
        filters=None
    ):

        try:


            query = (

                self.client

                .table(
                    table_name
                )

                .select(
                    select
                )

            )


            if filters:


                for key, value in filters.items():


                    query = (

                        query

                        .eq(
                            key,
                            value
                        )

                    )


            result = query.execute()


            return result.data or []



        except Exception as e:


            log_error(

                message=
                f"Pricing query failed: {table_name}",

                exception=e

            )


            return []





    # ==========================================================================
    # Get Setting
    # ==========================================================================

    def get_setting(

        self,

        key,

        default=None

    ):


        data = self.safe_query(

            "settings",

            "value",

            {
                "key": key
            }

        )


        if data:


            return data[0].get(
                "value"
            )


        return default





    # ==========================================================================
    # Product Markup
    # ==========================================================================

    def get_product_markup(

        self,

        product_id

    ):


        data = self.safe_query(

            "products",

            """
            name,
            markup_percent,
            category_id
            """,

            {
                "id": product_id
            }

        )


        if data:


            product = data[0]


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


        return {


            "name":
                "",


            "product_markup":
                None,


            "category_id":
                None

        }





    # ==========================================================================
    # Category Markup
    # ==========================================================================

    def get_category_markup(

        self,

        category_id

    ):


        if not category_id:


            return {


                "name":
                    None,


                "markup":
                    None

            }



        data = self.safe_query(

            "categories",

            """
            name,
            markup_percent
            """,

            {
                "id": category_id
            }

        )


        if data:


            category = data[0]


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



        return {


            "name":
                None,


            "markup":
                None

        }





    # ==========================================================================
    # Price Calculation
    # ==========================================================================

    def calculate_selling_price(

        self,

        cost,

        product_id

    ):


        try:


            cost = Decimal(
                str(
                    cost or 0
                )
            )



            # --------------------------------------------------
            # Settings
            # --------------------------------------------------

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

                )

                .lower()

                ==
                "true"

            )



            enable_category = (

                str(

                    self.get_setting(

                        "ENABLE_CATEGORY_MARKUP",

                        "true"

                    )

                )

                .lower()

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




            # --------------------------------------------------
            # Markup Sources
            # --------------------------------------------------

            product = (

                self

                .get_product_markup(

                    product_id

                )

            )


            product_markup = product.get(

                "product_markup"

            )



            category = (

                self

                .get_category_markup(

                    product.get(
                        "category_id"
                    )

                )

            )


            category_markup = category.get(

                "markup"

            )




            # --------------------------------------------------
            # Default
            # --------------------------------------------------

            final_markup = global_markup


            source = (

                "GLOBAL_DEFAULT_MARKUP"

            )




            # --------------------------------------------------
            # Priority Engine
            # --------------------------------------------------

            if priority == "PRODUCT_FIRST":



                if (

                    enable_product

                    and product_markup is not None

                ):


                    final_markup = Decimal(

                        str(
                            product_markup
                        )

                    )


                    source = (

                        "PRODUCT_MARKUP"

                    )



                elif (

                    enable_category

                    and category_markup is not None

                ):


                    final_markup = Decimal(

                        str(
                            category_markup
                        )

                    )


                    source = (

                        "CATEGORY_MARKUP"

                    )





            elif priority == "CATEGORY_FIRST":



                if (

                    enable_category

                    and category_markup is not None

                ):


                    final_markup = Decimal(

                        str(
                            category_markup
                        )

                    )


                    source = (

                        "CATEGORY_MARKUP"

                    )



                elif (

                    enable_product

                    and product_markup is not None

                ):


                    final_markup = Decimal(

                        str(
                            product_markup
                        )

                    )


                    source = (

                        "PRODUCT_MARKUP"

                    )





            elif priority == "GLOBAL_FIRST":


                final_markup = global_markup


                source = (

                    "GLOBAL_DEFAULT_MARKUP"

                )





            # --------------------------------------------------
            # Calculate Final Price
            # --------------------------------------------------

            selling_price = (

                cost +

                (

                    cost *

                    final_markup /

                    Decimal(
                        "100"
                    )

                )

            ).quantize(

                Decimal(
                    "1"
                ),

                rounding=ROUND_HALF_UP

            )





            return {


                "success":
                    True,


                "product_id":
                    product_id,


                "product_name":
                    product.get(
                        "name"
                    ),


                "cost":
                    float(
                        cost
                    ),


                "product_markup":
                    float(product_markup)
                    if product_markup is not None
                    else None,


                "category_markup":
                    float(category_markup)
                    if category_markup is not None
                    else None,


                "global_markup":
                    float(
                        global_markup
                    ),


                "final_markup_percent":
                    float(
                        final_markup
                    ),


                "markup_source":
                    source,


                "selling_price":
                    float(
                        selling_price
                    )

            }




        except Exception as e:


            log_error(

                message=
                "Pricing calculation failed",

                exception=e

            )


            return {


                "success":
                    False,


                "message":
                    str(e)

            }





    # ==========================================================================
    # Pricing Health Check
    # ==========================================================================

    def health_check(self):


        try:


            result = (

                self.client

                .table(
                    "products"
                )

                .select(
                    "id"
                )

                .limit(
                    1
                )

                .execute()

            )


            return {


                "service":
                    "PricingService",


                "status":
                    "PASS",


                "database":
                    "CONNECTED",


                "rows":
                    len(
                        result.data or []
                    )

            }



        except Exception as e:


            return {


                "service":
                    "PricingService",


                "status":
                    "FAIL",


                "message":
                    str(e)

            }





# ==============================================================================
# Export
# ==============================================================================


__all__ = [

    "PricingService"

]
