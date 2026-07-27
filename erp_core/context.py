# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE CONTEXT + CACHE MANAGER
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

        self.current_transaction_id = str(uuid.uuid4())

        self.transaction_started_at = time.time()



    def to_dict(self):

        return {

            "user_id": self.user_id,

            "warehouse_id": self.warehouse_id,

            "customer_id": self.customer_id,

            "transaction_id":
                self.current_transaction_id

        }



    @classmethod
    def get_current(cls):

        if cls.SESSION_KEY not in st.session_state:

            st.session_state[
                cls.SESSION_KEY
            ] = cls(

                user_id=st.session_state.get(
                    "user_id"
                ),

                warehouse_id=st.session_state.get(
                    "warehouse_id"
                ),

                customer_id=st.session_state.get(
                    "customer_id"
                )

            )


        return st.session_state[
            cls.SESSION_KEY
        ]



    @classmethod
    def set_current(
        cls,
        context
    ):

        if isinstance(
            context,
            cls
        ):

            st.session_state[
                cls.SESSION_KEY
            ] = context



    @classmethod
    def clear_current(cls):

        st.session_state.pop(
            cls.SESSION_KEY,
            None
        )



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


                "inventory_version":1,

                "product_version":1,

                "sales_version":1,

                "updated_at":
                    time.time()

            }




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




    @classmethod
    def bump_version(
        cls,
        key
    ):

        return cls.bump(key)




    @classmethod
    def clear_inventory(cls):

        return cls.bump(
            "inventory_version"
        )



    @classmethod
    def clear_products(cls):

        return cls.bump(
            "product_version"
        )



    @classmethod
    def clear_sales(cls):

        return cls.bump(
            "sales_version"
        )



    @classmethod
    def reset(cls):

        st.session_state[
            cls.VERSION_KEY
        ] = {

            "inventory_version":1,

            "product_version":1,

            "sales_version":1,

            "updated_at":
                time.time()

        }




# ==============================================================================
# LEGACY COMPATIBILITY
# ==============================================================================


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



def refresh_inventory():

    return CacheManager.clear_inventory()



def refresh_products():

    return CacheManager.clear_products()



def refresh_sales():

    return CacheManager.clear_sales()
