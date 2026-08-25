# ==============================================================================
# erp_pages/pos/receipt_nicegui.py
# ERP ENTERPRISE POS RECEIPT MODULE v13.0 FINAL
# NiceGUI Version
#
# Responsibilities:
# - Receipt display
# - Safe receipt mapping
# - Myanmar Time
# - PDF generation
# - Thermal printing
# - New sale reset
#
# FLOW:
#
# CHECKOUT
#    ↓
# SALE DATA
#    ↓
# RECEIPT DISPLAY
#    ↓
# PDF / THERMAL PRINT
#
# ==============================================================================

from nicegui import ui, app
from typing import Optional, Dict, Any, List
import asyncio
import pandas as pd
import io

from utils.receipt_pdf import generate_pdf
from utils.thermal_receipt import print_thermal, build_receipt_data
from utils.timezone import format_datetime

# ==============================================================================
# MONEY FORMAT
# ==============================================================================

def money(value) -> str:
    """Format money value to MMK"""
    try:
        return f"{float(value):,.0f} MMK"
    except Exception:
        return "0 MMK"

# ==============================================================================
# SAFE FLOAT
# ==============================================================================

def safe_float(value) -> float:
    """Safely convert value to float"""
    try:
        return float(value or 0)
    except Exception:
        return 0.0

# ==============================================================================
# RECEIPT ITEM NORMALIZER
# ==============================================================================

def build_receipt_rows(items: List[Dict]) -> List[Dict]:
    """Build normalized receipt rows from items"""
    rows = []
    
    for item in items or []:
        name = (
            item.get("name")
            or item.get("product_name")
            or "Unknown Product"
        )
        
        qty = safe_float(
            item.get("quantity", item.get("qty", 0))
        )
        
        price = safe_float(
            item.get("unit_price", item.get("selling_price", 0))
        )
        
        amount = safe_float(
            item.get("total", qty * price)
        )
        
        rows.append({
            "Product": name,
            "Qty": qty,
            "Price Source": item.get("price_source", "SYSTEM"),
            "Unit Price": money(price),
            "Amount": money(amount)
        })
    
    return rows

# ==============================================================================
# RECEIPT COMPONENT
# ==============================================================================

