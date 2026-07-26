# ==============================================================================
# erp_pages/11_Pricing_Report.py
# ERP ENTERPRISE PRICING REPORT v2.0
# Product Cost, Markup & Selling Price Analysis
# ==============================================================================


import streamlit as st

from erp_core.loaders.product_loader import get_products
from reports.pricing_report_excel import create_pricing_excel_report



# ==============================================================================
# PAGE CONFIG
# ==============================================================================

st.set_page_config(
    page_title="Pricing Report",
    page_icon="💰",
    layout="wide"
)



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
    # LOAD PRODUCTS
    # ==========================================================================

    products = get_products(
        warehouse_id=None
    )


    if not products:

        st.warning(
            "No products found"
        )

        return



    # ==========================================================================
    # NORMALIZE DATA
    # ==========================================================================

    report_products = []



    for p in products:


        cost = float(

            p.get(
                "purchase_price",
                0
            )
            or 0

        )


        selling = float(

            p.get(
                "selling_price",
                0
            )
            or 0

        )


        profit = selling - cost



        # =====================================================
        # MARKUP ENGINE
        # Product Override
        # Else Calculate From Cost
        # =====================================================


        stored_markup = p.get(
            "markup_percent"
        )


        if stored_markup is not None:


            markup = float(
                stored_markup
            )


            markup_source = (
                "Product Override"
            )


        elif cost > 0:


            markup = (

                (selling - cost)

                /

                cost

            ) * 100


            markup_source = (
                "Calculated"
            )


        else:


            markup = 0


            markup_source = (
                "No Cost"
            )



        report_products.append(

            {


                "id":

                    p.get(
                        "id"
                    ),



                "name":

                    p.get(
                        "name",
                        ""
                    ),



                "sku":

                    p.get(
                        "sku",
                        ""
                    ),



                "category":

                    p.get(
                        "category"
                    )
                    or
                    "Uncategorized",



                "purchase_price":

                    cost,



                "selling_price":

                    selling,



                "profit":

                    profit,



                "markup_percent":

                    round(
                        markup,
                        2
                    ),



                "markup_source":

                    markup_source


            }

        )



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

            {

                p["category"]

                for p in report_products

            }

        )


        category_filter = st.selectbox(

            "📂 Category",

            [
                "All"
            ]
            +
            categories

        )



    filtered = report_products



    if search:


        filtered = [

            p

            for p in filtered

            if search.lower()

            in

            p["name"].lower()

        ]



    if category_filter != "All":


        filtered = [

            p

            for p in filtered

            if p["category"]

            ==
            category_filter

        ]



    # ==========================================================================
    # KPI
    # ==========================================================================


    total_products = len(
        filtered
    )


    total_profit = sum(

        p["profit"]

        for p in filtered

    )


    avg_markup = (

        sum(

            p["markup_percent"]

            for p in filtered

        )

        /

        total_products

        if total_products

        else 0

    )



    c1, c2, c3 = st.columns(3)



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



    display_rows = []



    for p in filtered:


        display_rows.append(

            {


                "Product":

                    p["name"],



                "SKU":

                    p["sku"],



                "Category":

                    p["category"],



                "Cost":

                    f"{p['purchase_price']:,.0f}",



                "Selling":

                    f"{p['selling_price']:,.0f}",



                "Profit":

                    f"{p['profit']:,.0f}",



                "Markup %":

                    f"{p['markup_percent']:.2f}%",



                "Source":

                    p["markup_source"]


            }

        )



    st.dataframe(

        display_rows,

        use_container_width=True,

        hide_index=True

    )



    # ==========================================================================
    # EXCEL EXPORT
    # ==========================================================================


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
