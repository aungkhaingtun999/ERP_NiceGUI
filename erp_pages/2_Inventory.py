# ==============================================================================
# erp_pages/2_Inventory.py
# ERP ENTERPRISE INVENTORY ROUTER v1.0
#
# Inventory modules separated architecture
#
# ==============================================================================


import streamlit as st


from erp_pages.inventory.page import (
    run_inventory_page
)



def run():

    run_inventory_page()



if __name__ == "__main__":

    run()
