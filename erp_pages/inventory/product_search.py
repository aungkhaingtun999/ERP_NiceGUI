# ==============================================================================
# erp_pages/inventory/product_search.py
# MOBILE INVENTORY v2
# Product Search Engine
# ==============================================================================


from database import supabase



# ==============================================================================
# SEARCH BY BARCODE / SKU / NAME
# ==============================================================================


def search_product(keyword):

    if not keyword:
        return None


    keyword = keyword.strip()


    # -------------------------------------------------
    # 1. Barcode Exact
    # -------------------------------------------------

    result = (
        supabase
        .table("products")
        .select("*")
        .eq("barcode", keyword)
        .execute()
    )


    if result.data:
        return result.data[0]



    # -------------------------------------------------
    # 2. SKU Exact
    # -------------------------------------------------

    result = (
        supabase
        .table("products")
        .select("*")
        .eq("sku", keyword)
        .execute()
    )


    if result.data:
        return result.data[0]



    # -------------------------------------------------
    # 3. Product Name Search
    # -------------------------------------------------

    result = (
        supabase
        .table("products")
        .select("*")
        .ilike(
            "name",
            f"%{keyword}%"
        )
        .limit(10)
        .execute()
    )


    if result.data:

        return result.data[0]


    return None



# ==============================================================================
# PRODUCT CARD FORMAT
# ==============================================================================


def product_card(product):

    if not product:
        return None


    return {

        "id":
            product.get("id"),

        "barcode":
            product.get("barcode"),

        "sku":
            product.get("sku"),

        "name":
            product.get("name"),

        "purchase_price":
            product.get("purchase_price",0),

        "selling_price":
            product.get("selling_price",0),

        "stock":
            product.get("stock",0),

        "unit":
            product.get("unit","pcs")

    }