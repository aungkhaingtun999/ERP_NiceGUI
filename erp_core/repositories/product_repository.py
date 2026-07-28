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



from ..config import (
    TABLE_PRODUCT_VIEW
)


from ..base_repo import (
    log_error
)


from .base_repository import (
    BaseRepository
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
