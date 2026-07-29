# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v5.0 FINAL
#
# Features:
#
#   Settings Cache
#   Product Markup
#   Category Markup
#   Global Default Markup
#   Priority Engine
#   Price Trace
#   POS Ready
#
# Flow:
#
# Product Markup
#        ↓
# Category Markup
#        ↓
# Global Default
#
# ==============================================================================


from decimal import (
    Decimal,
    ROUND_HALF_UP
)

from typing import (
    Any,
    Dict,
    Optional
)

import time


from ..base_repo import (
    log_error
)





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


        self.settings_cache = {}


        self.settings_cache_time = 0


        self.cache_ttl = 300






    # ==========================================================================
    # SAFE QUERY
    # ==========================================================================


    def safe_query(

        self,

        table,

        select="*",

        filters=None

    ):


        try:


            query = (

                self.client

                .table(

                    table

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



            result = (

                query

                .execute()

            )


            return result.data or []




        except Exception as e:


            log_error(

                message=

                f"Pricing query failed {table}",

                exception=e

            )


            return []








    # ==========================================================================
    # SETTINGS CACHE
    # ==========================================================================


    def load_settings(self):


        try:


            now = time.time()



            if (

                self.settings_cache

                and

                now - self.settings_cache_time

                <

                self.cache_ttl

            ):


                return self.settings_cache





            rows = self.safe_query(

                "erp_settings",

                "*"

            )



            self.settings_cache = {


                row.get("key"):

                row.get("value")


                for row in rows


            }



            self.settings_cache_time = now



            return self.settings_cache





        except Exception as e:


            log_error(

                message="Settings cache load failed",

                exception=e

            )


            return {}







    def clear_settings_cache(self):


        self.settings_cache = {}


        self.settings_cache_time = 0







    # ==========================================================================
    # GET SETTING
    # ==========================================================================


    def get_setting(

        self,

        key,

        default=None

    ):


        settings = self.load_settings()



        return settings.get(

            key,

            default

        )







    # ==========================================================================
    # PRODUCT MARKUP
    # ==========================================================================


    def get_product_markup(

        self,

        product_id:int

    ):


        try:


            rows = self.safe_query(

                "products",

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


                product = rows[0]



                return {


                    "product_id":

                    product.get("id"),



                    "name":

                    product.get("name"),



                    "markup":

                    product.get("markup_percent"),



                    "category_id":

                    product.get("category_id")


                }



        except Exception as e:


            log_error(

                message="Product markup failed",

                exception=e

            )



        return {


            "product_id":

            product_id,


            "name":

            "",


            "markup":

            None,


            "category_id":

            None

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


                "name":

                None,


                "markup":

                None

            }





        try:


            rows = self.safe_query(

                "categories",

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


                category = rows[0]



                return {


                    "name":

                    category.get("name"),



                    "markup":

                    category.get("markup_percent")

                }




        except Exception as e:


            log_error(

                message="Category markup failed",

                exception=e

            )



        return {


            "name":

            None,


            "markup":

            None

        }






    # ==========================================================================
    # MARKUP CONVERTER
    # ==========================================================================


    def to_decimal(

        self,

        value

    ):


        try:


            return Decimal(

                str(

                    value or 0

                )

            )



        except Exception:


            return Decimal("0")




# ============================================================================== 
# PART 1 END
# ==============================================================================
# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v5.0 FINAL
#
# PART 2/2
#
# ==============================================================================




    # ==========================================================================
    # PRICE CALCULATION ENGINE
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



            # --------------------------------------------------------------
            # LOAD SETTINGS
            # --------------------------------------------------------------


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



            global_markup = self.to_decimal(

                self.get_setting(

                    "DEFAULT_MARKUP_PERCENT",

                    "20"

                )

            )





            # --------------------------------------------------------------
            # LOAD MARKUP SOURCES
            # --------------------------------------------------------------


            product = self.get_product_markup(

                product_id

            )



            category = self.get_category_markup(

                product.get(

                    "category_id"

                )

            )



            product_markup = self.to_decimal(

                product.get(

                    "markup"

                )

            )



            category_markup = self.to_decimal(

                category.get(

                    "markup"

                )

            )





            # --------------------------------------------------------------
            # DEFAULT TRACE
            # --------------------------------------------------------------


            applied_markup = global_markup


            source = "GLOBAL_DEFAULT_MARKUP"




            # --------------------------------------------------------------
            # PRIORITY ENGINE
            # --------------------------------------------------------------


            if priority == "PRODUCT_FIRST":



                if (

                    enable_product

                    and

                    product.get("markup") is not None

                ):


                    applied_markup = product_markup


                    source = "PRODUCT_MARKUP"



                elif (

                    enable_category

                    and

                    category.get("markup") is not None

                ):


                    applied_markup = category_markup


                    source = "CATEGORY_MARKUP"






            elif priority == "CATEGORY_FIRST":



                if (

                    enable_category

                    and

                    category.get("markup") is not None

                ):


                    applied_markup = category_markup


                    source = "CATEGORY_MARKUP"



                elif (

                    enable_product

                    and

                    product.get("markup") is not None

                ):


                    applied_markup = product_markup


                    source = "PRODUCT_MARKUP"






            elif priority == "GLOBAL_FIRST":


                applied_markup = global_markup


                source = "GLOBAL_DEFAULT_MARKUP"







            # --------------------------------------------------------------
            # FINAL PRICE
            # --------------------------------------------------------------


            selling_price = (

                cost

                +

                (

                    cost

                    *

                    applied_markup

                    /

                    Decimal("100")

                )

            ).quantize(

                Decimal("1"),

                rounding=ROUND_HALF_UP

            )







            # --------------------------------------------------------------
            # PRICE TRACE
            # --------------------------------------------------------------


            trace = {


                "cost":

                    float(cost),



                "product_markup":

                    float(product_markup),



                "category_markup":

                    float(category_markup),



                "global_markup":

                    float(global_markup),



                "applied_markup":

                    float(applied_markup),



                "source":

                    source,



                "priority":

                    priority

            }







            # --------------------------------------------------------------
            # POS READY RESPONSE
            # --------------------------------------------------------------


            return {


                "success":

                    True,



                "product_id":

                    product_id,



                "product_name":

                    product.get(

                        "name"

                    ),



                "selling_price":

                    float(

                        selling_price

                    ),



                "price_source":

                    source,



                "markup_percent":

                    float(

                        applied_markup

                    ),



                "trace":

                    trace

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
    # SIMPLE PRICE API FOR POS
    # ==========================================================================


    def get_pos_price(

        self,

        product_id,

        cost

    ):


        result = self.calculate_selling_price(

            cost,

            product_id

        )


        return result







    # ==========================================================================
    # HEALTH CHECK
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



                "version":

                    "5.0",



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



                "version":

                    "5.0",



                "status":

                    "FAIL",



                "message":

                    str(e)

            }






# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "PricingService"

                ]
