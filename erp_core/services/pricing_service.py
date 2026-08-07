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
    # pages/2_Inventory.py
    #
    # ==========================================================================


    def calculate_selling_price(

        self,

        cost,

        product_id=None,

        product=None

    ):


        result = self.calculate_price(

            product_id=product_id,

            base_price=cost,

            product=product

        )


        return {


            "selling_price":

                float(result["price"]),



            "final_markup_percent":

                float(result["markup"]),



            "markup_source":

                result["source"]

        }





    # ==========================================================================
    # PRODUCT MARKUP
    # ==========================================================================


    def get_product_markup(

        self,

        product_id

    ):


        try:


            rows = (

                self.client

                .table(

                    Tables.PRODUCTS

                )

                .select(

                    """
                    id,
                    owner_selling_price,
                    owner_price_locked,
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


            if rows.data:

                return rows.data[0]



        except Exception as e:


            log_error(

                message="Product pricing load failed",

                exception=e

            )



        return {}





    # ==========================================================================
    # CATEGORY MARKUP
    # ==========================================================================


    def get_category_markup(

        self,

        category_id

    ):


        if not category_id:

            return None



        try:


            result = (

                self.client

                .table(

                    Tables.CATEGORIES

                )

                .select(

                    "markup_percent"

                )

                .eq(

                    "id",

                    category_id

                )

                .maybe_single()

                .execute()

            )


            if result.data:

                return result.data.get(
                    "markup_percent"
                )



        except Exception as e:


            log_error(

                message="Category markup error",

                exception=e

            )


        return None

            # ==========================================================================
    # GLOBAL DEFAULT MARKUP
    # ==========================================================================


    def get_global_markup(self):


        try:


            value = self.get_setting(

                "DEFAULT_MARKUP_PERCENT",

                20

            )


            return safe_decimal(value)



        except Exception as e:


            log_error(

                message="Global markup error",

                exception=e

            )


            return Decimal("20")





    # ==========================================================================
    # FINAL PRICE CALCULATION
    #
    # OWNER FIRST ENGINE
    #
    # ==========================================================================


    def calculate_price(

        self,

        product_id,

        base_price,

        product=None

    ):


        try:


            cost = safe_decimal(
                base_price
            )



            # --------------------------------------------------------------
            # LOAD PRODUCT DATA
            # --------------------------------------------------------------


            if product is None and product_id:


                product = self.get_product_markup(

                    product_id

                )



            product = product or {}



            # --------------------------------------------------------------
            # 1. OWNER PRICE FIRST
            # --------------------------------------------------------------


            pricing_method = self.get_setting(

                "PRICING_METHOD",

                "OWNER_FIRST"

            )



            if pricing_method == "OWNER_FIRST":



                owner_price = safe_decimal(

                    product.get(

                        "owner_selling_price"

                    )

                )



                owner_locked = product.get(

                    "owner_price_locked",

                    False

                )



                if owner_price > 0 or owner_locked:



                    return {


                        "price":

                        owner_price.quantize(

                            Decimal("0.01"),

                            rounding=ROUND_HALF_UP

                        ),



                        "markup":

                        Decimal("0"),



                        "source":

                        "OWNER_PRICE"

                    }




            # --------------------------------------------------------------
            # 2. PRODUCT MARKUP
            # --------------------------------------------------------------


            markup = product.get(

                "markup_percent"

            )



            if markup is not None:



                markup = safe_decimal(
                    markup
                )


                final_price = cost * (

                    Decimal("1")

                    +

                    (

                        markup /

                        Decimal("100")

                    )

                )


                return {


                    "price":

                    final_price.quantize(

                        Decimal("0.01"),

                        rounding=ROUND_HALF_UP

                    ),


                    "markup":

                    markup,


                    "source":

                    "PRODUCT_MARKUP"

                }




            # --------------------------------------------------------------
            # 3. CATEGORY MARKUP
            # --------------------------------------------------------------


            category_markup = self.get_category_markup(

                product.get(

                    "category_id"

                )

            )



            if category_markup is not None:



                markup = safe_decimal(

                    category_markup

                )


                final_price = cost * (

                    Decimal("1")

                    +

                    (

                        markup /

                        Decimal("100")

                    )

                )


                return {


                    "price":

                    final_price.quantize(

                        Decimal("0.01"),

                        rounding=ROUND_HALF_UP

                    ),


                    "markup":

                    markup,


                    "source":

                    "CATEGORY_MARKUP"

                }




            # --------------------------------------------------------------
            # 4. GLOBAL DEFAULT MARKUP
            # --------------------------------------------------------------


            markup = self.get_global_markup()



            final_price = cost * (

                Decimal("1")

                +

                (

                    markup /

                    Decimal("100")

                )

            )



            return {


                "price":

                final_price.quantize(

                    Decimal("0.01"),

                    rounding=ROUND_HALF_UP

                ),



                "markup":

                markup,



                "source":

                "DEFAULT"

            }




        except Exception as e:


            log_error(

                message=

                "Final price calculation failed",

                exception=e

            )


            return {


                "price":

                safe_decimal(base_price),



                "markup":

                Decimal("0"),



                "source":

                "ERROR"

            }





# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "PricingService"

]
