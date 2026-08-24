# ==============================================================================
# erp_pages/Branch_Profit.py
# ERP ENTERPRISE BRANCH PROFIT DASHBOARD
# NICE GUI VERSION
# ==============================================================================

from typing import Dict, Any, Optional, List
import pandas as pd
import plotly.express as px
from nicegui import ui

from database import get_supabase


# ==============================================================================
# DATABASE
# ==============================================================================

supabase = get_supabase()


# ==============================================================================
# HELPERS
# ==============================================================================

def safe_float(value: Any) -> float:
    """Safely convert value to float."""
    try:
        return float(value or 0)
    except:
        return 0.0


def load_branch_profit_data() -> pd.DataFrame:
    """Load branch profit data from database."""
    try:
        res = supabase.table('branch_profit_report').select('*').execute()
        
        if res.data:
            return pd.DataFrame(res.data)
        else:
            return pd.DataFrame()
    
    except Exception as e:
        ui.notify(f"Failed to load branch profit data: {e}", type='error', position='top')
        return pd.DataFrame()


# ==============================================================================
# KPI CARDS
# ==============================================================================

def build_kpi_cards(container: Any, revenue: float, cogs: float, profit: float):
    """Build KPI metric cards."""
    container.clear()
    
    with container:
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # Revenue
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-blue-50'):
                ui.label('Revenue').classes('text-sm text-gray-600')
                ui.label(f'{revenue:,.2f}').classes('text-2xl font-bold text-blue-700')
            
            # COGS
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-orange-50'):
                ui.label('COGS').classes('text-sm text-gray-600')
                ui.label(f'{cogs:,.2f}').classes('text-2xl font-bold text-orange-700')
            
            # Gross Profit
            with ui.card().classes('p-4 flex-1 min-w-[200px] bg-green-50'):
                ui.label('Gross Profit').classes('text-sm text-gray-600')
                ui.label(f'{profit:,.2f}').classes('text-2xl font-bold text-green-700')


# ==============================================================================
# TABLE
# ==============================================================================

def build_table(container: Any, df: pd.DataFrame):
    """Build product profit table."""
    container.clear()
    
    if df.empty:
        with container:
            with ui.card().classes('w-full p-4 bg-gray-50'):
                ui.label('No data to display').classes('text-gray-500 text-center')
        return
    
    with container:
        # Select columns for display
        display_df = df[
            [
                'branch_name',
                'product_name',
                'sold_qty',
                'revenue',
                'cogs',
                'gross_profit',
                'profit_margin_percent'
            ]
        ].copy()
        
        # Format numeric columns
        for col in ['sold_qty']:
            if col in display_df.columns:
                display_df[col] = display_df[col].map(
                    lambda x: f"{int(x):,}" if pd.notna(x) else ""
                )
        
        for col in ['revenue', 'cogs', 'gross_profit']:
            if col in display_df.columns:
                display_df[col] = display_df[col].map(
                    lambda x: f"{safe_float(x):,.2f}" if pd.notna(x) else ""
                )
        
        if 'profit_margin_percent' in display_df.columns:
            display_df['profit_margin_percent'] = display_df['profit_margin_percent'].map(
                lambda x: f"{safe_float(x):.2f}%" if pd.notna(x) else ""
            )
        
        # Convert to table format
        columns = [
            {'name': col, 'label': col, 'field': col, 'sortable': True}
            for col in display_df.columns
        ]
        
        rows = display_df.to_dict('records')
        
        ui.table(
            columns=columns,
            rows=rows,
            row_key='product_name',
            pagination=20,
            title='Product Profit',
        ).classes('w-full')


# ==============================================================================
# CHART
# ==============================================================================

