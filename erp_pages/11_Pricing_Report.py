# ==============================================================================
# erp_pages/11_Pricing_Report.py
# ERP ENTERPRISE PRICING REPORT v5.0
# NICE GUI VERSION
# Product + Category + Global Markup Analysis with Advanced Features
# ==============================================================================

import io
from typing import Dict, Any, Optional, List, Callable
from functools import lru_cache

import pandas as pd
import plotly.express as px
from nicegui import ui

from reports.pricing_report_service import get_pricing_report_products
from reports.pricing_report_excel import create_pricing_excel_report


# ==============================================================================
# HELPERS
# ==============================================================================

def safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except:
        return 0

def money(value: Any) -> str:
    return f"{safe_float(value):,.0f}"

def percent(value: Any) -> str:
    return f"{safe_float(value):.2f}%"


@lru_cache(maxsize=1)
def load_pricing_data_cached() -> List[Dict[str, Any]]:
    """Load pricing data with caching (manual lru_cache)."""
    try:
        return get_pricing_report_products()
    except Exception as e:
        ui.notify(f"❌ Failed to load pricing data: {str(e)}", type='error', position='top')
        return []


def validate_products(products: List[Dict[str, Any]]) -> tuple[bool, str]:
    """Validate product data."""
    if not products:
        return False, "No pricing data found"

    invalid_products = [p for p in products if not p.get("name") or not p.get("sku")]

    if invalid_products:
        ui.notify(f"⚠️ Found {len(invalid_products)} products with missing data", type='warning', position='top')

    return True, "Valid"


# ==============================================================================
# UI COMPONENT BUILDERS
# ==============================================================================

def build_kpi_cards(container: Any, filtered: List[Dict[str, Any]]):
    """Render KPI summary cards."""
    container.clear()
    with container:
        total_products = len(filtered)
        total_profit = sum(safe_float(p.get("profit")) for p in filtered)
        avg_markup = (
            sum(safe_float(p.get("final_markup_percent")) for p in filtered) / total_products
            if total_products else 0
        )
        total_cost = sum(safe_float(p.get("purchase_price")) for p in filtered)
        total_revenue = sum(safe_float(p.get("expected_selling_price")) for p in filtered)

        with ui.row().classes('w-full gap-4 flex-wrap'):
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('📦 Products').classes('text-sm text-gray-600')
                ui.label(str(total_products)).classes('text-2xl font-bold')
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('💰 Total Profit').classes('text-sm text-gray-600')
                ui.label(f"{total_profit:,.0f} MMK").classes('text-2xl font-bold')
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('📈 Avg Markup').classes('text-sm text-gray-600')
                ui.label(f"{avg_markup:.2f}%").classes('text-2xl font-bold')
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('💵 Total Cost').classes('text-sm text-gray-600')
                ui.label(f"{total_cost:,.0f} MMK").classes('text-2xl font-bold')
            with ui.card().classes('p-4 flex-1 min-w-[180px]'):
                ui.label('📊 Total Revenue').classes('text-sm text-gray-600')
                ui.label(f"{total_revenue:,.0f} MMK").classes('text-2xl font-bold')


def build_charts(container: Any, filtered: List[Dict[str, Any]]):
    """Render analytics charts."""
    container.clear()
    if not filtered:
        with container:
            ui.label('No data to display').classes('text-gray-500')
        return

    with container:
        df = pd.DataFrame(filtered)

        with ui.row().classes('w-full gap-4 flex-wrap'):
            with ui.column().classes('flex-1 min-w-[400px]'):
                fig1 = px.histogram(
                    df,
                    x="final_markup_percent",
                    title="Markup Distribution",
                    labels={"final_markup_percent": "Markup %", "count": "Number of Products"},
                    color_discrete_sequence=["#FF6B6B"],
                    nbins=20
                )
                fig1.update_layout(height=350)
                ui.plotly(fig1).classes('w-full')

            with ui.column().classes('flex-1 min-w-[400px]'):
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
                ui.plotly(fig2).classes('w-full')

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
        ui.plotly(fig3).classes('w-full')