class ReceiptComponent:
    """Receipt UI Component for NiceGUI"""
    
    def __init__(self):
        self.data = app.storage.user.get('sale_data', None)
        self.pdf_bytes: Optional[bytes] = None
        self.pdf_filename: Optional[str] = None
        
        # UI Elements
        self.debug_container: Optional[ui.element] = None
        self.items_table: Optional[ui.table] = None
        self.pdf_download_button: Optional[ui.button] = None
        
    def build_receipt_header(self, invoice_no: str, sale_date: str, cashier: str):
        """Build receipt header section"""
        with ui.card().classes('w-full p-4 bg-blue-50 mb-4'):
            with ui.column().classes('gap-2'):
                with ui.row().classes('w-full justify-between'):
                    ui.label('Invoice No:').classes('text-sm text-gray-600')
                    ui.label(str(invoice_no)).classes('text-sm font-bold')
                
                with ui.row().classes('w-full justify-between'):
                    ui.label('Date:').classes('text-sm text-gray-600')
                    ui.label(str(sale_date)).classes('text-sm font-bold')
                
                with ui.row().classes('w-full justify-between'):
                    ui.label('Cashier:').classes('text-sm text-gray-600')
                    ui.label(str(cashier)).classes('text-sm font-bold')
    
    def build_debug_section(self):
        """Build debug data section"""
        with ui.expansion('🔎 DEBUG RECEIPT DATA', icon='bug_report').classes('w-full mb-4'):
            import json
            ui.code(
                json.dumps(self.data, indent=2, default=str),
                language='json'
            ).classes('w-full')
    
    def build_items_table(self, rows: List[Dict]):
        """Build items table"""
        if rows:
            columns = [
                {'name': 'product', 'label': 'Product', 'field': 'Product', 'align': 'left'},
                {'name': 'qty', 'label': 'Qty', 'field': 'Qty', 'align': 'center'},
                {'name': 'price_source', 'label': 'Price Source', 'field': 'Price Source', 'align': 'center'},
                {'name': 'unit_price', 'label': 'Unit Price', 'field': 'Unit Price', 'align': 'right'},
                {'name': 'amount', 'label': 'Amount', 'field': 'Amount', 'align': 'right'},
            ]
            
            self.items_table = ui.table(
                columns=columns,
                rows=rows,
                row_key='product'
            ).classes('w-full mb-4').props('dense flat bordered')
        else:
            ui.label('No items found.').classes('text-yellow-600 mb-4')
    
    def build_total_summary(
        self,
        subtotal: float,
        tax_rate: float,
        tax_amount: float,
        discount: float,
        grand_total: float,
        paid: float,
        change: float
    ):
        """Build total summary section"""
        with ui.card().classes('w-full p-4 bg-green-50 mb-4'):
            with ui.column().classes('gap-2'):
                with ui.row().classes('w-full justify-between'):
                    ui.label('Subtotal:').classes('text-sm')
                    ui.label(money(subtotal)).classes('text-sm font-semibold')
                
                with ui.row().classes('w-full justify-between'):
                    ui.label(f'Tax Rate ({tax_rate:.2f}%):').classes('text-sm')
                    ui.label(money(tax_amount)).classes('text-sm font-semibold')
                
                with ui.row().classes('w-full justify-between'):
                    ui.label('Discount:').classes('text-sm')
                    ui.label(money(discount)).classes('text-sm font-semibold')
                
                ui.separator()
                
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('GRAND TOTAL:').classes('text-lg font-bold')
                    ui.label(money(grand_total)).classes('text-xl font-bold text-primary')
                
                ui.separator()
                
                with ui.row().classes('w-full justify-between'):
                    ui.label('Paid:').classes('text-sm')
                    ui.label(money(paid)).classes('text-sm font-semibold')
                
                with ui.row().classes('w-full justify-between'):
                    ui.label('Change:').classes('text-sm')
                    ui.label(money(change)).classes('text-sm font-semibold text-green-600')
    
    async def print_receipt(self):
        """Handle thermal printing"""
        try:
            items = self.data.get('items', [])
            receipt_print_data = await asyncio.to_thread(
                build_receipt_data,
                self.data,
                items
            )
            
            result = await asyncio.to_thread(
                print_thermal,
                receipt_print_data
            )
            
            if result:
                ui.notify('✅ Receipt printed', type='positive')
            else:
                ui.notify('Printer returned no result', type='warning')
                
        except Exception as e:
            ui.notify(f'Printer Error: {str(e)}', type='negative')
    
    async def generate_pdf_receipt(self):
        """Generate PDF receipt"""
        try:
            items = self.data.get('items', [])
            receipt_pdf_data = await asyncio.to_thread(
                build_receipt_data,
                self.data,
                items
            )
            
            result = await asyncio.to_thread(
                generate_pdf,
                receipt_pdf_data
            )
            
            if result:
                self.pdf_bytes, self.pdf_filename = result
                ui.notify('✅ PDF generated successfully', type='positive')
                
                # Show download button
                if self.pdf_download_button:
                    self.pdf_download_button.set_visibility(True)
            else:
                ui.notify('PDF generation failed', type='negative')
                
        except Exception as e:
            ui.notify(f'PDF Error: {str(e)}', type='negative')
    
    def download_pdf(self):
        """Download generated PDF"""
        if self.pdf_bytes:
            ui.download(
                src=self.pdf_bytes,
                filename=f'{self.pdf_filename}.pdf',
                media_type='application/pdf'
            )
    
    async def new_sale(self):
        """Reset POS for new sale"""
        reset_pos()
        ui.notify('✅ New Sale Ready', type='positive')
        await asyncio.sleep(0.5)
        ui.navigate.to('/pos')
    
    def build_action_buttons(self):
        """Build action buttons"""
        with ui.row().classes('w-full gap-2'):
            # Print button
            ui.button(
                '🖨 Print Receipt',
                on_click=self.print_receipt
            ).classes('flex-1 bg-blue-500 text-white')
            
            # Generate PDF button
            ui.button(
                '📄 Generate PDF',
                on_click=self.generate_pdf_receipt
            ).classes('flex-1 bg-green-500 text-white')
            
            # New sale button
            ui.button(
                '🆕 New Sale',
                on_click=self.new_sale
            ).classes('flex-1 bg-orange-500 text-white')
        
        # PDF download button (initially hidden)
        self.pdf_download_button = ui.button(
            '⬇ Download PDF',
            on_click=self.download_pdf
        ).classes('w-full bg-purple-500 text-white mt-2')
        self.pdf_download_button.set_visibility(False)
    
    def build(self):
        """Build the receipt component"""
        if not self.data:
            with ui.column().classes('w-full items-center p-8'):
                ui.icon('error', size='48px').classes('text-red-500')
                ui.label('Receipt data missing.').classes('text-xl font-semibold')
            return
        
        # Main receipt container
        with ui.column().classes('w-full max-w-3xl mx-auto p-4 gap-4'):
            # Title
            ui.label('🧾 Sales Receipt').classes('text-2xl font-bold text-center')
            
            # Debug section
            self.build_debug_section()
            
            # Safe data mapping
            invoice_no = self.data.get('invoice_no', '-')
            
            raw_date = (
                self.data.get('date')
                or self.data.get('created_at')
            )
            
            if raw_date:
                sale_date = format_datetime(raw_date)
            else:
                sale_date = '-'
            
            cashier = self.data.get('cashier', 'Admin')
            items = self.data.get('items', [])
            
            # Totals mapping
            subtotal = safe_float(self.data.get('subtotal'))
            discount = safe_float(self.data.get('discount'))
            tax_rate = safe_float(self.data.get('tax_rate'))
            tax_amount = safe_float(self.data.get('tax'))
            grand_total = safe_float(
                self.data.get('total')
                or self.data.get('total_amount')
            )
            paid = safe_float(self.data.get('paid_amount'))
            change = safe_float(self.data.get('change_amount'))
            
            # Build sections
            self.build_receipt_header(invoice_no, sale_date, cashier)
            
            # Items table
            rows = build_receipt_rows(items)
            self.build_items_table(rows)
            
            # Total summary
            self.build_total_summary(
                subtotal,
                tax_rate,
                tax_amount,
                discount,
                grand_total,
                paid,
                change
            )
            
            # Action buttons
            self.build_action_buttons()

