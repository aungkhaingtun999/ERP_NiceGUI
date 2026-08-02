# ==============================================================================
# erp_pages/inventory/product_search.py
# MOBILE INVENTORY v3
# Product Search Engine
# ==============================================================================
from database import get_products

def search_product(keyword):

if not keyword:
    return None

keyword = str(keyword).strip()

products = get_products()

for p in products:

    barcode = str(
        p.get("barcode", "")
    ).strip()

    if barcode == keyword:
        return p

return None
