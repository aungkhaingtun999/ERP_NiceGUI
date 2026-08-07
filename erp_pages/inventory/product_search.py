# ==============================================================================
# MOBILE INVENTORY PRODUCT SEARCH ENGINE v5
#
# Barcode + SKU + Warehouse Stock
# Owner First Pricing Compatible
#
# ==============================================================================


from database import db




def search_product(

    keyword,

    warehouse_id=None

):


    if not keyword:

        return None



    keyword = str(
        keyword
    ).strip()



    try:


        client = db()



        query = (

            client

            .table(
                "products"
            )

            .select(
                """
                id,
                name,
                barcode,
                sku,

                purchase_price,

                selling_price,

                owner_selling_price,

                final_selling_price,

                price_source,

                owner_price_locked,

                markup_percent,

                unit,

                is_active,

                warehouse_stock(
                    warehouse_id,
                    qty,
                    available_qty
                )
                """
            )

            .or_(
                f"barcode.eq.{keyword},sku.eq.{keyword}"
            )

        )



        result = (
            query
            .execute()
        )



        products = result.data or []



        if not products:

            return None




        product = products[0]




        # ----------------------------------------------------------------------
        # WAREHOUSE STOCK
        # ----------------------------------------------------------------------


        warehouse_rows = product.get(
            "warehouse_stock",
            []
        )



        if warehouse_id is not None:


            warehouse_rows = [

                w

                for w in warehouse_rows

                if w.get(
                    "warehouse_id"
                )
                ==
                int(
                    warehouse_id
                )

            ]




        available_qty = sum(

            float(
                w.get(
                    "available_qty",
                    0
                )
                or 0
            )

            for w in warehouse_rows

        )



        product["stock"] = available_qty




        # ----------------------------------------------------------------------
        # FINAL DISPLAY PRICE
        # ----------------------------------------------------------------------


        product["display_price"] = (

            product.get(
                "final_selling_price"
            )

            or

            product.get(
                "owner_selling_price"
            )

            or

            product.get(
                "selling_price"
            )

            or 0

        )



        return product




    except Exception as e:


        print(
            "Product Search Error:",
            e
        )


        return None