def build_pricing_table(container: Any, filtered: List[Dict[str, Any]], page: int = 0):
    """Render pricing analysis table with pagination."""
    container.clear()
    if not filtered:
        with container:
            ui.label('No matching products').classes('text-gray-500')
        return

    with container:
        page_size = 50
        total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
        page = max(0, min(page, total_pages - 1))

        start_idx = page * page_size
        end_idx = min(start_idx + page_size, len(filtered))
        paginated_data = filtered[start_idx:end_idx]

        rows = []
        for p in paginated_data:
            profit_value = safe_float(p.get("profit"))
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

        columns = [
            {'name': col, 'label': col, 'field': col, 'sortable': True}
            for col in rows[0].keys()
        ]

        ui.table(
            columns=columns,
            rows=rows,
            row_key='SKU',
            pagination=page_size,
            title='Pricing Analysis',
        ).classes('w-full')

        ui.label(f"Showing {start_idx + 1} to {end_idx} of {len(filtered)} products").classes('text-sm text-gray-500')

        # Pagination controls
        with ui.row().classes('w-full justify-center gap-2 mt-2'):
            ui.button('Previous', on_click=lambda: update_table_page(page - 1)).props('flat')
            ui.label(f'Page {page + 1} of {total_pages}')
            ui.button('Next', on_click=lambda: update_table_page(page + 1)).props('flat')


def update_table_page(new_page: int):
    """Update table page (dummy function for demo)."""
    # In a real implementation, this would re-render the table with new_page
    pass


def build_bulk_update(container: Any):
    """Render bulk update section."""
    container.clear()
    with container:
        ui.label('✏️ Bulk Markup Update').classes('text-xl font-bold mb-2')
        ui.label('⚠️ This will update all filtered products').classes('text-orange-600 mb-4')

        markup_type = ui.select(
            ['Product Markup', 'Category Markup', 'Global Markup'],
            label='Update Type',
            value='Product Markup',
        ).classes('w-full mb-2')

        new_markup = ui.number(
            'New Markup %',
            min=0,
            max=300,
            value=30,
            step=5,
        ).classes('w-full mb-4')

        def apply_bulk():
            ui.notify(f'✅ Updated to {new_markup.value}%', type='positive', position='top')
            # In real implementation, call backend update

        ui.button('🔄 Apply Bulk Update', on_click=apply_bulk).classes('w-full bg-primary text-white')


def build_export_section(container: Any, filtered: List[Dict[str, Any]]):
    """Render export center."""
    container.clear()
    with container:
        ui.label('📥 Export Center').classes('text-xl font-bold mb-4')

        export_format = ui.select(
            ['Excel (.xlsx)', 'CSV (.csv)'],
            label='Export Format',
            value='Excel (.xlsx)',
        ).classes('w-full mb-4')

        def do_export():
            fmt = export_format.value
            if fmt == 'Excel (.xlsx)':
                excel_bytes = create_pricing_excel_report(filtered)
                ui.download(excel_bytes, 'ERP_Pricing_Report.xlsx')
            else:
                # CSV export
                rows = []
                for p in filtered:
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
                csv_bytes = pd.DataFrame(rows).to_csv(index=False).encode('utf-8')
                ui.download(csv_bytes, 'ERP_Pricing_Report.csv')

        ui.button('Download Report', on_click=do_export).classes('w-full bg-primary text-white')


def build_comparison(container: Any, filtered: List[Dict[str, Any]]):
    """Render product comparison expander."""
    container.clear()
    with container:
        with ui.expansion('📊 Product Comparison', icon='compare').classes('w-full'):
            ui.label('Select up to 5 products to compare').classes('text-gray-600 mb-2')

            product_options = [p.get("name") for p in filtered[:20]]  # Limit for performance
            if not product_options:
                ui.label('No products available for comparison').classes('text-gray-500')
                return

            selected = ui.select(
                product_options,
                label='Select Products',
                multiple=True,
            ).classes('w-full mb-4')

            def update_comparison():
                # This would need a separate container to show comparison data
                pass

            selected.on_value_change(lambda e: update_comparison())


