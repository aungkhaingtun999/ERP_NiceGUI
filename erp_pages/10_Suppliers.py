# ==========================================================
# pages/10_Suppliers.py
# ERP ENTERPRISE v15
# Supplier Management
# NICE GUI VERSION
# ==========================================================

from typing import Dict, Any, Optional, List, Callable
import time
from nicegui import ui

from database import get_supabase
from utils.ui import (
    show_table,
    page_title,
    page_header,
    success,
    error,
    warning,
    info,
    empty_data,
    confirm_dialog,
)

# ----------------------------------------------------------
# DATABASE
# ----------------------------------------------------------

supabase = get_supabase()

# ----------------------------------------------------------
# FUNCTIONS
# ----------------------------------------------------------

def get_suppliers() -> List[Dict[str, Any]]:
    """Get all suppliers from database
    
    Returns:
        List of supplier dictionaries
    """
    try:
        response = (
            supabase
            .table("suppliers")
            .select("*")
            .order("id", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        ui.notify("Failed to load suppliers.", type='error', position='top')
        print(f"Error loading suppliers: {e}")
        return []


def add_supplier(
    company_name: str,
    phone: str,
    address: str,
    email: str = "",
    contact_name: str = ""
) -> Optional[Dict[str, Any]]:
    """Add new supplier
    
    Args:
        company_name: Company name
        phone: Phone number
        address: Address
        email: Email address
        contact_name: Contact person name
    
    Returns:
        Created supplier data or None
    """
    try:
        supplier_code = f"SUP-{int(time.time())}"
        
        response = (
            supabase
            .table("suppliers")
            .insert({
                "supplier_code": supplier_code,
                "company_name": company_name,
                "contact_name": contact_name,
                "phone": phone,
                "email": email,
                "address": address,
                "is_active": True
            })
            .execute()
        )
        
        return response.data[0] if response.data else None
    
    except Exception as e:
        ui.notify("Supplier insert failed", type='error', position='top')
        print(f"Error adding supplier: {e}")
        return None


def update_supplier(
    supplier_id: str,
    data: Dict[str, Any]
) -> bool:
    """Update supplier information
    
    Args:
        supplier_id: Supplier ID
        data: Updated supplier data
    
    Returns:
        Success status
    """
    try:
        supabase.table("suppliers").update(data).eq(
            "id", supplier_id
        ).execute()
        
        return True
    
    except Exception as e:
        print(f"Error updating supplier: {e}")
        return False


def delete_supplier(supplier_id: str) -> bool:
    """Delete supplier
    
    Args:
        supplier_id: Supplier ID
    
    Returns:
        Success status
    """
    try:
        supabase.table("suppliers").delete().eq(
            "id", supplier_id
        ).execute()
        
        return True
    
    except Exception as e:
        print(f"Error deleting supplier: {e}")
        return False


# ----------------------------------------------------------
# UI COMPONENTS
# ----------------------------------------------------------

def show_supplier_table(
    suppliers: List[Dict[str, Any]],
    container: Optional[Any] = None
):
    """Display supplier table with search
    
    Args:
        suppliers: List of suppliers
        container: NiceGUI container
    """
    target = container or ui.column()
    
    if not suppliers:
        with target:
            empty_data("No suppliers found")
        return
    
    with target:
        # Search input
        search_input = ui.input(
            '🔍 Search Supplier',
            placeholder='Search by company name...'
        ).classes('w-full mb-4')
        
        # Table container
        table_container = ui.column().classes('w-full')
        
        def update_table(search_text: str = ""):
            """Update table based on search"""
            table_container.clear()
            
            filtered = suppliers
            
            if search_text:
                search_lower = search_text.lower()
                filtered = [
                    s for s in suppliers
                    if search_lower in str(s.get("company_name", "")).lower()
                ]
            
            if filtered:
                with table_container:
                    show_table(
                        filtered,
                        serial=True,
                        pagination=20,
                        title='Suppliers'
                    )
            else:
                with table_container:
                    empty_data("No matching suppliers found")
        
        # Initial table
        update_table()
        
        # Update on search
        search_input.on_value_change(
            lambda e: update_table(e.value or "")
        )


def show_edit_delete_section(
    suppliers: List[Dict[str, Any]],
    container: Optional[Any] = None,
    on_change: Optional[Callable] = None
):
    """Display edit/delete supplier section
    
    Args:
        suppliers: List of suppliers
        container: NiceGUI container
        on_change: Callback after update/delete
    """
    target = container or ui.column()
    
    if not suppliers:
        with target:
            empty_data("No suppliers found")
        return
    
    with target:
        ui.label('✏️ Edit / Delete Supplier').classes('text-xl font-bold mb-4')
        
        # Supplier selection
        supplier_map = {
            f"{s.get('supplier_code')} - {s.get('company_name')}": s
            for s in suppliers
        }
        
        selected_key = ui.select(
            list(supplier_map.keys()),
            label='Select Supplier',
        ).classes('w-full mb-4')
        
        # Edit form container
        edit_container = ui.column().classes('w-full')
        
        def load_supplier_details():
            """Load selected supplier details"""
            edit_container.clear()
            
            supplier = supplier_map.get(selected_key.value)
            
            if not supplier:
                return
            
            with edit_container:
                edit_company = ui.input(
                    'Supplier Name',
                    value=supplier.get("company_name", "")
                ).classes('w-full mb-2')
                
                edit_contact = ui.input(
                    'Contact Person',
                    value=supplier.get("contact_name", "")
                ).classes('w-full mb-2')
                
                edit_phone = ui.input(
                    'Phone',
                    value=supplier.get("phone", "")
                ).classes('w-full mb-2')
                
                edit_email = ui.input(
                    'Email',
                    value=supplier.get("email", "")
                ).classes('w-full mb-2')
                
                edit_address = ui.textarea(
                    'Address',
                    value=supplier.get("address", "")
                ).classes('w-full mb-4')
                
                with ui.row().classes('w-full gap-2'):
                    # Update button
                    update_btn = ui.button(
                        '💾 Update Supplier',
                        on_click=lambda: handle_update(
                            supplier["id"],
                            {
                                "company_name": edit_company.value,
                                "contact_name": edit_contact.value,
                                "phone": edit_phone.value,
                                "email": edit_email.value,
                                "address": edit_address.value,
                            },
                            update_btn,
                            on_change
                        )
                    ).classes('flex-1 bg-blue-500 text-white')
                    
                    # Delete button
                    delete_btn = ui.button(
                        '🗑 Delete Supplier',
                        on_click=lambda: show_delete_confirmation(
                            supplier,
                            delete_btn,
                            on_change
                        )
                    ).classes('flex-1 bg-red-500 text-white')
        
        # Load initial supplier
        load_supplier_details()
        
        # Reload on selection change
        selected_key.on_value_change(lambda e: load_supplier_details())


def handle_update(
    supplier_id: str,
    data: Dict[str, Any],
    update_btn: Any,
    on_change: Optional[Callable] = None
):
    """Handle supplier update
    
    Args:
        supplier_id: Supplier ID
        data: Updated data
        update_btn: Update button instance
        on_change: Callback after update
    """
    try:
        update_btn.disable()
        update_btn.text = '⏳ Updating...'
        
        if update_supplier(supplier_id, data):
            ui.notify('Supplier Updated', type='positive', position='top')
            
            if on_change:
                on_change()
        else:
            ui.notify('Failed to update supplier', type='error', position='top')
    
    except Exception as e:
        ui.notify(f'Update error: {e}', type='error', position='top')
    
    finally:
        update_btn.enable()
        update_btn.text = '💾 Update Supplier'


def show_delete_confirmation(
    supplier: Dict[str, Any],
    delete_btn: Any,
    on_change: Optional[Callable] = None
):
    """Show delete confirmation dialog
    
    Args:
        supplier: Supplier data
        delete_btn: Delete button instance
        on_change: Callback after delete
    """
    with ui.dialog() as dialog, ui.card().classes('p-4 min-w-[400px]'):
        ui.label('Confirm Delete').classes('text-xl font-bold mb-4')
        
        ui.label('Are you sure you want to delete this supplier?').classes('mb-4')
        
        # Supplier info
        with ui.card().classes('w-full p-3 bg-gray-50 mb-4'):
            ui.label(f"Code: {supplier.get('supplier_code', '')}").classes('font-mono')
            ui.label(f"Name: {supplier.get('company_name', '')}").classes('font-semibold')
        
        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).props('flat')
            
            ui.button(
                'Yes, Delete',
                on_click=lambda: handle_delete(
                    supplier["id"],
                    dialog,
                    delete_btn,
                    on_change
                )
            ).classes('bg-red-500 text-white')
    
    dialog.open()


def handle_delete(
    supplier_id: str,
    dialog: Any,
    delete_btn: Any,
    on_change: Optional[Callable] = None
):
    """Handle supplier delete
    
    Args:
        supplier_id: Supplier ID
        dialog: Dialog instance
        delete_btn: Delete button instance
        on_change: Callback after delete
    """
    try:
        delete_btn.disable()
        delete_btn.text = '⏳ Deleting...'
        
        if delete_supplier(supplier_id):
            ui.notify('Supplier Deleted', type='positive', position='top')
            dialog.close()
            
            if on_change:
                on_change()
        else:
            ui.notify('Failed to delete supplier', type='error', position='top')
    
    except Exception as e:
        ui.notify(f'Delete error: {e}', type='error', position='top')
    
    finally:
        delete_btn.enable()
        delete_btn.text = '🗑 Delete Supplier'


def show_add_supplier_form(
    container: Optional[Any] = None,
    on_success: Optional[Callable] = None
):
    """Display add supplier form
    
    Args:
        container: NiceGUI container
        on_success: Callback after successful add
    """
    target = container or ui.column()
    
    with target:
        ui.label('➕ Add Supplier').classes('text-xl font-bold mb-4')
        
        with ui.card().classes('w-full p-4'):
            company_name = ui.input(
                'Supplier Name *',
                placeholder='Enter company name'
            ).classes('w-full mb-2')
            
            contact_name = ui.input(
                'Contact Person',
                placeholder='Enter contact person name'
            ).classes('w-full mb-2')
            
            phone = ui.input(
                'Phone',
                placeholder='Enter phone number'
            ).classes('w-full mb-2')
            
            email = ui.input(
                'Email',
                placeholder='Enter email address'
            ).classes('w-full mb-2')
            
            address = ui.textarea(
                'Address',
                placeholder='Enter address'
            ).classes('w-full mb-4')
            
            # Submit button
            submit_btn = ui.button(
                '💾 Save Supplier',
                on_click=lambda: handle_add(
                    company_name.value,
                    phone.value,
                    address.value,
                    email.value,
                    contact_name.value,
                    company_name,
                    submit_btn,
                    on_success
                )
            ).classes('w-full bg-primary text-white font-semibold')


def handle_add(
    company_name: str,
    phone: str,
    address: str,
    email: str,
    contact_name: str,
    company_input: Any,
    submit_btn: Any,
    on_success: Optional[Callable] = None
):
    """Handle add supplier
    
    Args:
        company_name: Company name
        phone: Phone number
        address: Address
        email: Email address
        contact_name: Contact person
        company_input: Company name input
        submit_btn: Submit button
        on_success: Callback after successful add
    """
    try:
        # Validation
        if not company_name:
            ui.notify('Please enter the Supplier Name.', type='warning', position='top')
            return
        
        # Disable button
        submit_btn.disable()
        submit_btn.text = '⏳ Saving...'
        
        # Add supplier
        result = add_supplier(
            company_name=company_name,
            phone=phone,
            address=address,
            email=email,
            contact_name=contact_name
        )
        
        if result is not None:
            ui.notify('Supplier Saved Successfully!', type='positive', position='top')
            
            # Clear form
            company_input.value = ''
            
            # Call callback
            if on_success:
                on_success()
        
    except Exception as e:
        ui.notify(f'Error saving supplier: {e}', type='error', position='top')
    
    finally:
        submit_btn.enable()
        submit_btn.text = '💾 Save Supplier'


# ----------------------------------------------------------
# MAIN RUN FUNCTION
# ----------------------------------------------------------

def run(container: Optional[Any] = None):
    """Main page entry point
    
    Args:
        container: NiceGUI container to render in
    """
    target = container or ui.column()
    
    with target:
        page_title('🏭 Supplier Management')
        
        # Supplier List
        page_header('📋 Supplier List')
        
        suppliers = get_suppliers()
        
        show_supplier_table(suppliers, target)
        
        # Edit / Delete section
        ui.separator().classes('my-4')
        show_edit_delete_section(suppliers, target, on_change=lambda: run(target))
        
        # Add supplier section
        ui.separator().classes('my-4')
        show_add_supplier_form(target, on_success=lambda: run(target))


# ==========================================================
# ADVANCED SUPPLIER MANAGEMENT
# ==========================================================

def run_advanced(container: Optional[Any] = None):
    """Advanced supplier management with tabs
    
    Args:
        container: NiceGUI container to render in
    """
    target = container or ui.column()
    
    with target:
        page_title('🏭 Supplier Management')
        
        with ui.tabs().classes('w-full mb-4') as tabs:
            tab_list = ui.tab('Supplier List', icon='list')
            tab_add = ui.tab('Add Supplier', icon='add')
            tab_edit = ui.tab('Edit/Delete', icon='edit')
        
        with ui.tab_panels(tabs, value=tab_list).classes('w-full'):
            with ui.tab_panel(tab_list):
                suppliers = get_suppliers()
                show_supplier_table(suppliers)
            
            with ui.tab_panel(tab_add):
                show_add_supplier_form()
            
            with ui.tab_panel(tab_edit):
                suppliers = get_suppliers()
                show_edit_delete_section(suppliers)


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    run()
