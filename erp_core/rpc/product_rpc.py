# ==============================================================================
# erp_core/rpc/product_rpc.py
# ERP ENTERPRISE PRODUCT RPC v1.0
#
# Product Master Update RPC
# Compatible:
#     pages/2_Inventory.py
#     database.py legacy bridge
#
# ==============================================================================


from ..base_repo import db, log_error



# ==============================================================================
# UPDATE PRODUCT
# ==============================================================================


def update_product_rpc(

    product_id,

    name,

    sku,

    barcode,

    purchase_price,

    selling_price,

    minimum_stock,

    unit,

    notes,

    is_active=True

):


    try:


        client = db()



        # ==============================================================
        # LOAD OLD PRODUCT
        # ==============================================================


        old_result = (

            client

            .table("products")

            .select(

                """
                id,
                sku,
                barcode,
                minimum_stock,
                unit,
                notes
                """

            )

            .eq(

                "id",

                int(product_id)

            )

            .single()

            .execute()

        )



        old_data = old_result.data



        if not old_data:


            return {

                "success": False,

                "message":
                f"Product ID {product_id} not found"

            }




        # ==============================================================
        # KEEP OLD VALUES
        # ==============================================================


        final_sku = (

            str(sku).strip()

            if sku and str(sku).strip()

            else old_data.get("sku")

        )



        final_barcode = (

            str(barcode).strip()

            if barcode and str(barcode).strip()

            else old_data.get("barcode")

        )



        final_min_stock = (

            int(minimum_stock)

            if minimum_stock is not None

            else int(
                old_data.get(
                    "minimum_stock",
                    0
                )
            )

        )




        # ==============================================================
        # UPDATE PAYLOAD
        # ==============================================================


        payload = {


            "name":
            str(name).strip(),



            "sku":
            final_sku,



            "barcode":
            final_barcode,



            "purchase_price":
            float(purchase_price),



            "selling_price":
            float(selling_price),



            "minimum_stock":
            final_min_stock,



            "unit":
            str(unit).strip()
            if unit
            else "pcs",



            "notes":
            notes,



            "is_active":
            bool(is_active)


        }



        print(
            "ERP PRODUCT UPDATE PAYLOAD =",
            payload
        )




        # ==============================================================
        # UPDATE
        # ==============================================================


        result = (

            client

            .table("products")

            .update(

                payload

            )

            .eq(

                "id",

                int(product_id)

            )

            .execute()

        )




        # ==============================================================
        # VERIFY
        # ==============================================================


        verify = (

            client

            .table("products")

            .select(

                """
                id,
                name,
                sku,
                barcode,
                purchase_price,
                selling_price,
                minimum_stock,
                unit,
                notes
                """

            )

            .eq(

                "id",

                int(product_id)

            )

            .single()

            .execute()

        )



        return {


            "success":

            True,


            "message":

            "Product updated successfully",



            "data":

            verify.data


        }





    except Exception as e:


        log_error(

            message=
            "update_product_rpc failed",

            exception=e

        )


        return {


            "success":

            False,


            "message":

            str(e)


        }
