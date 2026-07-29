# ==============================================================================
# erp_core/loaders/receipt_loader.py
# ERP ENTERPRISE RECEIPT LOADER v3.0 FINAL
#
# Features:
#
# - Receipt Header Loading
# - Tax Rate Recovery
# - Receipt Items Join
# - Product Name Support
# - Full Receipt Package
#
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


            product = item.get(

                "products"

            ) or {}



            name = product.get(

                "name"

            )



            if not name:


                name = (

                    item.get(

                        "product_name"

                    )

                    or

                    f"Product #{item.get('product_id')}"

                )



            item["name"] = name


            item["product_name"] = name


            item["qty"] = item.get(

                "quantity",

                0

            )



        return items




    except Exception as e:


        log_error(

            message="Load sale items failed",

            exception=e

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

                """
                id,
                invoice_no,

                customer_id,
                cashier_id,

                subtotal,
                discount,

                tax,
                tax_rate,

                total,
                total_amount,

                paid_amount,
                change_amount,

                payment_method,

                sale_status,
                status,

                warehouse_id,
                counter_id,

                created_at
                """

            )

            .eq(

                "invoice_no",

                invoice_no

            )

            .single()

            .execute()

        )



        sale = response.data or {}




        # ==============================================================
        # TAX RATE RECOVERY
        # ==============================================================


        tax_rate = sale.get(

            "tax_rate"

        )



        if tax_rate is None or tax_rate == 0:


            subtotal = float(

                sale.get(

                    "subtotal",

                    0

                )

            )


            tax = float(

                sale.get(

                    "tax",

                    0

                )

            )



            if subtotal > 0 and tax > 0:


                sale["tax_rate"] = round(

                    (

                        tax

                        /

                        subtotal

                    )

                    *

                    100,

                    2

                )


            else:


                sale["tax_rate"] = 0





        return sale





    except Exception as e:


        log_error(

            message="Get receipt failed",

            exception=e

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

                "success":

                    False,

                "sale":

                    {},

                "items":

                    []

            }





        items = get_sale_items(

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





    except Exception as e:


        log_error(

            message="Full receipt load failed",

            exception=e

        )


        return {


            "success":

                False,


            "sale":

                {},


            "items":

                []

        }








# ==============================================================================
# SEARCH RECEIPTS
# ==============================================================================


def search_receipts(

    keyword: str = ""

) -> List[Dict]:


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


            query = query.ilike(

                "invoice_no",

                f"%{keyword}%"

            )



        result = (

            query

            .order(

                "created_at",

                desc=True

            )

            .execute()

        )



        return result.data or []





    except Exception as e:


        log_error(

            message="Search receipts failed",

            exception=e

        )


        return []








# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "get_receipt",

    "get_sale_items",

    "get_full_receipt",

    "search_receipts"

]
