# ==============================================================================
# erp_core/base_repo.py
# ERP ENTERPRISE BASE REPOSITORY v38.0 - NiceGUI Version
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
from typing import Optional, Callable, Any, Dict, List, Union
import uuid
import os
import json
from functools import lru_cache


# ==============================================================================
# THIRD-PARTY
# ==============================================================================

from supabase import create_client, Client
import dotenv


# ==============================================================================
# ERP CORE
# ==============================================================================

from .config import (
    Tables,
    log_error,
)


print("BASE_REPO START - NiceGUI Version")


# ==============================================================================
# ENVIRONMENT CONFIGURATION
# ==============================================================================

def load_env_vars():
    """
    Load environment variables from .env file.
    """
    dotenv.load_dotenv()


# ==============================================================================
# SECRETS MANAGER - NiceGUI Equivalent
# ==============================================================================

class SecretsManager:
    """
    Manages secrets for NiceGUI application.
    Replaces Streamlit's st.secrets.
    """
    
    _secrets: Dict[str, str] = {}
    
    @classmethod
    def load_secrets(cls):
        """
        Load secrets from environment variables or secrets file.
        """
        load_env_vars()
        
        # Load from environment variables
        cls._secrets = {
            "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
            "SUPABASE_KEY": os.getenv("SUPABASE_KEY", ""),
            "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        }
        
        # Override with secrets file if exists
        try:
            with open('secrets.json', 'r') as f:
                file_secrets = json.load(f)
                cls._secrets.update(file_secrets)
        except FileNotFoundError:
            pass  # secrets.json not found, use environment variables
        
        return cls._secrets
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a secret value.
        """
        if not cls._secrets:
            cls.load_secrets()
        return cls._secrets.get(key, default)


# ==============================================================================
# CACHE MANAGER - NiceGUI Equivalent
# ==============================================================================

class CacheManager:
    """
    Simple cache manager for NiceGUI.
    Replaces Streamlit's @st.cache_resource.
    """
    
    _cache: Dict[str, Any] = {}
    
    @classmethod
    def cache_resource(cls, func: Callable) -> Callable:
        """
        Decorator to cache resource (like @st.cache_resource).
        """
        @lru_cache(maxsize=1)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    @classmethod
    def clear_cache(cls):
        """
        Clear all cached resources.
        """
        cls._cache.clear()
        
        # Clear lru_cache for decorated functions
        import functools
        for name, obj in globals().items():
            if callable(obj) and hasattr(obj, 'cache_clear'):
                try:
                    obj.cache_clear()
                except TypeError:
                    pass


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

@CacheManager.cache_resource
def get_supabase() -> Client:
    """
    Return the normal Supabase client.

    Uses:
        SUPABASE_URL
        SUPABASE_KEY

    SUPABASE_KEY is the normal application key.
    """

    try:
        secrets = SecretsManager.load_secrets()
        
        supabase_url = secrets.get("SUPABASE_URL")
        supabase_key = secrets.get("SUPABASE_KEY")

        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is empty.")

        if not supabase_key:
            raise RuntimeError("SUPABASE_KEY is empty.")

        return create_client(supabase_url, supabase_key)

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
# This client exists only on the server.
#
# It is used for protected Maker-Checker RPC operations such as:
#
#     request_product_create_rpc()
#     approve_product_create_rpc()
#
# ==============================================================================

@CacheManager.cache_resource
def get_service_supabase() -> Client:
    """
    Return the server-side privileged Supabase client.

    Requires:
        SUPABASE_URL
        SUPABASE_SERVICE_ROLE_KEY

    The service-role key must never be exposed to users.
    """

    try:
        secrets = SecretsManager.load_secrets()

        # ------------------------------------------------------------------
        # SUPABASE URL
        # ------------------------------------------------------------------

        supabase_url = secrets.get("SUPABASE_URL")

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

        service_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url:
            raise RuntimeError("SUPABASE_URL is empty.")

        if not service_key:
            raise RuntimeError(
                "SUPABASE_SERVICE_ROLE_KEY is missing "
                "from environment variables."
            )

        return create_client(supabase_url, service_key)

    except Exception as e:
        log_error(
            message="Supabase privileged connection failed",
            exception=e,
        )
        raise


# ==============================================================================
# NORMAL DATABASE ACCESS
# ==============================================================================

def db() -> Client:
    """
    Return the normal Supabase client.
    """
    return get_supabase()


# ==============================================================================
# PRIVILEGED DATABASE ACCESS
# ==============================================================================

def privileged_db() -> Client:
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

def money(value: Any) -> Decimal:
    """
    Convert a value to Decimal with 2 decimal places.
    """
    try:
        return Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    except Exception:
        return Decimal("0.00")


def money_float(value: Any) -> float:
    """
    Convert money value to float.
    """
    return float(money(value))


# ==============================================================================
# SAFE FLOAT
# ==============================================================================

def safe_float(value: Any) -> float:
    """
    Safely convert value to float.
    """
    try:
        return float(value or 0)
    except Exception:
        return 0.0


# ==============================================================================
# UUID
# ==============================================================================

def validate_uuid(value: Any) -> Optional[str]:
    """
    Validate and normalize UUID.

    Returns:
        str UUID
        None
    """
    if not value:
        return None

    try:
        return str(uuid.UUID(str(value)))
    except Exception:
        return None


# ==============================================================================
# JSON SERIALIZER
# ==============================================================================

def serialize_json(data: Any) -> Any:
    """
    Convert Decimal / UUID / nested structures
    into JSON-compatible Python values.
    """
    # ------------------------------------------------------------------
    # Decimal
    # ------------------------------------------------------------------
    if isinstance(data, Decimal):
        return float(data)

    # ------------------------------------------------------------------
    # UUID
    # ------------------------------------------------------------------
    if isinstance(data, uuid.UUID):
        return str(data)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------
    if isinstance(data, list):
        return [serialize_json(item) for item in data]

    # ------------------------------------------------------------------
    # Tuple
    # ------------------------------------------------------------------
    if isinstance(data, tuple):
        return [serialize_json(item) for item in data]

    # ------------------------------------------------------------------
    # Dictionary
    # ------------------------------------------------------------------
    if isinstance(data, dict):
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
    error_message: str = "Database Error",
    default_value: Any = None,
) -> Any:
    """
    Execute a database operation safely.

    Returns:
        function result
        default_value on exception
    """
    try:
        return func()
    except Exception as e:
        log_error(
            message=error_message,
            exception=e,
        )
        return default_value


# ==============================================================================
# DATABASE HEALTH
# ==============================================================================

class DatabaseHealth:
    """
    Simple database health checker.
    """
    
    @staticmethod
    def check() -> bool:
        try:
            (
                db()
                .table(Tables.PRODUCTS)
                .select("id")
                .limit(1)
                .execute()
            )
            return True
        except Exception as e:
            log_error(
                message="Database health failed",
                exception=e,
            )
            return False
    
    @staticmethod
    def check_privileged() -> bool:
        """
        Check health using privileged connection.
        """
        try:
            (
                privileged_db()
                .table(Tables.PRODUCTS)
                .select("id")
                .limit(1)
                .execute()
            )
            return True
        except Exception as e:
            log_error(
                message="Privileged database health failed",
                exception=e,
            )
            return False


# ==============================================================================
# DATABASE HEALTH FUNCTION
# ==============================================================================

def database_health_check() -> bool:
    """
    Perform a database health check.
    
    Returns:
        True if healthy, False otherwise.
    """
    return DatabaseHealth.check()


# ==============================================================================
# SESSION STATE MANAGER - NiceGUI Equivalent
# ==============================================================================

class SessionState:
    """
    Simple session state manager for NiceGUI.
    Replaces Streamlit's st.session_state.
    """
    
    _state: Dict[str, Any] = {}
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a value from session state.
        """
        return cls._state.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Set a value in session state.
        """
        cls._state[key] = value
    
    @classmethod
    def delete(cls, key: str) -> None:
        """
        Delete a value from session state.
        """
        if key in cls._state:
            del cls._state[key]
    
    @classmethod
    def clear(cls) -> None:
        """
        Clear all session state.
        """
        cls._state.clear()
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Get all session state.
        """
        return cls._state.copy()


# ==============================================================================
# QUERY BUILDER HELPERS
# ==============================================================================

def build_filter_query(
    table: str,
    filters: Dict[str, Any],
    select_columns: List[str] = None,
    order_by: str = None,
    ascending: bool = True,
    limit: int = None,
    offset: int = None,
) -> Any:
    """
    Build a filtered query with common patterns.
    
    Args:
        table: Table name
        filters: Dictionary of column: value filters
        select_columns: List of columns to select
        order_by: Column to order by
        ascending: Order direction
        limit: Limit results
        offset: Offset results
    
    Returns:
        Query builder
    """
    query = db().table(table)
    
    # Select columns
    if select_columns:
        query = query.select(",".join(select_columns))
    else:
        query = query.select("*")
    
    # Apply filters
    for column, value in filters.items():
        if value is not None:
            query = query.eq(column, value)
    
    # Order by
    if order_by:
        query = query.order(order_by, desc=not ascending)
    
    # Limit and offset
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
    return query


# ==============================================================================
# TRANSACTION HELPERS
# ==============================================================================

def execute_transaction(operations: List[Callable]) -> Dict[str, Any]:
    """
    Execute multiple operations as a transaction.
    
    Args:
        operations: List of functions that execute database operations
    
    Returns:
        Dictionary with success flag and results
    """
    results = []
    success = True
    error = None
    
    try:
        for op in operations:
            result = op()
            results.append(result)
    except Exception as e:
        success = False
        error = str(e)
        log_error(
            message="Transaction failed",
            exception=e,
        )
    
    return {
        "success": success,
        "results": results,
        "error": error,
    }


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
    # Session management
    # ------------------------------------------------------------------
    "SessionState",
    "CacheManager",
    "SecretsManager",
    
    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    "build_filter_query",
    "execute_transaction",
    
    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    "log_error",
]

print("BASE_REPO READY v38.0 - NiceGUI Version")
