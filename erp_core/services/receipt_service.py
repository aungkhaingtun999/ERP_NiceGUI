# ==============================================================================
# erp_core/services/receipt_service.py
# ERP ENTERPRISE RECEIPT SERVICE v3.0 FINAL
#
# Responsibilities:
#
# - Receipt Read
# - Receipt Items
# - Full Receipt Package
# - Search
# - Print Ready Data
#
# Flow:
#
# UI
#  |
# ReceiptService
#  |
# ReceiptLoader
#  |
# Supabase
#
# ==============================================================================


from typing import (
    Any,
    Dict,
    List,
    Optional
)


from ..loaders import (

    get_receipt,

    get_sale_items,

    search_receipts

)





# ==============================================================================
# RECEIPT SERVICE
# ==============================================================================


class ReceiptService:



    def __init__(

        self,

        client: Any = None

    ):


        self.client = client






    # ==========================================================================
    # GET RECEIPT HEADER
    # ==========================================================================


    def get_receipt(

        self,

        invoice_no: str

    ) -> Optional[Dict]:



        if not invoice_no:


            return None



        return get_receipt(

            invoice_no

        )








    # ==========================================================================
    # GET ITEMS
    # ==========================================================================


    def get_sale_items(

        self,

        sale_id: int

    ) -> List[Dict]:



        if not sale_id:


            return []



        return get_sale_items(

            sale_id

        )








    # ==========================================================================
    # SEARCH
    # ==========================================================================


    def search_receipts(

        self,

        keyword: str = ""

    ) -> List[Dict]:



        return search_receipts(

            keyword

        )








    # ==========================================================================
    # FULL RECEIPT
    #
    # Return:
    #
    # {
    #    sale : {},
    #    items : []
    # }
    #
    # ==========================================================================


    def load_receipt(

        self,

        invoice_no: str

    ) -> Optional[Dict]:



        sale = self.get_receipt(

            invoice_no

        )



        if not sale:


            return None





        items = self.get_sale_items(

            sale.get(

                "id"

            )

        )





        return {


            "success":

                True,


            "sale":

                sale,


            "items":

                items

        }








    # ==========================================================================
    # RECEIPT EXISTS
    # ==========================================================================


    def receipt_exists(

        self,

        invoice_no: str

    ) -> bool:



        return (

            self.get_receipt(

                invoice_no

            )

            is not None

        )







# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "ReceiptService"

]
