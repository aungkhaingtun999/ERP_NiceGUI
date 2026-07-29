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
