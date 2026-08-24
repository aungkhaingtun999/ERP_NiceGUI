# ==============================================================================
# utils/ui.py
# ERP ENTERPRISE UI LIBRARY v2.1.5
# CORE UI FRAMEWORK
# NICE GUI VERSION
# ==============================================================================

from datetime import date, datetime
import io
import math
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import pandas as pd
from nicegui import ui, events

UI_VERSION = "2.1.5 Enterprise ERP (NiceGUI)"


# ==============================================================================
# GLOBAL FORMAT UTILS
# ==============================================================================

def format_number(value: Any, decimals: int = 0) -> str:
    """Formats numeric values with thousand separators (e.g., 1,500,000)
    
    Supports optional decimals for exchange rates, taxes, and unit prices.
    Safe for KPIs, Receipts, and UI Displays.
    """
    if pd.isna(value):
        return ""
    try:
        val = float(value)
        format_str = f"{{:,.{decimals}f}}"
        return format_str.format(val)
    except (ValueError, TypeError):
        return str(value)


# ==============================================================================
# PAGE COMPONENTS
# ==============================================================================

def page_title(title: str, icon: str = "📦"):
    """Render page title"""
    ui.label(f"{icon} {title}").classes('text-3xl font-bold mb-4')


def page_header(title: str, subtitle: str = ""):
    """Render page header with subtitle"""
    ui.label(title).classes('text-2xl font-semibold mb-2')
    if subtitle:
        ui.label(subtitle).classes('text-sm text-gray-500 mb-2')
    ui.separator().classes('my-4')


def section(title: str):
    """Render section heading"""
    ui.markdown(f"### {title}").classes('mb-2')


def divider():
    """Render divider"""
    ui.separator().classes('my-4')


# ==============================================================================
# MESSAGE COMPONENTS
# ==============================================================================

def success(message: str, position: str = 'top'):
    """Show success message"""
    ui.notify(message, type='positive', position=position)


def error(message: str, position: str = 'top'):
    """Show error message"""
    ui.notify(message, type='error', position=position, timeout=5000)


def warning(message: str, position: str = 'top'):
    """Show warning message"""
    ui.notify(message, type='warning', position=position)


def info(message: str, position: str = 'top'):
    """Show info message"""
    ui.notify(message, type='info', position=position)


def empty_data(message: str = "No data available"):
    """Show empty data message"""
    with ui.card().classes('w-full p-4 bg-gray-50'):
        ui.label(message).classes('text-gray-500 text-center')


# ==============================================================================
# TABLE ENGINE
# ==============================================================================

def add_serial(df: pd.DataFrame) -> pd.DataFrame:
    """Add serial number column"""
    if df is None:
        return df
    
    df = df.copy()
    
    if "No." not in df.columns:
        df.insert(0, "No.", range(1, len(df) + 1))
    
    return df


def show_table(
    df: Union[pd.DataFrame, List[Dict], str, None],
    serial: bool = True,
    pagination: int = 20,
    title: Optional[str] = None
):
    """Enterprise Safe Table Engine with Display-Only Number Formatting
    
    Supports:
        - pandas.DataFrame
        - list[dict]
        - empty dataframe
        - None
        - string message
    """
    
    if df is None:
        empty_data()
        return
    
    # Allow passing message string
    if isinstance(df, str):
        info(df)
        return
    
    # Convert list -> DataFrame
    if isinstance(df, list):
        df = pd.DataFrame(df)
    
    # Invalid object
    if not isinstance(df, pd.DataFrame):
        error(f"show_table() expects DataFrame, got {type(df).__name__}")
        return
    
    # Empty dataframe
    if df.empty:
        empty_data()
        return
    
    # Add serial column
    if serial:
        df = add_serial(df)
    
    # Display-only number formatting (safe copy)
    display_df = df.copy()
    
    numeric_cols = display_df.select_dtypes(include=["number"]).columns
    
    for col in numeric_cols:
        col_lower = col.lower()
        
        # Keep ID columns as-is
        if col_lower == "id":
            continue
        # Keep serial numbers as integers
        elif col_lower == "no.":
            display_df[col] = display_df[col].map(
                lambda x: f"{int(x)}" if pd.notna(x) else ""
            )
        else:
            display_df[col] = display_df[col].map(
                lambda x: f"{x:,.0f}" if pd.notna(x) else ""
            )
    
    # Convert to NiceGUI table format
    columns = [
        {
            'name': col,
            'label': col,
            'field': col,
            'align': 'left',
            'sortable': True,
        }
        for col in display_df.columns
    ]
    
    rows = display_df.to_dict('records')
    
    # Create table with pagination
    ui.table(
        columns=columns,
        rows=rows,
        row_key='No.' if serial and 'No.' in display_df.columns else display_df.columns[0],
        pagination=pagination,
        title=title,
    ).classes('w-full')


