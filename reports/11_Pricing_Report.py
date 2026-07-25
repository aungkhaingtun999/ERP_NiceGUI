# ==============================================================================
# pages/11_Pricing_Report.py
# ERP ENTERPRISE PRICING REPORT v1.0
# Product Pricing Analysis + Excel Export
# ==============================================================================


import streamlit as st

import pandas as pd

from decimal import Decimal


from erp_core import (
    get_products
)


from reports.pricing_report_excel import (
    create_pricing_excel_report
)



# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(

    page_title="Pricing Report",

    page_icon="💰",

    layout="wide"

)



# ==============================================================================
# HELPERS
# ==============================================================================


def money(value):

    try:

        return f"{Decimal(str(value)):,.2f} MMK"

    except:

        return "0.00 MMK"



# ==============================================================================
# MAIN
# ==============================================================================


def run():


    st.title(
        "💰 Product Pricing Report"
    )


    st.caption(
        "Markup Analysis | Selling Price Control | Profit Report"
    )



    # ==========================================================================
    # LOAD PRODUCTS
    # ==========================================================================


    try:

        products = get_products(
            limit=5000
        )


    except Exception as e:

        st.error(
            f"Product loading error : {e}"
        )

        return



    if not products:

        st.warning(
            "No products found"
        )

        return



    # ==========================================================================
    # SEARCH + FILTER
    # ==========================================================================


    col1, col2 = st.columns(2)



    with col1:

        search = st.text_input(

            "🔍 Search Product",

            placeholder="Enter product name..."

        )



    with col2:

        categories = [

            "All"

        ]


        for p in products:

            cat = p.get(
                "category",
                ""
            )

            if cat and cat not in categories:

                categories.append(cat)



        selected_category = st.selectbox(

            "📂 Category",

            categories

        )



    # ==========================================================================
    # FILTER
    # ==========================================================================


    filtered = []



    for p in products:


        name = str(
            p.get(
                "name",
                ""
            )
        )


        category = str(
            p.get(
                "category",
                ""
            )
        )



        if search:

            if search.lower() not in name.lower():

                continue



        if selected_category != "All":


            if category != selected_category:

                continue



        filtered.append(p)



    if not filtered:

        st.info(
            "No matching products"
        )

        return



    # ==========================================================================
    # REPORT DATA
    # ==========================================================================


    rows = []



    total_profit = Decimal("0")



    for p in filtered:


        cost = Decimal(

            str(

                p.get(
                    "purchase_price",
                    0
                )
                or 0

            )

        )



        selling = Decimal(

            str(

                p.get(
                    "selling_price",
                    0
                )
                or 0

            )

        )



        profit = selling - cost



        total_profit += profit



        rows.append(

            {

                "Product":

                    p.get(
                        "name",
                        ""
                    ),


                "SKU":

                    p.get(
                        "sku",
                        ""
                    ),


                "Category":

                    p.get(
                        "category",
                        ""
                    ),


                "Purchase Cost":

                    float(cost),


                "Markup %":

                    p.get(
                        "markup_percent",
                        0
                    )
                    or 0,


                "Selling Price":

                    float(selling),


                "Profit":

                    float(profit)

            }

        )



    df = pd.DataFrame(
        rows
    )



    # ==========================================================================
    # KPI
    # ==========================================================================


    c1,c2,c3 = st.columns(3)



    with c1:

        st.metric(

            "Total Products",

            len(filtered)

        )



    with c2:

        st.metric(

            "Total Profit",

            money(total_profit)

        )



    with c3:

        avg_markup = (

            df["Markup %"].mean()

            if not df.empty

            else 0

        )


        st.metric(

            "Average Markup",

            f"{avg_markup:.2f}%"

        )



    st.divider()



    # ==========================================================================
    # TABLE
    # ==========================================================================


    st.subheader(
        "📊 Pricing Details"
    )



    st.dataframe(

        df,

        use_container_width=True,

        hide_index=True

    )



    st.divider()



    # ==========================================================================
    # EXCEL EXPORT
    # ==========================================================================


    st.subheader(
        "📥 Export Report"
    )



    excel_file = create_pricing_excel_report(

        filtered

    )



    st.download_button(

        "📥 Download Excel Pricing Report",

        excel_file,

        "pricing_report.xlsx",

        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

        use_container_width=True

    )



# ==============================================================================
# RUN
# ==============================================================================


if __name__ == "__main__":

    run()
