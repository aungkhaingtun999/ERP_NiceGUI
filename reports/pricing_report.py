# ==============================================================================
# reports/pricing_report.py
# ERP ENTERPRISE PRICING REPORT UI v3.0
# Product + Category + Global Markup Analysis
# ==============================================================================

import streamlit as st
import pandas as pd

from reports.pricing_report_service import (
    get_pricing_report_products
)

from reports.pricing_report_excel import (
    create_pricing_excel_report
)


# ==============================================================================
# RUN
# ==============================================================================

def run():

    st.title(
        "💰 Product Pricing Report"
    )

    st.caption(
        "MYANMAR ERP - Product Cost, Markup & Selling Price Analysis"
    )


    # =====================================================
    # LOAD DATA
    # =====================================================

    products = get_pricing_report_products()


    if not products:

        st.warning(
            "No products found"
        )

        return



    # =====================================================
    # FILTER DATA
    # =====================================================

    col1, col2 = st.columns(2)


    with col1:

        search = st.text_input(
            "🔍 Search Product"
        )


    with col2:

        categories = sorted(
            list(
                set(
                    [
                        p.get(
                            "category",
                            "-"
                        )
                        for p in products
                    ]
                )
            )
        )


        category_filter = st.selectbox(

            "📂 Category",

            [
                "All"
            ]
            +
            categories

        )



    filtered = products.copy()



    if search:


        filtered = [

            p for p in filtered

            if search.lower()
            in
            p.get(
                "name",
                ""
            ).lower()

        ]



    if category_filter != "All":


        filtered = [

            p for p in filtered

            if p.get(
                "category"
            )
            ==
            category_filter

        ]




    # =====================================================
    # KPI
    # =====================================================

    total_products = len(filtered)


    total_profit = sum(

        float(
            p.get(
                "profit",
                0
            )
            or 0
        )

        for p in filtered

    )


    avg_markup = (

        sum(

            float(
                p.get(
                    "final_markup_percent",
                    0
                )
                or 0
            )

            for p in filtered

        )

        /

        total_products

        if total_products

        else 0

    )



    c1,c2,c3 = st.columns(3)



    c1.metric(

        "📦 Products",

        total_products

    )


    c2.metric(

        "💰 Total Profit",

        f"{total_profit:,.2f}"

    )


    c3.metric(

        "📈 Avg Markup %",

        f"{avg_markup:.2f}%"

    )



    st.divider()



    # =====================================================
    # REPORT TABLE
    # =====================================================


    rows = []


    for p in filtered:


        rows.append({

            "Product":

                p.get(
                    "name"
                ),


            "SKU":

                p.get(
                    "sku"
                ),


            "Category":

                p.get(
                    "category"
                ),


            "Cost":

                p.get(
                    "purchase_price"
                ),


            "Selling":

                p.get(
                    "selling_price"
                ),


            "Profit":

                p.get(
                    "profit"
                ),



            "Product Markup %":

                p.get(
                    "product_markup"
                ),



            "Category Markup %":

                p.get(
                    "category_markup"
                ),



            "Global Markup %":

                p.get(
                    "global_markup"
                ),



            "Final Markup %":

                f"{p.get('final_markup_percent',0)}%"


            ,


            "Markup Source":

                p.get(
                    "markup_source"
                )

        })



    df = pd.DataFrame(
        rows
    )



    st.dataframe(

        df,

        use_container_width=True,

        hide_index=True

    )



    # =====================================================
    # EXCEL EXPORT
    # =====================================================


    excel = create_pricing_excel_report(

        filtered

    )


    st.download_button(

        label="📥 Download Pricing Excel",

        data=excel,

        file_name="pricing_report.xlsx",

        mime=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )



# ==============================================================================
# STREAMLIT ENTRY
# ==============================================================================

if __name__ == "__main__":

    run()
