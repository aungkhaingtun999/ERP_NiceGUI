# ==============================================================================
# erp_pages/99_System_Test.py
# ERP SYSTEM TEST CENTER
# Custom Router Compatible
# ==============================================================================


import streamlit as st


from supabase_client import get_supabase


from erp_core.services.inventory_service import (
    InventoryService
)



# ==============================================================================
# PAGE ENTRY
# ==============================================================================


def run():


    st.title(
        "🧪 ERP SYSTEM TEST CENTER"
    )


    st.caption(
        "Enterprise Health Monitoring"
    )


    st.divider()



    # ======================================================
    # DATABASE TEST
    # ======================================================


    st.subheader(
        "🗄 Database Connection"
    )


    if st.button(
        "Test Database",
        use_container_width=True
    ):


        try:


            result = (
                supabase
                .table("products")
                .select("id,name")
                .limit(5)
                .execute()
            )


            st.success(
                "Database Connection PASS ✅"
            )


            st.dataframe(
                result.data
            )


        except Exception as e:


            st.error(
                str(e)
            )



    st.divider()



    # ======================================================
    # INVENTORY SERVICE TEST
    # ======================================================


    st.subheader(
        "📦 Inventory Service"
    )



    if st.button(
        "Run Inventory KPI Test",
        use_container_width=True
    ):


        try:


            data = (
                InventoryService
                .get_inventory_kpi()
            )


            st.success(
                "Inventory Service PASS ✅"
            )


            st.json(
                data
            )



        except Exception as e:


            st.error(
                f"Inventory Error : {e}"
            )



    st.divider()



    # ======================================================
    # SYSTEM INFO
    # ======================================================


    st.subheader(
        "⚙️ System Information"
    )


    st.write(
        {
            "ERP Version":
                "Enterprise v30.12",

            "Router":
                "Custom Router",

            "Page":
                "99_System_Test"
        }
    )



# ==============================================================================
# DIRECT RUN SUPPORT
# ==============================================================================


if __name__ == "__main__":

    run()