def table_panel(
    df: Union[pd.DataFrame, List[Dict], None],
    title: str = "Records"
):
    """Render table with panel"""
    section(title)
    show_table(df)
    
    if df is None:
        count = 0
    elif isinstance(df, pd.DataFrame):
        count = len(df)
    elif isinstance(df, list):
        count = len(df)
    else:
        count = 0
    
    ui.label(f"Total Records : {count}").classes('text-sm text-gray-500 mt-2')


# ==============================================================================
# KPI / METRIC
# ==============================================================================

def metric_card(
    label: str,
    value: Any,
    delta: Optional[str] = None,
    icon: Optional[str] = None
):
    """Render metric card"""
    with ui.card().classes('p-4 min-w-[200px]'):
        with ui.row().classes('items-center gap-2'):
            if icon:
                ui.icon(icon).classes('text-3xl text-primary')
            ui.label(label).classes('text-sm text-gray-600')
        
        ui.label(str(value)).classes('text-2xl font-bold')
        
        if delta:
            color = 'text-green-600' if not delta.startswith('-') else 'text-red-600'
            ui.label(delta).classes(f'text-sm {color}')


def metric_row(items: List[Tuple]):
    """Render metric cards in a row"""
    with ui.row().classes('w-full gap-4 flex-wrap'):
        for item in items:
            if len(item) == 2:
                label, value = item
                delta = None
                icon = None
            elif len(item) == 3:
                label, value, delta = item
                icon = None
            else:
                label, value, delta, icon = item
            
            metric_card(label, value, delta, icon)


# ==============================================================================
# SEARCH
# ==============================================================================

def search_box(
    label: str = "🔍 Search",
    placeholder: str = "Search...",
    on_change: Optional[Callable] = None
) -> ui.input:
    """Create search input"""
    search_input = ui.input(
        label=label,
        placeholder=placeholder,
        on_change=on_change
    ).classes('w-full')
    
    return search_input


def search_filter(
    search_label: str = "🔍 Search",
    categories: Optional[List[str]] = None,
    search_value: str = ""
) -> Tuple[ui.input, Optional[ui.select]]:
    """Create search with filter"""
    with ui.row().classes('w-full gap-4'):
        search = search_box(search_label)
        search.value = search_value
        
        selected = None
        if categories:
            selected = ui.select(
                categories,
                label='Category',
                value=categories[0] if categories else None
            ).classes('min-w-[200px]')
    
    return search, selected


# ==============================================================================
# TOOLBAR / FILTER / ACTION COMPONENTS
# ==============================================================================

def toolbar(columns: int = 4):
    """Create toolbar with columns"""
    return ui.row().classes('w-full gap-4')


