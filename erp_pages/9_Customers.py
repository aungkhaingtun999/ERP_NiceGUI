# ==============================================================================
# erp_pages/9_Customers.py
# ERP ENTERPRISE CUSTOMER MANAGEMENT
# NICE GUI VERSION
# ==============================================================================

from typing import Dict, Any, Optional, List
from datetime import datetime
from nicegui import ui, app

from database import get_supabase
from utils.ui import show_table
from auth import is_authenticated


# ==============================================================================
# DATABASE
# ==============================================================================

supabase = get_supabase()


# ==============================================================================
# SESSION STATE
# ==============================================================================

class CustomerState:
    """Session state for customer management."""
    
    def __init__(self):
        self.edit_customer: Optional[Dict[str, Any]] = None
        self.search_query: str = ""


def get_state() -> CustomerState:
    """Get or create customer state."""
    client_id = app.context.client.id if app.context.client else 'default'
    
    if not hasattr(app.storage, 'customer_state'):
        app.storage.customer_state = {}
    
    if client_id not in app.storage.customer_state:
        app.storage.customer_state[client_id] = CustomerState()
    
    return app.storage.customer_state[client_id]


# ==============================================================================
# LOAD CUSTOMERS
# ==============================================================================

def load_customers() -> List[Dict[str, Any]]:
    """Load customers from database."""
    try:
        result = (
            supabase
            .table("customers")
            .select("*")
            .order("id", desc=True)
            .execute()
        )
        
        return result.data or []
    
    except Exception as e:
        ui.notify(f'Error loading customers: {e}', type='error', position='top')
        return []


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main customer management page."""
    
    if not is_authenticated():
        with ui.card().classes('w-full p-4 bg-orange-50'):
            ui.label('Please login first').classes('text-orange-700')
        return
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        ui.label('👥 Customer Management').classes('text-3xl font-bold mb-4')
        
        customers = load_customers()
        
        # ======================================================================
        # CUSTOMER LIST
        # ======================================================================
        
        ui.label('Customer List').classes('text-xl font-bold mb-4')
        
        if not customers:
            with ui.card().classes('w-full p-4 bg-gray-50'):
                ui.label('No customers found.').classes('text-gray-500 text-center')
        else:
            # Search
            search_input = ui.input(
                '🔍 Search Customer',
                placeholder='Search by name, phone...',
                value=state.search_query,
            ).classes('w-full mb-4')
            
            customers_container = ui.column().classes('w-full')
            
            def render_customers(search_text: str = ""):
                """Render customer list."""
                customers_container.clear()
                state.search_query = search_text
                
                filtered = customers
                if search_text:
                    search_lower = search_text.lower()
                    filtered = [
                        c for c in customers
                        if search_lower in str(c.get("full_name", "")).lower()
                        or search_lower in str(c.get("phone", "")).lower()
                        or search_lower in str(c.get("customer_code", "")).lower()
                    ]
                
                if not filtered:
                    with customers_container:
                        ui.label('No matching customers found').classes('text-gray-500')
                    return
                
                with customers_container:
                    for c in filtered:
                        with ui.expansion(
                            f"👤 {c.get('full_name', 'Unknown')}",
                            icon='person'
                        ).classes('w-full mb-2') as expansion:
                            
                            with ui.column().classes('w-full gap-1 p-2'):
                                ui.label(f'Code: {c.get("customer_code", "N/A")}').classes('text-sm text-gray-600')
                                ui.label(f'Phone: {c.get("phone", "N/A")}').classes('text-sm text-gray-600')
                                ui.label(f'Address: {c.get("address", "N/A")}').classes('text-sm text-gray-600')
                                
                                if c.get("loyalty_points"):
                                    ui.label(f'Loyalty Points: {c.get("loyalty_points")}').classes('text-sm text-blue-600')
                                
                                ui.separator().classes('my-2')
                                
                                with ui.row().classes('w-full gap-2'):
                                    edit_btn = ui.button(
                                        '✏️ Edit',
                                        on_click=lambda cust=c: show_edit_form(cust, state, render_customers)
                                    ).props('flat').classes('flex-1 bg-blue-50 text-blue-700')
                                    
                                    delete_btn = ui.button(
                                        '🗑 Delete',
                                        on_click=lambda cust=c: show_delete_dialog(cust, render_customers)
                                    ).props('flat').classes('flex-1 bg-red-50 text-red-700')
            
            search_input.on_value_change(lambda e: render_customers(e.value or ""))
            render_customers()
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # EDIT FORM
        # ======================================================================
        
        edit_container = ui.column().classes('w-full mb-4')
        
        def show_edit_form(customer: Dict, state: CustomerState, refresh_callback: callable):
            """Show edit form for customer."""
            state.edit_customer = customer
            edit_container.clear()
            
            with edit_container:
                ui.label('✏️ Edit Customer').classes('text-xl font-bold mb-4')
                
                with ui.card().classes('w-full p-4'):
                    new_name = ui.input(
                        'Customer Name',
                        value=customer.get("full_name", "")
                    ).classes('w-full mb-2')
                    
                    new_phone = ui.input(
                        'Phone',
                        value=customer.get("phone", "")
                    ).classes('w-full mb-2')
                    
                    new_address = ui.textarea(
                        'Address',
                        value=customer.get("address", "")
                    ).classes('w-full mb-4')
                    
                    with ui.row().classes('w-full gap-2'):
                        update_btn = ui.button(
                            '💾 Update Customer',
                            on_click=lambda: handle_update(
                                customer["id"],
                                new_name.value,
                                new_phone.value,
                                new_address.value,
                                state,
                                update_btn,
                                refresh_callback
                            )
                        ).classes('flex-1 bg-primary text-white')
                        
                        cancel_btn = ui.button(
                            'Cancel',
                            on_click=lambda: cancel_edit(state, edit_container)
                        ).props('flat').classes('flex-1 bg-gray-100')
        
        def cancel_edit(state: CustomerState, container: Any):
            """Cancel edit."""
            state.edit_customer = None
            container.clear()
        
        def handle_update(customer_id, name, phone, address, state, update_btn, refresh_callback):
            """Handle customer update."""
            try:
                update_btn.disable()
                update_btn.text = '⏳ Updating...'
                
                supabase.table("customers").update({
                    "full_name": name,
                    "phone": phone,
                    "address": address,
                    "updated_at": datetime.now().isoformat(),
                }).eq("id", customer_id).execute()
                
                ui.notify('Customer updated', type='positive', position='top')
                
                state.edit_customer = None
                edit_container.clear()
                
                # Refresh customer list
                refresh_callback(state.search_query)
            
            except Exception as e:
                ui.notify(f'Update error: {e}', type='error', position='top')
            
            finally:
                update_btn.enable()
                update_btn.text = '💾 Update Customer'
        
        def show_delete_dialog(customer: Dict, refresh_callback: callable):
            """Show delete confirmation dialog."""
            with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
                ui.label('Confirm Delete').classes('text-xl font-bold mb-4')
                
                ui.label(f'Are you sure you want to delete customer:').classes('mb-2')
                ui.label(f'👤 {customer.get("full_name", "Unknown")}').classes('font-bold mb-4')
                
                with ui.row().classes('w-full justify-end gap-2'):
                    ui.button('Cancel', on_click=dialog.close).props('flat')
                    
                    ui.button(
                        'Yes, Delete',
                        on_click=lambda: handle_delete(customer["id"], dialog, refresh_callback)
                    ).classes('bg-red-500 text-white')
            
            dialog.open()
        
        def handle_delete(customer_id, dialog, refresh_callback):
            """Handle customer delete."""
            try:
                supabase.table("customers").delete().eq("id", customer_id).execute()
                
                ui.notify('Customer deleted', type='positive', position='top')
                dialog.close()
                
                # Refresh customer list
                refresh_callback(state.search_query)
            
            except Exception as e:
                ui.notify(f'Delete error: {e}', type='error', position='top')
        
        ui.separator().classes('my-4')
        
        # ======================================================================
        # ADD CUSTOMER
        # ======================================================================
        
        ui.label('➕ Add Customer').classes('text-xl font-bold mb-4')
        
        with ui.card().classes('w-full p-4'):
            name_input = ui.input(
                'Customer Name',
                placeholder='Enter customer name'
            ).classes('w-full mb-2')
            
            phone_input = ui.input(
                'Phone Number',
                placeholder='Enter phone number'
            ).classes('w-full mb-2')
            
            address_input = ui.textarea(
                'Address',
                placeholder='Enter address'
            ).classes('w-full mb-4')
            
            save_btn = ui.button(
                '💾 Save Customer',
                on_click=lambda: handle_add_customer(
                    name_input.value,
                    phone_input.value,
                    address_input.value,
                    name_input,
                    save_btn,
                    lambda: render_customers(state.search_query)
                )
            ).classes('w-full bg-primary text-white')


def handle_add_customer(name: str, phone: str, address: str, name_input: Any, save_btn: Any, refresh_callback: callable):
    """Handle add customer."""
    try:
        if not name.strip():
            ui.notify('Customer name required', type='error', position='top')
            return
        
        save_btn.disable()
        save_btn.text = '⏳ Saving...'
        
        supabase.table("customers").insert({
            "customer_code": "CUS" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "full_name": name,
            "phone": phone,
            "address": address,
            "loyalty_points": 0,
            "is_active": True,
        }).execute()
        
        ui.notify('Customer added', type='positive', position='top')
        
        # Clear form
        name_input.value = ''
        
        # Refresh list
        refresh_callback()
    
    except Exception as e:
        ui.notify(f'Add error: {e}', type='error', position='top')
    
    finally:
        save_btn.enable()
        save_btn.text = '💾 Save Customer'


# ==============================================================================
# ADVANCED VIEW
# ==============================================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced customer management with tabs."""
    
    if not is_authenticated():
        ui.label('Please login first').classes('text-orange-700')
        return
    
    state = get_state()
    target = container or ui.column()
    
    with target:
        ui.label('👥 Customer Management').classes('text-3xl font-bold mb-4')
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_list = ui.tab('👥 Customers', icon='people')
            tab_add = ui.tab('➕ Add', icon='person_add')
            tab_edit = ui.tab('✏️ Edit', icon='edit')
        
        with ui.tab_panels(tabs, value=tab_list).classes('w-full'):
            with ui.tab_panel(tab_list):
                render_customer_list_panel()
            
            with ui.tab_panel(tab_add):
                render_add_customer_panel()
            
            with ui.tab_panel(tab_edit):
                render_edit_customer_panel()