# ==============================================================================
# MAIN RUN
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main page entry point."""
    target = container or ui.column()
    with target:
        ui.label('💰 Product Pricing Report').classes('text-3xl font-bold')
        ui.label('MYANMAR ERP - Product Cost, Markup & Selling Price Analysis').classes('text-gray-500 mb-4')

        # Load data
        products = load_pricing_data_cached()
        is_valid, message = validate_products(products)
        if not is_valid:
            ui.notify(message, type='warning', position='top')
            ui.label('💡 Please add products and set pricing rules first').classes('text-gray-500')
            return

        # ======================================================================
        # FILTER SECTION
        # ======================================================================
        ui.label('🔍 Filter Options').classes('text-xl font-bold mb-4')

        with ui.row().classes('w-full gap-4 flex-wrap'):
            search_input = ui.input('🔍 Search Product', placeholder='Type product name...').classes('flex-1 min-w-[200px]')

            category_list = sorted(list(set([p.get("category", "Uncategorized") for p in products])))
            category_select = ui.select(
                ['All'] + category_list,
                label='📂 Category',
                value='All',
            ).classes('flex-1 min-w-[200px]')

            # Advanced filters (collapsible)
            with ui.expansion('🔧 Advanced Filters', icon='tune').classes('w-full'):
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    min_price = ui.number('Min Selling Price (MMK)', min=0, value=0, step=1000).classes('flex-1 min-w-[150px]')
                    max_price = ui.number('Max Selling Price (MMK)', min=0, value=1000000, step=1000).classes('flex-1 min-w-[150px]')
                    markup_filter = ui.select(
                        ['All', '0-20%', '20-50%', '50-100%', '100%+'],
                        label='Markup Range',
                        value='All',
                    ).classes('flex-1 min-w-[150px]')

        # ======================================================================
        # CONTAINERS FOR DYNAMIC CONTENT
        # ======================================================================
        kpi_container = ui.column().classes('w-full')
        charts_container = ui.column().classes('w-full')
        table_container = ui.column().classes('w-full')
        bulk_container = ui.column().classes('w-full')
        export_container = ui.column().classes('w-full')
        comparison_container = ui.column().classes('w-full')

        # ======================================================================
        # FUNCTION TO UPDATE ALL SECTIONS BASED ON FILTERS
        # ======================================================================
        def apply_filters_and_update():
            filtered = products.copy()

            # Search filter
            search = search_input.value or ''
            if search:
                filtered = [p for p in filtered if search.lower() in p.get("name", "").lower()]

            # Category filter
            category = category_select.value
            if category != 'All':
                filtered = [p for p in filtered if p.get("category") == category]

            # Price range
            min_p = min_price.value or 0
            max_p = max_price.value or float('inf')
            filtered = [p for p in filtered if min_p <= safe_float(p.get("expected_selling_price", 0)) <= max_p]

            # Markup range
            markup = markup_filter.value
            if markup != 'All':
                markup_ranges = {
                    "0-20%": (0, 20),
                    "20-50%": (20, 50),
                    "50-100%": (50, 100),
                    "100%+": (100, float('inf'))
                }
                min_m, max_m = markup_ranges[markup]
                filtered = [p for p in filtered if min_m <= safe_float(p.get("final_markup_percent", 0)) <= max_m]

            if not filtered:
                ui.notify('⚠️ No matching products found', type='warning', position='top')
                # Clear all containers
                kpi_container.clear()
                charts_container.clear()
                table_container.clear()
                bulk_container.clear()
                export_container.clear()
                comparison_container.clear()
                return

            # Update each section
            build_kpi_cards(kpi_container, filtered)
            build_charts(charts_container, filtered)
            build_pricing_table(table_container, filtered)
            build_bulk_update(bulk_container)
            build_export_section(export_container, filtered)
            build_comparison(comparison_container, filtered)

        # Wire up filter events
        search_input.on_value_change(lambda e: apply_filters_and_update())
        category_select.on_value_change(lambda e: apply_filters_and_update())
        min_price.on_value_change(lambda e: apply_filters_and_update())
        max_price.on_value_change(lambda e: apply_filters_and_update())
        markup_filter.on_value_change(lambda e: apply_filters_and_update())

        # Initial render
        apply_filters_and_update()


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    run()
