# ==============================================================================
# erp_pages/11_Pricing_Report.py
# ERP ENTERPRISE PRICING REPORT v3.0
# Product + Category + Global Markup Analysis
# ==============================================================================


import streamlit as st

from reports.pricing_report import (
    get_pricing_report_products
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


def safe_float(value):

    try:

        return float(value or 0)

    except:

        return 0



def safe_percent(value):

    return f"{safe_float(value):.2f}%"



# ==============================================================================
# MAIN
# ==============================================================================


def run():


    st.title(
        "💰 Product Pricing Report"
    )


    st.caption(
        "MYANMAR ERP - Product Cost, Markup & Selling Price Analysis"
    )



    # ==========================================================================
    # LOAD DATA FROM PRICING ENGINE
    # ==========================================================================


    products = get_pricing_report_products()



    if not products:

        st.warning(
            "No products found"
        )

        return



    # ==========================================================================
    # FILTER
    # ==========================================================================


    col1, col2 = st.columns(2)



    with col1:

        search = st.text_input(
            "🔍 Search Product"
        )



    with col2:


        categories = sorted(

            list(

                set(

                    p.get(
                        "category",
                        "Uncategorized"
                    )

                    for p in products

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



    filtered = products



    if search:


        filtered = [

            p

            for p in filtered

            if search.lower()

            in

            p.get(
                "name",
                ""
            )
            .lower()

        ]



    if category_filter != "All":


        filtered = [

            p

            for p in filtered

            if p.get(
                "category"
            )
            ==
            category_filter

        ]



    # ==========================================================================
    # KPI
    # ==========================================================================


    total_products = len(filtered)



    total_profit = sum(

        safe_float(
            p.get("profit")
        )

        for p in filtered

    )



    avg_markup = (

        sum(

            safe_float(

                p.get(
                    "final_markup_percent"
                )

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

        f"{total_profit:,.0f} MMK"

    )



    c3.metric(

        "📈 Average Markup",

        f"{avg_markup:.2f}%"

    )



    # ==========================================================================
    # TABLE
    # ==========================================================================


    st.divider()


    st.subheader(
        "📋 Pricing Analysis"
    )



    rows = []



    for p in filtered:



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
                        "-"
                    ),



                "Cost":

                    f"{safe_float(p.get('purchase_price')):,.0f}",



                "Product Markup":

                    safe_percent(
                        p.get(
                            "product_markup"
                        )
                    ),



                "Category Markup":

                    safe_percent(
                        p.get(
                            "category_markup"
                        )
                    ),



                "Global Markup":

                    safe_percent(
                        p.get(
                            "global_markup"
                        )
                    ),



                "Final Markup":

                    safe_percent(
                        p.get(
                            "final_markup_percent"
                        )
                    ),



                "Source":

                    p.get(
                        "markup_source",
                        ""
                    ),



                "Selling Price":

                    f"{safe_float(p.get('selling_price')):,.0f}",



                "Profit":

                    f"{safe_float(p.get('profit')):,.0f}"

            }

        )



    st.dataframe(

        rows,

        use_container_width=True,

        hide_index=True

    )



    # ==========================================================================
    # EXCEL EXPORT
    # ==========================================================================


    st.divider()



    excel_file = create_pricing_excel_report(

        filtered

    )



    st.download_button(

        label="📥 Download Excel Pricing Report",

        data=excel_file,

        file_name="pricing_report.xlsx",

        mime=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )



# ==============================================================================
# ENTRY
# ==============================================================================


if __name__ == "__main__":

    run()
