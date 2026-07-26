# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE CACHE CONTEXT v31.2
# STREAMLIT SAFE CACHE VERSION MANAGER
# ==============================================================================


import time
import streamlit as st



class CacheManager:
    """
    ERP Global Cache Version Manager

    Flow:

    Database Update
          |
          v
    CacheManager.bump()
          |
          v
    Version changes
          |
          v
    @st.cache_data receives new version
          |
          v
    Fresh data reload
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
    # BUMP VERSION
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
    # INVENTORY REFRESH
    # ------------------------------------------------------------------

    @classmethod
    def clear_inventory(cls):

        return cls.bump(
            "inventory_version"
        )



    # Legacy name support

    @classmethod
    def refresh_inventory(cls):

        return cls.clear_inventory()



    # ------------------------------------------------------------------
    # PRODUCT REFRESH
    # ------------------------------------------------------------------

    @classmethod
    def clear_products(cls):

        return cls.bump(
            "product_version"
        )



    @classmethod
    def refresh_products(cls):

        return cls.clear_products()



    # ------------------------------------------------------------------
    # SALES REFRESH
    # ------------------------------------------------------------------

    @classmethod
    def clear_sales(cls):

        return cls.bump(
            "sales_version"
        )



    @classmethod
    def refresh_sales(cls):

        return cls.clear_sales()



    # ------------------------------------------------------------------
    # RESET
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



def refresh_inventory():

    return CacheManager.refresh_inventory()



def refresh_products():

    return CacheManager.refresh_products()



def refresh_sales():

    return CacheManager.refresh_sales()
