# ==============================================================================
# ERP ENTERPRISE PRICING REPORT SERVICE v3.0
# Product + Category + Global Markup Analysis
# ==============================================================================


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
# PRICING REPORT PRODUCTS
# ==============================================================================


def get_pricing_report_products():


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



    # =====================================================
    # GLOBAL SETTING
    # =====================================================

    global_markup = float(

        get_setting(

            "DEFAULT_MARKUP_PERCENT",

            20

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
    # LOOP PRODUCTS
    # =====================================================


    for p in products:



        # -------------------------------------------------
        # CATEGORY
        # -------------------------------------------------


        category_markup = None


        category_name = "-"



        if p.get("category_id"):


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

                    p.get("category_id")

                )

                .execute()

            )



            if category.data:


                category_name = (

                    category.data[0]

                    .get("name")

                )


                category_markup = (

                    category.data[0]

                    .get("markup_percent")

                )



        p["category"] = category_name


        p["category_markup"] = category_markup




        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------


        cost = float(

            p.get(
                "purchase_price"
            )
            or 0

        )


        selling = float(

            p.get(
                "selling_price"
            )
            or 0

        )



        p["profit"] = (

            selling - cost

        )




        # -------------------------------------------------
        # MARKUP ENGINE
        #
        # PRODUCT
        # ↓
        # CATEGORY
        # ↓
        # GLOBAL
        # -------------------------------------------------


        product_markup = p.get(

            "markup_percent"

        )



        final_markup = global_markup


        source = "GLOBAL_DEFAULT_MARKUP"




        if priority == "PRODUCT_FIRST":



            if (

                enable_product

                and product_markup is not None

            ):


                final_markup = float(

                    product_markup

                )


                source = "PRODUCT_MARKUP"



            elif (

                enable_category

                and category_markup is not None

            ):


                final_markup = float(

                    category_markup

                )


                source = "CATEGORY_MARKUP"





        elif priority == "CATEGORY_FIRST":



            if (

                enable_category

                and category_markup is not None

            ):


                final_markup = float(

                    category_markup

                )


                source = "CATEGORY_MARKUP"



            elif (

                enable_product

                and product_markup is not None

            ):


                final_markup = float(

                    product_markup

                )


                source = "PRODUCT_MARKUP"





        elif priority == "GLOBAL_FIRST":


            final_markup = global_markup


            source = "GLOBAL_DEFAULT_MARKUP"





        # -------------------------------------------------
        # REPORT FIELDS
        # -------------------------------------------------


        p["product_markup"] = (

            float(product_markup)

            if product_markup is not None

            else None

        )



        p["global_markup"] = global_markup



        p["final_markup_percent"] = round(

            final_markup,

            2

        )



        p["markup_source"] = source




    return products
