# ==============================================================================
# erp_core/base_repo.py
# TEST CLEAN VERSION
# ==============================================================================

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

import streamlit as st

from supabase import create_client


from .config import (
    Tables,
    log_error
)


@st.cache_resource
def get_supabase():

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )



def db():

    return get_supabase()



get_connection = db



def money(value):

    try:

        return Decimal(
            str(value)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    except Exception:

        return Decimal("0.00")



def money_float(value):

    return float(
        money(value)
    )



def safe_float(value):

    try:

        return float(value or 0)

    except Exception:

        return 0.0



def validate_uuid(value) -> Optional[str]:

    if not value:

        return None


    import uuid


    try:

        return str(
            uuid.UUID(
                str(value)
            )
        )

    except Exception:

        return None



def serialize_json(data):

    import uuid


    if isinstance(data, Decimal):

        return float(data)


    if isinstance(data, uuid.UUID):

        return str(data)


    if isinstance(data, list):

        return [
            serialize_json(x)
            for x in data
        ]


    if isinstance(data, dict):

        return {
            k: serialize_json(v)
            for k,v in data.items()
        }


    return data



class DatabaseHealth:


    @staticmethod
    def check():

        try:

            db().table(
                Tables.PRODUCTS
            ).select(
                "id"
            ).limit(
                1
            ).execute()


            return True


        except Exception:

            return False



def database_health_check():

    return DatabaseHealth.check()



def safe_execute(
    func,
    error_message="Database Error"
):

    try:

        return func()

    except Exception as e:

        log_error(
            message=error_message,
            exception=e
        )

        return None



__all__ = [

    "db",

    "get_supabase",

    "get_connection",

    "money",

    "money_float",

    "safe_float",

    "validate_uuid",

    "serialize_json",

    "DatabaseHealth",

    "database_health_check",

    "safe_execute"

]
