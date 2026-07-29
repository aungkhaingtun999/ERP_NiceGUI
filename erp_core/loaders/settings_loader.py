# ==============================================================================
# erp_core/loaders/settings_loader.py
# ERP ENTERPRISE SETTINGS LOADER v30
# ==============================================================================
import streamlit as st


@st.cache_data(
    ttl=300,
    show_spinner=False
)
def get_setting_cached(key):

    ...

from ..base_repo import (
    db,
    log_error
)


from ..config import (
    Tables
)





def get_setting(
    key: str,
    default=None
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

            return result.data[0]["value"]


    except Exception as e:

        log_error(
            message=f"get_setting error: {e}"
        )


    return default
