# ==============================================================================
# erp_pages/inventory/product_search.py
# MOBILE INVENTORY v5
# PRODUCT + WAREHOUSE STOCK SEARCH
# ==============================================================================

from database import db


def search_product(keyword):

    if not keyword:
        return None


    keyword = str(keyword).strip()


    try:

        client = db()


        result = (
            client
            .table("products")
            .select(
                """
                id,
                name,
                barcode,
                sku,
                purchase_price,
                selling_price,
                stock,
                warehouse_stock(
                    warehouse_id,
                    qty,
                    available_qty
                )
                """
            )
            .eq(
                "barcode",
                keyword
            )
            .limit(1)
            .execute()
        )


        if result.data:

            product = result.data[0]


            # Warehouse stock ပြောင်းထည့်
            stocks = product.get(
                "warehouse_stock",
                []
            )


            if stocks:

                product["stock"] = stocks[0].get(
                    "available_qty",
                    0
                )


            return product


        # SKU နဲ့ ထပ်ရှာမယ်

        result = (
            client
            .table("products")
            .select(
                """
                id,
                name,
                barcode,
                sku,
                purchase_price,
                selling_price,
                stock,
                warehouse_stock(
                    warehouse_id,
                    qty,
                    available_qty
                )
                """
            )
            .eq(
                "sku",
                keyword
            )
            .limit(1)
            .execute()
        )


        if result.data:

            product = result.data[0]

            stocks = product.get(
                "warehouse_stock",
                []
            )

            if stocks:

                product["stock"] = stocks[0].get(
                    "available_qty",
                    0
                )

            return product


        return None


    except Exception as e:

        print(
            "Product Search Error:",
            e
        )

        return None
