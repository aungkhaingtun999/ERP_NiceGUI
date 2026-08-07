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


from decimal import (
    Decimal,
    ROUND_HALF_UP
)

import time


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
# PRICING SERVICE
# ==============================================================================


class PricingService:
    # ==========================================================================
    # SIMPLE PRICE CALCULATION (COMPATIBILITY METHOD)
    # ==========================================================================

    def calculate_selling_price(
        self,
        cost,
        product_id=None
    ):

        markup = float(
            self.get_setting(
                "DEFAULT_MARKUP_PERCENT"
            ) or 20
        )

        cost = float(cost or 0)

        selling_price = round(
            cost + (cost * markup / 100),
            2
        )

        return {
            "selling_price": selling_price,
            "final_markup_percent": markup,
            "markup_source": "DEFAULT"
        }
        


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

        self.cache_time = 0

        self.cache_ttl = 300





    # ==========================================================================
    # SAFE QUERY
    # ==========================================================================


    def query(

        self,

        table,

        select="*",

        filters=None

    ):


        try:


            q = (

                self.client

                .table(

                    table

                )

                .select(

                    select

                )

            )


            if filters:


                for key,value in filters.items():


                    q = q.eq(

                        key,

                        value

                    )


            result = q.execute()


            return result.data or []



        except Exception as e:


            log_error(

                message=f"Pricing query failed {table}",

                exception=e

            )


            return []






    # ==========================================================================
    # SETTINGS
    # ==========================================================================


    def get_setting(

        self,

        key

    ):


        return self.settings_service.get_setting(

            key

        )






    # ==========================================================================
    # PRODUCT MARKUP
    # ==========================================================================


    def get_product_markup(

        self,

        product_id

    ):


        try:


            rows = self.query(

                Tables.PRODUCTS,

                """
                id,
                name,
                markup_percent,
                category_id
                """,

                {

                    "id":

                    product_id

                }

            )


            if rows:


                return rows[0]



        except Exception as e:


            log_error(

                message="Product markup load failed",

                exception=e

            )



        return {

            "id":product_id,

            "name":"",

            "markup_percent":None,

            "category_id":None

        }






    # ==========================================================================
    # CATEGORY MARKUP
    # ==========================================================================


    def get_category_markup(

        self,

        category_id

    ):


        if not category_id:


            return {


                "name":None,

                "markup_percent":None

            }



        try:


            rows = self.query(

                Tables.CATEGORIES,

                """
                name,
                markup_percent
                """,

                {

                    "id":

                    category_id

                }

            )



            if rows:

                return rows[0]



        except Exception as e:


            log_error(

                message="Category markup load failed",

                exception=e

            )



        return {


            "name":None,

            "markup_percent":None

        }