# ==============================================================================
# RESET POS
# ==============================================================================

def reset_pos():
    """Reset POS state for new sale"""
    app.storage.user['cart'] = []
    app.storage.user['sale_data'] = None
    app.storage.user['show_receipt'] = False
    app.storage.user['processing'] = False
    app.storage.user['received_amount'] = 0
    app.storage.user['discount'] = 0
    app.storage.user['payment_method'] = 'CASH'
    app.storage.user['mobile_provider'] = ''
    app.storage.user['mobile_txn'] = ''

# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render_receipt(container: Optional[ui.element] = None):
    """
    Render receipt component
    Compatible with both Streamlit-style calls and NiceGUI
    """
    receipt_component = ReceiptComponent()
    
    if container:
        with container:
            receipt_component.build()
    else:
        receipt_component.build()

# ==============================================================================
# PAGE ROUTE
# ==============================================================================

@ui.page('/pos/receipt')
def receipt_page():
    """Receipt page route"""
    with ui.header().classes('items-center justify-between'):
        ui.label('Sales Receipt').classes('text-xl font-bold')
    
    with ui.column().classes('w-full'):
        render_receipt()

# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'ReceiptComponent',
    'render_receipt',
    'receipt_page',
    'reset_pos',
    'build_receipt_rows',
    'safe_float',
    'money'
]
