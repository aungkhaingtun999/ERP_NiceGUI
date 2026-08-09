
# ==============================================================================
# erp_core/base_repo.py
# ERP ENTERPRISE BASE REPOSITORY v36.0
#
# NORMAL CLIENT
# PRIVILEGED SERVER CLIENT
# MAKER / CHECKER RPC SUPPORT
#
# IMPORTANT:
# ------------------------------------------------------------------------------
# db()
#     -> normal publishable client
#
# privileged_db()
#     -> server-only secret/service-role client
#
# NEVER expose privileged_db() to browser/client-side code.
# ==============================================================================

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Callable
import uuid

import streamlit as st
from supabase import create_client

from .config import Tables, log_error


print("BASE_REPO START")


# ==============================================================================
# SUPABASE URL
# ==============================================================================

def _get_supabase_url():

    url = st.secrets.get("SUPABASE_URL")

    if not url:

        raise RuntimeError(
            "SUPABASE_URL is not configured."
        )

    return url


# ==============================================================================
# NORMAL SUPABASE CLIENT
#
# Used for normal application operations.
# ==============================================================================

@st.cache_resource
def get_supabase():

    try:

        url = _get_supabase_url()

        key = st.secrets.get(
            "SUPABASE_KEY"
        )

        if not key:

            raise RuntimeError(
                "SUPABASE_KEY is not configured."
            )

        return create_client(
            url,
            key
        )

    except Exception as e:

        log_error(
            message="Supabase normal connection failed",
            exception=e
        )

        raise


# ==============================================================================
# PRIVILEGED SERVER CLIENT
#
# Priority:
#
# 1. SUPABASE_SECRET_KEY  -> new Supabase key
# 2. SUPABASE_SERVICE_ROLE_KEY -> legacy key
#
# NEVER use SUPABASE_KEY here.
# ==============================================================================

@st.cache_resource
def get_service_supabase():

    try:

        url = _get_supabase_url()

        # ----------------------------------------------------------------------
        # NEW SUPABASE SECRET KEY
        # ----------------------------------------------------------------------

        secret_key = st.secrets.get(
            "SUPABASE_SECRET_KEY"
        )

        # ----------------------------------------------------------------------
        # LEGACY SERVICE ROLE KEY
        # ----------------------------------------------------------------------

        service_role_key = st.secrets.get(
            "SUPABASE_SERVICE_ROLE_KEY"
        )

        privileged_key = (
            secret_key
            or service_role_key
        )

        if not privileged_key:

            raise RuntimeError(
                "Neither SUPABASE_SECRET_KEY nor "
                "SUPABASE_SERVICE_ROLE_KEY is configured."
            )

        return create_client(
            url,
            privileged_key
        )

    except Exception as e:

        log_error(
            message="Supabase privileged connection failed",
            exception=e
        )

        raise


# ==============================================================================
# DATABASE CLIENTS
# ==============================================================================

def db():

    return get_supabase()


def privileged_db():

    return get_service_supabase()


# ==============================================================================
# BACKWARD COMPATIBILITY
# ==============================================================================

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

def validate_uuid(
    value
) -> Optional[str]:

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
# SAFE EXECUTE
# ==============================================================================

def safe_execute(
    func: Callable,
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


# ==============================================================================
# HEALTH CHECK
# ==============================================================================

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

        except Exception as e:

            log_error(
                message="Database health failed",
                exception=e
            )

            return False


def database_health_check():

    return DatabaseHealth.check()


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [

    # Normal
    "db",
    "get_supabase",
    "get_connection",

    # Privileged
    "privileged_db",
    "get_service_supabase",

    # Utilities
    "money",
    "money_float",
    "safe_float",
    "validate_uuid",
    "serialize_json",
    "safe_execute",

    # Health
    "DatabaseHealth",
    "database_health_check",

    # Logging
    "log_error",
]


print(
    "BASE_REPO READY v36.0"
)

