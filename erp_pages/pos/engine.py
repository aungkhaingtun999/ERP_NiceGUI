# ==============================================================================
# erp_pages/pos/engine.py
# ERP ENTERPRISE POS PRICE ENGINE v12.9 FINAL
#
# Responsibilities:
# - Final selling price calculation
# - Owner price priority
# - Product markup
# - Category markup
# - Global markup
# - Settings driven pricing
#
# Flow:
#
# OWNER PRICE LOCK
#        ↓
# PRODUCT MARKUP
#        ↓
# CATEGORY MARKUP
#        ↓
# GLOBAL MARKUP
#        ↓
# FINAL SELLING PRICE
#
# ==============================================================================


from typing import (
    Dict,
    Any
)



from erp_core.loaders.settings_loader import (
    get_setting
)


from erp_core.config import (
    PRICE_SOURCE_OWNER,
    PRICE_SOURCE_PRODUCT,
    PRICE_SOURCE_CATEGORY,
    PRICE_SOURCE_GLOBAL,
    PRICE_SOURCE_SYSTEM
)





# ==============================================================================
# SAFE NUMBER
# ==============================================================================


def safe_float(value, default=0.0):


    try:

        return float(value)


    except Exception:

        return float(default)





# ==============================================================================
# GET SETTINGS
# ==============================================================================


def pricing_settings():


    return {


        "enable_product":

            str(

                get_setting(

                    "ENABLE_PRODUCT_MARKUP",

                    True

                )

            ).lower() == "true",



        "enable_category":

            str(

                get_setting(

                    "ENABLE_CATEGORY_MARKUP",

                    True

                )

            ).lower() == "true",



        "default_markup":

            safe_float(

                get_setting(

                    "DEFAULT_MARKUP_PERCENT",

                    40

                )

            ),



        "priority":

            str(

                get_setting(

                    "PRICING_PRIORITY",

                    "PRODUCT_FIRST"

                )

            ),



        "method":

            str(

                get_setting(

                    "PRICING_METHOD",

                    "MARKUP"

                )

            )

    }





# ==============================================================================
# MARKUP CALCULATION
# ==============================================================================


def apply_markup(

    cost,

    markup

):


    return round(

        cost +

        (

            cost *

            markup /

            100

        ),

        2

    )





# ==============================================================================
# FINAL PRICE ENGINE
# ==============================================================================


def get_final_price(

    product: Dict[str, Any]

):


    if not product:


        return {


            "price":

                0,


            "source":

                PRICE_SOURCE_SYSTEM


        }





    settings = pricing_settings()



    # --------------------------------------------------
    # COST BASE
    # --------------------------------------------------


    cost = safe_float(

        product.get(

            "purchase_price",

            product.get(

                "cost",

                0

            )

        )

    )





    # --------------------------------------------------
    # OWNER PRICE LOCK
    # --------------------------------------------------


    owner_locked = product.get(

        "owner_price_locked",

        False

    )



    owner_price = product.get(

        "owner_selling_price"

    )



    if owner_locked and owner_price:


        return {


            "price":

                safe_float(

                    owner_price

                ),



            "source":

                PRICE_SOURCE_OWNER

        }





    # --------------------------------------------------
    # CURRENT SELLING PRICE
    # --------------------------------------------------


    current_price = safe_float(

        product.get(

            "selling_price",

            product.get(

                "final_selling_price",

                0

            )

        )

    )





    # --------------------------------------------------
    # PRODUCT MARKUP
    # --------------------------------------------------


    product_markup = safe_float(

        product.get(

            "product_markup",

            product.get(

                "markup_percent",

                0

            )

        )

    )





    category_markup = safe_float(

        product.get(

            "category_markup",

            0

        )

    )





    default_markup = settings[

        "default_markup"

    ]





    priority = settings[

        "priority"

    ]





    # --------------------------------------------------
    # PRODUCT FIRST
    # --------------------------------------------------


    if priority == "PRODUCT_FIRST":



        if (

            settings["enable_product"]

            and

            product_markup > 0

        ):


            return {


                "price":

                    apply_markup(

                        cost,

                        product_markup

                    ),



                "source":

                    PRICE_SOURCE_PRODUCT

            }




        if (

            settings["enable_category"]

            and

            category_markup > 0

        ):


            return {


                "price":

                    apply_markup(

                        cost,

                        category_markup

                    ),



                "source":

                    PRICE_SOURCE_CATEGORY

            }






    # --------------------------------------------------
    # CATEGORY FIRST
    # --------------------------------------------------


    if priority == "CATEGORY_FIRST":



        if (

            settings["enable_category"]

            and

            category_markup > 0

        ):


            return {


                "price":

                    apply_markup(

                        cost,

                        category_markup

                    ),



                "source":

                    PRICE_SOURCE_CATEGORY

            }





        if (

            settings["enable_product"]

            and

            product_markup > 0

        ):


            return {


                "price":

                    apply_markup(

                        cost,

                        product_markup

                    ),



                "source":

                    PRICE_SOURCE_PRODUCT

            }





    # --------------------------------------------------
    # GLOBAL MARKUP
    # --------------------------------------------------


    if default_markup > 0:


        return {


            "price":

                apply_markup(

                    cost,

                    default_markup

                ),



            "source":

                PRICE_SOURCE_GLOBAL

        }





    # --------------------------------------------------
    # FALLBACK CURRENT PRICE
    # --------------------------------------------------


    return {


        "price":

            current_price,



        "source":

            PRICE_SOURCE_SYSTEM

    }
