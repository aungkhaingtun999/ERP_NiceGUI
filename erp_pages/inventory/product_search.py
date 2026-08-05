# ==============================================================================
# erp_pages/inventory/product_search.py
# MOBILE INVENTORY v4
# ERP PRODUCT SEARCH ENGINE
# ==============================================================================

from database import db


def search_product(keyword):

    if not keyword:
        return None


    keyword = str(keyword).strip()


    try:

        client = db()


        # --------------------------------------------------
        # 1. Barcode Search
        # --------------------------------------------------

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
                unit,
                minimum_stock
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

            return result.data[0]


        # --------------------------------------------------
        # 2. SKU Search
        # --------------------------------------------------

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
                unit,
                minimum_stock
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

            return result.data[0]


        return None


    except Exception as e:

        print(
            "Product Search Error:",
            e
        )

        return None
