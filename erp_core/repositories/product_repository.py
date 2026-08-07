# ==============================================================================
# erp_core/repositories/product_repository.py
# ERP ENTERPRISE PRODUCT REPOSITORY v30.1 FINAL
#
# Database Layer
#
# Supabase
#     ↓
# Repository
#     ↓
# Loader
#     ↓
# POS / Inventory / Sales
#
# ==============================================================================


from typing import (
    List,
    Dict,
    Any,
    Optional
)



from ..base_repo import (
    log_error
)


from .base_repository import (
    BaseRepository
)

from ..config import (
    TABLE_PRODUCT_VIEW,
    TABLE_PRODUCTS,
    TABLE_WAREHOUSE_STOCK
)



# ==============================================================================
# PRODUCT REPOSITORY
# ==============================================================================


class ProductRepository(BaseRepository):


    """
    ERP Product Database Operations

    Source:

    pos_products_view

    Contains:

    - Product Info
    - Pricing Engine Result
    - Warehouse Stock
    - Available Quantity

    """

    # ==========================================================================
    # INVENTORY MASTER VIEW
    # ==========================================================================

    def get_inventory_products(
        self,
        warehouse_id=None,
        keyword=None,
        limit=100
    ):

        try:

            query = (

                self.client

                .table(
                    "warehouse_stock"
                )

                .select(
                    """
                    warehouse_id,
                    qty,
                    reserved_qty,
                    available_qty,

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
                    owner_price_locked,

                    markup_percent,

                    minimum_stock,
                    unit,
                    notes,
                    is_active
                 )

                    warehouses(
                        id,
                        name
                    )
                    """
                )

            )


            if warehouse_id is not None:

                query = (
                    query.eq(
                        "warehouse_id",
                        int(warehouse_id)
                    )
                )


            if keyword:

                keyword = str(keyword).strip()

                query = (
                    query
                    .or_(
                        f"products.name.ilike.%{keyword}%,"
                        f"products.sku.ilike.%{keyword}%,"
                        f"products.barcode.ilike.%{keyword}%"
                    )
                )


            result = (
                query
                .limit(limit)
                .execute()
            )


            rows = []


            for x in result.data or []:

                p = x.get("products") or {}
                w = x.get("warehouses") or {}


                rows.append({

                    "id":
                    p.get("id"),

                    "name":
                    p.get("name"),

                    "sku":
                    p.get("sku"),

                    "barcode":
                    p.get("barcode"),

                    "purchase_price":
                    p.get("purchase_price"),

                    "selling_price":
                    p.get("selling_price"),

                    "minimum_stock":
                    p.get("minimum_stock"),
                    "owner_selling_price":
                    p.get("owner_selling_price"),

                    "final_selling_price":
                     p.get("final_selling_price"),

                    "price_source":
                     p.get("price_source"),

                    "owner_price_locked":
                     p.get("owner_price_locked"),

                    "markup_percent":
                     p.get("markup_percent"),

                    "unit":
                    p.get("unit"),

                    "warehouse_id":
                    x.get("warehouse_id"),

                    "warehouse":
                    w.get("name"),

                    "qty":
                    x.get("qty"),

                    "reserved_qty":
                    x.get("reserved_qty"),

                    "available_qty":
                    x.get("available_qty"),

                })


            return rows


        except Exception as e:

            log_error(
                message="Inventory product load failed",
                exception=e
            )

            return []


    # ==========================================================================
    # GET PRODUCTS
    # ==========================================================================


    def get_products(

        self,

        warehouse_id: Optional[int] = None,

        offset: int = 0,

        limit: int = 100

    ) -> List[Dict[str, Any]]:


        try:


            query = (

                self.client

                .table(

                    TABLE_PRODUCT_VIEW

                )

                .select("*")

            )




            if warehouse_id is not None:


                query = (

                    query

                    .eq(

                        "warehouse_id",

                        int(warehouse_id)

                    )

                )





            result = (

                query

                .range(

                    offset,

                    offset + limit - 1

                )

                .execute()

            )




            return result.data or []




        except Exception as e:


            log_error(

                message=

                "Product get_products failed",

                exception=e

            )


            return []







    # ==========================================================================
    # GET SINGLE PRODUCT
    # ==========================================================================


    def get_product(

        self,

        product_id: int

    ) -> Optional[Dict[str, Any]]:


        try:


            result = (

                self.client

                .table(

                    TABLE_PRODUCT_VIEW

                )

                .select("*")

                .eq(

                    "id",

                    int(product_id)

                )

                .maybe_single()

                .execute()

            )



            return result.data





        except Exception as e:


            log_error(

                message=

                "Product get_product failed",

                exception=e

            )


            return None







    # ==========================================================================
    # SEARCH PRODUCT
    # ==========================================================================


    def search(

        self,

        keyword: Optional[str] = None,

        warehouse_id: Optional[int] = None

    ) -> List[Dict[str, Any]]:



        try:



            query = (

                self.client

                .table(

                    TABLE_PRODUCT_VIEW

                )

                .select("*")

            )





            if warehouse_id is not None:


                query = (

                    query

                    .eq(

                        "warehouse_id",

                        int(warehouse_id)

                    )

                )






            if keyword:



                keyword = str(

                    keyword

                ).strip()



                query = (

                    query

                    .or_(

                        f"name.ilike.%{keyword}%,"

                        f"sku.ilike.%{keyword}%,"

                        f"barcode.ilike.%{keyword}%"

                    )

                )






            result = (

                query

                .execute()

            )





            return result.data or []






        except Exception as e:


            log_error(

                message=

                "Product search failed",

                exception=e

            )


            return []







    # ==========================================================================
    # BARCODE LOOKUP
    # ==========================================================================


    def get_by_barcode(

        self,

        barcode: str,

        warehouse_id: Optional[int] = None

    ):


        try:


            query = (

                self.client

                .table(

                    TABLE_PRODUCT_VIEW

                )

                .select("*")

                .eq(

                    "barcode",

                    barcode

                )

            )




            if warehouse_id is not None:


                query = (

                    query

                    .eq(

                        "warehouse_id",

                        int(warehouse_id)

                    )

                )





            result = (

                query

                .maybe_single()

                .execute()

            )




            return result.data




        except Exception as e:


            log_error(

                message=

                "Barcode lookup failed",

                exception=e

            )


            return None






    # ==========================================================================
    # SKU LOOKUP
    # ==========================================================================


    def get_by_sku(

        self,

        sku: str,

        warehouse_id: Optional[int] = None

    ):


        try:


            query = (

                self.client

                .table(

                    TABLE_PRODUCT_VIEW

                )

                .select("*")

                .eq(

                    "sku",

                    sku

                )

            )




            if warehouse_id is not None:


                query = (

                    query

                    .eq(

                        "warehouse_id",

                        int(warehouse_id)

                    )

                )





            result = (

                query

                .maybe_single()

                .execute()

            )




            return result.data





        except Exception as e:


            log_error(

                message=

                "SKU lookup failed",

                exception=e

            )


            return None
                
