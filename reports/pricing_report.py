# ==============================================================================
# reports/pricing_report.py
# ERP ENTERPRISE PRICING REPORT UI v4.0
# Product + Category + Global Markup Analysis
# Part 1/3
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

    st.title("💰 Product Pricing Report")

    st.caption(
        "MYANMAR ERP - Product Cost, Markup & Selling Price Analysis"
    )

    # =====================================================
    # LOAD DATA
    # =====================================================

    products = get_pricing_report_products()

    if not products:
        st.warning("No products found.")
        return

    # =====================================================
    # FILTERS
    # =====================================================

    col1, col2 = st.columns(2)

    with col1:
        search = st.text_input(
            "🔍 Search Product"
        )

    with col2:

        categories = sorted(
            list(
                {
                    p.get("category", "Uncategorized")
                    for p in products
                }
            )
        )

        category_filter = st.selectbox(
            "📂 Category",
            ["All"] + categories
        )

    filtered = products.copy()

    # Search
    if search:

        filtered = [

            p

            for p in filtered

            if search.lower()

            in

            str(
                p.get("name", "")
            ).lower
                # =====================================================
    # REPORT TABLE
    # =====================================================

    rows = []

    for p in filtered:

        product_markup = (
            float(p["product_markup"])
            if p.get("product_markup") is not None
            else None
        )

        category_markup = (
            float(p["category_markup"])
            if p.get("category_markup") is not None
            else None
        )

        global_markup = (
            float(p.get("global_markup") or 0)
        )

        final_markup = (
            float(p.get("final_markup_percent") or 0)
        )

        rows.append({

            "Product":
                p.get("name", ""),

            "SKU":
                p.get("sku", ""),

            "Category":
                p.get("category", "-"),

            "Cost (MMK)":
                f"{float(p.get('purchase_price') or 0):,.2f}",

            "Selling (MMK)":
                f"{float(p.get('selling_price') or 0):,.2f}",

            "Profit (MMK)":
                f"{float(p.get('profit') or 0):,.2f}",

            "Product Markup":
                (
                    f"{product_markup:.2f}%"
                    if product_markup is not None
                    else "-"
                ),

            "Category Markup":
                (
                    f"{category_markup:.2f}%"
                    if category_markup is not None
                    else "-"
                ),

            "Global Markup":
                f"{global_markup:.2f}%",

            "Final Markup":
                f"{final_markup:.2f}%",

            "Applied Source":
                p.get("markup_source", "-")

        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
        )
        # =====================================================
    # EXCEL EXPORT
    # =====================================================

    st.divider()

    st.subheader(
        "📥 Export Pricing Report"
    )

    excel = create_pricing_excel_report(
        filtered
    )

    st.download_button(
        label="📥 Download Pricing Excel",
        data=excel,
        file_name="pricing_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.success(
        f"Showing {len(filtered)} of {len(products)} products."
    )


# ==============================================================================
# STREAMLIT ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
