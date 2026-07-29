# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE CONTEXT + CACHE MANAGER v31 FINAL
#
# Responsibilities:
#
# - User Context
# - Warehouse Context
# - Transaction Context
# - ERP Global Cache Version Control
#
# Used By:
#
# POS
# Inventory
# Pricing
# Settings
# Dashboard
#
# ==============================================================================


import uuid
import time

import streamlit as st





# ==============================================================================
# ERP CONTEXT
# ==============================================================================


class ERPContext:


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



        self.current_transaction_id = str(

            uuid.uuid4()

        )


        self.transaction_started_at = time.time()





    # --------------------------------------------------------------------------
    # EXPORT CONTEXT
    # --------------------------------------------------------------------------


    def to_dict(self):


        return {


            "user_id":

                self.user_id,


            "warehouse_id":

                self.warehouse_id,


            "customer_id":

                self.customer_id,


            "transaction_id":

                self.current_transaction_id


        }






    # --------------------------------------------------------------------------
    # GET CURRENT CONTEXT
    # --------------------------------------------------------------------------


    @classmethod
    def get_current(cls):


        if cls.SESSION_KEY not in st.session_state:


            st.session_state[

                cls.SESSION_KEY

            ] = cls(


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



        return st.session_state[

            cls.SESSION_KEY

        ]






    # --------------------------------------------------------------------------
    # SET CURRENT CONTEXT
    # --------------------------------------------------------------------------


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






    # --------------------------------------------------------------------------
    # NEW TRANSACTION
    # --------------------------------------------------------------------------


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





    # --------------------------------------------------------------------------
    # INITIALIZE
    # --------------------------------------------------------------------------


    @classmethod
    def init(cls):


        if cls.VERSION_KEY not in st.session_state:


            st.session_state[

                cls.VERSION_KEY

            ] = {


                "inventory_version":

                    1,


                "product_version":

                    1,


                "pricing_version":

                    1,


                "settings_version":

                    1,


                "sales_version":

                    1,


                "customer_version":

                    1,


                "supplier_version":

                    1,


                "updated_at":

                    time.time()


            }







    # --------------------------------------------------------------------------
    # GET VERSION
    # --------------------------------------------------------------------------


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







    # --------------------------------------------------------------------------
    # INCREASE VERSION
    # --------------------------------------------------------------------------


    @classmethod
    def bump(

        cls,

        key

    ):


        cls.init()


        data = st.session_state[

            cls.VERSION_KEY

        ]



        data[key] = data.get(

            key,

            1

        ) + 1



        data["updated_at"] = time.time()



        return data[key]







    # --------------------------------------------------------------------------
    # GENERIC VERSION UPDATE
    # --------------------------------------------------------------------------


    @classmethod
    def bump_version(

        cls,

        key

    ):


        return cls.bump(

            key

        )








    # --------------------------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------------------------


    @classmethod
    def clear_inventory(cls):


        return cls.bump(

            "inventory_version"

        )







    # --------------------------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------------------------


    @classmethod
    def clear_products(cls):


        return cls.bump(

            "product_version"

        )







    # --------------------------------------------------------------------------
    # PRICING
    # --------------------------------------------------------------------------


    @classmethod
    def clear_pricing(cls):


        return cls.bump(

            "pricing_version"

        )







    # --------------------------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------------------------


    @classmethod
    def clear_settings(cls):


        return cls.bump(

            "settings_version"

        )







    # --------------------------------------------------------------------------
    # SALES
    # --------------------------------------------------------------------------


    @classmethod
    def clear_sales(cls):


        return cls.bump(

            "sales_version"

        )







    # --------------------------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------------------------


    @classmethod
    def clear_customers(cls):


        return cls.bump(

            "customer_version"

        )







    # --------------------------------------------------------------------------
    # SUPPLIER
    # --------------------------------------------------------------------------


    @classmethod
    def clear_suppliers(cls):


        return cls.bump(

            "supplier_version"

        )







# ==============================================================================
# LEGACY COMPATIBILITY
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





def bump_pricing_version():


    return CacheManager.clear_pricing()





def bump_settings_version():


    return CacheManager.clear_settings()





def bump_sales_version():


    return CacheManager.clear_sales()





def bump_customer_version():


    return CacheManager.clear_customers()





def bump_supplier_version():


    return CacheManager.clear_suppliers()





# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [


    "ERPContext",


    "CacheManager",


    "get_cache_version",


    "bump_cache",


    "bump_inventory_version",


    "bump_product_version",


    "bump_pricing_version",


    "bump_settings_version",


    "bump_sales_version",


    "bump_customer_version",


    "bump_supplier_version"


]
