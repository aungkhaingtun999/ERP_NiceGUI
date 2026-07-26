# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE CONTEXT & CACHE MANAGER v30
# Streamlit Session Cache Control
# ==============================================================================

from typing import Any, Dict
import streamlit as st
import time


# ==============================================================================
# CACHE MANAGER
# ==============================================================================

class CacheManager:
    """
    Enterprise Cache Version Manager

    Purpose:
    - Control Streamlit cached data refresh
    - Inventory change invalidation
    - Product stock refresh
    - Dashboard refresh
    - ERP module synchronization
    """


    # --------------------------------------------------------------------------
    # GET CACHE VERSION
    # --------------------------------------------------------------------------

    @staticmethod
    def get_version(
        key: str
    ) -> int:

        """
        Return current cache version.

        Example:
            CacheManager.get_version(
                "inventory_version"
            )
        """

        version_key = (
            f"erp_cache_version_{key}"
        )


        if version_key not in st.session_state:

            st.session_state[
                version_key
            ] = 0


        return st.session_state[
            version_key
        ]



    # --------------------------------------------------------------------------
    # BUMP CACHE VERSION
    # --------------------------------------------------------------------------

    @staticmethod
    def bump_version(
        key: str
    ) -> int:

        """
        Increase cache version.

        Used after:
        - Sale
        - Purchase
        - Transfer
        - Stock Adjustment
        - Refund
        """


        version_key = (
            f"erp_cache_version_{key}"
        )


        current = st.session_state.get(
            version_key,
            0
        )


        current += 1


        st.session_state[
            version_key
        ] = current


        return current



    # --------------------------------------------------------------------------
    # CLEAR ALL ERP CACHE VERSIONS
    # --------------------------------------------------------------------------

    @staticmethod
    def clear_versions():

        keys = [
            key
            for key in st.session_state.keys()
            if key.startswith(
                "erp_cache_version_"
            )
        ]


        for key in keys:

            del st.session_state[key]



    # --------------------------------------------------------------------------
    # INVENTORY REFRESH
    # --------------------------------------------------------------------------

    @staticmethod
    def refresh_inventory():

        """
        Call after stock movement.
        """

        return CacheManager.bump_version(
            "inventory_version"
        )



    # --------------------------------------------------------------------------
    # PRODUCT REFRESH
    # --------------------------------------------------------------------------

    @staticmethod
    def refresh_products():

        return CacheManager.bump_version(
            "product_version"
        )



    # --------------------------------------------------------------------------
    # DASHBOARD REFRESH
    # --------------------------------------------------------------------------

    @staticmethod
    def refresh_dashboard():

        return CacheManager.bump_version(
            "dashboard_version"
        )



# ==============================================================================
# ERP APPLICATION CONTEXT
# ==============================================================================

class ERPContext:
    """
    Global ERP runtime context.

    Stores:
    - Current user
    - Warehouse
    - Language
    - Session information
    """


    @staticmethod
    def set(
        key: str,
        value: Any
    ):

        st.session_state[
            f"erp_context_{key}"
        ] = value



    @staticmethod
    def get(
        key: str,
        default=None
    ):

        return st.session_state.get(
            f"erp_context_{key}",
            default
        )



    @staticmethod
    def clear():

        keys = [
            key
            for key in st.session_state.keys()
            if key.startswith(
                "erp_context_"
            )
        ]


        for key in keys:

            del st.session_state[key]



# ==============================================================================
# REQUEST CONTEXT
# ==============================================================================

class RequestContext:
    """
    Temporary request metadata.
    Useful for:
    - Audit log
    - RPC tracking
    - Debugging
    """


    @staticmethod
    def create():

        return {

            "request_id":
                f"REQ-{int(time.time()*1000)}",

            "timestamp":
                time.time()

        }