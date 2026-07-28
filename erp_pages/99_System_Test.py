# ==============================================================================
# pages/99_System_Test.py
# ERP ENTERPRISE SYSTEM TEST CENTER
# ==============================================================================


import streamlit as st
from datetime import datetime


# ------------------------------------------------------------------------------
# ERP Imports
# ------------------------------------------------------------------------------

from database import get_supabase

from erp_core.services.inventory_service import (
    InventoryService
)


# ------------------------------------------------------------------------------
# Page Config
# ------------------------------------------------------------------------------

st.set_page_config(
    page_title="ERP System Test Center",
    page_icon="🧪",
    layout="wide"
)


# ------------------------------------------------------------------------------
# Header
# ------------------------------------------------------------------------------

st.title("🧪 ERP SYSTEM TEST CENTER")

st.caption(
    "Enterprise Health Monitoring & Service Verification"
)


st.divider()



# ==============================================================================
# Database Test
# ==============================================================================

st.subheader("🗄 Database Connection")


if st.button("Test Database"):


    try:

        supabase = get_supabase()


        result = (
            supabase
            .table("products")
            .select("id")
            .limit(1)
            .execute()
        )


        st.success(
            "Database Connection PASS ✅"
        )


        st.write(
            result.data
        )


    except Exception as e:


        st.error(
            f"Database Failed ❌ : {e}"
        )



# ==============================================================================
# Inventory Service Test
# ==============================================================================


st.divider()

st.subheader("📦 Inventory Service")


if st.button("Run Inventory Test"):


    try:


        data = (
            InventoryService
            .get_inventory_kpi()
        )


        st.success(
            "Inventory Service PASS ✅"
        )


        st.json(data)



    except Exception as e:


        st.error(
            f"Inventory Service Failed ❌ : {e}"
        )



# ==============================================================================
# System Summary
# ==============================================================================


st.divider()

st.subheader("System Information")


col1, col2 = st.columns(2)


with col1:

    st.info(
        f"""
ERP Version:
Enterprise

Check Time:
{datetime.now()}
"""
    )



with col2:

    st.info(
        """
Modules:

✅ Inventory
✅ Pricing
✅ FIFO
✅ Transfer
✅ Adjustment
"""
    )