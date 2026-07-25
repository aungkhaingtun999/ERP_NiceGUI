# ==============================================================================
# erp_pages/11_Pricing_Report.py
# ERP ENTERPRISE PRICING REPORT
# Excel + Search + Category Filter
# ==============================================================================


import streamlit as st

from erp_core.loaders.product_loader import get_products
from reports.pricing_report_excel import create_pricing_excel_report


def run():

    st.title("💰 Product Pricing Report")

    st.caption(
        "MYANMAR ERP - Product Cost, Markup & Selling Price Analysis"
    )

    products = get_products(warehouse_id=None)

    if not products:
        st.warning("No products found")
        return

    # အောက်က code အားလုံး (Normalize, Filter, KPI,
    # Dataframe, Download Button...) ကို
    # ဒီ run() function အတွင်းကို indent လုပ်ပြီးထည့်ပါ။


# ==============================================================================
# PAGE CONFIG
# ==============================================================================


st.set_page_config(

    page_title="Pricing Report",

    page_icon="💰",

    layout="wide"

)



# ==============================================================================
# TITLE
# ==============================================================================


st.title(
    "💰 Product Pricing Report"
)


st.caption(
    "MYANMAR ERP - Product Cost, Markup & Selling Price Analysis"
)



# ==============================================================================
# LOAD PRODUCTS
# ==============================================================================


products = get_products(
    warehouse_id=None
)



if not products:

    st.warning(
        "No products found"
    )

    st.stop()



# ==============================================================================
# NORMALIZE DATA
# ==============================================================================


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



    report_products.append(

        {

            "id":
                p.get("id"),


            "name":
                p.get("name",""),


            "sku":
                p.get("sku",""),


            "category": p.get("category") or "Uncategorized",


            "purchase_price":
                cost,


            "markup_percent":
                p.get(
                    "markup_percent",
                    0
                ),


            "selling_price":
                selling,


            "profit":
                profit

        }

    )



# ==============================================================================
# FILTER
# ==============================================================================


col1, col2 = st.columns(2)



with col1:

    search = st.text_input(

        "🔍 Search Product"

    )



with col2:

    categories = sorted(
    {
        p.get("category") or "Uncategorized"
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

        p for p in filtered

        if search.lower()

        in p["name"].lower()

    ]



if category_filter != "All":


    filtered = [

        p for p in filtered

        if p["category"]

        ==
        category_filter

    ]



# ==============================================================================
# SUMMARY KPI
# ==============================================================================


total_products = len(filtered)


total_profit = sum(

    p["profit"]

    for p in filtered

)



c1,c2,c3 = st.columns(3)



with c1:

    st.metric(

        "Products",

        total_products

    )



with c2:

    st.metric(

        "Total Profit",

        f"{total_profit:,.2f}"

    )



with c3:

    avg_margin = (

        total_profit / total_products

        if total_products

        else 0

    )


    st.metric(

        "Average Profit",

        f"{avg_margin:,.2f}"

    )



# ==============================================================================
# TABLE
# ==============================================================================


st.divider()



st.dataframe(

    filtered,

    use_container_width=True,

    hide_index=True

)



# ==============================================================================
# EXCEL EXPORT
# ==============================================================================


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
