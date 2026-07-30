# ==============================================================================
# erp_pages/3_Reports.py
# ERP ENTERPRISE SALES ANALYTICS REPORT v4.0
# Sales Summary + Cashier + Payment + Export
# ==============================================================================


from utils.timezone import (
    format_datetime
)
from io import BytesIO
import json


import pandas as pd
import streamlit as st


from erp_core.base_repo import db

from utils.notification import toast_success
from utils.ui import show_table




# ==============================================================================
# HELPERS
# ==============================================================================


def safe_number(value):

    try:
        return float(value or 0)

    except:

        return 0.0




# ==============================================================================
# RUN
# ==============================================================================


def run():


    st.title(
        "📊 ERP Executive Analytics & Reports"
    )


    st.caption(
        "MYANMAR ERP - Sales Performance Analytics"
    )



    # =====================================================
    # DATE FILTER
    # =====================================================


    c1,c2 = st.columns(2)


    start_date = c1.date_input(
        "Start Date",
        value=date.today()
    )


    end_date = c2.date_input(
        "End Date",
        value=date.today()
    )



    start_iso = start_date.isoformat()


    end_iso = (
        end_date
        +
        timedelta(days=1)
    ).isoformat()




    # =====================================================
    # LOAD SALES
    # =====================================================


    @st.cache_data(ttl=60)

    def get_sales():

        try:

            response = (

                db()

                .table("sales")

                .select(
                    """
                    id,
                    total,
                    discount,
                    tax,
                    subtotal,
                    paid_amount,
                    payment_method,
                    created_at,
                    cashier_id,
                    users(
                        username,
                        employee_code
                    )
                    """
                )

                .gte(
                    "created_at",
                    start_iso
                )

                .lt(
                    "created_at",
                    end_iso
                )

                .order(
                    "created_at",
                    desc=True
                )

                .execute()

            )


            return response.data or []


        except Exception as e:

            st.error(
                f"Sales loading error : {e}"
            )

            return []



    sales = get_sales()



    if not sales:

        st.warning(
            "No sales data found"
        )

        return




    df = pd.DataFrame(
        sales
    )




    # =====================================================
    # NORMALIZE
    # =====================================================


    money_columns = [

        "total",

        "discount",

        "tax",

        "subtotal",

        "paid_amount"

    ]



    for col in money_columns:


        if col in df.columns:

            df[col] = (

                pd.to_numeric(

                    df[col],

                    errors="coerce"

                )

                .fillna(0)

            )



    # Myanmar Time


    df["created_at"] = pd.to_datetime(

        df["created_at"],

        utc=True

    )


    df["created_at"] = (

        df["created_at"]

        .dt.tz_convert(
            "Asia/Yangon"
        )

        .dt.tz_localize(None)

    )




    # =====================================================
    # CASHIER FORMAT
    # =====================================================


    def cashier_name(user):

        if isinstance(
            user,
            dict
        ):

            return (

                user.get(
                    "employee_code",
                    ""
                )

                +

                " "

                +

                user.get(
                    "username",
                    ""
                )

            )


        return "SYSTEM"



    df["Cashier"] = (

        df["users"]

        .apply(
            cashier_name
        )

        if "users" in df.columns

        else "SYSTEM"

    )




    # =====================================================
    # FILTER
    # =====================================================


    st.sidebar.subheader(
        "🔎 Filters"
    )


    cashier_options = [

        "All"

    ] + sorted(

        df["Cashier"]

        .unique()

        .tolist()

    )


    selected_cashier = st.sidebar.selectbox(

        "Cashier",

        cashier_options

    )



    if selected_cashier != "All":

        df = df[

            df["Cashier"]

            ==
            selected_cashier

        ]



    if df.empty:

        st.warning(
            "No data after filter"
        )

        return




    # =====================================================
    # KPI
    # =====================================================


    revenue = df["total"].sum()

    discount = df["discount"].sum()

    tax = df["tax"].sum()

    bills = len(df)



    c1,c2,c3,c4 = st.columns(4)



    c1.metric(

        "💰 Revenue",

        f"{revenue:,.0f} MMK"

    )


    c2.metric(

        "🧾 Bills",

        bills

    )


    c3.metric(

        "🏷 Discount",

        f"{discount:,.0f}"

    )


    c4.metric(

        "🧮 Tax",

        f"{tax:,.0f}"

    )




    st.divider()




    # =====================================================
    # TABS
    # =====================================================


    tab1,tab2,tab3,tab4 = st.tabs(

        [

            "📈 Sales Summary",

            "👨‍💼 Cashier",

            "💳 Payment",

            "📥 Export"

        ]

    )




    # -----------------------------------------------------
    # SALES SUMMARY
    # -----------------------------------------------------


    with tab1:


        st.subheader(
            "Daily Sales"
        )


        daily = (

            df.groupby(

                df["created_at"]

                .dt.date

            )

            ["total"]

            .sum()

            .reset_index()

        )


        show_table(
            daily
        )




        st.subheader(
            "Monthly Sales"
        )


        monthly = (

            df.groupby(

                df["created_at"]

                .dt.to_period("M")

                .astype(str)

            )

            ["total"]

            .sum()

            .reset_index()

        )


        show_table(
            monthly
        )




    # -----------------------------------------------------
    # CASHIER
    # -----------------------------------------------------


    with tab2:


        cashier = (

            df.groupby(
                "Cashier"
            )

            .agg(

                Bills=("id","count"),

                Sales=("total","sum")

            )

            .reset_index()

        )


        show_table(
            cashier
        )





    # -----------------------------------------------------
    # PAYMENT
    # -----------------------------------------------------


    with tab3:


        payment = (

            df.groupby(
                "payment_method"
            )

            .agg(

                Bills=("id","count"),

                Amount=("total","sum")

            )

            .reset_index()

        )


        show_table(
            payment
        )




    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------


    with tab4:


        export_df = df.copy()


        export_df.drop(

            columns=[

                "cashier_id",

                "users"

            ],

            errors="ignore",

            inplace=True

        )



        for col in export_df.columns:


            if export_df[col].dtype == "object":

                export_df[col] = export_df[col].apply(

                    lambda x:

                    json.dumps(x)

                    if isinstance(
                        x,
                        (dict,list)
                    )

                    else x

                )



        export_df = export_df.fillna("")



        csv = export_df.to_csv(

            index=False

        ).encode("utf-8")



        st.download_button(

            "⬇ Download CSV",

            csv,

            "ERP_Sales_Report.csv",

            "text/csv"

        )



        output = BytesIO()


        with pd.ExcelWriter(

            output,

            engine="openpyxl"

        ) as writer:


            export_df.to_excel(

                writer,

                index=False,

                sheet_name="Sales"

            )



        st.download_button(

            "⬇ Download Excel",

            output.getvalue(),

            "ERP_Sales_Report.xlsx",

            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        )



if __name__ == "__main__":

    run()
