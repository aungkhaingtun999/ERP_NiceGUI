# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v31.0 FINAL
#
# Responsibility:
#
# - Settings Read Layer
# - Settings Cache
# - Type Conversion
# - Service Bridge
#
# Flow:
#
# Supabase
#      ↓
# SettingsService
#      ↓
# SettingsLoader
#      ↓
# ERP UI / Engine
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
# SERVICE INSTANCE
# ==============================================================================


def get_settings_service():

    return SettingsService(

        db()

    )







# ==============================================================================
# CACHE VERSION
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

            message="Cached settings load failed",

            exception=e

        )


        return {}







# ==============================================================================
# GET SETTING
# ==============================================================================


def get_setting(

    key: str,

    default=None

):


    try:


        settings = get_all_settings_cached()


        return settings.get(

            key,

            default

        )



    except Exception as e:


        log_error(

            message="get_setting loader failed",

            exception=e

        )


        return default







# ==============================================================================
# SAVE SETTING
# ==============================================================================


def save_setting(

    key: str,

    value

):


    try:


        service = get_settings_service()


        result = service.save_setting(

            key,

            value

        )


        # Clear cache

        get_all_settings_cached.clear()



        return result



    except Exception as e:


        log_error(

            message="save_setting loader failed",

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

    settings: dict

):


    try:


        service = get_settings_service()



        result = service.save_settings(

            settings

        )


        get_all_settings_cached.clear()



        return result



    except Exception as e:


        log_error(

            message="bulk settings save failed",

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
# ==============================================================================


def get_bool(

    key,

    default=False

):


    value = get_setting(

        key,

        default

    )


    return (

        str(value)

        .lower()

        ==

        "true"

    )







def get_float(

    key,

    default=0.0

):


    try:


        return float(

            get_setting(

                key,

                default

            )

        )



    except Exception:


        return float(default)







def get_int(

    key,

    default=0

):


    try:


        return int(

            get_setting(

                key,

                default

            )

        )



    except Exception:


        return int(default)








def get_text(

    key,

    default=""

):


    return str(

        get_setting(

            key,

            default

        )

    )







# ==============================================================================
# CACHE CLEAR
# ==============================================================================


def clear_settings_cache():


    try:


        get_all_settings_cached.clear()


        return True



    except Exception:


        return False







# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "get_setting",

    "save_setting",

    "save_settings",

    "get_bool",

    "get_float",

    "get_int",

    "get_text",

    "clear_settings_cache"

]
