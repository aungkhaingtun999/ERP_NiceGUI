# ==============================================================================
# erp_core/config.py
# ERP ENTERPRISE CORE CONFIG v30.6 FINAL
#
# Core Configuration
# Database Map
# Pricing Engine
# Cache System
# Security
# Logging
# ==============================================================================


import logging



# ==============================================================================
# ERP INFO
# ==============================================================================

ERP_VERSION = "30.6"

DEBUG = False

DEFAULT_PAGE_SIZE = 100

CURRENCY = "MMK"





# ==============================================================================
# SECURITY
# ==============================================================================

SENSITIVE_KEYS = (

    "password",
    "token",
    "secret",
    "authorization",
    "api_key",
    "jwt"

)





# ==============================================================================
# DATABASE TABLE MAP
# ==============================================================================


class Tables:


    # ------------------------------------------------------------------
    # PRODUCT
    # ------------------------------------------------------------------

    PRODUCTS = "products"

    PRODUCT_VIEW = "pos_products_view"

    CATEGORIES = "categories"



    # ------------------------------------------------------------------
    # INVENTORY
    # ------------------------------------------------------------------

    WAREHOUSES = "warehouses"

    WAREHOUSE_STOCK = "warehouse_stock"

    INVENTORY_LEDGER = "inventory_ledgers"

    INVENTORY_COST_TRANSACTIONS = (
        "inventory_cost_transactions"
    )



    # ------------------------------------------------------------------
    # SALES
    # ------------------------------------------------------------------

    SALES = "sales"

    SALE_ITEMS = "sale_items"



    # ------------------------------------------------------------------
    # PURCHASE
    # ------------------------------------------------------------------

    PURCHASES = "purchases"

    PURCHASE_ITEMS = "purchase_items"



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



    # ------------------------------------------------------------------
    # USER SECURITY
    # ------------------------------------------------------------------

    USERS = "users"

    ROLES = "roles"

    PERMISSIONS = "permissions"

    ROLE_PERMISSIONS = "role_permissions"



    # ------------------------------------------------------------------
    # SETTINGS
    # ------------------------------------------------------------------

    SETTINGS = "erp_settings"



    # ------------------------------------------------------------------
    # ACCOUNTING
    # ------------------------------------------------------------------

    ACCOUNT_JOURNALS = "accounting_journals"

    ACCOUNT_ENTRIES = "accounting_entries"

    CHART_OF_ACCOUNTS = "chart_of_accounts"



    # ------------------------------------------------------------------
    # SYSTEM
    # ------------------------------------------------------------------

    AUDIT_LOGS = "audit_logs"

    TRANSACTIONS = "erp_transactions"

    SYNC_QUEUE = "sync_queue"





# ==============================================================================
# QUICK TABLE ACCESS
# ==============================================================================


TABLE_PRODUCTS = Tables.PRODUCTS

TABLE_PRODUCT_VIEW = Tables.PRODUCT_VIEW

TABLE_CATEGORIES = Tables.CATEGORIES


TABLE_WAREHOUSES = Tables.WAREHOUSES

TABLE_WAREHOUSE_STOCK = Tables.WAREHOUSE_STOCK


TABLE_SALES = Tables.SALES

TABLE_SALE_ITEMS = Tables.SALE_ITEMS


TABLE_PURCHASES = Tables.PURCHASES

TABLE_PURCHASE_ITEMS = Tables.PURCHASE_ITEMS


TABLE_USERS = Tables.USERS





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





# ==============================================================================
# CACHE VERSION SYSTEM
# ==============================================================================


CACHE_KEYS = {


    "inventory":

        "inventory_version",



    "products":

        "product_version",



    "pricing":

        "pricing_version",



    "settings":

        "settings_version",



    "sales":

        "sales_version"


}





# ==============================================================================
# LOGGING
# ==============================================================================


logging.basicConfig(

    filename="erp_database.log",

    level=logging.ERROR,

    format=(

        "%(asctime)s | "

        "%(levelname)s | "

        "%(message)s"

    ),

    force=True

)





# ==============================================================================
# SECURITY CLEANER
# ==============================================================================


def sanitize_payload(payload):


    if not isinstance(payload, dict):

        return {}



    clean = {}



    for key, value in payload.items():


        if any(

            secret in key.lower()

            for secret in SENSITIVE_KEYS

        ):

            clean[key] = "***"


        else:

            clean[key] = value



    return clean





# ==============================================================================
# ERROR LOGGER
# ==============================================================================


def log_error(

    message=None,

    exception=None,

    payload=None,

    rpc=None,

    msg=None,

    rpc_name=None

):


    actual_message = (

        message

        or

        msg

        or

        "Unknown error"

    )



    actual_rpc = (

        rpc

        or

        rpc_name

        or

        ""

    )



    logging.error(

        "MESSAGE=%s | RPC=%s | PAYLOAD=%s | ERROR=%s",

        actual_message,

        actual_rpc,

        sanitize_payload(payload),

        exception

    )