def build_chart(container: Any, df: pd.DataFrame):
    """Build gross profit by product chart."""
    container.clear()
    
    if df.empty:
        with container:
            with ui.card().classes('w-full p-4 bg-gray-50'):
                ui.label('No data to display').classes('text-gray-500 text-center')
        return
    
    with container:
        # Group by product
        chart_df = (
            df.groupby('product_name', as_index=False)['gross_profit']
            .sum()
            .sort_values('gross_profit', ascending=False)
        )
        
        # Limit to top 20 products for better visualization
        top_chart_df = chart_df.head(20)
        
        # Create bar chart using Plotly
        fig = px.bar(
            top_chart_df,
            x='product_name',
            y='gross_profit',
            title='Gross Profit by Product (Top 20)',
            labels={
                'product_name': 'Product',
                'gross_profit': 'Gross Profit'
            },
            color='gross_profit',
            color_continuous_scale='Viridis',
        )
        
        fig.update_layout(
            height=400,
            xaxis_tickangle=-45,
            showlegend=False,
            margin=dict(t=50, b=100),
        )
        
        ui.plotly(fig).classes('w-full')


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main page entry point."""
    target = container or ui.column()
    
    with target:
        # Header
        ui.label('🏢 Branch Profit Dashboard').classes('text-3xl font-bold mb-4')
        
        # Load data
        df = load_branch_profit_data()
        
        if df.empty:
            with ui.card().classes('w-full p-4 bg-orange-50'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('warning').classes('text-orange-500')
                    ui.label('No branch profit data found.').classes('text-orange-700')
            return
        
        # Branch filter
        branches = ['All'] + sorted(df['branch_name'].dropna().unique().tolist())
        
        with ui.row().classes('w-full gap-4 items-end mb-4'):
            branch_select = ui.select(
                branches,
                label='Select Branch',
                value='All',
            ).classes('min-w-[250px]')
        
        # Dynamic containers
        kpi_container = ui.column().classes('w-full mb-4')
        table_container = ui.column().classes('w-full mb-4')
        chart_container = ui.column().classes('w-full')
        
        # Function to update all sections
        def update_dashboard():
            filtered_df = df.copy()
            
            # Apply branch filter
            branch = branch_select.value
            if branch != 'All':
                filtered_df = filtered_df[filtered_df['branch_name'] == branch]
            
            # Calculate KPIs
            revenue = safe_float(filtered_df['revenue'].sum())
            cogs = safe_float(filtered_df['cogs'].sum())
            profit = safe_float(filtered_df['gross_profit'].sum())
            
            # Update sections
            build_kpi_cards(kpi_container, revenue, cogs, profit)
            build_table(table_container, filtered_df)
            build_chart(chart_container, filtered_df)
        
        # Wire up filter event
        branch_select.on_value_change(lambda e: update_dashboard())
        
        # Initial render
        update_dashboard()


# ==============================================================================
# ADVANCED DASHBOARD WITH ADDITIONAL FEATURES
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced dashboard with additional features."""
    target = container or ui.column()
    
    with target:
        ui.label('🏢 Branch Profit Dashboard').classes('text-3xl font-bold mb-4')
        
        # Load data
        df = load_branch_profit_data()
        
        if df.empty:
            with ui.card().classes('w-full p-4 bg-orange-50'):
                ui.label('No branch profit data found.').classes('text-orange-700')
            return
        
        # Filters row
        with ui.row().classes('w-full gap-4 flex-wrap items-end mb-4'):
            # Branch filter
            branches = ['All'] + sorted(df['branch_name'].dropna().unique().tolist())
            branch_select = ui.select(
                branches,
                label='Branch',
                value='All',
            ).classes('min-w-[200px]')
            
            # Sort options
            sort_options = ['Gross Profit (High to Low)', 'Gross Profit (Low to High)', 
                           'Revenue (High to Low)', 'Revenue (Low to High)']
            sort_select = ui.select(
                sort_options,
                label='Sort By',
                value='Gross Profit (High to Low)',
            ).classes('min-w-[250px]')
            
            # Show top N
            top_n = ui.number(
                'Top N Products',
                min=5,
                max=100,
                value=20,
                step=5,
            ).classes('w-40')
        
        # Containers
        kpi_container = ui.column().classes('w-full mb-4')
        chart_container = ui.column().classes('w-full mb-4')
        table_container = ui.column().classes('w-full')
        
        # Function to update dashboard
        def update_dashboard():
            filtered_df = df.copy()
            
            # Apply filters
            branch = branch_select.value
            if branch != 'All':
                filtered_df = filtered_df[filtered_df['branch_name'] == branch]
            
            # Calculate KPIs
            revenue = safe_float(filtered_df['revenue'].sum())
            cogs = safe_float(filtered_df['cogs'].sum())
            profit = safe_float(filtered_df['gross_profit'].sum())
            
            # Update KPI cards
            build_kpi_cards(kpi_container, revenue, cogs, profit)
            
            # Update chart with sorting
            chart_container.clear()
            with chart_container:
                chart_df = (
                    filtered_df.groupby('product_name', as_index=False)['gross_profit']
                    .sum()
                )
                
                # Apply sorting
                sort_option = sort_select.value
                if 'Low to High' in sort_option:
                    chart_df = chart_df.sort_values('gross_profit', ascending=True)
                else:
                    chart_df = chart_df.sort_values('gross_profit', ascending=False)
                
                # Apply top N
                n = int(top_n.value)
                chart_df = chart_df.head(n)
                
                # Create chart
                fig = px.bar(
                    chart_df,
                    x='product_name',
                    y='gross_profit',
                    title=f'Gross Profit by Product (Top {n})',
                    labels={'product_name': 'Product', 'gross_profit': 'Gross Profit'},
                    color='gross_profit',
                    color_continuous_scale='Viridis',
                )
                
                fig.update_layout(
                    height=400,
                    xaxis_tickangle=-45,
                    showlegend=False,
                )
                
                ui.plotly(fig).classes('w-full')
            
            # Update table
            build_table(table_container, filtered_df)
        
        # Wire up events
        branch_select.on_value_change(lambda e: update_dashboard())
        sort_select.on_value_change(lambda e: update_dashboard())
        top_n.on_value_change(lambda e: update_dashboard())
        
        # Initial render
        update_dashboard()


