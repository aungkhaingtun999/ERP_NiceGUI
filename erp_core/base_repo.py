# ==============================================================================
# erp_core/base_repo.py
# ERP ENTERPRISE DATABASE CORE v31.1 STABLE
#
# Supabase Connection
# Database Gateway
# Money Engine
# Serialization
# Health Check
# Legacy Compatible
# ==============================================================================


import time

from decimal import (
    Decimal,
    ROUND_HALF_UP
)

from typing import (
    Optional,
    Callable,
    Any
)


import streamlit as st


from supabase import (
    create_client,
    Client
)


try:

    from postgrest.exceptions import APIError


except ImportError:

    APIError = Exception



from .config import (

    log_error,

    Tables

)





# ==============================================================================
# SUPABASE CONNECTION
# ==============================================================================


@st.cache_resource
def get_supabase() -> Client:


    try:

        url = st.secrets[
            "SUPABASE_URL"
        ]


        key = st.secrets[
            "SUPABASE_KEY"
        ]


        return create_client(

            url,

            key

        )


    except Exception as e:


        log_error(

            message="Supabase connection failed",

            exception=e

        )


        raise





# ==============================================================================
# DATABASE SHORTCUT
# ==============================================================================


def db() -> Client:

    return get_supabase()



get_connection = db





# ==============================================================================
# MONEY
# ==============================================================================


def money(
    value: Any
) -> Decimal:


    try:

        return Decimal(

            str(value)

        ).quantize(

            Decimal("0.01"),

            rounding=ROUND_HALF_UP

        )


    except Exception:

        return Decimal(
            "0.00"
        )





def money_float(
    value: Any
) -> float:


    return float(
        money(value)
    )





def safe_float(
    value: Any
) -> float:


    try:

        return float(
            value or 0
        )


    except Exception:

        return 0.0





# ==============================================================================
# UUID
# ==============================================================================


def validate_uuid(
    value
) -> Optional[str]:


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


def serialize_json(
    data
):


    import uuid



    if isinstance(
        data,
        Decimal
    ):

        return float(data)



    if isinstance(
        data,
        uuid.UUID
    ):

        return str(data)



    if isinstance(
        data,
        list
    ):

        return [

            serialize_json(x)

            for x in data

        ]



    if isinstance(
        data,
        dict
    ):

        return {

            k: serialize_json(v)

            for k, v in data.items()

        }



    return data





# ==============================================================================
# SAFE DATABASE EXECUTE
# ==============================================================================


def safe_execute(

    func: Callable,

    error_message="Database operation failed"

):


    retry = 3



    for attempt in range(retry):


        try:


            result = func()



            if hasattr(

                result,

                "data"

            ):

                return result.data



            return result



        except (

            APIError,

            ConnectionError,

            TimeoutError

        ) as e:



            if attempt < retry - 1:


                time.sleep(

                    0.5 *

                    (

                        attempt + 1

                    )

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
    def check() -> bool:


        try:


            response = (

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


            return response is not None



        except Exception as e:


            log_error(

                message="Database health check failed",

                exception=e

            )


            return False





def database_health_check():


    return DatabaseHealth.check()





# ==============================================================================
# EXPORT
# ==============================================================================


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



print(
    "ERP BASE REPO v31.1 LOADED"
)
