# ==============================================================================
# erp_pages/inventory/product_search.py
# MOBILE INVENTORY v3
# Product Search Engine
# ==============================================================================
from database import get_products


def search_product(keyword):

    if keyword is None:
        return None

    keyword = str(keyword).strip()

    products = get_products()

    for p in products:

        barcode = str(
            p.get("barcode") or ""
        ).strip()

        sku = str(
            p.get("sku") or ""
        ).strip()

        if barcode == keyword:
            return p

        if sku == keyword:
            return p

    return None
