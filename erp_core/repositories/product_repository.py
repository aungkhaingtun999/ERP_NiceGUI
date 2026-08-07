# ==============================================================================
# erp_core/repositories/product_repository.py
# ERP ENTERPRISE PRODUCT REPOSITORY v31.0
#
# Owner Price + Dynamic Pricing Ready
#
# Supabase
#       ↓
# Repository
#       ↓
# Loader
#       ↓
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
    ERP Product Database Layer

    Supports:

    - Warehouse Stock
    - Owner Price
    - Product Markup
    - Dynamic Selling Price
    - POS Search

    """



    # ==========================================================================
    # INVENTORY MASTER PRODUCTS
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
                    TABLE_WAREHOUSE_STOCK
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

                    ),


                    warehouses(

                        id,

                        name

                    )

                    """

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



            if keyword:


                keyword = str(
                    keyword
                ).strip()



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



            for row in result.data or []:


                product = row.get(
                    "products"
                ) or {}



                warehouse = row.get(
                    "warehouses"
                ) or {}



                rows.append({


                    "id":

                    product.get(
                        "id"
                    ),



                    "name":

                    product.get(
                        "name"
                    ),



                    "sku":

                    product.get(
                        "sku"
                    ),



                    "barcode":

                    product.get(
                        "barcode"
                    ),



                    "purchase_price":

                    product.get(
                        "purchase_price"
                    ),



                    "selling_price":

                    product.get(
                        "selling_price"
                    ),



                    # ==============================
                    # OWNER PRICE SYSTEM
                    # ==============================


                    "owner_selling_price":

                    product.get(
                        "owner_selling_price"
                    ),



                    "final_selling_price":

                    product.get(
                        "final_selling_price"
                    ),



                    "price_source":

                    product.get(
                        "price_source"
                    ),



                    "owner_price_locked":

                    product.get(
                        "owner_price_locked"
                    ),



                    "markup_percent":

                    product.get(
                        "markup_percent"
                    ),



                    "minimum_stock":

                    product.get(
                        "minimum_stock"
                    ),



                    "unit":

                    product.get(
                        "unit"
                    ),



                    "notes":

                    product.get(
                        "notes"
                    ),



                    "warehouse_id":

                    row.get(
                        "warehouse_id"
                    ),



                    "warehouse":

                    warehouse.get(
                        "name"
                    ),



                    "qty":

                    row.get(
                        "qty"
                    ),



                    "reserved_qty":

                    row.get(
                        "reserved_qty"
                    ),



                    "available_qty":

                    row.get(
                        "available_qty"
                    )

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

                message="Product get_products failed",

                exception=e

            )


            return []







    # ==========================================================================
    # GET SINGLE PRODUCT
    # Pricing Engine Source
    # ==========================================================================


    def get_product(

        self,

        product_id: int

    ) -> Optional[Dict[str, Any]]:


        try:


            result = (

                self.client

                .table(

                    TABLE_PRODUCTS

                )

                .select(

                    """

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

                    category_id,


                    minimum_stock,

                    unit,

                    notes,

                    is_active

                    """

                )

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

                message="Product get_product failed",

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

                message="Product search failed",

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

                message="Barcode lookup failed",

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

                message="SKU lookup failed",

                exception=e

            )


            return None
