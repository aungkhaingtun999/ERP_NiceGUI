# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE CACHE & RUNTIME CONTEXT v32
# ==============================================================================

import time
import streamlit as st


class ERPContext:
    """
    ERP Runtime Context & Cache Manager

    Used by:
    - Services
    - Sales Engine
    - Inventory Engine
    """

    VERSION_KEY = "erp_cache_versions"

    def __init__(
        self,
        user_id=None,
        warehouse_id=None,
        customer_id=None
    ):
        """Initializes the runtime context with user, warehouse, and customer IDs."""
        self.user_id = user_id
        self.warehouse_id = warehouse_id
        self.customer_id = customer_id

    def to_dict(self):
        """Converts the runtime context instance to a dictionary."""
        return {
            "user_id": self.user_id,
            "warehouse_id": self.warehouse_id,
            "customer_id": self.customer_id
        }

    # ------------------------------------------------------------------
    # INITIALIZE
    # ------------------------------------------------------------------

    @classmethod
    def init(cls):
        """Initializes cache versions dictionary in session state if missing."""
        if cls.VERSION_KEY not in st.session_state:
            st.session_state[cls.VERSION_KEY] = {
                "inventory_version": 1,
                "product_version": 1,
                "sales_version": 1,
                "updated_at": time.time()
            }

    # ------------------------------------------------------------------
    # GET VERSION
    # ------------------------------------------------------------------

    @classmethod
    def get_version(
        cls,
        key: str
    ):
        """Retrieves the current version number for a specific cache key."""
        cls.init()
        return st.session_state[cls.VERSION_KEY].get(
            key,
            1
        )

    # ------------------------------------------------------------------
    # BUMP VERSION
    # ------------------------------------------------------------------

    @classmethod
    def bump(
        cls,
        key: str
    ):
        """Increments the version number for a given cache key and updates timestamp."""
        cls.init()
        versions = st.session_state[cls.VERSION_KEY]
        versions[key] = (
            versions.get(
                key,
                1
            )
            + 1
        )
        versions["updated_at"] = time.time()
        return versions[key]

    # ------------------------------------------------------------------
    # INVENTORY REFRESH
    # ------------------------------------------------------------------

    @classmethod
    def clear_inventory(cls):
        """Invalidates inventory cache by bumping its version."""
        return cls.bump(
            "inventory_version"
        )

    @classmethod
    def refresh_inventory(cls):
        """Legacy name support for clearing inventory."""
        return cls.clear_inventory()

    # ------------------------------------------------------------------
    # PRODUCT REFRESH
    # ------------------------------------------------------------------

    @classmethod
    def clear_products(cls):
        """Invalidates product cache by bumping its version."""
        return cls.bump(
            "product_version"
        )

    @classmethod
    def refresh_products(cls):
        """Legacy name support for clearing products."""
        return cls.clear_products()

    # ------------------------------------------------------------------
    # SALES REFRESH
    # ------------------------------------------------------------------

    @classmethod
    def clear_sales(cls):
        """Invalidates sales cache by bumping its version."""
        return cls.bump(
            "sales_version"
        )

    @classmethod
    def refresh_sales(cls):
        """Legacy name support for clearing sales."""
        return cls.clear_sales()

    # ------------------------------------------------------------------
    # RESET
    # ------------------------------------------------------------------

    @classmethod
    def reset(cls):
        """Resets all cache versions back to their initial defaults."""
        st.session_state[cls.VERSION_KEY] = {
            "inventory_version": 1,
            "product_version": 1,
            "sales_version": 1,
            "updated_at": time.time()
        }


# ==============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ==============================================================================


def get_cache_version(
    key: str
):
    """Legacy helper to get cache version."""
    return ERPContext.get_version(
        key
    )


def bump_cache(
    key: str
):
    """Legacy helper to bump a cache version."""
    return ERPContext.bump(
        key
    )


def bump_inventory_version():
    """Legacy helper to clear inventory cache."""
    return ERPContext.clear_inventory()


def bump_product_version():
    """Legacy helper to clear product cache."""
    return ERPContext.clear_products()


def bump_sales_version():
    """Legacy helper to clear sales cache."""
    return ERPContext.clear_sales()


def refresh_inventory():
    """Legacy helper to refresh inventory cache."""
    return ERPContext.refresh_inventory()


def refresh_products():
    """Legacy helper to refresh product cache."""
    return ERPContext.refresh_products()


def refresh_sales():
    """Legacy helper to refresh sales cache."""
    return ERPContext.refresh_sales()
