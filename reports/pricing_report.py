# ==============================================================================
# ERP ENTERPRISE PRICING REPORT SERVICE
# ==============================================================================


from erp_core.base_repo import db



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


    for p in products:


        category = (

            db()

            .table("categories")

            .select(
                "name,markup_percent"
            )

            .eq(
                "id",
                p.get("category_id")
            )

            .execute()

        )


        if category.data:

            p["category"] = category.data[0]["name"]

            p["category_markup"] = (
                category.data[0]
                .get("markup_percent")
            )

        else:

            p["category"] = "-"

            p["category_markup"] = None



        cost = float(
            p.get("purchase_price") or 0
        )

        selling = float(
            p.get("selling_price") or 0
        )


        p["profit"] = selling - cost



    return products