# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v4.0 FINAL
#
# Responsibility:
#
# - Settings Read Layer
# - Settings Cache
# - Type Conversion
# - Settings Service Bridge
#
# Flow:
#
# Supabase
#      ↓
# SettingsService
#      ↓
# SettingsLoader
#      ↓
# ERP UI / Pricing Engine / POS
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
# CACHE LOAD
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

            message="Load settings cache failed",

            exception=e

        )


        return {}







# ==============================================================================
# GET SINGLE SETTING
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
# SAVE SETTING
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

            "success":

                False,


            "message":

                str(e)

        }








# ==============================================================================
# SAVE MULTIPLE
# ==============================================================================


def save_settings(

    settings:dict

):


    try:


        service = get_settings_service()


        result = service.save_settings(

            settings

        )


        clear_settings_cache()


        return result



    except Exception as e:


        log_error(

            message="Save multiple settings failed",

            exception=e

        )


        return {

            "success":

                False,


            "message":

                str(e)

        }








# ==============================================================================
# TYPE HELPERS
#
# Supports:
#
# New:
# get_float(settings,"KEY",10)
#
# Old:
# get_float("KEY",10)
#
# ==============================================================================


def _normalize_args(

    settings,

    key,

    default

):


    if isinstance(

        settings,

        str

    ):


        return (

            get_all_settings_cached(),

            settings,

            key if key is not None else default

        )



    return (

        settings,

        key,

        default

    )







def get_bool(

    settings,

    key=None,

    default=False

):


    try:


        settings,key,default = _normalize_args(

            settings,

            key,

            default

        )



        value = str(

            settings.get(

                key,

                default

            )

        ).lower()



        return value in (

            "true",

            "1",

            "yes",

            "on"

        )



    except Exception:


        return bool(default)







def get_float(

    settings,

    key=None,

    default=0.0

):


    try:


        settings,key,default = _normalize_args(

            settings,

            key,

            default

        )



        return float(

            settings.get(

                key,

                default

            )

        )



    except Exception:


        return float(default)







def get_int(

    settings,

    key=None,

    default=0

):


    try:


        settings,key,default = _normalize_args(

            settings,

            key,

            default

        )



        return int(

            settings.get(

                key,

                default

            )

        )



    except Exception:


        return int(default)







def get_text(

    settings,

    key=None,

    default=""

):


    try:


        settings,key,default = _normalize_args(

            settings,

            key,

            default

        )



        return str(

            settings.get(

                key,

                default

            )

        )



    except Exception:


        return str(default)







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

    "save_settings",

    "get_bool",

    "get_float",

    "get_int",

    "get_text",

    "clear_settings_cache"

]