# ==============================================================================
# COMPACT DASHBOARD
# ==============================================================================

def run_compact(container: Optional[Any] = None):
    """Compact dashboard for smaller screens."""
    target = container or ui.column()
    
    with target:
        ui.label('🏢 Branch Profit').classes('text-2xl font-bold mb-2')
        
        # Load data
        df = load_branch_profit_data()
        
        if df.empty:
            ui.label('No data found').classes('text-gray-500')
            return
        
        # Branch filter
        branches = ['All'] + sorted(df['branch_name'].dropna().unique().tolist())
        branch_select = ui.select(branches, label='Branch', value='All').classes('w-full mb-2')
        
        # Content container
        content = ui.column().classes('w-full')
        
        def update():
            content.clear()
            filtered_df = df.copy()
            
            if branch_select.value != 'All':
                filtered_df = filtered_df[filtered_df['branch_name'] == branch_select.value]
            
            revenue = safe_float(filtered_df['revenue'].sum())
            cogs = safe_float(filtered_df['cogs'].sum())
            profit = safe_float(filtered_df['gross_profit'].sum())
            
            with content:
                # Compact KPI row
                with ui.row().classes('w-full gap-2 flex-wrap'):
                    with ui.card().classes('p-2 flex-1 min-w-[120px]'):
                        ui.label('Revenue').classes('text-xs text-gray-500')
                        ui.label(f'{revenue:,.0f}').classes('text-lg font-bold')
                    
                    with ui.card().classes('p-2 flex-1 min-w-[120px]'):
                        ui.label('COGS').classes('text-xs text-gray-500')
                        ui.label(f'{cogs:,.0f}').classes('text-lg font-bold')
                    
                    with ui.card().classes('p-2 flex-1 min-w-[120px]'):
                        ui.label('Profit').classes('text-xs text-gray-500')
                        ui.label(f'{profit:,.0f}').classes('text-lg font-bold')
                
                # Simple table
                display_df = filtered_df[['product_name', 'sold_qty', 'gross_profit']].copy()
                
                columns = [
                    {'name': col, 'label': col, 'field': col, 'sortable': True}
                    for col in display_df.columns
                ]
                
                rows = display_df.to_dict('records')
                
                ui.table(
                    columns=columns,
                    rows=rows,
                    row_key='product_name',
                    pagination=10,
                ).classes('w-full')
        
        branch_select.on_value_change(lambda e: update())
        update()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
