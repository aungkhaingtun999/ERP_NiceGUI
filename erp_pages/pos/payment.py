# ==============================================================================
# erp_pages/pos/payment_nicegui.py
# ERP ENTERPRISE POS PAYMENT MODULE v15.0 STABLE
# NiceGUI Version
# ==============================================================================

from nicegui import ui, app
import datetime
from typing import Optional, Dict, Any
import asyncio

from database import generate_payment_qr
from erp_core.repositories.payment_account_repository import \
    get_payment_account
from supabase_client import get_supabase
from .cart import calculate_subtotal
from .checkout import process_checkout
from .engine import get_default_tax_rate
from .session import start_processing, stop_processing


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
# HELPER: POST JOURNAL ENTRY FOR DOUBLE ENTRY SYSTEM
# ==============================================================================

def post_sale_journal_entry(sale_id: int, total_amount: float, payment_method: str = "CASH") -> bool:
    """
    အရောင်းအဝယ် (Sale) ပြီးမြောက်ပါက journal_entries ဇယားသို့ 
    Double Entry (Debit နှင့် Credit) အလိုအလျောက် ထည့်သွင်းပေးသည်။
    """
    try:
        supabase = get_supabase()
        if not supabase:
            return False

        if total_amount <= 0:
            return True

        # ငွေပေးချေမှုပုံစံအလိုက် Account ID သတ်မှတ်ခြင်း
        debit_account_id = 1 if "CASH" in payment_method.upper() else 2  # 1: Cash, 2: Bank/AR
        credit_account_id = 4  # Sales Revenue

        journal_rows = [
            {
                "sale_id": sale_id,
                "account_id": debit_account_id,
                "debit": total_amount,
                "credit": 0.00,
                "description": f"Sale #{sale_id} - Payment via {payment_method}",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            {
                "sale_id": sale_id,
                "account_id": credit_account_id,
                "debit": 0.00,
                "credit": total_amount,
                "description": f"Sale #{sale_id} - Revenue",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        ]

        response = supabase.table("journal_entries").insert(journal_rows).execute()
        return bool(response.data)

    except Exception as e:
        print(f"Error posting journal entry: {str(e)}")
        return False


# ==============================================================================
# PAYMENT UI COMPONENT
# ==============================================================================

class PaymentComponent:
    """Payment UI Component for NiceGUI"""
    
    def __init__(self, warehouse_id: str):
        self.warehouse_id = warehouse_id
        self.cart = app.storage.user.get('cart', [])
        self.discount = float(app.storage.user.get('discount', 0))
        self.payment_method = app.storage.user.get('payment_method', 'CASH')
        self.mobile_provider = app.storage.user.get('mobile_provider', 'KBZ Pay')
        self.mobile_txn = app.storage.user.get('mobile_txn', '')
        self.received_amount = 0.0
        
        # UI Elements
        self.summary_container: Optional[ui.element] = None
        self.discount_input: Optional[ui.number] = None
        self.payment_method_select: Optional[ui.select] = None
        self.mobile_payment_container: Optional[ui.element] = None
        self.received_input: Optional[ui.number] = None
        self.change_label: Optional[ui.label] = None
        self.complete_button: Optional[ui.button] = None
        
        # Calculate initial values
        self.subtotal = calculate_subtotal(self.cart)
        self.total_qty = sum(int(item.get("qty", 0)) for item in self.cart)
        self.tax_rate = get_default_tax_rate()
        self.tax_amount = self.subtotal * self.tax_rate / 100
        self.grand_total = max(0, self.subtotal + self.tax_amount - self.discount)
        
    def create_summary_section(self):
        """Create order summary section"""
        with ui.row().classes('w-full gap-4 mb-4'):
            # Items count
            with ui.card().classes('flex-1 p-3'):
                ui.label('Items').classes('text-sm text-gray-500')
                ui.label(str(len(self.cart))).classes('text-xl font-bold')
            
            # Total quantity
            with ui.card().classes('flex-1 p-3'):
                ui.label('Total Qty').classes('text-sm text-gray-500')
                ui.label(str(self.total_qty)).classes('text-xl font-bold')
            
            # Subtotal
            with ui.card().classes('flex-1 p-3'):
                ui.label('Subtotal').classes('text-sm text-gray-500')
                ui.label(money(self.subtotal)).classes('text-xl font-bold')
        
        # Tax info
        with ui.row().classes('w-full mb-4'):
            ui.label(f'🧾 Tax {self.tax_rate:.2f}% : {money(self.tax_amount)}').classes('text-sm')
    
    def create_discount_section(self):
        """Create discount input section"""
        with ui.column().classes('w-full mb-4 gap-2'):
            ui.label('Discount (MMK)').classes('text-sm font-semibold')
            
            self.discount_input = ui.number(
                label='Discount',
                value=self.discount,
                min=0,
                step=100,
                format='%.0f'
            ).classes('w-full').props('outlined dense')
            
            def on_discount_change(e):
                self.discount = float(e.value or 0)
                app.storage.user['discount'] = self.discount
                self.update_totals()
            
            self.discount_input.on('update:model-value', on_discount_change)
    
    def create_total_section(self):
        """Create total payable section"""
        self.total_container = ui.column().classes('w-full mb-4 gap-1')
        
        with self.total_container:
            ui.label('💰 Total Payable').classes('text-sm text-gray-600')
            ui.label(money(self.grand_total)).classes('text-3xl font-bold text-primary')
            
            with ui.column().classes('w-full mt-2 gap-0'):
                ui.label(f'Subtotal : {money(self.subtotal)}').classes('text-xs text-gray-500')
                ui.label(f'Tax : {money(self.tax_amount)}').classes('text-xs text-gray-500')
                ui.label(f'Discount : {money(self.discount)}').classes('text-xs text-gray-500')
    
    def update_totals(self):
        """Update total calculations"""
        self.grand_total = max(0, self.subtotal + self.tax_amount - self.discount)
        
        # Update total display
        if hasattr(self, 'total_container'):
            self.total_container.clear()
            with self.total_container:
                ui.label('💰 Total Payable').classes('text-sm text-gray-600')
                ui.label(money(self.grand_total)).classes('text-3xl font-bold text-primary')
                
                with ui.column().classes('w-full mt-2 gap-0'):
                    ui.label(f'Subtotal : {money(self.subtotal)}').classes('text-xs text-gray-500')
                    ui.label(f'Tax : {money(self.tax_amount)}').classes('text-xs text-gray-500')
                    ui.label(f'Discount : {money(self.discount)}').classes('text-xs text-gray-500')
        
        # Update mobile payment if active
        if self.payment_method == 'MOBILE' and self.mobile_payment_container:
            self.update_mobile_payment()
        
        # Update change calculation
        self.update_change()
    
    def create_payment_method_section(self):
        """Create payment method selector"""
        with ui.column().classes('w-full mb-4 gap-2'):
            ui.label('Payment Method').classes('text-sm font-semibold')
            
            self.payment_method_select = ui.select(
                options=['CASH', 'BANK', 'MOBILE', 'CREDIT'],
                value=self.payment_method,
                label='Payment Method'
            ).classes('w-full').props('outlined dense')
            
            def on_payment_method_change(e):
                self.payment_method = e.value or 'CASH'
                app.storage.user['payment_method'] = self.payment_method
                self.update_payment_method_ui()
            
            self.payment_method_select.on('update:model-value', on_payment_method_change)
    
    def create_mobile_payment_section(self):
        """Create mobile payment section"""
        self.mobile_payment_container = ui.column().classes('w-full mb-4 gap-3')
        
        with self.mobile_payment_container:
            # Provider selector
            provider_select = ui.select(
                options=['KBZ Pay', 'Wave Pay', 'AYA Pay'],
                value=self.mobile_provider,
                label='Mobile Provider'
            ).classes('w-full').props('outlined dense')
            
            def on_provider_change(e):
                self.mobile_provider = e.value or 'KBZ Pay'
                app.storage.user['mobile_provider'] = self.mobile_provider
                self.update_mobile_payment()
            
            provider_select.on('update:model-value', on_provider_change)
            
            # Mobile payment details container
            self.mobile_details_container = ui.column().classes('w-full gap-2')
            
            # Transaction ID input
            self.mobile_txn_input = ui.input(
                label='Transaction ID',
                placeholder='Enter mobile banking transaction number',
                value=self.mobile_txn
            ).classes('w-full').props('outlined dense')
            
            def on_txn_change(e):
                self.mobile_txn = e.value or ''
                app.storage.user['mobile_txn'] = self.mobile_txn
            
            self.mobile_txn_input.on('update:model-value', on_txn_change)
            
            # Update mobile payment details
            self.update_mobile_payment()
    
    def update_mobile_payment(self):
        """Update mobile payment QR and details"""
        if not hasattr(self, 'mobile_details_container'):
            return
            
        self.mobile_details_container.clear()
        
        with self.mobile_details_container:
            branch_id = app.storage.user.get('branch_id', 1)
            account = get_payment_account(self.mobile_provider, branch_id=branch_id)
            
            if not account:
                ui.label(f'{self.mobile_provider} account not configured').classes('text-red-500')
                return
            
            account_name = account.get('account_name', 'ERP SHOP')
            account_no = account.get('account_no', '')
            qr_mode = account.get('qr_mode', 'DYNAMIC')
            
            # Generate QR code
            try:
                if self.mobile_provider == 'KBZ Pay' and qr_mode == 'STATIC' and account.get('qr_payload_template'):
                    qr_buffer = generate_payment_qr(
                        provider=self.mobile_provider,
                        account_name=account_name,
                        account_no=account_no,
                        amount=self.grand_total,
                        sale_id='TEMP',
                        raw_payload=account.get('qr_payload_template')
                    )
                else:
                    qr_buffer = generate_payment_qr(
                        provider=self.mobile_provider,
                        account_name=account_name,
                        account_no=account_no,
                        amount=self.grand_total,
                        sale_id='TEMP'
                    )
                
                # Display QR code
                if qr_buffer:
                    import io
                    from PIL import Image
                    img = Image.open(io.BytesIO(qr_buffer))
                    ui.image(qr_buffer).classes('w-64 h-64 mx-auto')
                    ui.label(f'Scan to pay with {self.mobile_provider}').classes('text-sm text-center')
            except Exception as e:
                ui.label(f'Error generating QR: {str(e)}').classes('text-red-500')
            
            # Payment info
            with ui.card().classes('w-full p-3 bg-blue-50'):
                ui.label('💰 Payment Amount').classes('text-sm text-gray-600')
                ui.label(f'{self.grand_total:,.0f} MMK').classes('text-xl font-bold')
                
                ui.label('Pay to:').classes('text-sm text-gray-600 mt-2')
                ui.label(f'👤 {account_name}').classes('text-sm')
                ui.label(f'📱 {account_no}').classes('text-sm')
                ui.label(f'Amount: {self.grand_total:,.0f} MMK').classes('text-sm font-semibold')
            
            # QR mode info
            if qr_mode == 'STATIC':
                ui.label(f'Scan with {self.mobile_provider} and pay to {account_name} ({account_no})').classes('text-xs text-gray-500')
                ui.label('⚠️ Static QR is enabled. Customer may need to enter amount manually.').classes('text-xs text-yellow-600')
            else:
                ui.label(f'Pay MMK {self.grand_total:,.0f} to {account_name} ({account_no})').classes('text-xs text-gray-500')
    
    def create_received_section(self):
        """Create received amount section"""
        with ui.column().classes('w-full mb-4 gap-2'):
            self.received_input = ui.number(
                label='Received Amount',
                value=0,
                min=0,
                step=100,
                format='%.0f'
            ).classes('w-full').props('outlined dense')
            
            def on_received_change(e):
                self.received_amount = float(e.value or 0)
                self.update_change()
            
            self.received_input.on('update:model-value', on_received_change)
            
            # Change display
            self.change_container = ui.column().classes('w-full gap-0')
            self.update_change()
    
    def update_change(self):
        """Update change calculation"""
        if hasattr(self, 'change_container'):
            self.change_container.clear()
            with self.change_container:
                change = max(0, self.received_amount - self.grand_total)
                ui.label(f'Received : {money(self.received_amount)}').classes('text-xs text-gray-500')
                ui.label(f'Change : {money(change)}').classes('text-xs font-semibold text-green-600')
    
    def update_payment_method_ui(self):
        """Update UI based on payment method"""
        # Show/hide mobile payment container
        if self.mobile_payment_container:
            self.mobile_payment_container.set_visibility(self.payment_method == 'MOBILE')
        
        # Show/hide received amount input
        if hasattr(self, 'received_input'):
            self.received_input.set_visibility(self.payment_method != 'MOBILE')
    
    async def complete_sale(self):
        """Complete the sale transaction"""
        if self.payment_method == 'MOBILE':
            self.received_amount = self.grand_total
        
        if self.received_amount < self.grand_total:
            ui.notify('Insufficient payment.', type='negative')
            return
        
        start_processing()
        
        try:
            # Show loading state
            self.complete_button.disable()
            self.complete_button.props('loading')
            
            # Process checkout (run in thread to avoid blocking)
            result = await asyncio.to_thread(
                process_checkout,
                cart=self.cart,
                paid_amount=self.received_amount,
                warehouse_id=self.warehouse_id,
                cashier_id=app.storage.user.get('user', {}).get('id'),
                payment_method=self.payment_method,
                discount=self.discount
            )
            
            if result.get('success', False):
                raw_data = result.get('data', {})
                
                # Handle Supabase response format
                if isinstance(raw_data, list) and len(raw_data) > 0:
                    sale_data = raw_data[0]
                elif isinstance(raw_data, dict):
                    sale_data = raw_data
                else:
                    sale_data = {}
                
                sale_id = sale_data.get('id')
                
                # Post journal entry
                if sale_id:
                    await asyncio.to_thread(
                        post_sale_journal_entry,
                        sale_id=int(sale_id),
                        total_amount=float(self.grand_total),
                        payment_method=str(self.payment_method)
                    )
                else:
                    # Fallback to get latest sale ID
                    try:
                        supabase = get_supabase()
                        latest_sale = await asyncio.to_thread(
                            lambda: supabase.table("sales").select("id").order("id", desc=True).limit(1).execute()
                        )
                        if latest_sale.data:
                            fallback_sale_id = latest_sale.data[0]['id']
                            await asyncio.to_thread(
                                post_sale_journal_entry,
                                sale_id=int(fallback_sale_id),
                                total_amount=float(self.grand_total),
                                payment_method=str(self.payment_method)
                            )
                    except Exception:
                        pass
                
                # Update sale data
                change = max(0, self.received_amount - self.grand_total)
                sale_data.update({
                    'subtotal': self.subtotal,
                    'discount': self.discount,
                    'tax': self.tax_amount,
                    'tax_rate': self.tax_rate,
                    'total': self.grand_total,
                    'paid_amount': self.received_amount,
                    'change_amount': change,
                    'payment_method': self.payment_method,
                    'items': self.cart
                })
                
                # Add mobile payment info
                if self.payment_method == 'MOBILE':
                    sale_data.update({
                        'mobile_provider': self.mobile_provider,
                        'mobile_txn': self.mobile_txn
                    })
                
                # Store sale data and show receipt
                app.storage.user['sale_data'] = sale_data
                app.storage.user['show_receipt'] = True
                
                # Clear cart
                app.storage.user['cart'] = []
                app.storage.user['discount'] = 0
                
                ui.notify('Sale completed successfully!', type='positive')
                
                # Navigate to receipt
                ui.navigate.to('/pos/receipt')
                
            else:
                ui.notify(
                    result.get('message', 'Checkout Failed'),
                    type='negative'
                )
        
        except Exception as e:
            ui.notify(f'Checkout Error: {str(e)}', type='negative')
        
        finally:
            stop_processing()
            if hasattr(self, 'complete_button'):
                self.complete_button.enable()
                self.complete_button.props(remove='loading')
    
    def create_complete_button(self):
        """Create complete sale button"""
        self.complete_button = ui.button(
            '✅ Complete Sale',
            on_click=self.complete_sale
        ).classes('w-full bg-primary text-white font-bold py-3')
    
    def build(self, container: Optional[ui.element] = None):
        """Build the payment component"""
        target = container if container else ui.column().classes('w-full')
        
        with target:
            ui.separator()
            ui.label('💳 Payment').classes('text-xl font-bold mb-4')
            
            # Summary section
            self.create_summary_section()
            
            # Discount section
            self.create_discount_section()
            
            # Total section
            self.create_total_section()
            
            # Payment method section
            self.create_payment_method_section()
            
            # Mobile payment section (initially hidden unless MOBILE selected)
            self.create_mobile_payment_section()
            
            # Received amount section
            self.create_received_section()
            
            # Complete button
            self.create_complete_button()
            
            # Initial UI state
            self.update_payment_method_ui()


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render_payment(warehouse_id: str, container: Optional[ui.element] = None):
    """
    Render payment component
    Compatible with both Streamlit-style calls and NiceGUI
    """
    cart = app.storage.user.get('cart', [])
    
    if not cart:
        return
    
    payment_component = PaymentComponent(warehouse_id)
    payment_component.build(container)


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    'PaymentComponent',
    'render_payment',
    'post_sale_journal_entry',
    'money'
]
