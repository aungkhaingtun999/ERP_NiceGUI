# ==============================================================================
# MOBILE INVENTORY PRODUCT SEARCH ENGINE v4
# Barcode + SKU + Warehouse Stock
# ==============================================================================

from database import db


def search_product(keyword):

    if not keyword:
        return None


    keyword = str(keyword).strip()


    try:

        client = db()


        response = (
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
            .or_(
                f"barcode.eq.{keyword},sku.eq.{keyword}"
            )
            .execute()
        )


        products = response.data


        if not products:
            return None


        product = products[0]


        # Warehouse stock priority
        warehouse_stock = product.get(
            "warehouse_stock",
            []
        )


        if warehouse_stock:

            total_qty = sum(
                int(
                    w.get("available_qty",0)
                )
                for w in warehouse_stock
            )

            product["stock"] = total_qty


        return product


    except Exception as e:

        print(
            "Product Search Error:",
            e
        )

        return None
