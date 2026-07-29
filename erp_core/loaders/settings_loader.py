# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v4.0 FINAL
#
# Compatible:
#
# 12_Settings.py
# PricingService
# POS
# ERP Core
#
# Supports:
#
# get_float(key)
# get_float(settings,key,default)
#
# ==============================================================================


import streamlit as st



from ..base_repo import (
    db,
    log_error
)


from ..services.settings_service import (
    SettingsService
)



# ==============================================================================
# SERVICE
# ==============================================================================


def get_settings_service():

    return SettingsService(
        db()
    )



# ==============================================================================
# CACHE
# ==============================================================================


@st.cache_data(
    ttl=300,
    show_spinner=False
)
def get_all_settings_cached():


    try:

        service = get_settings_service()

        return service.get_all_settings()


    except Exception as e:

        log_error(
            message="Settings cache failed",
            exception=e
        )

        return {}



# ==============================================================================
# GET SINGLE
# ==============================================================================


def get_setting(

    key,

    default=None

):


    settings = get_all_settings_cached()


    return settings.get(

        key,

        default

    )



# ==============================================================================
# SAVE
# ==============================================================================


def save_setting(

    key,

    value

):


    try:

        service = get_settings_service()


        result = service.save_setting(
            key,
            value
        )


        clear_settings_cache()


        return result



    except Exception as e:


        log_error(
            message="Save setting failed",
            exception=e
        )


        return {

            "success":False,

            "message":str(e)

        }

# ==============================================================================
# TYPE HELPERS
# ==============================================================================


def _resolve_setting_args(

    args,

    default=None

):

    """
    Support:

    get_float(key)

    get_float(settings,key,default)

    """



    if len(args) == 1:


        key = args[0]


        settings = get_all_settings_cached()



    elif len(args) >= 2:


        if isinstance(
            args[0],
            dict
        ):

            settings = args[0]

            key = args[1]


            if len(args) >= 3:

                default = args[2]



        else:

            key = args[0]

            settings = get_all_settings_cached()


            if len(args) >= 2:

                default = args[1]



    else:


        raise ValueError(
            "Invalid setting arguments"
        )



    return (

        settings,

        key,

        default

    )






# ==============================================================================
# BOOLEAN
# ==============================================================================


def get_bool(

    *args

):


    try:


        settings, key, default = _resolve_setting_args(
            args,
            False
        )


        value = settings.get(

            key,

            default

        )



        return str(value).lower() == "true"



    except Exception:


        return False






# ==============================================================================
# FLOAT
# ==============================================================================


def get_float(

    *args

):


    try:


        settings, key, default = _resolve_setting_args(
            args,
            0.0
        )


        value = settings.get(

            key,

            default

        )


        return float(value)



    except Exception:


        try:

            return float(default)

        except Exception:

            return 0.0







# ==============================================================================
# INTEGER
# ==============================================================================


def get_int(

    *args

):


    try:


        settings, key, default = _resolve_setting_args(
            args,
            0
        )


        value = settings.get(

            key,

            default

        )


        return int(value)



    except Exception:


        try:

            return int(default)

        except Exception:

            return 0







# ==============================================================================
# TEXT
# ==============================================================================


def get_text(

    *args

):


    try:


        settings, key, default = _resolve_setting_args(
            args,
            ""
        )


        return str(

            settings.get(

                key,

                default

            )

        )



    except Exception:


        return str(default or "")

# ==============================================================================
# CACHE CLEAR
# ==============================================================================


def clear_settings_cache():


    try:


        get_all_settings_cached.clear()


        return True



    except Exception as e:


        log_error(

            message="Clear settings cache failed",

            exception=e

        )


        return False







# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "get_all_settings_cached",

    "get_setting",

    "save_setting",

    "get_bool",

    "get_float",

    "get_int",

    "get_text",

    "clear_settings_cache"

]



# ==============================================================================
# END
# ==============================================================================
