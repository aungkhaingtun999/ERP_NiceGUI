# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v31 FINAL
# ==============================================================================


import streamlit as st


from ..base_repo import (
    db,
    log_error
)


from ..config import (
    Tables
)





# ==============================================================================
# CACHE LOAD
# ==============================================================================


@st.cache_data(
    ttl=300,
    show_spinner=False
)
def get_setting_cached(key):


    try:


        result = (

            db()

            .table(

                Tables.SETTINGS

            )

            .select("*")

            .eq(

                "key",

                key

            )

            .order(

                "id",

                desc=True

            )

            .limit(1)

            .execute()

        )


        if result.data:


            return result.data[0].get(
                "value"
            )



    except Exception as e:


        log_error(

            message="Settings cache load failed",

            exception=e

        )



    return None





# ==============================================================================
# GET SETTING
# ==============================================================================


def get_setting(

    key:str,

    default=None

):


    value = get_setting_cached(
        key
    )


    if value is None:


        return default



    return value





# ==============================================================================
# NUMBER SETTING
# ==============================================================================


def get_float_setting(

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





# ==============================================================================
# BOOLEAN SETTING
# ==============================================================================


def get_bool_setting(

    key,

    default=False

):


    value = str(

        get_setting(

            key,

            default

        )

    ).lower()



    return value == "true"





# ==============================================================================
# CLEAR CACHE
# ==============================================================================


def clear_settings_cache():

    get_setting_cached.clear()




# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [

    "get_setting",

    "get_float_setting",

    "get_bool_setting",

    "clear_settings_cache"

]
