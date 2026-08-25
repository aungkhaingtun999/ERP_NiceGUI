# ==============================================================================
# erp_core/config.py
# ERP ENTERPRISE CORE CONFIG v30.6 - NiceGUI Version
#
# Core Configuration
# Database Map
# Pricing Engine
# Cache System
# Security
# Logging
# NiceGUI-Specific Settings
# ==============================================================================

import logging
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from enum import Enum


# ==============================================================================
# ERP INFO
# ==============================================================================

ERP_VERSION = "30.6-nicegui"
DEBUG = os.getenv("ERP_DEBUG", "False").lower() == "true"
DEFAULT_PAGE_SIZE = int(os.getenv("ERP_PAGE_SIZE", "100"))
CURRENCY = os.getenv("ERP_CURRENCY", "MMK")
TIMEZONE = os.getenv("ERP_TIMEZONE", "Asia/Yangon")

# ------------------------------------------------------------------------------
# NiceGUI Specific Settings
# ------------------------------------------------------------------------------

NICEGUI_HOST = os.getenv("NICEGUI_HOST", "0.0.0.0")
NICEGUI_PORT = int(os.getenv("NICEGUI_PORT", "8080"))
NICEGUI_TITLE = os.getenv("NICEGUI_TITLE", "ERP Enterprise System")
NICEGUI_FAVICON = os.getenv("NICEGUI_FAVICON", "🏢")
NICEGUI_DARK = os.getenv("NICEGUI_DARK", "False").lower() == "true"

# Theme settings
THEME_PRIMARY = os.getenv("THEME_PRIMARY", "#1976D2")
THEME_SECONDARY = os.getenv("THEME_SECONDARY", "#26A69A")
THEME_ACCENT = os.getenv("THEME_ACCENT", "#9C27B0")
THEME_SUCCESS = os.getenv("THEME_SUCCESS", "#4CAF50")
THEME_WARNING = os.getenv("THEME_WARNING", "#FF9800")
THEME_ERROR = os.getenv("THEME_ERROR", "#F44336")

# ------------------------------------------------------------------------------
# UI Configuration
# ------------------------------------------------------------------------------

UI_CONFIG = {
    "sidebar_width": 280,
    "header_height": 64,
    "footer_height": 48,
    "max_content_width": 1400,
    "animation_duration": 300,
    "toast_duration": 3000,
    "dialog_width": "600px",
    "mobile_breakpoint": 768,
}


# ==============================================================================
# SECURITY
# ==============================================================================

SENSITIVE_KEYS = (
    "password",
    "token",
    "secret",
    "authorization",
    "api_key",
    "jwt",
    "service_role",
    "private_key",
    "credit_card",
    "cvv",
    "pin",
)

# Session configuration
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION = int(os.getenv("LOCKOUT_DURATION", "900"))  # 15 minutes

# CSRF protection
CSRF_ENABLED = os.getenv("CSRF_ENABLED", "True").lower() == "true"
CSRF_TOKEN_LENGTH = 32


# ==============================================================================
# DATABASE TABLE MAP
# ==============================================================================

