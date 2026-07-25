# ==============================================================================
# erp_core/loaders/__init__.py
# ERP ENTERPRISE LOADERS PACKAGE
# ==============================================================================


from .settings_loader import (
    get_setting
)


from .product_loader import (
    get_products,
    get_active_products
)


from .warehouse_loader import (
    get_warehouses,
    get_default_warehouse_id
)


from .customer_loader import (
    get_customers
)


from .supplier_loader import (
    get_suppliers
)


from .inventory_loader import (
    get_inventory_view
)
from .receipt_loader import (
    get_receipt,
    get_sale_items,
    search_receipts
)



__all__ = [

    "get_setting",

    "get_products",

    "get_warehouses",

    "get_customers",

    "get_suppliers",

    "get_inventory_view",

    "get_default_warehouse_id",
    "get_products",
    "get_active_products",

]
