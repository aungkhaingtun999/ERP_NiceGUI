# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v3.0 FINAL
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
# SERVICE INSTANCE
# ==============================================================================


def get_settings_service():


    return SettingsService(

        db()

    )






# ==============================================================================
# CACHE LOAD ALL SETTINGS
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
# GET SETTING
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

            message="Save setting loader failed",

            exception=e

        )


        return {


            "success":

                False,


            "message":

                str(e)

        }








# ==============================================================================
# SAVE MULTIPLE SETTINGS
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

            message="Bulk save loader failed",

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

    settings,

    key,

    default=False

):


    try:


        value = settings.get(

            key,

            default

        )


        return str(value).lower() == "true"



    except Exception:


        return bool(default)







def get_float(

    settings,

    key,

    default=0.0

):


    try:


        value = settings.get(

            key,

            default

        )


        return float(value)



    except Exception:


        return float(default)







def get_int(

    settings,

    key,

    default=0

):


    try:


        value = settings.get(

            key,

            default

        )


        return int(value)



    except Exception:


        return int(default)







def get_text(

    settings,

    key,

    default=""

):


    try:


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