class Tables:
    """Database table names and views."""

    # ------------------------------------------------------------------
    # PRODUCT
    # ------------------------------------------------------------------
    PRODUCTS = "products"
    PRODUCT_VIEW = "pos_products_view"
    CATEGORIES = "categories"
    BRANDS = "brands"
    UNITS = "units"

    # ------------------------------------------------------------------
    # INVENTORY
    # ------------------------------------------------------------------
    WAREHOUSES = "warehouses"
    WAREHOUSE_STOCK = "warehouse_stock"
    INVENTORY_LEDGER = "inventory_ledgers"
    INVENTORY_COST_TRANSACTIONS = "inventory_cost_transactions"
    STOCK_ADJUSTMENTS = "stock_adjustments"
    STOCK_COUNTS = "stock_counts"

    # ------------------------------------------------------------------
    # SALES
    # ------------------------------------------------------------------
    SALES = "sales"
    SALE_ITEMS = "sale_items"
    SALES_RETURNS = "sales_returns"
    PAYMENTS = "payments"

    # ------------------------------------------------------------------
    # PURCHASE
    # ------------------------------------------------------------------
    PURCHASES = "purchases"
    PURCHASE_ITEMS = "purchase_items"
    PURCHASE_RETURNS = "purchase_returns"

    # ------------------------------------------------------------------
    # REFUND
    # ------------------------------------------------------------------
    REFUNDS = "refunds"
    REFUND_ITEMS = "refund_items"

    # ------------------------------------------------------------------
    # CUSTOMER / SUPPLIER
    # ------------------------------------------------------------------
    CUSTOMERS = "customers"
    SUPPLIERS = "suppliers"
    CONTACTS = "contacts"
    ADDRESSES = "addresses"

    # ------------------------------------------------------------------
    # USER SECURITY
    # ------------------------------------------------------------------
    USERS = "users"
    ROLES = "roles"
    PERMISSIONS = "permissions"
    ROLE_PERMISSIONS = "role_permissions"
    USER_SESSIONS = "user_sessions"
    LOGIN_ATTEMPTS = "login_attempts"

    # ------------------------------------------------------------------
    # SETTINGS
    # ------------------------------------------------------------------
    SETTINGS = "settings"
    SETTINGS_CHANGE_REQUESTS = "settings_change_requests"
    SETTINGS_HISTORY = "settings_history"

    # ------------------------------------------------------------------
    # ACCOUNTING
    # ------------------------------------------------------------------
    ACCOUNT_JOURNALS = "accounting_journals"
    ACCOUNT_ENTRIES = "accounting_entries"
    CHART_OF_ACCOUNTS = "chart_of_accounts"
    ACCOUNT_PERIODS = "accounting_periods"

    # ------------------------------------------------------------------
    # SYSTEM
    # ------------------------------------------------------------------
    AUDIT_LOGS = "audit_logs"
    TRANSACTIONS = "erp_transactions"
    SYNC_QUEUE = "sync_queue"
    SYSTEM_LOGS = "system_logs"
    EMAIL_QUEUE = "email_queue"
    NOTIFICATIONS = "notifications"

    # ------------------------------------------------------------------
    # MAKER-CHECKER
    # ------------------------------------------------------------------
    APPROVAL_REQUESTS = "approval_requests"
    APPROVAL_QUEUE = "approval_queue"
    APPROVAL_HISTORY = "approval_history"

    # ------------------------------------------------------------------
    # REPORTING
    # ------------------------------------------------------------------
    REPORTS = "reports"
    REPORT_TEMPLATES = "report_templates"
    DASHBOARDS = "dashboards"


# ==============================================================================
# QUICK TABLE ACCESS
# ==============================================================================

TABLE_PRODUCTS = Tables.PRODUCTS
TABLE_PRODUCT_VIEW = Tables.PRODUCT_VIEW
TABLE_CATEGORIES = Tables.CATEGORIES
TABLE_BRANDS = Tables.BRANDS
TABLE_UNITS = Tables.UNITS

TABLE_WAREHOUSES = Tables.WAREHOUSES
TABLE_WAREHOUSE_STOCK = Tables.WAREHOUSE_STOCK
TABLE_INVENTORY_LEDGER = Tables.INVENTORY_LEDGER

TABLE_SALES = Tables.SALES
TABLE_SALE_ITEMS = Tables.SALE_ITEMS
TABLE_PAYMENTS = Tables.PAYMENTS

TABLE_PURCHASES = Tables.PURCHASES
TABLE_PURCHASE_ITEMS = Tables.PURCHASE_ITEMS

TABLE_CUSTOMERS = Tables.CUSTOMERS
TABLE_SUPPLIERS = Tables.SUPPLIERS

TABLE_USERS = Tables.USERS
TABLE_ROLES = Tables.ROLES
TABLE_PERMISSIONS = Tables.PERMISSIONS

TABLE_APPROVAL_REQUESTS = Tables.APPROVAL_REQUESTS
TABLE_AUDIT_LOGS = Tables.AUDIT_LOGS


# ==============================================================================
# PRICE ENGINE
#
# Priority
#
# OWNER PRICE
#       ↓
# PRODUCT MARKUP
#       ↓
# CATEGORY MARKUP
#       ↓
# GLOBAL MARKUP
#       ↓
# CURRENT PRICE
#
# ==============================================================================

PRICE_SOURCE_OWNER = "OWNER"
PRICE_SOURCE_PRODUCT = "PRODUCT_MARKUP"
PRICE_SOURCE_CATEGORY = "CATEGORY_MARKUP"
PRICE_SOURCE_GLOBAL = "GLOBAL_MARKUP"
PRICE_SOURCE_CURRENT = "CURRENT_PRICE"
PRICE_SOURCE_SYSTEM = "SYSTEM"

PRICE_SOURCES = (
    PRICE_SOURCE_OWNER,
    PRICE_SOURCE_PRODUCT,
    PRICE_SOURCE_CATEGORY,
    PRICE_SOURCE_GLOBAL,
    PRICE_SOURCE_CURRENT,
    PRICE_SOURCE_SYSTEM,
)

