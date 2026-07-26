# ==============================================================================
# erp_core/loaders/receipt_loader.py
# ERP ENTERPRISE RECEIPT LOADER v2.0
# PRODUCT NAME JOIN ENABLED
# ==============================================================================


from typing import (
    Dict,
    Any,
    List
)


from ..base_repo import (
    db,
    log_error
)





# ==============================================================================
# SALE ITEMS
# ==============================================================================


def get_sale_items(
    sale_id: int
) -> List[Dict[str, Any]]:


    try:


        response = (

            db()

            .table(
                "sale_items"
            )

            .select(
                """
                id,
                sale_id,
                product_id,
                quantity,
                unit_price,
                discount,
                total,
                products(
                    name
                )
                """
            )

            .eq(
                "sale_id",
                sale_id
            )

            .execute()

        )



        items = response.data or []



        for item in items:


            # --------------------------------------------------
            # Product Name From Join
            # --------------------------------------------------

            product = item.get(
                "products"
            ) or {}



            product_name = product.get(
                "name"
            )



            if not product_name:


                product_name = (

                    item.get(
                        "product_name"
                    )

                    or

                    f"Product #{item.get('product_id')}"

                )



            # --------------------------------------------------
            # Compatibility Fields
            # --------------------------------------------------


            item["name"] = product_name


            item["product_name"] = product_name



            item["qty"] = item.get(
                "quantity",
                0
            )



        return items




    except Exception as e:


        log_error(
            f"get_sale_items error : {e}"
        )


        return []







# ==============================================================================
# GET RECEIPT
# ==============================================================================


def get_receipt(
    invoice_no: str
) -> Dict[str, Any]:


    try:


        response = (

            db()

            .table(
                "sales"
            )

            .select(
                "*"
            )

            .eq(
                "invoice_no",
                invoice_no
            )

            .single()

            .execute()

        )


        return response.data or {}




    except Exception as e:


        log_error(
            f"get_receipt error : {e}"
        )


        return {}







# ==============================================================================
# FULL RECEIPT
# ==============================================================================


def get_full_receipt(
    invoice_no: str
) -> Dict[str, Any]:


    try:


        sale = get_receipt(
            invoice_no
        )



        if not sale:


            return {

                "success": False,

                "sale": None,

                "items": []

            }




        items = get_sale_items(

            sale.get(
                "id"
            )

        )



        return {


            "success": True,

            "sale": sale,

            "items": items


        }




    except Exception as e:


        log_error(
            f"get_full_receipt error : {e}"
        )



        return {


            "success": False,

            "sale": None,

            "items": []

        }







# ==============================================================================
# SEARCH RECEIPTS
# ==============================================================================


def search_receipts(
    keyword: str = ""
) -> List[Dict[str, Any]]:


    try:


        query = (

            db()

            .table(
                "sales"
            )

            .select(
                "*"
            )

        )



        if keyword:


            query = (

                query

                .ilike(

                    "invoice_no",

                    f"%{keyword}%"

                )

            )



        response = (

            query

            .order(

                "created_at",

                desc=True

            )

            .execute()

        )



        return response.data or []




    except Exception as e:


        log_error(
            f"search_receipts error : {e}"
        )


        return []
