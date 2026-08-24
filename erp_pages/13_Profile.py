# ==============================================================================
# erp_pages/13_Profile.py
# ERP ENTERPRISE
# MULTI-TENANT USER PROFILE
# NICE GUI VERSION
#
# Responsibilities:
# - Current user profile
# - Tenant context
# - Account status
# - Password change
#
# IMPORTANT:
# - User can only view their own profile
# - Tenant context is READ-ONLY here
# - Password change is handled by auth.change_password()
# ==============================================================================

from typing import Dict, Any, Optional
from nicegui import ui

from auth import (
    require_login,
    change_password,
    get_current_user,
    get_current_tenant_context,
    get_current_tenant_role,
    TENANT_ROLE_MAP,
)


# ==============================================================================
# HELPERS
# ==============================================================================

def safe_value(value: Any, default: str = "—") -> Any:
    """Return a display-safe value.
    
    Args:
        value: Value to check
        default: Default value if None or empty
    
    Returns:
        Safe display value
    """
    if value is None:
        return default
    
    if isinstance(value, str) and not value.strip():
        return default
    
    return value


def tenant_role_name(role: str) -> str:
    """Convert tenant role key into display name.
    
    Args:
        role: Tenant role key
    
    Returns:
        Display name
    """
    if not role:
        return "—"
    
    return TENANT_ROLE_MAP.get(role, str(role).title())


# ==============================================================================
# PROFILE HEADER
# ==============================================================================

def render_profile_header(user: Dict[str, Any], container: Optional[Any] = None):
    """Render basic account information.
    
    Args:
        user: Current user dictionary
        container: NiceGUI container
    """
    target = container or ui.column()
    
    with target:
        ui.label('👤 My Profile').classes('text-3xl font-bold mb-2')
        ui.label('Manage your personal account and security settings.').classes(
            'text-gray-500 mb-4'
        )
        ui.separator().classes('my-4')
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # Account column
            with ui.card().classes('p-4 flex-1 min-w-[300px]'):
                ui.label('👤 Account').classes('text-xl font-bold mb-4')
                
                with ui.column().classes('gap-2'):
                    ui.label('Username:').classes('font-semibold')
                    ui.label(safe_value(user.get('username'))).classes('text-gray-700')
                    
                    ui.separator().classes('my-1')
                    
                    ui.label('Full Name:').classes('font-semibold')
                    ui.label(safe_value(user.get('full_name'))).classes('text-gray-700')
                    
                    ui.separator().classes('my-1')
                    
                    ui.label('System Role:').classes('font-semibold')
                    ui.label(safe_value(user.get('role'))).classes('text-gray-700')
            
            # Status column
            with ui.card().classes('p-4 flex-1 min-w-[300px]'):
                ui.label('🔐 Status').classes('text-xl font-bold mb-4')
                
                is_active = bool(user.get('is_active', False))
                
                if is_active:
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('check_circle').classes('text-green-500')
                        ui.label('Account Active').classes('text-green-700 font-semibold')
                else:
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon('error').classes('text-red-500')
                        ui.label('Account Inactive').classes('text-red-700 font-semibold')
                
                ui.label('User ID:').classes('font-semibold mt-4')
                ui.label(str(safe_value(user.get('id')))).classes(
                    'font-mono text-gray-700'
                )


# ==============================================================================
# TENANT CONTEXT
# ==============================================================================

