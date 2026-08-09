
# ==============================================================================
# erp_core/base_repo.py
# ERP ENTERPRISE BASE REPOSITORY v38.0
#
# PURPOSE
# ------------------------------------------------------------------------------
# 1. Normal Supabase client
# 2. Privileged server-side Supabase client
# 3. Maker-Checker protected RPC support
# 4. Common money / UUID / JSON helpers
# 5. Database health check
#
# SECURITY
# ------------------------------------------------------------------------------
# SUPABASE_KEY
#     -> Normal application client
#
# SUPABASE_SERVICE_ROLE_KEY
#     -> Server-side privileged client ONLY
#
# IMPORTANT
# ------------------------------------------------------------------------------
# NEVER expose SUPABASE_SERVICE_ROLE_KEY to:
#     - browser JavaScript
#     - frontend components
#     - client-side scanner
#     - public source code
#
# ==============================================================================


# ==============================================================================
# STANDARD LIBRARY
# ==============================================================================

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Callable
import uuid


# ==============================================================================
# THIRD-PARTY
# ==============================================================================

import streamlit as st
from supabase import create_client


# ==============================================================================
# ERP CORE
# ==============================================================================

from .config import (
    Tables,
    log_error,
)


print("BASE_REPO START")


# ==============================================================================
# NORMAL SUPABASE CLIENT
# ==============================================================================
#
# Used for normal ERP operations:
#
#     products
#     warehouses
#     customers
#     suppliers
#     reports
#     normal RPCs
#
# ==============================================================================

@st.cache_resource
def get_supabase():
    """
    Return the normal Supabase client.

    Uses:
        SUPABASE_URL
        SUPABASE_KEY

    SUPABASE_KEY is the normal application key.
    """

    try:

        supabase_url = st.secrets["SUPABASE_URL"]

        supabase_key = st.secrets["SUPABASE_KEY"]

        if not supabase_url:

            raise RuntimeError(
                "SUPABASE_URL is empty."
            )

        if not supabase_key:

            raise RuntimeError(
                "SUPABASE_KEY is empty."
            )

        return create_client(
            supabase_url,
            supabase_key,
        )

    except Exception as e:

        log_error(
            message="Supabase normal connection failed",
            exception=e,
        )

        raise


# ==============================================================================
# PRIVILEGED SERVER-SIDE SUPABASE CLIENT
# ==============================================================================
#
# IMPORTANT:
#
# This client MUST use:
#
#     SUPABASE_SERVICE_ROLE_KEY
#
# NOT:
#
#     SUPABASE_KEY
#
# This client exists only on the Streamlit server.
#
# It is used for protected Maker-Checker RPC operations such as:
#
#     request_product_create_rpc()
#     approve_product_create_rpc()
#
# ==============================================================================

@st.cache_resource
def get_service_supabase():
    """
    Return the server-side privileged Supabase client.

    Requires:
        SUPABASE_URL
        SUPABASE_SERVICE_ROLE_KEY

    The service-role key must never be exposed to users.
    """

    try:

        # ------------------------------------------------------------------
        # SUPABASE URL
        # ------------------------------------------------------------------

        supabase_url = st.secrets["SUPABASE_URL"]

        # ------------------------------------------------------------------
        # SERVICE ROLE / SECRET KEY
        # ------------------------------------------------------------------
        #
        # IMPORTANT:
        #
        # Do NOT use SUPABASE_KEY here.
        #
        # SUPABASE_KEY is the normal publishable application key.
        #
        # ------------------------------------------------------------------

        service_key = st.secrets.get(
            "SUPABASE_SERVICE_ROLE_KEY"
        )

        if not supabase_url:

            raise RuntimeError(
                "SUPABASE_URL is empty."
            )

        if not service_key:

            raise RuntimeError(
                "SUPABASE_SERVICE_ROLE_KEY is missing "
                "from Streamlit Secrets."
            )

        return create_client(
            supabase_url,
            service_key,
        )

    except Exception as e:

        log_error(
            message="Supabase privileged connection failed",
            exception=e,
        )

        raise


