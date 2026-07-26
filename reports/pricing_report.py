# ==============================================================================
# ERP ENTERPRISE PRICING REPORT SERVICE v4.0
# Product + Category + Global Markup Analysis Engine
# ==============================================================================


from decimal import Decimal, ROUND_HALF_UP

from erp_core.base_repo import db



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
# PRICING REPORT
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
    # GLOBAL SETTINGS
    # =====================================================


    global_markup = Decimal(

        str(

            get_setting(

                "DEFAULT_MARKUP_PERCENT",

                "20"

            )

        )

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





    # =====================================================
    # PRODUCT LOOP
    # =====================================================


    for p in products:



        # -------------------------------------------------
        # BASIC PRICE
        # -------------------------------------------------


        cost = Decimal(

            str(

                p.get(
                    "purchase_price"
                )
                or 0

            )

        )


        selling = Decimal(

            str(

                p.get(
                    "selling_price"
                )
                or 0

            )

        )



        p["cost"] = float(cost)

        p["actual_selling_price"] = float(selling)



        p["profit"] = float(

            selling - cost

        )





        # -------------------------------------------------
        # CATEGORY MARKUP
        # -------------------------------------------------


        category_name = "-"

        category_markup = None



        category_id = p.get(
            "category_id"
        )



        if category_id:


            try:


                category = (

                    db()

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



                if category.data:


                    category_name = (

                        category.data[0]

                        .get(
                            "name"
                        )

                    )


                    category_markup = (

                        category.data[0]

                        .get(
                            "markup_percent"
                        )

                    )


            except Exception:


                pass




        p["category"] = category_name


        p["category_markup"] = category_markup





        # -------------------------------------------------
        # PRODUCT MARKUP
        # -------------------------------------------------


        product_markup = p.get(

            "markup_percent"

        )



        p["product_markup"] = (


            float(product_markup)

            if product_markup is not None

            else None


        )





        # -------------------------------------------------
        # MARKUP PRIORITY ENGINE
        #
        # PRODUCT
        #    ↓
        # CATEGORY
        #    ↓
        # GLOBAL
        # -------------------------------------------------



        final_markup = global_markup


        source = "GLOBAL_DEFAULT_MARKUP"




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






        # -------------------------------------------------
        # PRICE CALCULATION
        # -------------------------------------------------


        expected_price = (

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





        # -------------------------------------------------
        # REPORT OUTPUT FIELDS
        # -------------------------------------------------


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
