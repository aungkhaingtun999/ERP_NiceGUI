# ==============================================================================
# erp_core/services/price_import_service.py
#
# ERP ENTERPRISE PRICE IMPORT SERVICE v2.0
#
# Responsibilities:
# - Bulk Price Import Logic
# - Pricing Validation
# - Markup Calculation
# - Owner Price Protection
# - Import Queue Management
#
# Flow:
#
# Excel / API
#       |
#       ↓
# Price Import Service
#       |
#       ↓
# Price Import Repository
#       |
#       ↓
# price_import_queue
#
# ==============================================================================


from typing import (
    Dict,
    Any,
    List
)



from erp_core.loaders.settings_loader import (
    get_setting
)



from erp_core.repositories.price_import_repo import (
    create_price_import,
    get_pending_price_imports,
    get_price_import_history,
    update_price_import_status
)
from erp_core.repositories.product_price_repo import (
    update_product_price
)




# ==============================================================================
# SAFE NUMBER
# ==============================================================================


def safe_float(
    value,
    default=0
):

    try:

        return float(value)

    except Exception:

        return float(default)







# ==============================================================================
# MARKUP CALCULATION
# ==============================================================================


def calculate_selling_price(

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
# GET DEFAULT MARKUP
# ==============================================================================


def get_default_markup():


    return safe_float(

        get_setting(

            "DEFAULT_MARKUP_PERCENT",

            20

        )

    )








# ==============================================================================
# VALIDATE PRODUCT
# ==============================================================================


def validate_product(

    product: Dict[str, Any]

):


    errors = []


    if not product:


        errors.append(

            "Product not found"

        )


        return errors





    # OWNER LOCK CHECK

    if product.get(

        "owner_price_locked",

        False

    ):


        errors.append(

            "Owner price locked"

        )




    return errors







# ==============================================================================
# CREATE IMPORT QUEUE
# ==============================================================================


def import_product_price(

    product: Dict[str,Any],

    markup_percent=None,

    created_by=None

):


    errors = validate_product(
        product
    )



    if errors:


        return {


            "success": False,


            "message":

                ", ".join(errors)


        }




    if markup_percent is None:


        markup_percent = get_default_markup()





    new_price = calculate_selling_price(

        product.get(

            "purchase_price",

            0

        ),

        markup_percent

    )






    payload = {


        "product_id":

            product.get(

                "id"

            ),



        "barcode":

            product.get(

                "barcode"

            ),



        "sku":

            product.get(

                "sku"

            ),



        "name":

            product.get(

                "name"

            ),



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

            markup_percent,



        "new_selling_price":

            new_price,



        "price_source":

            "IMPORT",



        "status":

            "PENDING",



        "created_by":

            created_by


    }






    result = create_price_import(

        payload

    )



    return {


        "success": True,


        "data": result


    }








# ==============================================================================
# BULK IMPORT
# ==============================================================================


def bulk_import_prices(

    products: List[Dict],

    created_by=None

):


    results = []


    for product in products:


        result = import_product_price(

            product,

            created_by=created_by

        )


        results.append(

            result

        )



    return results







# ==============================================================================
# QUEUE
# ==============================================================================


def pending_imports():


    return get_pending_price_imports()







# ==============================================================================
# HISTORY
# ==============================================================================


def import_history(

    limit=100

):


    return get_price_import_history(

        limit

    )








# ==============================================================================
# APPROVE / REJECT
# ==============================================================================


def approve_import(

    import_id,

    user_id

):


    return update_price_import_status(

        import_id,

        "APPROVED",

        user_id

    )





def reject_import(

    import_id,

    user_id,

    reason=None

):


    return update_price_import_status(

        import_id,

        "REJECTED",

        user_id,

        reason

    )






# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "calculate_selling_price",

    "import_product_price",

    "bulk_import_prices",

    "pending_imports",

    "import_history",

    "approve_import",

    "reject_import"

]