def date_filter(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Tuple[ui.input, ui.input]:
    """Create date range filter"""
    start_date = start_date or date.today()
    end_date = end_date or date.today()
    
    with ui.row().classes('w-full gap-4'):
        start = ui.input(
            'From',
            value=start_date.strftime('%Y-%m-%d')
        ).props('type=date').classes('min-w-[200px]')
        
        end = ui.input(
            'To',
            value=end_date.strftime('%Y-%m-%d')
        ).props('type=date').classes('min-w-[200px]')
    
    return start, end


def status_filter(
    statuses: List[str],
    label: str = "Status",
    value: Optional[str] = None
) -> ui.select:
    """Create status filter dropdown"""
    return ui.select(
        statuses,
        label=label,
        value=value or statuses[0] if statuses else None
    ).classes('min-w-[200px]')


def refresh_button(on_click: Optional[Callable] = None):
    """Create refresh button"""
    return ui.button(
        '🔄 Refresh',
        on_click=on_click
    ).props('flat').classes('bg-blue-50 hover:bg-blue-100')


def action_buttons(
    add: bool = True,
    edit: bool = True,
    delete: bool = False,
    export: bool = False,
    on_add: Optional[Callable] = None,
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_export: Optional[Callable] = None
) -> Dict[str, ui.button]:
    """Create action buttons"""
    result = {}
    
    with ui.row().classes('gap-2'):
        if add:
            result["add"] = ui.button(
                '➕ Add',
                on_click=on_add
            ).classes('bg-green-500 text-white')
        
        if edit:
            result["edit"] = ui.button(
                '✏️ Edit',
                on_click=on_edit
            ).classes('bg-blue-500 text-white')
        
        if delete:
            result["delete"] = ui.button(
                '🗑 Delete',
                on_click=on_delete
            ).classes('bg-red-500 text-white')
        
        if export:
            result["export"] = ui.button(
                '📄 Export',
                on_click=on_export
            ).classes('bg-gray-500 text-white')
    
    return result


def primary_button(
    text: str,
    on_click: Optional[Callable] = None,
    icon: Optional[str] = None
) -> ui.button:
    """Create primary button"""
    if icon:
        text = f"{icon} {text}"
    
    return ui.button(
        text,
        on_click=on_click
    ).classes('w-full bg-primary text-white')


# ==============================================================================
# STATUS BADGE & COLOR UTILS
# ==============================================================================

def status_badge(status: str):
    """Render status badge"""
    status = str(status).lower()
    
    if status in ["active", "completed", "success", "paid"]:
        ui.badge(status.title()).classes('bg-green-100 text-green-700')
    elif status in ["pending", "waiting"]:
        ui.badge(status.title()).classes('bg-orange-100 text-orange-700')
    elif status in ["cancelled", "inactive", "failed"]:
        ui.badge(status.title()).classes('bg-red-100 text-red-700')
    else:
        ui.badge(status.title()).classes('bg-blue-100 text-blue-700')


def status_color(status: str) -> str:
    """Get status color"""
    status = str(status).lower()
    
    if status in ["active", "completed", "success", "paid"]:
        return "green"
    
    if status in ["pending", "waiting"]:
        return "orange"
    
    if status in ["cancelled", "inactive", "failed"]:
        return "red"
    
    return "blue"


def status_chip(status: str):
    """Render status as chip"""
    color = status_color(status)
    ui.chip(
        status.title(),
        color=color,
        text_color='white'
    )


# ==============================================================================
# PAGINATION
# ==============================================================================

def paginate(
    data: Union[pd.DataFrame, List],
    page: int = 1,
    page_size: int = 20
) -> Union[pd.DataFrame, List]:
    """Paginate data"""
    if data is None:
        return []
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return (
        data.iloc[start:end]
        if isinstance(data, pd.DataFrame)
        else data[start:end]
    )


def page_selector(
    total_rows: int,
    page_size: int = 20,
    value: int = 1,
    on_change: Optional[Callable] = None
) -> ui.number:
    """Create page selector"""
    pages = max(1, math.ceil(total_rows / page_size))
    
    return ui.number(
        'Page',
        min=1,
        max=pages,
        value=value,
        step=1,
        on_change=on_change
    ).classes('w-24')


# ==============================================================================
# EXPORT ENGINE
# ==============================================================================

def download_csv(
    df: Union[pd.DataFrame, List[Dict]],
    filename: str = "report.csv"
):
    """Create CSV download button"""
    if df is None:
        return
    
    if isinstance(df, list):
        df = pd.DataFrame(df)
    
    csv_data = df.to_csv(index=False)
    
    ui.button(
        '⬇️ Download CSV',
        on_click=lambda: ui.download(
            csv_data.encode('utf-8'),
            filename
        )
    ).props('flat')


def download_excel(
    df: Union[pd.DataFrame, List[Dict]],
    filename: str = "report.xlsx"
):
    """Create Excel download button"""
    if df is None:
        return
    
    if isinstance(df, list):
        df = pd.DataFrame(df)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    
    ui.button(
        '⬇️ Download Excel',
        on_click=lambda: ui.download(
            output.getvalue(),
            filename
        )
    ).props('flat')


def export_bar(
    df: Union[pd.DataFrame, List[Dict]],
    filename: str = "report"
):
    """Create export buttons bar"""
    with ui.row().classes('gap-2'):
        download_csv(df, filename + ".csv")
        download_excel(df, filename + ".xlsx")


# ==============================================================================
# ADVANCED ERP COMPONENTS
# ==============================================================================

def loading(
    text: str = "Loading...",
    container: Optional[Any] = None
):
    """Show loading spinner"""
    target = container or ui.column()
    
    with target:
        with ui.row().classes('items-center gap-2'):
            ui.spinner()
            ui.label(text)


def panel(
    title: str,
    expanded: bool = True,
    icon: Optional[str] = None
):
    """Create expandable panel"""
    return ui.expansion(
        title,
        icon=icon or 'expand_more',
        value=expanded
    ).classes('w-full')


def quick_stats(items: List[Tuple]):
    """Render quick stats cards
    
    Example:
        quick_stats([
            ("Products", 100),
            ("Stock", 500),
            ("Sales", "2M")
        ])
    """
    with ui.row().classes('w-full gap-4 flex-wrap'):
        for item in items:
            metric_card(item[0], item[1])


def low_stock(
    df: Union[pd.DataFrame, List[Dict]],
    qty_column: str = "qty",
    minimum_column: str = "minimum_stock"
) -> pd.DataFrame:
    """Filter low stock items"""
    if df is None:
        return pd.DataFrame()
    
    if isinstance(df, list):
        df = pd.DataFrame(df)
    
    if qty_column not in df.columns:
        return df
    
    if minimum_column not in df.columns:
        return df
    
    return df[df[qty_column] <= df[minimum_column]]


def table_summary(df: Union[pd.DataFrame, List[Dict]]):
    """Show table summary"""
    if df is None:
        return
    
    count = len(df)
    ui.label(f"Total Records : {count}").classes('text-sm text-gray-500')


def info_card(title: str, value: Any):
    """Render info card"""
    with ui.card().classes('p-4'):
        ui.label(title).classes('text-sm text-gray-600')
        ui.label(str(value)).classes('text-xl font-bold')


def form_columns(number: int = 2):
    """Create form columns"""
    return ui.row().classes(f'w-full gap-4 grid grid-cols-{number}')


def confirm_box(message: str):
    """Show confirmation box"""
    with ui.card().classes('p-4 bg-orange-50 border border-orange-200'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('warning').classes('text-orange-500')
            ui.label(message).classes('text-orange-700')


def box(title: str):
    """Create box container"""
    container = ui.card().classes('w-full p-4')
    
    with container:
        ui.markdown(f"### {title}")
        ui.separator().classes('my-2')
        
        inner_container = ui.column()
    
    return inner_container


def footer():
    """Render footer"""
    ui.separator().classes('my-4')
    ui.label(
        f"ERP Enterprise UI Library {UI_VERSION}"
    ).classes('text-sm text-gray-500 text-center')


# ==============================================================================
# DIALOG COMPONENTS
# ==============================================================================

def confirm_dialog(
    message: str,
    on_confirm: Callable,
    on_cancel: Optional[Callable] = None,
    title: str = "Confirm",
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel"
):
    """Show confirmation dialog"""
    with ui.dialog() as dialog, ui.card().classes('p-4'):
        ui.label(title).classes('text-xl font-bold mb-2')
        ui.label(message).classes('mb-4')
        
        with ui.row().classes('justify-end gap-2'):
            ui.button(
                cancel_text,
                on_click=lambda: (dialog.close(), on_cancel() if on_cancel else None)
            ).props('flat')
            
            ui.button(
                confirm_text,
                on_click=lambda: (dialog.close(), on_confirm())
            ).classes('bg-red-500 text-white')
    
    dialog.open()


# ==============================================================================
# FORM COMPONENTS
# ==============================================================================

def form_input(
    label: str,
    value: Any = "",
    required: bool = False,
    placeholder: Optional[str] = None,
    icon: Optional[str] = None
) -> ui.input:
    """Create form input"""
    return ui.input(
        label=label + (" *" if required else ""),
        value=value,
        placeholder=placeholder
    ).props(f'{"required" if required else ""}').classes('w-full')


def form_select(
    label: str,
    options: List,
    value: Any = None,
    required: bool = False
) -> ui.select:
    """Create form select"""
    return ui.select(
        options,
        label=label + (" *" if required else ""),
        value=value
    ).classes('w-full')


def form_textarea(
    label: str,
    value: str = "",
    required: bool = False
) -> ui.textarea:
    """Create form textarea"""
    return ui.textarea(
        label=label + (" *" if required else ""),
        value=value
    ).classes('w-full')


def form_number(
    label: str,
    value: float = 0,
    min: Optional[float] = None,
    max: Optional[float] = None,
    step: float = 1,
    required: bool = False
) -> ui.number:
    """Create form number input"""
    return ui.number(
        label=label + (" *" if required else ""),
        value=value,
        min=min,
        max=max,
        step=step
    ).classes('w-full')


# ==============================================================================
# END OF FILE
# ==============================================================================