def render_customer_list_panel():
    """Render customer list panel."""
    customers = load_customers()
    
    if not customers:
        ui.label('No customers found').classes('text-gray-500')
        return
    
    # Search
    search = ui.input('🔍 Search').classes('w-full mb-4')
    container = ui.column().classes('w-full')
    
    def render(search_text=""):
        container.clear()
        filtered = customers
        
        if search_text:
            filtered = [c for c in customers if search_text.lower() in str(c.get("full_name", "")).lower()]
        
        with container:
            for c in filtered:
                with ui.card().classes('w-full p-3 mb-2'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('person').classes('text-gray-500')
                        ui.label(c.get("full_name", "Unknown")).classes('font-bold flex-1')
                        ui.label(c.get("phone", "N/A")).classes('text-sm text-gray-500')
    
    search.on_value_change(lambda e: render(e.value or ""))
    render()


def render_add_customer_panel():
    """Render add customer panel."""
    with ui.card().classes('w-full p-4'):
        name = ui.input('Customer Name').classes('w-full mb-2')
        phone = ui.input('Phone').classes('w-full mb-2')
        address = ui.textarea('Address').classes('w-full mb-4')
        
        ui.button(
            'Save Customer',
            on_click=lambda: handle_add_customer(name.value, phone.value, address.value, name, None, None)
        ).classes('w-full bg-primary text-white')


def render_edit_customer_panel():
    """Render edit customer panel."""
    customers = load_customers()
    
    if not customers:
        ui.label('No customers to edit').classes('text-gray-500')
        return
    
    opts = {str(c["id"]): c.get("full_name", "Unknown") for c in customers}
    selected_id = ui.select(list(opts.keys()), label='Select Customer').classes('w-full mb-4')
    
    container = ui.column().classes('w-full')
    
    def load_edit():
        container.clear()
        customer = next((c for c in customers if str(c["id"]) == selected_id.value), None)
        
        if customer:
            with container:
                name = ui.input('Name', value=customer.get("full_name", "")).classes('w-full mb-2')
                phone = ui.input('Phone', value=customer.get("phone", "")).classes('w-full mb-2')
                address = ui.textarea('Address', value=customer.get("address", "")).classes('w-full mb-4')
                
                ui.button(
                    'Update',
                    on_click=lambda: handle_update(customer["id"], name.value, phone.value, address.value, None, None, None)
                ).classes('w-full bg-primary text-white')
    
    selected_id.on_value_change(lambda e: load_edit())
    load_edit()


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
