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

Modular POS Architecture

Modules:

engine.py
    - Price engine
    - Owner price priority
    - Money formatting


product.py
    - Product loader
    - Search
    - Barcode


cart.py
    - Cart state
    - Add/remove/update quantity
    - Cart calculation


payment.py
    - Checkout RPC
    - Payment validation


receipt.py
    - Receipt rendering
    - PDF
    - Thermal printer


cache.py
    - Inventory cache refresh
"""


# ==============================================================================
# VERSION
# ==============================================================================

POS_VERSION = "12.0"


# ==============================================================================
# PACKAGE EXPORTS
# ==============================================================================

__all__ = [

    "engine",

    "product",

    "cart",

    "payment",

    "receipt",

    "cache",

]



# ==============================================================================
# OPTIONAL MODULE LOADER
# ==============================================================================

def load_pos_module(name):

    """
    Safe POS module loader

    Example:

        load_pos_module("product")

    """

    import importlib

    return importlib.import_module(
        f"erp_pages.pos.{name}"
    )
