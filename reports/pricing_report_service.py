# ==============================================================================
# reports/pricing_report_service.py
# ERP ENTERPRISE PRICING REPORT SERVICE v5.0
# Product + Category + Global Markup Analysis Engine
# Settings Controlled Pricing
# ==============================================================================


from decimal import Decimal, ROUND_HALF_UP

from erp_core.base_repo import db



# ==============================================================================
# SAFE DECIMAL
# ==============================================================================

def safe_decimal(value, default="0"):

    try:
        if value is None:
            return Decimal(default)

        return Decimal(
            str(value)
        )

    except Exception:
        return Decimal(default)



# ==============================================================================
# GET SETTING
# ==============================================================================

def get_setting(
    key,
    default=None
):

    try:

        result = (

            db()

            .table("settings")

            .select(
                "value"
            )

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




# ==============================================================================
# GET CATEGORY CACHE
# ==============================================================================

def get_categories():

    cache = {}


    try:

        result = (

            db()

            .table("categories")

            .select(
                """
                id,
                name,
                markup_percent
                """
            )

            .execute()

        )


        for row in result.data or []:

            cache[
                row["id"]
            ] = row


    except Exception:

        pass


    return cache




# ==============================================================================
# MAIN PRICING REPORT
# ==============================================================================


def get_pricing_report_products():



    try:

        result = (

            db()

            .table("products")

            .select(
                """
                id,
                name,
                sku,
                purchase_price,
                selling_price,
                markup_percent,
                category_id
                """
            )

            .order(
                "name"
            )

            .execute()

        )


        products = result.data or []


    except Exception:

        return []




    # =====================================================
    # SETTINGS CONTROLLED VALUES
    # =====================================================


    global_markup = safe_decimal(

        get_setting(
            "DEFAULT_MARKUP_PERCENT"
        ),

        "0"

    )



    priority = get_setting(

        "PRICING_PRIORITY",

        "PRODUCT_FIRST"

    )



    enable_product = (

        str(

            get_setting(

                "ENABLE_PRODUCT_MARKUP",

                "true"

            )

        ).lower()

        ==
        "true"

    )



    enable_category = (

        str(

            get_setting(

                "ENABLE_CATEGORY_MARKUP",

                "true"

            )

        ).lower()

        ==
        "true"

    )




    categories = get_categories()



    # =====================================================
    # PRODUCT LOOP
    # =====================================================


    for p in products:



        cost = safe_decimal(

            p.get(
                "purchase_price"
            )

        )


        selling = safe_decimal(

            p.get(
                "selling_price"
            )

        )



        p["cost"] = float(cost)


        p["actual_selling_price"] = float(
            selling
        )


        p["profit"] = float(

            selling - cost

        )



        # =================================================
        # CATEGORY DATA
        # =================================================


        category = categories.get(

            p.get(
                "category_id"
            )

        )


        category_markup = None


        category_name = "-"



        if category:

            category_name = category.get(
                "name",
                "-"
            )


            category_markup = category.get(
                "markup_percent"
            )



        p["category"] = category_name



        p["category_markup"] = (

            float(category_markup)

            if category_markup is not None

            else None

        )




        # =================================================
        # PRODUCT MARKUP
        # =================================================


        product_markup = p.get(

            "markup_percent"

        )



        p["product_markup"] = (

            float(product_markup)

            if product_markup is not None

            else None

        )




        # =================================================
        # PRIORITY ENGINE
        #
        # PRODUCT
        #    ↓
        # CATEGORY
        #    ↓
        # GLOBAL
        #
        # =================================================


        final_markup = global_markup


        source = "GLOBAL_DEFAULT_MARKUP"




        if priority == "PRODUCT_FIRST":


            if (

                enable_product

                and product_markup is not None

            ):


                final_markup = safe_decimal(

                    product_markup

                )


                source = "PRODUCT_MARKUP"



            elif (

                enable_category

                and category_markup is not None

            ):


                final_markup = safe_decimal(

                    category_markup

                )


                source = "CATEGORY_MARKUP"





        elif priority == "CATEGORY_FIRST":



            if (

                enable_category

                and category_markup is not None

            ):


                final_markup = safe_decimal(

                    category_markup

                )


                source = "CATEGORY_MARKUP"



            elif (

                enable_product

                and product_markup is not None

            ):


                final_markup = safe_decimal(

                    product_markup

                )


                source = "PRODUCT_MARKUP"





        elif priority == "GLOBAL_FIRST":


            final_markup = global_markup


            source = "GLOBAL_DEFAULT_MARKUP"






        # =================================================
        # EXPECTED PRICE
        # =================================================


        expected_price = (

            cost

            +

            (

                cost

                *

                final_markup

                /

                Decimal("100")

            )

        ).quantize(

            Decimal("0.01"),

            rounding=ROUND_HALF_UP

        )





        # =================================================
        # OUTPUT
        # =================================================


        p["global_markup"] = float(

            global_markup

        )


        p["final_markup_percent"] = float(

            final_markup

        )


        p["markup_source"] = source



        p["expected_selling_price"] = float(

            expected_price

        )


        p["price_difference"] = float(

            selling - expected_price

        )



    return products
