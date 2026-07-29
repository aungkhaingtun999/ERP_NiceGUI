# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v31 PERFORMANCE BUILD
#
# Database
#      ↓
# Cache Layer
#      ↓
# Price Engine / POS / ERP
#
# Optimization:
# - Setting query cache
# - Fast POS price calculation
# - Safe fallback
# - Cache refresh support
#
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
# INTERNAL DATABASE QUERY
# ==============================================================================


@st.cache_data(
    ttl=300,
    show_spinner=False
)
def _get_setting_from_db(

    key: str

):


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

            message=f"Setting query failed: {e}"

        )



    return None







# ==============================================================================
# PUBLIC GET SETTING
# ==============================================================================


def get_setting(

    key: str,

    default=None

):


    try:


        value = _get_setting_from_db(

            key

        )


        if value is None:


            return default



        return value



    except Exception as e:


        log_error(

            message=f"get_setting error: {e}"

        )


        return default







# ==============================================================================
# COMMON TYPE HELPERS
# ==============================================================================


def get_bool_setting(

    key,

    default=False

):


    value = get_setting(

        key,

        default

    )



    if isinstance(

        value,

        bool

    ):

        return value



    return str(

        value

    ).lower() in (

        "true",

        "1",

        "yes",

        "on"

    )







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


        return float(

            default

        )







def get_int_setting(

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


        return int(

            default

        )







# ==============================================================================
# CACHE REFRESH
# ==============================================================================


def refresh_settings_cache():


    try:


        _get_setting_from_db.clear()



    except Exception as e:


        log_error(

            message=f"Settings cache refresh failed: {e}"

        )
