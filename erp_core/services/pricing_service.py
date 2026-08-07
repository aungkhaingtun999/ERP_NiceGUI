# ==============================================================================
# erp_core/services/pricing_service.py
# ERP ENTERPRISE PRICING ENGINE v7.0
#
# SETTINGS CONTROLLED PRICING ENGINE
#
# Priority:
#
# OWNER_FIRST
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



    # ==========================================================================
    # QUERY
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

                .table(table)

                .select(select)

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



        except Exception:


            return default






    # ==========================================================================
    # GET PRODUCT
    # ==========================================================================


    def get_product(
        self,
        product_id
    ):


        rows = self.query(

            Tables.PRODUCTS,

            """
            id,
            name,

            purchase_price,
            selling_price,

            owner_selling_price,
            final_selling_price,

            price_source,
            owner_price_locked,

            markup_percent,
            category_id

            """,

            {
                "id":product_id
            }

        )


        if rows:

            return rows[0]


        return {}






    # ==========================================================================
    # PRODUCT MARKUP
    # ==========================================================================


    def get_product_markup(
        self,
        product_id
    ):


        product = self.get_product(
            product_id
        )


        return {

            "markup_percent":
            product.get(
                "markup_percent"
            ),

            "category_id":
            product.get(
                "category_id"
            )

        }






    # ==========================================================================
    # CATEGORY MARKUP
    # ==========================================================================


    def get_category_markup(
        self,
        category_id
    ):


        if not category_id:

            return None



        rows = self.query(

            Tables.CATEGORIES,

            """
            markup_percent
            """,

            {
                "id":category_id
            }

        )


        if rows:

            return rows[0].get(
                "markup_percent"
            )


        return None





    # ==========================================================================
    # GLOBAL MARKUP
    # ==========================================================================


    def get_global_markup(self):


        value = self.get_setting(

            "DEFAULT_MARKUP_PERCENT",

            0

        )


        return Decimal(
            str(value)
        )






    # ==========================================================================
    # PRICE CALCULATION
    # ==========================================================================


    def calculate_price(

        self,

        product_id,

        base_price

    ):


        try:


            base_price = Decimal(
                str(base_price or 0)
            )



            method = str(

                self.get_setting(

                    "PRICING_METHOD",

                    "OWNER_FIRST"

                )

            ).upper()



            product = self.get_product(

                product_id

            )



            # ==============================================================
            # 1. OWNER PRICE
            # ==============================================================


            if method == "OWNER_FIRST":


                owner_price = product.get(

                    "owner_selling_price"

                )



                if owner_price not in (
                    None,
                    "",
                    0
                ):


                    return {

                        "selling_price":
                        Decimal(str(owner_price))
                        .quantize(
                            Decimal("0.01")
                        ),

                        "final_markup_percent":
                        0,

                        "markup_source":
                        "OWNER_PRICE"

                    }





            # ==============================================================
            # 2. PRODUCT MARKUP
            # ==============================================================


            markup = product.get(

                "markup_percent"

            )


            source = "PRODUCT"




            # ==============================================================
            # 3. CATEGORY MARKUP
            # ==============================================================


            if markup is None:


                markup = self.get_category_markup(

                    product.get(
                        "category_id"
                    )

                )


                source = "CATEGORY"




            # ==============================================================
            # 4. GLOBAL DEFAULT
            # ==============================================================


            if markup is None:


                markup = self.get_global_markup()

                source = "DEFAULT"





            markup = Decimal(

                str(markup or 0)

            )



            final_price = (

                base_price

                *

                (

                    Decimal("1")

                    +

                    markup / Decimal("100")

                )

            )



            return {


                "selling_price":

                final_price.quantize(

                    Decimal("0.01"),

                    rounding=ROUND_HALF_UP

                ),



                "final_markup_percent":

                float(markup),



                "markup_source":

                source


            }





        except Exception as e:


            log_error(

                message="Pricing calculation failed",

                exception=e

            )


            return {


                "selling_price":

                Decimal(str(base_price or 0)),


                "final_markup_percent":

                0,


                "markup_source":

                "ERROR"

            }





    # ==========================================================================
    # COMPATIBILITY METHOD
    # Used by Inventory Preview
    # ==========================================================================


    def calculate_selling_price(

        self,

        cost,

        product_id=None

    ):


        return self.calculate_price(

            product_id,

            cost

        )
