# ==============================================================================
# pages/3_Dashboard.py
# ERP ENTERPRISE ANALYTICS DASHBOARD V30
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


# V30 Repository Layer
try:
    from erp_core.repositories import (
        get_warehouses
    )
except Exception:
    get_warehouses = lambda: []



# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run():

    st.set_page_config(
        page_title="ERP Enterprise Dashboard",
        page_icon="📈",
        layout="wide"
    )


    # --------------------------------------------------
    # AUTH
    # --------------------------------------------------

    require_login()

    user = current_user()



    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    st.title(
        "📈 Enterprise Analytics Dashboard"
    )

    st.caption(
        "Real-time financial, inventory, and sales performance metrics."
    )

    st.divider()



    # --------------------------------------------------
    # SIDEBAR FILTER
    # --------------------------------------------------

    st.sidebar.header(
        "📊 Dashboard Filters"
    )


    warehouses = get_warehouses()


    warehouse_options = [
        {
            "id": None,
            "name": "All Warehouses"
        }
    ]


    for w in warehouses or []:

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
            "Today",
            "Last 7 Days",
            "This Month",
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

    elif period == "This Month":

        start_date = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0
        )

    else:

        start_date = now.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0
        )


    end_date = now




    if st.sidebar.button(
        "🔄 Refresh"
    ):

        st.cache_data.clear()

        st.rerun()



    # --------------------------------------------------
# DATABASE
# --------------------------------------------------

supabase = db()


# DEBUG TEST (TEMPORARY)
try:
    test_sales = (
        supabase
        .table("sales")
        .select("id", count="exact")
        .execute()
    )

    st.write(
        "APP SALES COUNT:",
        test_sales
    )

except Exception as e:
    st.error(
        f"Sales Debug Error: {e}"
    )

    # --------------------------------------------------
    # SALES QUERY
    # --------------------------------------------------

    df_sales = pd.DataFrame()


    try:


        query = supabase.table(
            "sales"
        ).select(
            """
            id,
            total,
            total_amount,
            paid_amount,
            sale_status,
            warehouse_id,
            created_at
            """
        )


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
        )


        result = query.execute()


        df_sales = pd.DataFrame(
            result.data or []
        )
        st.write("DEBUG SALES RESULT:", result.data)
        st.write("DEBUG SALES DF:", df_sales)

    except Exception as e:


        st.warning(
            "Sales data unavailable"
        )



    # --------------------------------------------------
    # KPI
    # --------------------------------------------------

    st.subheader(
        "📌 Key Performance Indicators"
    )


    gross_sales = 0

    total_paid = 0

    refunds = 0

    transactions = 0


    total_sales_col = None



    if not df_sales.empty:


        transactions = len(
            df_sales
        )


        if "total" in df_sales.columns:
            total_sales_col = "total"

        elif "total_amount" in df_sales.columns:
            total_sales_col = "total_amount"



        if total_sales_col:

            gross_sales = (
                df_sales[total_sales_col]
                .apply(safe_float)
                .sum()
            )


        if "paid_amount" in df_sales.columns:

            total_paid = (
                df_sales["paid_amount"]
                .apply(safe_float)
                .sum()
            )


        if "refund_amount" in df_sales.columns:

            refunds = (
                df_sales["refund_amount"]
                .apply(safe_float)
                .sum()
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



    # --------------------------------------------------
    # SALES TREND
    # --------------------------------------------------

    col1, col2 = st.columns(2)



    with col1:


        st.subheader(
            "📈 Sales Trend"
        )


        if not df_sales.empty and "created_at" in df_sales:


            df_sales["date"] = (
                pd.to_datetime(
                    df_sales["created_at"]
                )
                .dt.date
            )


            chart_col = (
                total_sales_col
                or "total"
            )


            if chart_col in df_sales.columns:


                trend = (
                    df_sales
                    .groupby("date")[chart_col]
                    .sum()
                )


                st.line_chart(
                    trend
                )


        else:

            st.info(
                "No sales data"
            )




    # --------------------------------------------------
    # INVENTORY
    # --------------------------------------------------

    with col2:


        st.subheader(
            "📦 Inventory Health"
        )


        try:

            inv = (
                supabase
                .table(
                    "pos_products_view"
                )
                .select(
                    "name,stock,minimum_stock"
                )
            )


            data = inv.execute().data or []


            df_inv = pd.DataFrame(
                data
            )


            if not df_inv.empty:


                low = df_inv[
                    df_inv.stock
                    <=
                    df_inv.minimum_stock
                ]


                st.metric(
                    "Low Stock Items",
                    len(low)
                )


            else:

                st.info(
                    "No inventory data"
                )


        except Exception:


            st.info(
                "Inventory view unavailable"
            )



    st.divider()



    # --------------------------------------------------
    # RECENT SALES
    # --------------------------------------------------

    st.subheader(
        "📋 Recent Transactions"
    )


    if not df_sales.empty:


        st.dataframe(
            df_sales.head(20),
            use_container_width=True
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
