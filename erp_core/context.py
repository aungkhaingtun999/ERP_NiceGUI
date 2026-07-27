# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE RUNTIME CONTEXT + CACHE ENGINE
# VERSION: V31.0 PRODUCTION
# ==============================================================================

import uuid
import time
import streamlit as st



# ==============================================================================
# ERP CONTEXT
# ==============================================================================


class ERPContext:
    """
    ERP Runtime Context

    Stores:
    - Current User
    - Warehouse
    - Customer
    - Transaction ID
    """


    SESSION_KEY = "erp_context"



    def __init__(
        self,
        user_id=None,
        warehouse_id=None,
        customer_id=None
    ):

        self.user_id = user_id

        self.warehouse_id = warehouse_id

        self.customer_id = customer_id


        # Transaction Engine

        self.current_transaction_id = str(
            uuid.uuid4()
        )

        self.transaction_started_at = time.time()



    # ------------------------------------------------------------------
    # Convert Dictionary
    # ------------------------------------------------------------------

    def to_dict(self):

        return {

            "user_id":
                self.user_id,

            "warehouse_id":
                self.warehouse_id,

            "customer_id":
                self.customer_id

        }



    # ------------------------------------------------------------------
    # Get Current Context
    # ------------------------------------------------------------------

    @classmethod
    def get_current(cls):

        context = st.session_state.get(
            cls.SESSION_KEY
        )


        if context is None:

            context = ERPContext(

                user_id=
                    st.session_state.get(
                        "user_id"
                    ),

                warehouse_id=
                    st.session_state.get(
                        "warehouse_id"
                    ),

                customer_id=
                    st.session_state.get(
                        "customer_id"
                    )

            )


            st.session_state[
                cls.SESSION_KEY
            ] = context



        return context



    # ------------------------------------------------------------------
    # Save Context
    # ------------------------------------------------------------------

    @classmethod
    def set_current(
        cls,
        context
    ):


        if isinstance(
            context,
            ERPContext
        ):

            st.session_state[
                cls.SESSION_KEY
            ] = context



        elif isinstance(
            context,
            dict
        ):

            st.session_state[
                cls.SESSION_KEY
            ] = ERPContext(

                user_id=context.get(
                    "user_id"
                ),

                warehouse_id=context.get(
                    "warehouse_id"
                ),

                customer_id=context.get(
                    "customer_id"
                )

            )



    # ------------------------------------------------------------------
    # Clear Context
    # ------------------------------------------------------------------

    @classmethod
    def clear_current(cls):

        st.session_state.pop(
            cls.SESSION_KEY,
            None
        )



    # ------------------------------------------------------------------
    # New Transaction
    # ------------------------------------------------------------------

    def rotate_transaction(self):

        self.current_transaction_id = str(
            uuid.uuid4()
        )

        self.transaction_started_at = time.time()




# ==============================================================================
# CACHE MANAGER
# ==============================================================================


class CacheManager:


    VERSION_KEY = "erp_cache_versions"



    @classmethod
    def init(cls):

        if cls.VERSION_KEY not in st.session_state:


            st.session_state[
                cls.VERSION_KEY
            ] = {


                "inventory_version": 1,

                "product_version": 1,

                "sales_version": 1,

                "purchase_version": 1,

                "updated_at": time.time()

            }




    # ------------------------------------------------------------------
    # Get Version
    # ------------------------------------------------------------------

    @classmethod
    def get_version(
        cls,
        key
    ):

        cls.init()

        return st.session_state[
            cls.VERSION_KEY
        ].get(
            key,
            1
        )



    # ------------------------------------------------------------------
    # Increase Version
    # ------------------------------------------------------------------

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
            +
            1

        )


        versions["updated_at"] = time.time()


        return versions[key]



    # ------------------------------------------------------------------
    # Compatibility For Services (bump_version)
    # ------------------------------------------------------------------

    @classmethod
    def bump_version(
        cls,
        key
    ):

        return cls.bump(
            key
        )



    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    @classmethod
    def clear_inventory(cls):

        return cls.bump(
            "inventory_version"
        )


    @classmethod
    def refresh_inventory(cls):

        return cls.clear_inventory()



    # ------------------------------------------------------------------
    # Product
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
    # Sales
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
    # Reset
    # ------------------------------------------------------------------

    @classmethod
    def reset(cls):

        st.session_state[
            cls.VERSION_KEY
        ] = {


            "inventory_version": 1,

            "product_version": 1,

            "sales_version": 1,

            "purchase_version": 1,

            "updated_at": time.time()

        }




# ==============================================================================
# LEGACY SUPPORT FUNCTIONS
# ==============================================================================


def get_cache_version(key):

    return CacheManager.get_version(
        key
    )



def bump_cache(key):

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
