
# ==============================================================================
# erp_core/base_repo.py
# ERP ENTERPRISE BASE REPOSITORY v35.0
#
# PURPOSE
# ------------------------------------------------------------------------------
# 1. Normal database client
# 2. Server-side privileged client for protected Maker/Checker RPCs
# 3. Never expose service_role key to browser/client code
#
# MAKER-CHECKER
# ------------------------------------------------------------------------------
# request_product_create_rpc()
# approve_product_create_rpc()
#
# are protected at PostgreSQL function level.
#
# create_product_full()
# remains DIRECTLY UNAVAILABLE to authenticated users.
# ==============================================================================

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Callable
import uuid

import streamlit as st
from supabase import create_client

from .config import Tables, log_error


print("BASE_REPO START")


# ==============================================================================
# SUPABASE NORMAL CLIENT
# ------------------------------------------------------------------------------
# Used by normal ERP operations.
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
# SUPABASE SERVER / PRIVILEGED CLIENT
# ------------------------------------------------------------------------------
# IMPORTANT
# ------------------------------------------------------------------------------
# This client is created ONLY on the Streamlit server.
#
# The service_role key must NEVER be sent to the browser.
#
# It is used for protected server-side RPC calls where the application
# authenticates the user through public.users and PostgreSQL functions
# perform the actual Maker/Checker authorization.
# ==============================================================================

@st.cache_resource
def get_service_supabase():

    try:

        service_key = st.secrets.get(
            "SUPABASE_SERVICE_ROLE_KEY"
        )

        if not service_key:

            raise RuntimeError(
                "SUPABASE_SERVICE_ROLE_KEY is not configured."
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

    # Database
    "db",
    "privileged_db",
    "get_supabase",
    "get_service_supabase",
    "get_connection",

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


print("BASE_REPO READY v35.0")

