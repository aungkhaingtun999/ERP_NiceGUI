# ==============================================================================
# erp_core/services/price_import_service.py
#
# ERP ENTERPRISE PRICE IMPORT SERVICE v1.0
#
# Responsibilities:
# - Bulk price import validation
# - Pricing calculation
# - Owner price lock protection
# - Import queue creation
#
# ==============================================================================


from decimal import Decimal


from erp_core.loaders.settings_loader import (
    get_setting
)


from erp_core.base_repo import (
    execute_insert
)



# ==============================================================================
# SAFE NUMBER
# ==============================================================================


def safe_float(value, default=0):

    try:
        return float(value)

    except Exception:
        return float(default)





# ==============================================================================
# PRICE CALCULATION
# ==============================================================================


def calculate_import_price(
    purchase_price,
    markup_percent
):


    purchase_price = safe_float(
        purchase_price
    )


    markup_percent = safe_float(
        markup_percent
    )


    return round(
        purchase_price
        +
        (
            purchase_price
            *
            markup_percent
            /
            100
        ),
        2
    )





# ==============================================================================
# VALIDATE PRODUCT PRICE
# ==============================================================================


def validate_product_price(product):


    errors = []


    if not product:

        errors.append(
            "Product not found"
        )


    else:


        if product.get(
            "owner_price_locked"
        ):

            errors.append(
                "OWNER PRICE LOCKED"
            )



    return errors





# ==============================================================================
# CREATE IMPORT ROW
# ==============================================================================


def create_price_import_row(

    product,

    new_price,

    markup_percent,

    created_by=None

):


    errors = validate_product_price(
        product
    )


    if errors:


        return {

            "success": False,

            "message": ", ".join(errors)

        }



    data = {


        "product_id":
            product.get("id"),


        "barcode":
            product.get("barcode"),


        "sku":
            product.get("sku"),


        "name":
            product.get("name"),


        "old_selling_price":
            safe_float(
                product.get(
                    "selling_price",
                    0
                )
            ),


        "purchase_price":
            safe_float(
                product.get(
                    "purchase_price",
                    0
                )
            ),


        "markup_percent":
            safe_float(
                markup_percent
            ),


        "new_selling_price":
            safe_float(
                new_price
            ),


        "price_source":
            "IMPORT",


        "status":
            "PENDING",


        "created_by":
            created_by

    }


    result = execute_insert(
        "price_import_queue",
        data
    )


    return {


        "success": True,

        "data": result

    }