# ==============================================================================
# pages/3_Dashboard.py
# ERP ENTERPRISE ANALYTICS DASHBOARD V30.5 FIXED
# ==============================================================================

import streamlit as st
import pandas as pd

from datetime import datetime, timedelta


from auth import (
    require_login,
    current_user
)


from erp_core.base_repo import (
    db,
    safe_float
)


# Correct loader
try:
    from erp_core.loaders.warehouse_loader import (
        get_warehouses
    )
except Exception:
    get_warehouses = lambda: []



# ==============================================================================
# MAIN
# ==============================================================================

def run():

    st.set_page_config(
        page_title="ERP Enterprise Dashboard",
        page_icon="📈",
        layout="wide"
    )


    require_login()

    user = current_user()



    # ==========================================================================
    # HEADER
    # ==========================================================================

    st.title(
        "📈 Enterprise Analytics Dashboard"
    )

    st.caption(
        "Real-time financial, inventory, and sales performance metrics."
    )

    st.divider()



    # ==========================================================================
    # FILTERS
    # ==========================================================================

    st.sidebar.header(
        "📊 Dashboard Filters"
    )


    warehouses = get_warehouses() or []


    warehouse_options = [
        {
            "id": None,
            "name": "All Warehouses"
        }
    ]


    for w in warehouses:

        warehouse_options.append(
            {
                "id": w.get("id"),
                "name": w.get("name")
            }
        )


    selected_wh = st.sidebar.selectbox(
        "Select Warehouse",
        warehouse_options,
        format_func=lambda x: x["name"]
    )


    warehouse_id = selected_wh["id"]



    period = st.sidebar.selectbox(
        "Time Period",
        [
            "This Month",
            "Today",
            "Last 7 Days",
            "Year to Date"
        ]
    )



    now = datetime.now()



    if period == "Today":

        start_date = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )


    elif period == "Last 7 Days":

        start_date = now - timedelta(days=7)


    elif period == "Year to Date":

        start_date = now.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )


    else:

        start_date = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )


    end_date = now



    if st.sidebar.button("🔄 Refresh"):

        st.cache_data.clear()
        st.rerun()



    # ==========================================================================
    # DATABASE
    # ==========================================================================

    supabase = db()



    # ==========================================================================
    # SALES DATA
    # ==========================================================================

    df_sales = pd.DataFrame()


    try:

        query = (
            supabase
            .table("sales")
            .select(
                """
                id,
                total,
                total_amount,
                paid_amount,
                sale_status,
                status,
                warehouse_id,
                created_at
                """
            )
        )


        # Warehouse filter
        # NULL warehouse sales are included in All Warehouses

        if warehouse_id:

            query = query.eq(
                "warehouse_id",
                warehouse_id
            )


        query = (
            query
            .gte(
                "created_at",
                start_date.isoformat()
            )
            .lte(
                "created_at",
                end_date.isoformat()
            )
            .order(
                "created_at",
                desc=True
            )
        )


        result = query.execute()


        df_sales = pd.DataFrame(
            result.data or []
        )


    except Exception as e:

        st.error(
            f"Sales loading error: {e}"
        )
            # ==========================================================================
    # KPI CALCULATION
    # ==========================================================================

    gross_sales = 0
    total_paid = 0
    refunds = 0
    transactions = 0


    sales_column = None


    if not df_sales.empty:

        transactions = len(df_sales)


        # Prefer real total column
        if "total" in df_sales.columns:

            sales_column = "total"


        elif "total_amount" in df_sales.columns:

            sales_column = "total_amount"



        if sales_column:

            gross_sales = (
                df_sales[sales_column]
                .apply(safe_float)
                .sum()
            )



        if "paid_amount" in df_sales.columns:

            total_paid = (
                df_sales["paid_amount"]
                .apply(safe_float)
                .sum()
            )



    # ==========================================================================
    # KPI DISPLAY
    # ==========================================================================

    st.subheader(
        "📌 Key Performance Indicators"
    )


    c1, c2, c3, c4 = st.columns(4)



    c1.metric(
        "Gross Revenue",
        f"{gross_sales:,.0f} MMK",
        f"{transactions} transactions"
    )


    c2.metric(
        "Collections",
        f"{total_paid:,.0f} MMK"
    )


    c3.metric(
        "Refunds",
        f"{refunds:,.0f} MMK"
    )


    c4.metric(
        "Net Revenue",
        f"{gross_sales - refunds:,.0f} MMK"
    )



    st.divider()



    # ==========================================================================
    # SALES TREND
    # ==========================================================================

    col1, col2 = st.columns(2)


    with col1:

        st.subheader(
            "📈 Sales Trend"
        )


        if not df_sales.empty and sales_column:


            chart = df_sales.copy()


            chart["date"] = (
                pd.to_datetime(
                    chart["created_at"]
                )
                .dt.date
            )


            trend = (
                chart
                .groupby("date")[sales_column]
                .sum()
            )


            st.line_chart(
                trend
            )


        else:

            st.info(
                "No sales data"
            )



    # ==========================================================================
    # INVENTORY HEALTH
    # ==========================================================================

    with col2:

        st.subheader(
            "📦 Inventory Health"
        )


        try:

            inventory = (
                supabase
                .table(
                    "view_inventory_status"
                )
                .select(
                    """
                    warehouse_name,
                    product_name,
                    qty,
                    reorder_level
                    """
                )
                .execute()
                .data
                or []
            )


            df_inv = pd.DataFrame(
                inventory
            )


            if not df_inv.empty:


                low_stock = df_inv[
                    df_inv["qty"]
                    <=
                    df_inv["reorder_level"]
                ]


                st.metric(
                    "Low Stock Items",
                    len(low_stock)
                )


                if len(low_stock) > 0:

                    st.dataframe(
                        low_stock,
                        use_container_width=True,
                        hide_index=True
                    )


            else:

                st.info(
                    "No inventory data"
                )


        except Exception as e:

            st.error(
                f"Inventory error: {e}"
            )



    st.divider()



    # ==========================================================================
    # RECENT TRANSACTIONS
    # ==========================================================================

    st.subheader(
        "📋 Recent Transactions"
    )


    if not df_sales.empty:


        st.dataframe(
            df_sales.head(20),
            use_container_width=True,
            hide_index=True
        )


    else:


        st.info(
            "No transaction records found."
        )



# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":

    run()