def render_tenant_context(
    user: Dict[str, Any],
    tenant_context: Dict[str, Any],
    container: Optional[Any] = None
):
    """Display current Multi-Tenant context.
    
    READ ONLY.
    
    Profile page must never allow a user to arbitrarily change:
        shop_id, branch_id, tenant_role
    
    Those values are controlled by the authorization layer.
    
    Args:
        user: Current user dictionary
        tenant_context: Tenant context dictionary
        container: NiceGUI container
    """
    target = container or ui.column()
    
    with target:
        ui.separator().classes('my-4')
        ui.label('🏢 Tenant Context').classes('text-2xl font-bold mb-4')
        
        tenant_role = user.get("tenant_role") or get_current_tenant_role()
        
        shop_id = tenant_context.get("shop_id")
        branch_id = tenant_context.get("branch_id")
        
        shop_name = tenant_context.get("shop_name") or user.get("shop_name")
        shop_code = tenant_context.get("shop_code")
        
        branch_name = tenant_context.get("branch_name") or user.get("branch_name")
        branch_code = tenant_context.get("branch_code")
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # Tenant Role
            with ui.card().classes('p-4 flex-1 min-w-[250px]'):
                ui.label('🏷️ Tenant Role').classes('font-bold mb-2')
                ui.label(tenant_role_name(tenant_role)).classes('text-lg')
            
            # Shop
            with ui.card().classes('p-4 flex-1 min-w-[250px]'):
                ui.label('🏪 Shop').classes('font-bold mb-2')
                ui.label(safe_value(shop_name)).classes('text-lg')
                
                if shop_code:
                    ui.label(f'Code: {shop_code}').classes('text-sm text-gray-500')
                
                if shop_id is not None:
                    ui.label(f'Shop ID: {shop_id}').classes(
                        'text-sm text-gray-500 font-mono'
                    )
            
            # Branch
            with ui.card().classes('p-4 flex-1 min-w-[250px]'):
                ui.label('🏬 Branch').classes('font-bold mb-2')
                ui.label(safe_value(branch_name)).classes('text-lg')
                
                if branch_code:
                    ui.label(f'Code: {branch_code}').classes('text-sm text-gray-500')
                
                if branch_id is not None:
                    ui.label(f'Branch ID: {branch_id}').classes(
                        'text-sm text-gray-500 font-mono'
                    )
        
        ui.label(
            '🔒 Tenant assignment is controlled by the authorization and User Management system.'
        ).classes('text-sm text-gray-500 mt-2')


# ==============================================================================
# PASSWORD CHANGE
# ==============================================================================

def render_change_password(
    user: Dict[str, Any],
    container: Optional[Any] = None
):
    """Render secure password change form.
    
    Args:
        user: Current user dictionary
        container: NiceGUI container
    """
    target = container or ui.column()
    
    with target:
        ui.separator().classes('my-4')
        ui.label('🔐 Change Password').classes('text-2xl font-bold mb-2')
        ui.label('Change the password for your current account.').classes(
            'text-gray-500 mb-4'
        )
        
        with ui.card().classes('w-full max-w-md p-4'):
            current_password = ui.input(
                'Current Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-4')
            
            new_password = ui.input(
                'New Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-4')
            
            confirm_password = ui.input(
                'Confirm New Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-4')
            
            # Password strength indicator
            strength_container = ui.column().classes('w-full mb-4')
            
            new_password.on_value_change(
                lambda e: update_password_strength(strength_container, e.value)
            )
            
            # Submit button
            submit_button = ui.button(
                '💾 Change Password',
                on_click=lambda: handle_password_change(
                    user,
                    current_password.value,
                    new_password.value,
                    confirm_password.value,
                    current_password,
                    new_password,
                    confirm_password,
                    submit_button
                )
            ).classes('w-full bg-primary text-white font-semibold')


def update_password_strength(container: Any, password: str):
    """Update password strength indicator.
    
    Args:
        container: Container to update
        password: Password to check
    """
    container.clear()
    
    if not password:
        return
    
    with container:
        # Calculate strength
        strength = 0
        feedback = []
        
        if len(password) >= 6:
            strength += 1
        else:
            feedback.append("At least 6 characters")
        
        if len(password) >= 12:
            strength += 1
        
        if any(c.isupper() for c in password):
            strength += 1
        else:
            feedback.append("Add uppercase letter")
        
        if any(c.isdigit() for c in password):
            strength += 1
        else:
            feedback.append("Add number")
        
        if any(c in "!@#$%^&*" for c in password):
            strength += 1
        else:
            feedback.append("Add special character")
        
        # Display strength
        if strength <= 2:
            color = 'red'
            label = 'Weak'
        elif strength <= 4:
            color = 'orange'
            label = 'Medium'
        else:
            color = 'green'
            label = 'Strong'
        
        with ui.row().classes('items-center gap-2'):
            ui.label('Password Strength:').classes('text-sm font-semibold')
            ui.badge(label).classes(f'bg-{color}-100 text-{color}-700')
        
        if feedback:
            with ui.column().classes('gap-1 mt-2'):
                for item in feedback:
                    ui.label(f'• {item}').classes('text-sm text-gray-500')