# ==============================================================================
# NORMAL DATABASE ACCESS
# ==============================================================================

def db():
    """
    Return the normal Supabase client.
    """

    return get_supabase()


# ==============================================================================
# PRIVILEGED DATABASE ACCESS
# ==============================================================================

def privileged_db():
    """
    Return the server-side privileged Supabase client.

    Use ONLY for intentionally privileged server-side operations.
    """

    return get_service_supabase()


# ==============================================================================
# BACKWARD COMPATIBILITY
# ==============================================================================

get_connection = db


# ==============================================================================
# MONEY
# ==============================================================================

def money(value):
    """
    Convert a value to Decimal with 2 decimal places.
    """

    try:

        return Decimal(
            str(value)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    except Exception:

        return Decimal("0.00")


def money_float(value):
    """
    Convert money value to float.
    """

    return float(
        money(value)
    )


# ==============================================================================
# SAFE FLOAT
# ==============================================================================

def safe_float(value):
    """
    Safely convert value to float.
    """

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
    value,
) -> Optional[str]:
    """
    Validate and normalize UUID.

    Returns:
        str UUID
        None
    """

    if not value:

        return None

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
    """
    Convert Decimal / UUID / nested structures
    into JSON-compatible Python values.
    """

    # ------------------------------------------------------------------
    # Decimal
    # ------------------------------------------------------------------

    if isinstance(
        data,
        Decimal,
    ):

        return float(
            data
        )

    # ------------------------------------------------------------------
    # UUID
    # ------------------------------------------------------------------

    if isinstance(
        data,
        uuid.UUID,
    ):

        return str(
            data
        )

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    if isinstance(
        data,
        list,
    ):

        return [
            serialize_json(item)
            for item in data
        ]

    # ------------------------------------------------------------------
    # Tuple
    # ------------------------------------------------------------------

    if isinstance(
        data,
        tuple,
    ):

        return [
            serialize_json(item)
            for item in data
        ]

    # ------------------------------------------------------------------
    # Dictionary
    # ------------------------------------------------------------------

    if isinstance(
        data,
        dict,
    ):

        return {
            key: serialize_json(value)
            for key, value in data.items()
        }

    # ------------------------------------------------------------------
    # Other
    # ------------------------------------------------------------------

    return data


# ==============================================================================
# SAFE EXECUTE
# ==============================================================================

def safe_execute(
    func: Callable,
    error_message="Database Error",
):
    """
    Execute a database operation safely.

    Returns:
        function result
        None on exception
    """

    try:

        return func()

    except Exception as e:

        log_error(
            message=error_message,
            exception=e,
        )

        return None


# ==============================================================================
# DATABASE HEALTH
# ==============================================================================

class DatabaseHealth:
    """
    Simple database health checker.
    """

    @staticmethod
    def check():

        try:

            (
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

            return True

        except Exception as e:

            log_error(
                message="Database health failed",
                exception=e,
            )

            return False


# ==============================================================================
# DATABASE HEALTH FUNCTION
# ==============================================================================

def database_health_check():

    return DatabaseHealth.check()


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [

    # ------------------------------------------------------------------
    # Normal database
    # ------------------------------------------------------------------

    "db",
    "get_supabase",
    "get_connection",

    # ------------------------------------------------------------------
    # Privileged database
    # ------------------------------------------------------------------

    "privileged_db",
    "get_service_supabase",

    # ------------------------------------------------------------------
    # Money
    # ------------------------------------------------------------------

    "money",
    "money_float",
    "safe_float",

    # ------------------------------------------------------------------
    # UUID
    # ------------------------------------------------------------------

    "validate_uuid",

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    "serialize_json",

    # ------------------------------------------------------------------
    # Safe execute
    # ------------------------------------------------------------------

    "safe_execute",

    # ------------------------------------------------------------------
    # Database health
    # ------------------------------------------------------------------

    "DatabaseHealth",
    "database_health_check",

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    "log_error",

]


# ==============================================================================
# READY
# ==============================================================================

print(
    "BASE_REPO READY v38.0"
)

