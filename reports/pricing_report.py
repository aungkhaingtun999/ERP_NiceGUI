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


# Profit
p["profit"] = selling - cost


# =====================================================
# MARKUP ENGINE
# Priority:
# 1. Product Markup
# 2. Category Markup
# 3. Global Markup
# =====================================================

product_markup = p.get(
    "markup_percent"
)


category_markup = p.get(
    "category_markup"
)



if product_markup is not None:


    final_markup = float(
        product_markup
    )


    p["markup_source"] = (
        "Product Override"
    )



elif category_markup is not None:


    final_markup = float(
        category_markup
    )


    p["markup_source"] = (
        "Category"
    )



elif cost > 0:


    final_markup = (

        (selling - cost)

        /

        cost

    ) * 100


    p["markup_source"] = (
        "Calculated"
    )



else:


    final_markup = 0

    p["markup_source"] = (
        "No Cost"
    )



p["final_markup_percent"] = round(
    final_markup,
    2
)
