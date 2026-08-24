# ==============================================================================
# erp_pages/13_Price_Import.py
#
# ERP ENTERPRISE PRICE IMPORT CENTER v1.0
# NICE GUI VERSION
#
# Features:
# - CSV Price Import
# - Price Preview
# - Markup Calculation
# - Queue Import
# - Pending Approval View
#
# ==============================================================================

from typing import Dict, Any, Optional, List
import io
import pandas as pd
from nicegui import ui

from erp_core.services.price_import_service import (
    bulk_import_prices,
    pending_imports,
    approve_and_apply_price,
    reject_import
)

from auth import (
    is_authenticated,
    get_current_user,
)


# ==============================================================================
# MONEY FORMATTER
# ==============================================================================

def money(value: Any) -> str:
    """Format value as MMK currency."""
    try:
        return f"{float(value):,.0f} MMK"
    except Exception:
        return "0 MMK"


# ==============================================================================
# FILE UPLOAD HANDLER
# ==============================================================================

def handle_file_upload(e, preview_container, import_button):
    """Handle CSV file upload and preview."""
    try:
        # Read CSV content
        content = e.content.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Store dataframe in app storage for later use
        app.storage['price_import_df'] = df
        
        # Show preview
        preview_container.clear()
        
        with preview_container:
            ui.notify(f'{len(df)} Products Loaded', type='positive', position='top')
            
            # Show dataframe preview
            columns = [
                {'name': col, 'label': col, 'field': col, 'sortable': True}
                for col in df.columns
            ]
            
            rows = df.head(100).to_dict('records')
            
            ui.table(
                columns=columns,
                rows=rows,
                row_key='id' if 'id' in df.columns else df.columns[0],
                pagination=20,
                title='CSV Preview',
            ).classes('w-full')
            
            # Enable import button
            import_button.enable()
    
    except Exception as e:
        preview_container.clear()
        with preview_container:
            ui.notify(f'Error reading CSV: {e}', type='error', position='top')


def handle_import(import_button, on_success=None):
    """Handle import to queue."""
    try:
        # Get stored dataframe
        df = app.storage.get('price_import_df')
        
        if df is None:
            ui.notify('Please upload a CSV file first', type='warning', position='top')
            return
        
        # Disable button during import
        import_button.disable()
        import_button.text = '⏳ Importing...'
        
        # Convert to records
        products = df.to_dict(orient='records')
        
        # Get user
        user = get_current_user()
        user_id = user.get('id') if user else None
        
        # Bulk import
        result = bulk_import_prices(products, created_by=user_id)
        
        # Count success
        success_count = sum(1 for x in result if x.get('success'))
        
        ui.notify(
            f'{success_count} items added to approval queue',
            type='positive',
            position='top',
            timeout=5000
        )
        
        # Clear stored data
        app.storage.pop('price_import_df', None)
        
        # Call callback
        if on_success:
            on_success()
    
    except Exception as e:
        ui.notify(f'Import failed: {e}', type='error', position='top')
    
    finally:
        import_button.enable()
        import_button.text = '🚀 Import To Queue'


# ==============================================================================
# PENDING APPROVAL COMPONENTS
# ==============================================================================

