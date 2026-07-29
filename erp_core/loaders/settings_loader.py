# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v3.0 FINAL
#
# Settings Gateway
#
# Supabase
#     ↓
# SettingsService
#     ↓
# SettingsLoader
#     ↓
# ERP Modules
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
            message="Load settings failed",
            exception=e
        )

        return {}



# ==============================================================================
# SINGLE GET
# ==============================================================================


def get_setting(
    key
):

    settings = get_all_settings_cached()

    return settings.get(
        key
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
# BULK SAVE
# ==============================================================================


def save_settings(
    data:dict
):

    try:

        service = get_settings_service()

        result = service.save_settings(
            data
        )

        clear_settings_cache()

        return result


    except Exception as e:

        log_error(
            message="Bulk save failed",
            exception=e
        )

        return {
            "success":False,
            "message":str(e)
        }



# ==============================================================================
# TYPE CONVERTERS
# ==============================================================================


def get_bool(
    key
):

    value = get_setting(key)

    return str(value).lower() == "true"



def get_float(
    key
):

    try:

        value = get_setting(key)

        if value is None:
            return None

        return float(value)


    except Exception:

        return None



def get_int(
    key
):

    try:

        value = get_setting(key)

        if value is None:
            return None

        return int(value)


    except Exception:

        return None



def get_text(
    key
):

    value = get_setting(key)

    return value



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
