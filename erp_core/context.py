# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE CACHE CONTEXT v31.1
# STREAMLIT SAFE CACHE VERSION MANAGER
# ==============================================================================

import time
import streamlit as st



class CacheManager:
    """
    ERP Global Cache Version Manager

    Used for:
    - Inventory refresh
    - Product refresh
    - Sales refresh

    Cache flow:

    Database Change
          |
          v
    CacheManager.bump()
          |
          v
    Version number changes
          |
          v
    @st.cache_data receives new version
          |
          v
    Reload fresh data
    """


    VERSION_KEY = "erp_cache_versions"



    # ------------------------------------------------------------------
    # INITIALIZE
    # ------------------------------------------------------------------

    @classmethod
    def init(cls):

        if cls.VERSION_KEY not in st.session_state:

            st.session_state[
                cls.VERSION_KEY
            ] = {

                "inventory_version": 1,

                "product_version": 1,

                "sales_version": 1,

                "updated_at": time.time()

            }
                @classmethod
    def refresh_inventory(cls):
        """
        Legacy compatibility
        Refresh inventory cache
        """

        cls.bump(
            "inventory_version"
        )



    # ------------------------------------------------------------------
    # GET VERSION
    # ------------------------------------------------------------------

    @classmethod
    def get_version(
        cls,
        key: str
    ):

        cls.init()

        return st.session_state[
            cls.VERSION_KEY
        ].get(
            key,
            1
        )



    # ------------------------------------------------------------------
    # INCREASE VERSION
    # ------------------------------------------------------------------

    @classmethod
    def bump(
        cls,
        key: str
    ):

        cls.init()


        versions = st.session_state[
            cls.VERSION_KEY
        ]


        versions[key] = (

            versions.get(
                key,
                1
            )

            + 1

        )


        versions[
            "updated_at"
        ] = time.time()


        return versions[key]



    # ------------------------------------------------------------------
    # INVENTORY CACHE
    # ------------------------------------------------------------------

    @classmethod
    def clear_inventory(cls):

        return cls.bump(
            "inventory_version"
        )



    # ------------------------------------------------------------------
    # PRODUCT CACHE
    # ------------------------------------------------------------------

    @classmethod
    def clear_products(cls):

        return cls.bump(
            "product_version"
        )



    # ------------------------------------------------------------------
    # SALES CACHE
    # ------------------------------------------------------------------

    @classmethod
    def clear_sales(cls):

        return cls.bump(
            "sales_version"
        )



    # ------------------------------------------------------------------
    # RESET ALL CACHE
    # ------------------------------------------------------------------

    @classmethod
    def reset(cls):

        st.session_state[
            cls.VERSION_KEY
        ] = {

            "inventory_version": 1,

            "product_version": 1,

            "sales_version": 1,

            "updated_at": time.time()

        }



# ==============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# Keep old ERP modules working
# ==============================================================================


def get_cache_version(
    key: str
):

    return CacheManager.get_version(
        key
    )



def bump_cache(
    key: str
):

    return CacheManager.bump(
        key
    )



def bump_inventory_version():

    return CacheManager.clear_inventory()



def bump_product_version():

    return CacheManager.clear_products()



def bump_sales_version():

    return CacheManager.clear_sales()
