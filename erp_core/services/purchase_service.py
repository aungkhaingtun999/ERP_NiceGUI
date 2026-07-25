# ==============================================================================
# erp_core/services/purchase_service.py
# ERP ENTERPRISE PURCHASE SERVICE
# WITH AUTO PRICING ENGINE
# ==============================================================================


from typing import (
    Optional,
    Dict,
    Any
)


from ..base_repo import (
    money,
    validate_uuid,
    log_error
)


from ..context import (
    ERPContext,
    CacheManager
)


from ..rpc.engine import (
    RPCEngine
)


from .pricing_service import (
    PricingService
)





class PurchaseService:


    def __init__(
        self,
        client
    ):


        self.client = client


        # ----------------------------------------------------------
        # Pricing Engine
        # ----------------------------------------------------------

        self.pricing = PricingService(
            client
        )





    # ==================================================================
    # RECEIVE PURCHASE STOCK
    # ==================================================================

    def receive_stock(

        self,

        product_id: int,

        supplier_id: int,

        warehouse_id: int,

        qty: int,

        cost: Any,

        payment_method: str = "credit",

        remarks: str = "",

        user_id: Optional[str] = None

    ) -> Dict[str, Any]:



        try:


            context = ERPContext.get_current()


            context.rotate_transaction()



            # ------------------------------------------------------
            # AUTO SELLING PRICE CALCULATION
            # ------------------------------------------------------

            selling_price = (
    self.pricing
    .calculate_selling_price(
        cost,
        product_id
    )
            )


            # ------------------------------------------------------
            # CALL SUPABASE RPC
            # ------------------------------------------------------

            result = RPCEngine.execute(


                self.client,


                "purchase_receive_rpc",


                {


                    "p_product_id":

                        int(product_id),



                    "p_supplier_id":

                        int(supplier_id),



                    "p_warehouse_id":

                        int(warehouse_id),



                    "p_qty":

                        int(qty),



                    "p_price":

                        float(

                            money(cost)

                        ),



                    "p_selling_price":

                        float(

                            selling_price

                        ),



                    "p_notes":

                        str(

                            remarks

                        ),



                    "p_created_by":

                        validate_uuid(

                            user_id

                        )

                }

            )
            if result.get("success"):

    self.pricing.update_product_price(
        product_id,
        selling_price
    )



            # ------------------------------------------------------
            # CACHE REFRESH
            # ------------------------------------------------------

            if isinstance(result, dict):


                if result.get(
                    "success"
                ):


                    CacheManager.bump_version(

                        "inventory_version"

                    )


            return result



        except Exception as e:


            log_error(

                f"PurchaseService.receive_stock error: {e}"

            )


            return {


                "success": False,


                "message": str(e),


                "data": None

            }
