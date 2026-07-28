# ==============================================================================
# erp_pages/pos/__init__.py
# ERP ENTERPRISE POS MODULE PACKAGE
# Version v12.0
#
# POS Components
# - engine
# - product
# - cart
# - payment
# - receipt
# - cache
# ==============================================================================


"""
ERP Enterprise POS Package

This package contains POS modules:

engine.py
    - Price calculation
    - Money formatting

product.py
    - Product search
    - Product selection

cart.py
    - Cart management
    - Quantity control
    - Cart totals

payment.py
    - Payment processing
    - Checkout RPC

receipt.py
    - Receipt display
    - PDF
    - Thermal printing

cache.py
    - POS cache control
"""


# ==============================================================================
# PACKAGE VERSION
# ==============================================================================

POS_VERSION = "12.0"


# ==============================================================================
# SAFE IMPORT FLAG
# ==============================================================================

__all__ = [

    "engine",

    "product",

    "cart",

    "payment",

    "receipt",

    "cache",

]
