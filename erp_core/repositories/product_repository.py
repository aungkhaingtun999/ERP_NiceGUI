# ==============================================================================
# erp_core/repositories/product_repository.py
# ERP ENTERPRISE PRODUCT REPOSITORY v30
# ==============================================================================


from typing import (
    List,
    Dict,
    Any,
    Optional
)


from ..config import (
    Tables,
    TABLE_PRODUCT_VIEW,
)


from ..base_repo import (
    safe_execute,
    log_error,
)


from .base_repository import BaseRepository





class ProductRepository(BaseRepository):
    """
    Product database operations
    """



    # --------------------------------------------------------------------------
    # GET PRODUCTS
    # --------------------------------------------------------------------------

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

                query = query.eq(
                    "warehouse_id",
                    int(warehouse_id)
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
                f"get_products error: {e}"
            )

            return []





    # --------------------------------------------------------------------------
    # GET SINGLE PRODUCT
    # --------------------------------------------------------------------------

    def get_product(
        self,
        product_id: int
    ):


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
                f"get_product error: {e}"
            )

            return None





    # --------------------------------------------------------------------------
    # SEARCH PRODUCT
    # --------------------------------------------------------------------------

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


            if keyword:

                query = query.ilike(
                    "name",
                    f"%{keyword}%"
                )


            if warehouse_id:

                query = query.eq(
                    "warehouse_id",
                    int(warehouse_id)
                )


            result = (
                query
                .execute()
            )


            return result.data or []


        except Exception as e:

            log_error(
                f"product search error: {e}"
            )

            return []