def build_pending_queue(container: Any, on_change: Optional[callable] = None):
    """Build pending approval queue."""
    container.clear()
    
    queue = pending_imports()
    
    if not queue:
        with container:
            with ui.card().classes('w-full p-4 bg-gray-50'):
                ui.label('No pending price imports').classes('text-gray-500 text-center')
        return
    
    with container:
        for row in queue:
            with ui.card().classes('w-full p-4 mb-4 border border-gray-200'):
                # Product name
                ui.label(f"📦 {row.get('name', 'Unknown')}").classes('text-xl font-bold mb-2')
                
                # Price comparison
                with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
                    # Old price
                    with ui.card().classes('p-3 flex-1 min-w-[150px] bg-gray-50'):
                        ui.label('Old Price').classes('text-sm text-gray-600')
                        ui.label(money(row.get('old_selling_price'))).classes(
                            'text-lg font-semibold text-gray-700'
                        )
                    
                    # New price
                    with ui.card().classes('p-3 flex-1 min-w-[150px] bg-blue-50'):
                        ui.label('New Price').classes('text-sm text-gray-600')
                        ui.label(money(row.get('new_selling_price'))).classes(
                            'text-lg font-semibold text-blue-700'
                        )
                    
                    # Difference
                    old_price = float(row.get('old_selling_price', 0) or 0)
                    new_price = float(row.get('new_selling_price', 0) or 0)
                    diff = new_price - old_price
                    
                    with ui.card().classes('p-3 flex-1 min-w-[150px] bg-green-50'):
                        ui.label('Difference').classes('text-sm text-gray-600')
                        
                        if diff >= 0:
                            ui.label(f'+{money(diff)}').classes('text-lg font-semibold text-green-700')
                        else:
                            ui.label(f'-{money(abs(diff))}').classes('text-lg font-semibold text-red-700')
                
                # Action buttons
                with ui.row().classes('w-full gap-2'):
                    approve_btn = ui.button(
                        '✅ Approve',
                        on_click=lambda r=row: handle_approve(r, approve_btn, on_change)
                    ).classes('flex-1 bg-green-500 text-white')
                    
                    reject_btn = ui.button(
                        '❌ Reject',
                        on_click=lambda r=row: show_reject_dialog(r, reject_btn, on_change)
                    ).classes('flex-1 bg-red-500 text-white')


def handle_approve(row: Dict[str, Any], approve_btn: Any, on_change: Optional[callable] = None):
    """Handle price approval."""
    try:
        approve_btn.disable()
        approve_btn.text = '⏳ Approving...'
        
        user = get_current_user()
        
        result = approve_and_apply_price(row, user.get('id') if user else None)
        
        if result.get('success', False):
            ui.notify('Price Approved', type='positive', position='top')
            
            if on_change:
                on_change()
        else:
            ui.notify(
                result.get('message', 'Approval failed'),
                type='error',
                position='top'
            )
    
    except Exception as e:
        ui.notify(f'Approval error: {e}', type='error', position='top')
    
    finally:
        approve_btn.enable()
        approve_btn.text = '✅ Approve'


def show_reject_dialog(row: Dict[str, Any], reject_btn: Any, on_change: Optional[callable] = None):
    """Show reject confirmation dialog."""
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
        ui.label('Reject Price Import').classes('text-xl font-bold mb-4')
        
        ui.label(f"Product: {row.get('name', 'Unknown')}").classes('mb-2')
        ui.label(f"New Price: {money(row.get('new_selling_price'))}").classes('mb-4')
        
        # Rejection reason
        reason_input = ui.textarea(
            'Rejection Reason',
            placeholder='Enter reason for rejection...'
        ).classes('w-full mb-4')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            ui.button(
                'Confirm Reject',
                on_click=lambda: handle_reject(
                    row,
                    reason_input.value,
                    dialog,
                    reject_btn,
                    on_change
                )
            ).classes('bg-red-500 text-white')
    
    dialog.open()


def handle_reject(
    row: Dict[str, Any],
    reason: str,
    dialog: Any,
    reject_btn: Any,
    on_change: Optional[callable] = None
):
    """Handle price rejection."""
    try:
        reject_btn.disable()
        reject_btn.text = '⏳ Rejecting...'
        
        user = get_current_user()
        
        reject_import(
            row.get('id'),
            user.get('id') if user else None,
            reason or 'Rejected by admin'
        )
        
        ui.notify('Price Rejected', type='warning', position='top')
        dialog.close()
        
        if on_change:
            on_change()
    
    except Exception as e:
        ui.notify(f'Rejection error: {e}', type='error', position='top')
    
    finally:
        reject_btn.enable()
        reject_btn.text = '❌ Reject'


# ==============================================================================
# TEMPLATE SECTION
# ==============================================================================