def handle_password_change(
    user: Dict[str, Any],
    current_password: str,
    new_password: str,
    confirm_password: str,
    current_input: Any,
    new_input: Any,
    confirm_input: Any,
    submit_button: Any
):
    """Handle password change submission.
    
    Args:
        user: Current user dictionary
        current_password: Current password value
        new_password: New password value
        confirm_password: Confirm password value
        current_input: Current password input component
        new_input: New password input component
        confirm_input: Confirm password input component
        submit_button: Submit button component
    """
    try:
        # Disable button during submission
        submit_button.disable()
        submit_button.text = '⏳ Changing Password...'
        
        # ----------------------------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------------------------
        
        if not current_password:
            ui.notify('Current password is required.', type='error', position='top')
            return
        
        if not new_password:
            ui.notify('New password is required.', type='error', position='top')
            return
        
        if not confirm_password:
            ui.notify('Please confirm the new password.', type='error', position='top')
            return
        
        if new_password != confirm_password:
            ui.notify('New passwords do not match.', type='error', position='top')
            return
        
        if len(new_password) < 6:
            ui.notify('New password must be at least 6 characters.', type='error', position='top')
            return
        
        if current_password == new_password:
            ui.notify(
                'New password must be different from current password.',
                type='error',
                position='top'
            )
            return
        
        # ----------------------------------------------------------------------
        # USER ID
        # ----------------------------------------------------------------------
        
        user_id = user.get("id")
        
        if not user_id:
            ui.notify('Unable to identify the current user.', type='error', position='top')
            return
        
        # ----------------------------------------------------------------------
        # CHANGE PASSWORD
        # ----------------------------------------------------------------------
        
        success, message = change_password(
            user_id,
            current_password,
            new_password,
        )
        
        if success:
            # Clear inputs
            current_input.value = ''
            new_input.value = ''
            confirm_input.value = ''
            
            # Show success dialog
            with ui.dialog() as dialog, ui.card().classes('p-4'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('check_circle').classes('text-green-500 text-2xl')
                    ui.label('Success').classes('text-xl font-bold')
                
                ui.label(message).classes('mb-4')
                
                ui.button('OK', on_click=dialog.close).classes(
                    'w-full bg-green-500 text-white'
                )
            
            dialog.open()
        
        else:
            ui.notify(message, type='error', position='top', timeout=5000)
    
    except Exception as e:
        ui.notify(f'Password change error: {e}', type='error', position='top')
    
    finally:
        # Re-enable button
        submit_button.enable()
        submit_button.text = '💾 Change Password'


# ==============================================================================
# SECURITY INFORMATION
# ==============================================================================

def render_security_information(
    user: Dict[str, Any],
    container: Optional[Any] = None
):
    """Basic security information.
    
    No sensitive password information is displayed.
    
    Args:
        user: Current user dictionary
        container: NiceGUI container
    """
    target = container or ui.column()
    
    with target:
        ui.separator().classes('my-4')
        ui.label('🛡️ Security').classes('text-2xl font-bold mb-4')
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
            with ui.card().classes('p-4 flex-1 min-w-[250px]'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('lock').classes('text-gray-500')
                    ui.label('Password:').classes('font-semibold')
                    ui.label('Protected').classes('text-gray-700')
                
                ui.label(
                    'Your password is stored as a secure password hash.'
                ).classes('text-sm text-gray-500')
            
            with ui.card().classes('p-4 flex-1 min-w-[250px]'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('security').classes('text-gray-500')
                    ui.label('Session:').classes('font-semibold')
                    ui.label('Active').classes('text-gray-700')
                
                ui.label(
                    'Your session is protected by the ERP authentication system.'
                ).classes('text-sm text-gray-500')


# ==============================================================================
# MAIN PAGE
# ==============================================================================

def run(container: Optional[Any] = None):
    """Main page entry point.
    
    Args:
        container: NiceGUI container to render in
    """
    target = container or ui.column()
    
    with target:
        # ----------------------------------------------------------------------
        # LOGIN REQUIRED
        # ----------------------------------------------------------------------
        
        require_login()
        
        # ----------------------------------------------------------------------
        # CURRENT USER
        # ----------------------------------------------------------------------
        
        user = get_current_user()
        
        if not user:
            with ui.card().classes('w-full p-4 bg-red-50'):
                ui.label('Unable to load the current user profile.').classes(
                    'text-red-700'
                )
            return
        
        # ----------------------------------------------------------------------
        # TENANT CONTEXT
        # ----------------------------------------------------------------------
        
        tenant_context = get_current_tenant_context() or {}
        
        # ----------------------------------------------------------------------
        # PAGE
        # ----------------------------------------------------------------------
        
        render_profile_header(user, target)
        render_tenant_context(user, tenant_context, target)
        render_change_password(user, target)
        render_security_information(user, target)


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    run()
