# ==============================================================================
# erp_core/config.py
# ERP ENTERPRISE CORE CONFIG v30.5
#
# Product View
# Pricing Engine
# Warehouse
# Inventory
# Security
# ==============================================================================


import logging


# ==============================================================================
# ERP INFO
# ==============================================================================

ERP_VERSION = "30.5"

DEBUG = False

DEFAULT_PAGE_SIZE = 100

CURRENCY = "MMK"



# ==============================================================================
# SECURITY KEYS
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


    # --------------------------------------------------
    # PRODUCT / PRICING
    # --------------------------------------------------

    PRODUCTS = "products"

    PRODUCT_VIEW = "pos_products_view"


    # --------------------------------------------------
    # INVENTORY
    # --------------------------------------------------

    WAREHOUSES = "warehouses"

    WAREHOUSE_STOCK = "warehouse_stock"

    INVENTORY_LEDGER = "inventory_ledgers"

    COST_TRANSACTIONS = "inventory_cost_transactions"



    # --------------------------------------------------
    # SALES
    # --------------------------------------------------

    SALES = "sales"

    SALE_ITEMS = "sale_items"



    # --------------------------------------------------
    # PURCHASE
    # --------------------------------------------------

    PURCHASES = "purchases"

    PURCHASE_ITEMS = "purchase_items"



    # --------------------------------------------------
    # REFUND
    # --------------------------------------------------

    REFUNDS = "refunds"

    REFUND_ITEMS = "refund_items"



    # --------------------------------------------------
    # MASTER DATA
    # --------------------------------------------------

    CUSTOMERS = "customers"

    SUPPLIERS = "suppliers"



    # --------------------------------------------------
    # SECURITY
    # --------------------------------------------------

    USERS = "users"

    ROLES = "roles"

    PERMISSIONS = "permissions"

    ROLE_PERMISSIONS = "role_permissions"



    # --------------------------------------------------
    # SETTINGS
    # --------------------------------------------------

    SETTINGS = "erp_settings"



    # --------------------------------------------------
    # ACCOUNTING
    # --------------------------------------------------

    ACCOUNT_JOURNALS = "accounting_journals"

    ACCOUNT_ENTRIES = "accounting_entries"

    CHART_OF_ACCOUNTS = "chart_of_accounts"



    # --------------------------------------------------
    # SYSTEM
    # --------------------------------------------------

    AUDIT_LOGS = "audit_logs"

    TRANSACTIONS = "erp_transactions"

    SYNC_QUEUE = "sync_queue"





# ==============================================================================
# QUICK ACCESS CONSTANTS
# ==============================================================================


TABLE_USERS = Tables.USERS

TABLE_ROLE_PERMISSIONS = Tables.ROLE_PERMISSIONS


TABLE_PRODUCTS = Tables.PRODUCTS

TABLE_PRODUCT_VIEW = Tables.PRODUCT_VIEW


TABLE_WAREHOUSES = Tables.WAREHOUSES

TABLE_WAREHOUSE_STOCK = Tables.WAREHOUSE_STOCK


TABLE_CUSTOMERS = Tables.CUSTOMERS

TABLE_SUPPLIERS = Tables.SUPPLIERS


TABLE_SALES = Tables.SALES

TABLE_SALE_ITEMS = Tables.SALE_ITEMS



# ==============================================================================
# PRICING ENGINE CONSTANTS
#
# OWNER PRICE PRIORITY
#
# OWNER_MANUAL
#       ↓
# PRODUCT_MARKUP
#       ↓
# CATEGORY_MARKUP
#       ↓
# GLOBAL_MARKUP
# ==============================================================================


PRICE_SOURCE_OWNER = "OWNER"

PRICE_SOURCE_PRODUCT = "PRODUCT_MARKUP"

PRICE_SOURCE_CATEGORY = "CATEGORY_MARKUP"

PRICE_SOURCE_GLOBAL = "GLOBAL_MARKUP"

PRICE_SOURCE_CURRENT = "CURRENT_PRICE"



# ==============================================================================
# CACHE VERSION KEYS
# ==============================================================================


CACHE_KEYS = {

    "inventory": "inventory_version",

    "products": "products_version",

    "pricing": "pricing_version",

    "settings": "settings_version"

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
# SECURITY PAYLOAD CLEANER
# ==============================================================================


def sanitize_payload(payload):


    if not isinstance(payload, dict):

        return {}



    clean = {}



    for key,value in payload.items():


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

    )



    logging.error(

        "MESSAGE=%s | RPC=%s | PAYLOAD=%s | ERROR=%s",

        actual_message,

        actual_rpc,

        sanitize_payload(payload),

        exception

    )
