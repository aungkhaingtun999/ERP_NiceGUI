# ==============================================================================
# pos_sync.py
# ERP PRODUCT ACCESS BRIDGE
# Enterprise Migration v1
#
# OLD:
# Session Cache
#
# NEW:
# ERP Product Loader
# ==============================================================================


from erp_core.loaders.product_loader import (
    get_pos_products
)



def load_pos_products(
    warehouse_id=None,
    search=None
):
    """
    POS Product Loader
    Single Source Of Truth
    """

    return get_pos_products(
        warehouse_id=warehouse_id,
        search=search
    )