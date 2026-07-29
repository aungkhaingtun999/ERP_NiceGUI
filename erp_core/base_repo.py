# ==============================================================================
# erp_core/base_repo.py
# ERP ENTERPRISE DATABASE CORE v31.1 FIX
# ==============================================================================

import time
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Callable

import streamlit as st

from supabase import create_client, Client

try:
    from postgrest.exceptions import APIError
except Exception:
    APIError = Exception


from .config import (
    Tables,
    log_error
)



# ==============================================================================
# SUPABASE CONNECTION
# ==============================================================================

@st.cache_resource
def get_supabase() -> Client:

    try:

        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )

    except Exception as e:

        log_error(
            message="Supabase connection failed",
            exception=e
        )

        from .exceptions import DatabaseError

        raise DatabaseError(
            "Cannot connect database"
        )



def db():

    return get_supabase()



get_connection = db





# ==============================================================================
# MONEY
# ==============================================================================

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

        return float(
            value or 0
        )

    except Exception:

        return 0.0





# ==============================================================================
# UUID
# ==============================================================================

def validate_uuid(value):

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





# ==============================================================================
# JSON SERIALIZER
# ==============================================================================

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





# ==============================================================================
# SAFE EXECUTE
# ==============================================================================

def safe_execute(
    func: Callable,
    error_message="Database operation failed"
):

    for attempt in range(3):

        try:

            result = func()


            if hasattr(result,"data"):

                return result.data


            return result


        except (
            APIError,
            ConnectionError,
            TimeoutError
        ) as e:


            if attempt < 2:

                time.sleep(
                    0.5 * (attempt+1)
                )

                continue


            log_error(
                message=error_message,
                exception=e
            )

            raise


        except Exception as e:


            log_error(
                message=error_message,
                exception=e
            )

            raise



    return None





# ==============================================================================
# DATABASE HEALTH
# ==============================================================================

class DatabaseHealth:


    @staticmethod
    def check():


        try:

            result = (

                db()

                .table(
                    Tables.PRODUCTS
                )

                .select(
                    "id"
                )

                .limit(
                    1
                )

                .execute()

            )


            return result is not None


        except Exception as e:


            log_error(
                message="Database health failed",
                exception=e
            )

            return False





def database_health_check():

    return DatabaseHealth.check()





__all__ = [

    "get_supabase",

    "db",

    "get_connection",

    "money",

    "money_float",

    "safe_float",

    "validate_uuid",

    "serialize_json",

    "safe_execute",

    "DatabaseHealth",

    "database_health_check",

    "log_error"

]