# Price rounding rules
PRICE_ROUNDING = {
    "MMK": 50,  # Round to nearest 50
    "USD": 0.01,  # Round to nearest cent
    "EUR": 0.01,
    "SGD": 0.01,
    "THB": 0.25,  # Round to nearest quarter
}

# Default markup percentages
DEFAULT_MARKUP = {
    "retail": 0.30,  # 30% markup
    "wholesale": 0.15,  # 15% markup
    "distributor": 0.10,  # 10% markup
}


# ==============================================================================
# CACHE VERSION SYSTEM
# ==============================================================================

class CacheKeys:
    """Cache version keys for different domains."""

    INVENTORY = "inventory_version"
    PRODUCTS = "product_version"
    PRICING = "pricing_version"
    SETTINGS = "settings_version"
    SALES = "sales_version"
    PURCHASES = "purchases_version"
    CUSTOMERS = "customers_version"
    SUPPLIERS = "suppliers_version"
    USERS = "users_version"
    REPORTS = "reports_version"
    DASHBOARD = "dashboard_version"
    CATEGORIES = "categories_version"
    WAREHOUSES = "warehouses_version"

    # Cache TTL (Time To Live) in seconds
    TTL = {
        INVENTORY: 300,  # 5 minutes
        PRODUCTS: 600,  # 10 minutes
        PRICING: 60,  # 1 minute
        SETTINGS: 3600,  # 1 hour
        SALES: 60,  # 1 minute
        PURCHASES: 60,
        CUSTOMERS: 300,
        SUPPLIERS: 300,
        USERS: 600,
        REPORTS: 1800,  # 30 minutes
        DASHBOARD: 300,
        CATEGORIES: 3600,
        WAREHOUSES: 3600,
    }


# For backward compatibility
CACHE_KEYS = {
    "inventory": CacheKeys.INVENTORY,
    "products": CacheKeys.PRODUCTS,
    "pricing": CacheKeys.PRICING,
    "settings": CacheKeys.SETTINGS,
    "sales": CacheKeys.SALES,
}


# ==============================================================================
# LOGGING
# ==============================================================================

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


LOG_LEVEL = getattr(
    logging,
    os.getenv("ERP_LOG_LEVEL", "ERROR").upper(),
    logging.ERROR
)

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(filename)s:%(lineno)d | "
    "%(message)s"
)

# Log file configuration
LOG_DIR = Path(os.getenv("ERP_LOG_DIR", "logs"))
LOG_DIR.mkdir(exist_ok=True)

LOG_FILES = {
    "database": LOG_DIR / "erp_database.log",
    "security": LOG_DIR / "erp_security.log",
    "performance": LOG_DIR / "erp_performance.log",
    "audit": LOG_DIR / "erp_audit.log",
    "error": LOG_DIR / "erp_error.log",
    "app": LOG_DIR / "erp_app.log",
}

# Configure logging
logging.basicConfig(
    filename=str(LOG_FILES["database"]),
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    force=True,
)


# ==============================================================================
# SECURITY CLEANER
# ==============================================================================

def sanitize_payload(payload: Any) -> Any:
    """
    Sanitize sensitive data from payload.
    
    Args:
        payload: Input data (dict, list, or primitive)
    
    Returns:
        Sanitized data
    """
    if isinstance(payload, dict):
        clean = {}
        for key, value in payload.items():
            if any(secret in str(key).lower() for secret in SENSITIVE_KEYS):
                clean[key] = "***"
            else:
                clean[key] = sanitize_payload(value)
        return clean
    
    elif isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    
    elif isinstance(payload, tuple):
        return tuple(sanitize_payload(item) for item in payload)
    
    else:
        return payload


# ==============================================================================
# ERROR LOGGER
# ==============================================================================

def log_error(
    message: Optional[str] = None,
    exception: Optional[Exception] = None,
    payload: Optional[Dict] = None,
    rpc: Optional[str] = None,
    msg: Optional[str] = None,
    rpc_name: Optional[str] = None,
    user_id: Optional[str] = None,
    level: LogLevel = LogLevel.ERROR,
) -> None:
    """
    Log an error with context.
    
    Args:
        message: Error message
        exception: Exception object
        payload: Request payload
        rpc: RPC name (alternative to rpc_name)
        msg: Message (alternative to message)
        rpc_name: RPC name
        user_id: User ID who triggered the error
        level: Log level
    """
    actual_message = message or msg or "Unknown error"
    actual_rpc = rpc or rpc_name or "N/A"
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level.name,
        "message": actual_message,
        "rpc": actual_rpc,
        "user_id": user_id,
        "payload": sanitize_payload(payload),
        "exception": str(exception) if exception else None,
        "exception_type": type(exception).__name__ if exception else None,
    }
    
    # Log to file
    logging.log(
        level.value,
        "MESSAGE=%s | RPC=%s | USER=%s | PAYLOAD=%s | ERROR=%s",
        actual_message,
        actual_rpc,
        user_id,
        log_entry["payload"],
        exception,
    )
    
    # Also log to separate audit log for security events
    if any(secret in actual_message.lower() for secret in SENSITIVE_KEYS):
        audit_logger = logging.getLogger("security")
        audit_logger.error(
            "SECURITY_EVENT: %s | USER: %s | RPC: %s",
            actual_message,
            user_id,
            actual_rpc,
        )


