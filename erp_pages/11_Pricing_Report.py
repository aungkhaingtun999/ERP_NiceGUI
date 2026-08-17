# ==============================================================================
# erp_pages/11_Pricing_Report.py
# ERP ENTERPRISE PRICING REPORT v4.0
# Product + Category + Global Markup Analysis
# ==============================================================================

import streamlit as st
from reports.pricing_report_service import get_pricing_report_products
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
# HELPERS
# ==============================================================================

def safe_float(value):
    try:
        return float(value or 0)
    except:
        return 0

def money(value):
    return f"{safe_float(value):,.0f}"

def percent(value):
    return f"{safe_float(value):.2f}%"


# ==============================================================================
# RUN
# ==============================================================================

def run():
    st.title("💰 Product Pricing Report")
    st.caption("MYANMAR ERP - Product Cost, Markup & Selling Price Analysis")

    # ==========================================================================
    # LOAD PRICING ENGINE DATA
    # ==========================================================================

    products = get_pricing_report_products()

    if not products:
        st.warning("No pricing data found")
        return

    # ==========================================================================
    # FILTER
    # ==========================================================================

    col1, col2 = st.columns(2)

    with col1:
        search = st.text_input("🔍 Search Product")

    with col2:
        category_list = sorted(
            list(
                set(
                    [
                        p.get("category", "Uncategorized")
                        for p in products
                    ]
                )
            )
        )
        category_filter = st.selectbox(
            "📂 Category",
            ["All"] + category_list
        )

    filtered = products.copy()

    if search:
        filtered = [
            p for p in filtered
            if search.lower() in p.get("name", "").lower()
        ]

    if category_filter != "All":
        filtered = [
            p for p in filtered
            if p.get("category") == category_filter
        ]

    if not filtered:
        st.warning("No matching products")
        return

    # ==========================================================================
    # KPI SUMMARY
    # ==========================================================================

    total_products = len(filtered)
    total_profit = sum(
        safe_float(p.get("profit"))
        for p in filtered
    )
    average_markup = (
        sum(
            safe_float(p.get("final_markup_percent"))
            for p in filtered
        )
        / total_products
        if total_products
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("📦 Products", total_products)
    c2.metric("💰 Total Profit", f"{total_profit:,.0f} MMK")
    c3.metric("📈 Average Markup", f"{average_markup:.2f}%")
    c4.metric("⚙️ Pricing Rule", "Dynamic")

    st.divider()

    # ==========================================================================
    # MARKUP FLOW INFO
    # ==========================================================================

    st.info(
        """
        💰 Pricing Priority Engine

        Product Markup
              ↓
        Category Markup
              ↓
        Global Default Markup

        Controlled from ERP Settings
        """
    )

    # ==========================================================================
    # PRICING ANALYSIS TABLE
    # ==========================================================================

    st.subheader("📋 Pricing Analysis")

    rows = []

    for p in filtered:
        rows.append(
            {
                "Product": p.get("name", ""),
                "SKU": p.get("sku", ""),
                "Category": p.get("category", "-"),
                "Cost": money(p.get("purchase_price")),
                "Product Markup %": percent(p.get("product_markup")),
                "Category Markup %": percent(p.get("category_markup")),
                "Global Markup %": percent(p.get("global_markup")),
                "Final Markup %": percent(p.get("final_markup_percent")),
                "Applied Source": p.get("markup_source", "GLOBAL_DEFAULT_MARKUP"),
                "Current Selling": money(p.get("selling_price")),
                "Expected Selling": money(p.get("expected_selling_price")),
                "Difference": money(p.get("price_difference")),
                "Profit": money(p.get("profit"))
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
    st.subheader("📥 Export Center")

    excel_file = create_pricing_excel_report(filtered)

    st.download_button(
        label="📥 Download Pricing Excel Report",
        data=excel_file,
        file_name="ERP_Pricing_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
