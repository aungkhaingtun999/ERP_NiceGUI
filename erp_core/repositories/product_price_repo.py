# ==============================================================================
# erp_core/repositories/product_price_repo.py
#
# ERP ENTERPRISE PRODUCT PRICE REPOSITORY v1.0
#
# Responsibilities:
# - Update Product Selling Price
# - Update Final Price
# - Update Price Source
#
# ==============================================================================


from erp_core.base_repo import (
    db,
    safe_execute,
    serialize_json
)



# ==============================================================================
# UPDATE PRODUCT PRICE
# ==============================================================================


def update_product_price(

    product_id,

    selling_price,

    price_source="IMPORT"

):


    def action():


        payload = {


            "selling_price":
                selling_price,


            "final_selling_price":
                selling_price,


            "price_source":
                price_source


        }



        result = (

            db()
            .table(
                "products"
            )
            .update(
                serialize_json(
                    payload
                )
            )
            .eq(
                "id",
                product_id
            )
            .execute()

        )


        return result.data



    return safe_execute(

        action,

        "Update product price failed"

    )
