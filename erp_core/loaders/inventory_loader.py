# ==============================================================================
# erp_core/loaders/inventory_loader.py
# ERP ENTERPRISE INVENTORY LOADER v31
#
# Real Inventory Source:
# products
# +
# warehouse_stock
# +
# warehouses
#
# ==============================================================================

from ..base_repo import db, log_error


def get_inventory_view(warehouse_id=None, search=None, limit=100):
    """
    Enterprise Inventory View

    Source:

        products
        +
        warehouse_stock
        +
        warehouses


    Used by:

        Product Master
        Inventory Control Center
        Stock Adjustment

    """

    try:
        client = db()

        # --------------------------------------------------------------
        # PRODUCT + STOCK JOIN
        # --------------------------------------------------------------

        query = client.table("warehouse_stock").select(
            """
            warehouse_id,
            qty,
            reserved_qty,
            available_qty,

            product_id,

            products(
                id,
                name,
                sku,
                barcode,
                purchase_price,
                selling_price,
                minimum_stock,
                unit,
                notes,
                is_active
            ),

            warehouses(
                id,
                name
            )
            """
        )

        if warehouse_id is not None:
            query = query.eq("warehouse_id", int(warehouse_id))

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
                "id": product.get("id"),
                "name": product.get("name"),
                "sku": product.get("sku"),
                "barcode": product.get("barcode"),
                "purchase_price": product.get("purchase_price", 0),
                "selling_price": product.get("selling_price", 0),
                "minimum_stock": product.get("minimum_stock", 0),
                "unit": product.get("unit", "pcs"),
                "warehouse_id": item.get("warehouse_id"),
                "warehouse": warehouse.get("name"),
                "qty": item.get("qty", 0),
                "reserved_qty": item.get("reserved_qty", 0),
                "available_qty": item.get("available_qty", 0),
            }

            rows.append(row)

        # --------------------------------------------------------------
        # SEARCH
        # --------------------------------------------------------------

        if search:
            keyword = str(search).lower()

            rows = [
                r
                for r in rows
                if keyword in str(r.get("name", "")).lower()
                or keyword in str(r.get("sku", "")).lower()
                or keyword in str(r.get("barcode", "")).lower()
            ]

        return rows[:limit]

    except Exception as e:
        log_error(message="get_inventory_view failed", exception=e)

        return []
