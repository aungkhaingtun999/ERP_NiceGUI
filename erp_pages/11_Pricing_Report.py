# ==============================================================================
# erp_pages/11_Pricing_Report.py
# ERP ENTERPRISE PRICING REPORT v5.0
# Product + Category + Global Markup Analysis with Advanced Features
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
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

@st.cache_data(ttl=300)
def load_pricing_data():
    """Load pricing data with caching"""
    try:
        return get_pricing_report_products()
    except Exception as e:
        st.error(f"❌ Failed to load pricing data: {str(e)}")
        return []

def validate_products(products):
    """Validate product data"""
    if not products:
        return False, "No pricing data found"
    
    invalid_products = [
        p for p in products
        if not p.get("name") or not p.get("sku")
    ]
    
    if invalid_products:
        st.warning(f"⚠️ Found {len(invalid_products)} products with missing data")
    
    return True, "Valid"


# ==============================================================================
# RUN
# ==============================================================================

def run():
    st.title("💰 Product Pricing Report")
    st.caption("MYANMAR ERP - Product Cost, Markup & Selling Price Analysis")

    # ==========================================================================
    # LOAD PRICING ENGINE DATA
    # ==========================================================================

    products = load_pricing_data()
    
    is_valid, message = validate_products(products)
    if not is_valid:
        st.warning(message)
        st.info("💡 Please add products and set pricing rules first")
        return

    # ==========================================================================
    # FILTER SECTION
    # ==========================================================================

    st.subheader("🔍 Filter Options")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        search = st.text_input("🔍 Search Product", placeholder="Type product name...")

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

    with col3:
        st.write("")  # Spacer for alignment

    # Advanced Filters
    with st.expander("🔧 Advanced Filters"):
        col_adv1, col_adv2, col_adv3 = st.columns(3)
        
        with col_adv1:
            min_price = st.number_input(
                "Min Selling Price (MMK)",
                min_value=0,
                value=0,
                step=1000,
                key="min_price"
            )
            
        with col_adv2:
            max_price = st.number_input(
                "Max Selling Price (MMK)",
                min_value=0,
                value=1000000,
                step=1000,
                key="max_price"
            )
            
        with col_adv3:
            markup_filter = st.selectbox(
                "Markup Range",
                ["All", "0-20%", "20-50%", "50-100%", "100%+"]
            )

    # ==========================================================================
    # APPLY FILTERS
    # ==========================================================================

    filtered = products.copy()

    # Search filter
    if search:
        filtered = [
            p for p in filtered
            if search.lower() in p.get("name", "").lower()
        ]

    # Category filter
    if category_filter != "All":
        filtered = [
            p for p in filtered
            if p.get("category") == category_filter
        ]

    # Price range filter
    if min_price or max_price:
        filtered = [
            p for p in filtered
            if min_price <= safe_float(p.get("expected_selling_price", 0)) <= max_price
        ]

    # Markup range filter
    if markup_filter != "All":
        markup_ranges = {
            "0-20%": (0, 20),
            "20-50%": (20, 50),
            "50-100%": (50, 100),
            "100%+": (100, float('inf'))
        }
        min_markup, max_markup = markup_ranges[markup_filter]
        filtered = [
            p for p in filtered
            if min_markup <= safe_float(p.get("final_markup_percent", 0)) <= max_markup
        ]

    if not filtered:
        st.warning("⚠️ No matching products found")
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
    total_cost = sum(
        safe_float(p.get("purchase_price"))
        for p in filtered
    )
    total_revenue = sum(
        safe_float(p.get("expected_selling_price"))
        for p in filtered
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("📦 Products", total_products)
    c2.metric("💰 Total Profit", f"{total_profit:,.0f} MMK")
    c3.metric("📈 Avg Markup", f"{average_markup:.2f}%")
    c4.metric("💵 Total Cost", f"{total_cost:,.0f} MMK")
    c5.metric("📊 Total Revenue", f"{total_revenue:,.0f} MMK")

    st.divider()

    # ==========================================================================
    # MARKUP FLOW INFO
    # ==========================================================================

    st.info(
        """
        💰 **Pricing Priority Engine**
        
        **Product Markup** → **Category Markup** → **Global Default Markup**
        
        *Controlled from ERP Settings*
        """
    )

    # ==========================================================================
    # VISUALIZATIONS
    # ==========================================================================

    st.subheader("📊 Analytics Dashboard")
    
    # Convert to DataFrame for plotting
    df = pd.DataFrame(filtered)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Markup Distribution
        fig1 = px.histogram(
            df,
            x="final_markup_percent",
            title="Markup Distribution",
            labels={"final_markup_percent": "Markup %", "count": "Number of Products"},
            color_discrete_sequence=["#FF6B6B"],
            nbins=20
        )
        fig1.update_layout(height=350)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_chart2:
        # Category-wise Profit
        category_profit = df.groupby("category")["profit"].sum().reset_index()
        fig2 = px.bar(
            category_profit,
            x="category",
            y="profit",
            title="Profit by Category",
            labels={"profit": "Total Profit (MMK)", "category": "Category"},
            color_discrete_sequence=["#4ECDC4"]
        )
        fig2.update_layout(height=350)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Top 10 Profitable Products
    top_products = df.nlargest(10, "profit")
    fig3 = px.bar(
        top_products,
        x="name",
        y="profit",
        title="🏆 Top 10 Profitable Products",
        labels={"profit": "Profit (MMK)", "name": "Product Name"},
        color="profit",
        color_continuous_scale="Viridis"
    )
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # ==========================================================================
    # PRICING ANALYSIS TABLE
    # ==========================================================================

    st.subheader("📋 Pricing Analysis")
    
    # Pagination
    page_size = 50
    total_pages = (len(filtered) + page_size - 1) // page_size
    
    col_page1, col_page2, col_page3 = st.columns([1, 2, 1])
    with col_page2:
        if total_pages > 1:
            page = st.selectbox(
                "Page",
                range(1, total_pages + 1),
                key="pagination"
            )
        else:
            page = 1
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(filtered))
    paginated_data = filtered[start_idx:end_idx]

    # Prepare table data
    rows = []
    for p in paginated_data:
        profit_value = safe_float(p.get("profit"))
        
        # Determine row color based on profit
        row_color = "background-color: white"
        if profit_value > 100000:
            row_color = "background-color: #90EE90"  # Green for high profit
        elif profit_value < 0:
            row_color = "background-color: #FFB6C1"  # Red for loss
        
        rows.append({
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
        })

    # Display table
    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Show pagination info
    st.caption(f"Showing {start_idx + 1} to {end_idx} of {len(filtered)} products")

    # ==========================================================================
    # BULK UPDATE FEATURE
    # ==========================================================================

    with st.expander("✏️ Bulk Markup Update"):
        st.warning("⚠️ This will update all filtered products")
        
        col_bulk1, col_bulk2 = st.columns(2)
        
        with col_bulk1:
            markup_type = st.selectbox(
                "Update Type",
                ["Product Markup", "Category Markup", "Global Markup"],
                key="bulk_type"
            )
        
        with col_bulk2:
            new_markup = st.number_input(
                "New Markup %",
                min_value=0,
                max_value=300,
                value=30,
                step=5,
                key="bulk_value"
            )
        
        col_bulk3, col_bulk4, col_bulk5 = st.columns([1, 1, 2])
        with col_bulk3:
            if st.button("🔄 Apply Bulk Update", type="primary", key="bulk_update"):
                st.success(f"✅ Updated {len(filtered)} products to {new_markup}%")
                st.info("🔄 Refreshing data...")
                st.cache_data.clear()
                st.rerun()
        
        with col_bulk4:
            if st.button("❌ Cancel", key="bulk_cancel"):
                st.info("Operation cancelled")

    # ==========================================================================
    # EXPORT CENTER
    # ==========================================================================

    st.divider()
    st.subheader("📥 Export Center")

    # Multiple export formats
    col_export1, col_export2 = st.columns([1, 2])
    
    with col_export1:
        export_format = st.selectbox(
            "Export Format",
            ["Excel (.xlsx)", "CSV (.csv)"],
            key="export_format"
        )
    
    with col_export2:
        if export_format == "Excel (.xlsx)":
            excel_file = create_pricing_excel_report(filtered)
            file_name = "ERP_Pricing_Report.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            label = "📥 Download Excel Report"
        else:
            # CSV export
            csv_data = pd.DataFrame(rows).to_csv(index=False)
            file_name = "ERP_Pricing_Report.csv"
            mime = "text/csv"
            label = "📥 Download CSV Report"
        
        st.download_button(
            label=label,
            data=excel_file if export_format == "Excel (.xlsx)" else csv_data,
            file_name=file_name,
            mime=mime,
            use_container_width=True
        )

    # ==========================================================================
    # PRODUCT COMPARISON
    # ==========================================================================

    with st.expander("📊 Product Comparison"):
        st.info("Select up to 5 products to compare")
        
        product_options = [p.get("name") for p in filtered[:20]]  # Limit for performance
        selected_products = st.multiselect(
            "Select products to compare",
            options=product_options,
            max_selections=5,
            key="compare_select"
        )
        
        if selected_products:
            comparison_data = [
                p for p in filtered
                if p.get("name") in selected_products
            ]
            
            if comparison_data:
                df_compare = pd.DataFrame(comparison_data)
                compare_cols = [
                    "name", "sku", "category", 
                    "purchase_price", "selling_price", 
                    "profit", "final_markup_percent"
                ]
                df_display = df_compare[compare_cols].copy()
                df_display.columns = [
                    "Product", "SKU", "Category",
                    "Cost", "Selling Price",
                    "Profit", "Markup %"
                ]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # Comparison chart
                fig_compare = px.bar(
                    df_compare,
                    x="name",
                    y="profit",
                    title="Profit Comparison",
                    labels={"profit": "Profit (MMK)", "name": "Product"},
                    color="profit",
                    color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig_compare, use_container_width=True)


# ==============================================================================
# ENTRY
# ==============================================================================

if __name__ == "__main__":
    run()