def build_template_section(container: Any):
    """Build CSV template section."""
    container.clear()
    
    template_data = [
        {
            'id': 1,
            'name': 'Milk Tea',
            'barcode': 'TEA-001',
            'sku': 'TEA-001',
            'purchase_price': 2000,
            'selling_price': 2500
        }
    ]
    
    template_df = pd.DataFrame(template_data)
    
    with container:
        ui.label('📄 CSV Format').classes('text-xl font-bold mb-2')
        ui.label('Use the following format for your CSV file:').classes('text-gray-600 mb-4')
        
        # Show template table
        columns = [
            {'name': col, 'label': col, 'field': col}
            for col in template_df.columns
        ]
        
        ui.table(
            columns=columns,
            rows=template_df.to_dict('records'),
            row_key='id',
            title='Template',
        ).classes('w-full mb-4')
        
        # Download template button
        csv_bytes = template_df.to_csv(index=False).encode('utf-8')
        
        ui.button(
            '⬇️ Download Template',
            on_click=lambda: ui.download(csv_bytes, 'price_import_template.csv')
        ).props('flat').classes('bg-gray-100')


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def main(container: Optional[Any] = None):
    """Main page entry point."""
    
    # Auth check
    if not is_authenticated():
        with ui.card().classes('w-full p-4 bg-orange-50'):
            ui.label('Please login first.').classes('text-orange-700')
        return
    
    target = container or ui.column()
    
    with target:
        # Header
        ui.label('💰 ERP Price Import Center').classes('text-3xl font-bold mb-2')
        ui.label('Bulk Product Price Management').classes('text-gray-500 mb-4')
        
        # ======================================================================
        # UPLOAD SECTION
        # ======================================================================
        
        ui.label('📂 Import Price File').classes('text-xl font-bold mb-4')
        
        preview_container = ui.column().classes('w-full mb-4')
        
        import_button = ui.button(
            '🚀 Import To Queue',
            on_click=lambda: handle_import(import_button, refresh_page)
        ).classes('w-full bg-primary text-white font-semibold mb-4')
        
        import_button.disable()  # Disabled until file uploaded
        
        # File upload
        ui.upload(
            on_upload=lambda e: handle_file_upload(e, preview_container, import_button),
            auto_upload=True,
            label='Upload CSV File',
        ).props('accept=.csv').classes('w-full mb-4')
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # TEMPLATE SECTION
        # ======================================================================
        
        template_container = ui.column().classes('w-full mb-4')
        build_template_section(template_container)
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # PENDING QUEUE
        # ======================================================================
        
        ui.label('⏳ Pending Approval').classes('text-xl font-bold mb-4')
        
        pending_container = ui.column().classes('w-full')
        
        def refresh_page():
            """Refresh pending queue."""
            build_pending_queue(pending_container, refresh_page)
        
        # Initial render
        refresh_page()


# ==============================================================================
# ADVANCED VIEW WITH TABS
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced view with tabs."""
    
    if not is_authenticated():
        with ui.card().classes('w-full p-4 bg-orange-50'):
            ui.label('Please login first.').classes('text-orange-700')
        return
    
    target = container or ui.column()
    
    with target:
        ui.label('💰 ERP Price Import Center').classes('text-3xl font-bold mb-4')
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_import = ui.tab('📂 Import', icon='upload')
            tab_template = ui.tab('📄 Template', icon='description')
            tab_pending = ui.tab('⏳ Pending Approval', icon='pending')
        
        with ui.tab_panels(tabs, value=tab_import).classes('w-full'):
            with ui.tab_panel(tab_import):
                preview_container = ui.column().classes('w-full')
                
                import_button = ui.button(
                    '🚀 Import To Queue',
                    on_click=lambda: handle_import(import_button)
                ).classes('w-full bg-primary text-white mb-4')
                
                import_button.disable()
                
                ui.upload(
                    on_upload=lambda e: handle_file_upload(e, preview_container, import_button),
                    auto_upload=True,
                    label='Upload CSV File',
                ).props('accept=.csv').classes('w-full')
            
            with ui.tab_panel(tab_template):
                build_template_section(ui.column())
            
            with ui.tab_panel(tab_pending):
                pending_container = ui.column().classes('w-full')
                
                def refresh_pending():
                    build_pending_queue(pending_container, refresh_pending)
                
                refresh_pending()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    main()
