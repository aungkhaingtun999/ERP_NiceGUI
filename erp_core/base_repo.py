# ==============================================================================
# erp_core/base_repo.py
# ERP ENTERPRISE BASE REPOSITORY v36.0
#
# NORMAL CLIENT
# PRIVILEGED SERVER CLIENT
# MAKER-CHECKER RPC SUPPORT
# ==============================================================================

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Callable
import uuid

import streamlit as st
from supabase import create_client

from .config import Tables, log_error


print("BASE_REPO START")


# ==============================================================================
# NORMAL SUPABASE CLIENT
# ==============================================================================

@st.cache_resource
def get_supabase():

    try:

        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
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
# IMPORTANT:
# This function runs ONLY on Streamlit server.
#
# NEVER expose this key to browser JavaScript.
# ==============================================================================

@st.cache_resource
def get_service_supabase():

    try:

        service_key = st.secrets.get(
            "SUPABASE_SERVICE_ROLE_KEY"
        )

        if not service_key:

            raise RuntimeError(
                "SUPABASE_SERVICE_ROLE_KEY is missing "
                "from Streamlit Secrets."
            )

        return create_client(
            st.secrets["SUPABASE_URL"],
            service_key
        )

    except Exception as e:

        log_error(
            message="Supabase service connection failed",
            exception=e
        )

        raise


# ==============================================================================
# NORMAL DATABASE
# ==============================================================================

def db():

    return get_supabase()


# ==============================================================================
# PRIVILEGED DATABASE
# ==============================================================================

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

def validate_uuid(value) -> Optional[str]:

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
# DATABASE HEALTH
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

    # Money
    "money",
    "money_float",
    "safe_float",

    # UUID
    "validate_uuid",

    # JSON
    "serialize_json",

    # Execute
    "safe_execute",

    # Health
    "DatabaseHealth",
    "database_health_check",

    # Logging
    "log_error",
]


print("BASE_REPO READY v36.0")