# ==============================================================================
# ENVIRONMENT VALIDATION
# ==============================================================================

def validate_config() -> List[str]:
    """
    Validate configuration and return list of issues.
    
    Returns:
        List of configuration issues
    """
    issues = []
    
    required_env_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ]
    
    for var in required_env_vars:
        if not os.getenv(var):
            issues.append(f"Missing environment variable: {var}")
    
    # Check if SUPABASE_SERVICE_ROLE_KEY is set (warn if not)
    if not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        issues.append("WARNING: SUPABASE_SERVICE_ROLE_KEY not set - maker-checker features may not work")
    
    # Validate log directory
    if not LOG_DIR.exists():
        try:
            LOG_DIR.mkdir(parents=True)
        except Exception as e:
            issues.append(f"Cannot create log directory: {e}")
    
    return issues


# ==============================================================================
# NICE-GUI THEME CONFIGURATION
# ==============================================================================

class ThemeColors:
    """ERP theme colors for NiceGUI."""
    
    PRIMARY = THEME_PRIMARY
    SECONDARY = THEME_SECONDARY
    ACCENT = THEME_ACCENT
    SUCCESS = THEME_SUCCESS
    WARNING = THEME_WARNING
    ERROR = THEME_ERROR
    
    # Extended colors
    INFO = "#2196F3"
    DARK = "#1A1A1A"
    LIGHT = "#FFFFFF"
    BACKGROUND = "#F5F7FA"
    SURFACE = "#FFFFFF"
    
    # Status colors
    STATUS = {
        "draft": "#9E9E9E",
        "pending": "#FFC107",
        "approved": "#4CAF50",
        "rejected": "#F44336",
        "completed": "#2196F3",
        "cancelled": "#F44336",
        "archived": "#757575",
    }


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # ERP Info
    "ERP_VERSION",
    "DEBUG",
    "DEFAULT_PAGE_SIZE",
    "CURRENCY",
    "TIMEZONE",
    
    # NiceGUI Config
    "NICEGUI_HOST",
    "NICEGUI_PORT",
    "NICEGUI_TITLE",
    "NICEGUI_FAVICON",
    "NICEGUI_DARK",
    "UI_CONFIG",
    "ThemeColors",
    
    # Security
    "SENSITIVE_KEYS",
    "SESSION_TIMEOUT",
    "MAX_LOGIN_ATTEMPTS",
    "LOCKOUT_DURATION",
    "CSRF_ENABLED",
    "sanitize_payload",
    
    # Database
    "Tables",
    "TABLE_PRODUCTS",
    "TABLE_PRODUCT_VIEW",
    "TABLE_CATEGORIES",
    "TABLE_WAREHOUSES",
    "TABLE_WAREHOUSE_STOCK",
    "TABLE_INVENTORY_LEDGER",
    "TABLE_SALES",
    "TABLE_SALE_ITEMS",
    "TABLE_PURCHASES",
    "TABLE_PURCHASE_ITEMS",
    "TABLE_CUSTOMERS",
    "TABLE_SUPPLIERS",
    "TABLE_USERS",
    "TABLE_APPROVAL_REQUESTS",
    "TABLE_AUDIT_LOGS",
    
    # Price Engine
    "PRICE_SOURCE_OWNER",
    "PRICE_SOURCE_PRODUCT",
    "PRICE_SOURCE_CATEGORY",
    "PRICE_SOURCE_GLOBAL",
    "PRICE_SOURCE_CURRENT",
    "PRICE_SOURCE_SYSTEM",
    "PRICE_SOURCES",
    "PRICE_ROUNDING",
    "DEFAULT_MARKUP",
    
    # Cache
    "CacheKeys",
    "CACHE_KEYS",
    
    # Logging
    "LogLevel",
    "LOG_LEVEL",
    "LOG_FORMAT",
    "LOG_DIR",
    "LOG_FILES",
    "log_error",
    
    # Validation
    "validate_config",
]

print("ERP CONFIG READY - NiceGUI Version")
