# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE CACHE CONTEXT v31
# ==============================================================================

import streamlit as st
import time
import streamlit as st


class CacheManager:

    VERSION_KEY = "erp_cache_versions"

    @classmethod
    def init(cls):
        if cls.VERSION_KEY not in st.session_state:
            st.session_state[cls.VERSION_KEY] = {
                "inventory_version": 1,
                "product_version": 1,
                "sales_version": 1,
                "updated_at": time.time()
            }


    @classmethod
    def get_version(cls, key):
        cls.init()

        return st.session_state[
            cls.VERSION_KEY
        ].get(
            key,
            1
        )



    @classmethod
    def bump(
        cls,
        key
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


        versions["updated_at"] = time.time()



    @classmethod
    def clear_inventory(cls):

        cls.bump(
            "inventory_version"
        )



    @classmethod
    def clear_products(cls):

        cls.bump(
            "product_version"
        )



    @classmethod
    def clear_sales(cls):

        cls.bump(
            "sales_version"
        )



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
        # ==========================================================
# LEGACY COMPATIBILITY HELPERS
# ==========================================================

def get_cache_version(key):
    return CacheManager.get_version(key)



def bump_cache(key):
    return CacheManager.bump(key)



def bump_inventory_version():
    return CacheManager.clear_inventory()



def bump_product_version():
    return CacheManager.clear_products()



def bump_sales_version():
    return CacheManager.clear_sales()
