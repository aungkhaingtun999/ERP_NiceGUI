# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v2.0 FINAL
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
# SERVICE
# ==============================================================================


def get_settings_service():


    return SettingsService(

        db()

    )






# ==============================================================================
# LOAD ALL SETTINGS CACHE
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

            message="Settings cache load failed",

            exception=e

        )


        return {}






# ==============================================================================
# GET SINGLE SETTING
# ==============================================================================


def get_setting(

    key: str

):


    try:


        service = get_settings_service()


        return service.get_setting(

            key

        )


    except Exception as e:


        log_error(

            message="Get setting failed",

            exception=e

        )


        return None







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

    settings: dict

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

            message="Bulk settings save failed",

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

    key: str

):


    service = get_settings_service()


    return service.get_bool(

        key

    )






def get_float(

    key: str

):


    service = get_settings_service()


    return service.get_float(

        key

    )






def get_int(

    key: str

):


    service = get_settings_service()


    return service.get_int(

        key

    )






def get_text(

    key: str

):


    service = get_settings_service()


    return service.get_text(

        key

    )








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
