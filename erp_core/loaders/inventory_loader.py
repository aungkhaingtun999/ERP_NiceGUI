# ==============================================================================
# erp_core/loaders/inventory_loader.py
# ERP ENTERPRISE INVENTORY LOADER v32
# Product + Warehouse Stock + Pricing + Batch Information
# ==============================================================================

from ..base_repo import db, log_error


def get_inventory_view(warehouse_id=None, search=None, limit=100):

    try:

        client = db()

        query = client.table("warehouse_stock").select(
            """
            id,
            warehouse_id,
            qty,
            reserved_qty,
            available_qty,
            minimum_stock,
            maximum_stock,
            reorder_level,
            location,
            batch_no,
            expiry_date,
            warehouse_code,

            product_id,

            products(
                id,
                name,
                sku,
                barcode,

                purchase_price,
                selling_price,
                owner_selling_price,
                final_selling_price,
                price_source,
                markup_percent,

                minimum_stock,
                unit,
                notes,
                is_active,

                brand_name,
                category_name,
                supplier_code,

                max_stock,
                tax_rate,
                reorder_level,

                is_expiry_controlled,
                is_batch_controlled,
                country_of_origin,
                description
            ),

            warehouses(
                id,
                name
            )
            """
        )

        if warehouse_id is not None:

            query = query.eq(
                "warehouse_id",
                int(warehouse_id)
            )

        result = query.limit(limit).execute()

        rows = []

        for item in result.data or []:

            product = item.get("products") or {}

            if not product:

                print(
                    "BROKEN STOCK LINK:",
                    item
                )

                continue

            warehouse = item.get("warehouses") or {}

            row = {

                # ----------------------------------------------------------
                # PRODUCT
                # ----------------------------------------------------------

                "id":
                    product.get("id"),

                "name":
                    product.get("name"),

                "sku":
                    product.get("sku"),

                "barcode":
                    product.get("barcode"),

                # ----------------------------------------------------------
                # PRICING
                # ----------------------------------------------------------

                "purchase_price":
                    product.get(
                        "purchase_price",
                        0
                    ),

                "selling_price":
                    product.get(
                        "selling_price",
                        0
                    ),

                "owner_selling_price":
                    product.get(
                        "owner_selling_price"
                    ),

                "final_selling_price":
                    product.get(
                        "final_selling_price",
                        product.get(
                            "selling_price",
                            0
                        )
                    ),

                "price_source":
                    product.get(
                        "price_source",
                        "DEFAULT"
                    ),

                "markup_percent":
                    product.get(
                        "markup_percent",
                        0
                    ),

                # ----------------------------------------------------------
                # PRODUCT MASTER
                # ----------------------------------------------------------

                "unit":
                    product.get(
                        "unit",
                        "pcs"
                    ),

                "brand_name":
                    product.get(
                        "brand_name"
                    ),

                "category_name":
                    product.get(
                        "category_name"
                    ),

                "supplier_code":
                    product.get(
                        "supplier_code"
                    ),

                "tax_rate":
                    product.get(
                        "tax_rate",
                        0
                    ),

                "minimum_stock":
                    product.get(
                        "minimum_stock",
                        item.get(
                            "minimum_stock",
                            0
                        )
                    ),

                "max_stock":
                    product.get(
                        "max_stock",
                        item.get(
                            "maximum_stock",
                            0
                        )
                    ),

                "reorder_level":
                    product.get(
                        "reorder_level",
                        item.get(
                            "reorder_level",
                            0
                        )
                    ),

                "is_expiry_controlled":
                    product.get(
                        "is_expiry_controlled",
                        False
                    ),

                "is_batch_controlled":
                    product.get(
                        "is_batch_controlled",
                        False
                    ),

                "country_of_origin":
                    product.get(
                        "country_of_origin"
                    ),

                "description":
                    product.get(
                        "description"
                    ),

                "is_active":
                    product.get(
                        "is_active",
                        True
                    ),

                # ----------------------------------------------------------
                # WAREHOUSE
                # ----------------------------------------------------------

                "warehouse_id":
                    item.get(
                        "warehouse_id"
                    ),

                "warehouse":
                    warehouse.get(
                        "name"
                    ),

                "warehouse_code":
                    item.get(
                        "warehouse_code"
                    ),

                # ----------------------------------------------------------
                # STOCK
                # ----------------------------------------------------------

                "qty":
                    item.get(
                        "qty",
                        0
                    ),

                "reserved_qty":
                    item.get(
                        "reserved_qty",
                        0
                    ),

                "available_qty":
                    item.get(
                        "available_qty",
                        0
                    ),

                "location":
                    item.get(
                        "location"
                    ),

                # ----------------------------------------------------------
                # BATCH / EXPIRY
                # ----------------------------------------------------------

                "batch_no":
                    item.get(
                        "batch_no"
                    ),

                "expiry_date":
                    item.get(
                        "expiry_date"
                    ),

            }

            rows.append(row)

        # ------------------------------------------------------------------
        # SEARCH
        # ------------------------------------------------------------------

        if search:

            keyword = str(
                search
            ).lower().strip()

            rows = [

                r

                for r in rows

                if (
                    keyword
                    in str(
                        r.get(
                            "name",
                            ""
                        )
                    ).lower()

                    or

                    keyword
                    in str(
                        r.get(
                            "sku",
                            ""
                        )
                    ).lower()

                    or

                    keyword
                    in str(
                        r.get(
                            "barcode",
                            ""
                        )
                    ).lower()
                )
            ]

        return rows[:limit]

    except Exception as e:

        log_error(
            message="get_inventory_view failed",
            exception=e
        )

        return []
