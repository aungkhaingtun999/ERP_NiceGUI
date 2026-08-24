# ==============================================================================
# sidebar.py
# ERP ENTERPRISE SIDEBAR ENGINE
# Custom Router v30.12+
# Role Based Navigation
# NICE GUI VERSION
# ==============================================================================

from typing import Optional, Dict, Any, Callable
from nicegui import ui

from auth import (
    is_authenticated,
    logout,
    change_password,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_CASHIER,
)

from utils.notification import (
    show_notification_history
)


# ==============================================================================
# ERP MENU MASTER
# ==============================================================================

MENU = {
    ROLE_ADMIN: [
        ("🏠", "Dashboard", "3_Admin_Dashboard"),
        ("🛒", "POS", "1_POS"),
        ("📦", "Inventory", "2_Inventory"),
        ("📱", "Mobile Inventory", "2_Mobile_Inventory"),
        ("🧾", "Receipt", "2_Receipt"),
        ("🛍", "Purchase", "7_Purchase"),
        ("🔁", "Transfer", "8_Transfer"),
        ("👥", "Customers", "9_Customers"),
        ("🏭", "Suppliers", "10_Suppliers"),
        ("↩️", "Refund", "5_Refund"),
        ("✅", "Refund Approval", "6_Refund_Approval"),
        ("📊", "Refund Report", "6_Refund_Report"),
        ("📈", "Reports", "3_Reports"),
        ("💰", "Pricing Report", "11_Pricing_Report"),
        ("📥", "Price Import", "13_Price_Import"),
        ("🔐", "Integrity Check", "14_Integrity"),
        ("👤", "Users", "4_Users"),
        ("⚙️", "Settings", "12_Settings"),
        ("✅", "Settings Approval", "13_Settings_Approval"),
        ("👤", "My Profile", "__PROFILE__"),
        ("🧪", "System Test Center", "99_System_Test"),
    ],
    
    ROLE_MANAGER: [
        ("🏠", "Dashboard", "3_Admin_Dashboard"),
        ("🛒", "POS", "1_POS"),
        ("📦", "Inventory", "2_Inventory"),
        ("📱", "Mobile Inventory", "2_Mobile_Inventory"),
        ("🛍", "Purchase", "7_Purchase"),
        ("🔁", "Transfer", "8_Transfer"),
        ("👥", "Customers", "9_Customers"),
        ("🏭", "Suppliers", "10_Suppliers"),
        ("↩️", "Refund", "5_Refund"),
        ("✅", "Refund Approval", "6_Refund_Approval"),
        ("📊", "Refund Report", "6_Refund_Report"),
        ("📈", "Reports", "3_Reports"),
        ("💰", "Pricing Report", "11_Pricing_Report"),
        ("📥", "Price Import", "13_Price_Import"),
        ("🔐", "Integrity Check", "14_Integrity"),
        ("👤", "My Profile", "__PROFILE__"),
    ],
    
    ROLE_CASHIER: [
        ("🛒", "POS", "1_POS"),
        ("↩️", "Refund", "5_Refund"),
        ("💰", "Pricing Report", "11_Pricing_Report"),
        ("🔐", "Integrity Check", "14_Integrity"),
        ("👤", "My Profile", "13_Profile"),
    ],
}


# ==============================================================================
# SIDEBAR CLASS
# ==============================================================================

class ERPSidebar:
    """ERP Sidebar component for NiceGUI"""
    
    def __init__(
        self,
        session_state: Dict[str, Any],
        on_navigate: Callable[[str], None],
        on_logout: Callable[[], None]
    ):
        """
        Initialize sidebar
        
        Args:
            session_state: Shared session state dictionary
            on_navigate: Callback function for page navigation
            on_logout: Callback function for logout
        """
        self.session_state = session_state
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.drawer = None
        self.active_page = self.get_active_page()
        
    def get_active_page(self) -> str:
        """Get current active page"""
        if "active_page" not in self.session_state:
            user = self.session_state.get("user", {})
            
            if user.get("role_id") == ROLE_ADMIN:
                self.session_state["active_page"] = "3_Admin_Dashboard"
            else:
                self.session_state["active_page"] = "1_POS"
                
        return self.session_state.get("active_page", "1_POS")
    
    def get_user_display(self) -> Dict[str, str]:
        """Get user display information"""
        user = self.session_state.get("user", {})
        
        return {
            "name": user.get("full_name", "User"),
            "username": user.get("username", ""),
            "role": user.get("role", "Unknown"),
        }
    
    def render(self):
        """Render the complete sidebar"""
        if not is_authenticated():
            return
        
        user = self.session_state.get("user", {})
        role_id = user.get("role_id")
        
        # Create drawer
        with ui.left_drawer(
            value=True,
            bordered=True
        ).classes('bg-gray-50 w-72') as self.drawer:
            
            with ui.column().classes('w-full p-2 gap-1'):
                
                # Header
                self._render_header()
                
                # User Card
                self._render_user_card()
                
                # Notifications
                self._render_notifications()
                
                # Language Selector
                self._render_language_selector()
                
                # Navigation
                self._render_navigation(role_id)
                
                # System Status
                self._render_system_status()
                
                # Logout Button
                self._render_logout_button()
    
    def _render_header(self):
        """Render sidebar header"""
        with ui.column().classes('w-full items-center mb-2'):
            ui.label('🏭 Myanmar ERP').classes('text-2xl font-bold')
            ui.label('Enterprise Edition').classes('text-sm text-gray-500')
            ui.separator().classes('w-full my-2')
    
    def _render_user_card(self):
        """Render user information card"""
        info = self.get_user_display()
        
        with ui.card().classes('w-full bg-green-50 mb-2'):
            with ui.column().classes('w-full gap-1'):
                ui.label(f"👤 {info['name']}").classes('font-semibold')
                ui.label(f"Username: {info['username']}").classes('text-sm text-gray-600')
                ui.label(f"Role: {info['role']}").classes('text-sm text-gray-600')
        
        ui.separator().classes('w-full my-2')
    
    def _render_notifications(self):
        """Render notifications expander"""
        with ui.expansion(
            '🔔 Notifications',
            icon='notifications'
        ).classes('w-full mb-2') as expansion:
            with ui.column().classes('w-full p-2'):
                show_notification_history()
        
        ui.separator().classes('w-full my-2')
    
    def _render_language_selector(self):
        """Render language selector"""
        if "language" not in self.session_state:
            self.session_state["language"] = "English"
        
        language_options = ["English", "မြန်မာ"]
        
        ui.select(
            language_options,
            label='Language',
            value=self.session_state["language"],
            on_change=lambda e: self._change_language(e.value)
        ).classes('w-full mb-2')
        
        ui.separator().classes('w-full my-2')
    
    def _change_language(self, language: str):
        """Handle language change"""
        self.session_state["language"] = language
        # Reload current page with new language
        self.on_navigate(self.session_state.get("active_page", "1_POS"))
    
    def _render_navigation(self, role_id: str):
        """Render navigation menu"""
        ui.label('📂 Navigation').classes('font-bold text-lg mb-2')
        
        pages = MENU.get(role_id, [])
        
        with ui.column().classes('w-full gap-1'):
            for icon, title, page_id in pages:
                self._render_menu_item(icon, title, page_id)
        
        ui.separator().classes('w-full my-2')
    
    def _render_menu_item(
        self,
        icon: str,
        title: str,
        page_id: str
    ):
        """Render individual menu item"""
        is_active = self.active_page == page_id
        
        # Determine button styling
        if is_active:
            classes = 'w-full bg-blue-500 text-white font-semibold'
            icon_prefix = '✅'
        else:
            classes = 'w-full hover:bg-gray-200'
            icon_prefix = ''
        
        label = f"{icon_prefix} {icon} {title}".strip()
        
        # Create button
        ui.button(
            label,
            on_click=lambda pid=page_id: self._navigate(pid)
        ).props('flat align-left').classes(classes)
    
    def _navigate(self, page_id: str):
        """Handle navigation"""
        # Handle direct profile route
        if page_id == "__PROFILE__":
            self.session_state["active_page"] = "__PROFILE__"
        else:
            self.session_state["active_page"] = page_id
        
        self.active_page = page_id
        self.on_navigate(page_id)
    
    def _render_system_status(self):
        """Render system status indicators"""
        with ui.card().classes('w-full mb-2'):
            with ui.column().classes('w-full gap-1'):
                ui.label('🟢 System Online').classes('text-green-600 font-semibold')
                ui.label('Database: Connected').classes('text-xs text-gray-600')
                ui.label('Session: Active').classes('text-xs text-gray-600')
                ui.label('ERP Version: Enterprise').classes('text-xs text-gray-600')
        
        ui.separator().classes('w-full my-2')
    
    def _render_logout_button(self):
        """Render logout button"""
        ui.button(
            '🚪 Logout',
            on_click=self._handle_logout
        ).classes('w-full bg-red-500 text-white font-semibold')
    
    def _handle_logout(self):
        """Handle logout action"""
        logout()
        self.on_logout()


# ==============================================================================
# CHANGE PASSWORD DIALOG
# ==============================================================================

class ChangePasswordDialog:
    """Change password dialog component"""
    
    def __init__(self, session_state: Dict[str, Any]):
        self.session_state = session_state
        self.dialog = None
        
    def show(self):
        """Show change password dialog"""
        with ui.dialog() as self.dialog, ui.card().classes('w-96 p-4'):
            ui.label('🔐 Change Password').classes('text-xl font-bold mb-4')
            
            old_password = ui.input(
                'Current Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-2')
            
            new_password = ui.input(
                'New Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-2')
            
            confirm_password = ui.input(
                'Confirm New Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-4')
            
            def handle_change():
                self._process_password_change(
                    old_password.value,
                    new_password.value,
                    confirm_password.value
                )
            
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button(
                    'Cancel',
                    on_click=self.dialog.close
                ).props('flat')
                
                ui.button(
                    '💾 Change Password',
                    on_click=handle_change
                ).classes('bg-blue-500 text-white')
        
        self.dialog.open()
    
    def _process_password_change(
        self,
        old_password: str,
        new_password: str,
        confirm_password: str
    ):
        """Process password change request"""
        
        # Validation
        if not old_password:
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
        
        # Get current user ID
        user = self.session_state.get("user", {})
        user_id = user.get("id")
        
        if not user_id:
            ui.notify('Unable to identify the current user.', type='error', position='top')
            return
        
        # Change password
        success, message = change_password(
            user_id,
            old_password,
            new_password
        )
        
        # Show result
        if success:
            ui.notify(message, type='positive', position='top')
            ui.notify('🔐 Your password has been updated successfully.', type='info', position='top')
            self.dialog.close()
        else:
            ui.notify(message, type='error', position='top')


# ==============================================================================
# SIDEBAR FACTORY FUNCTION
# ==============================================================================

def show_sidebar(
    session_state: Dict[str, Any],
    on_navigate: Callable[[str], None],
    on_logout: Callable[[], None]
) -> ERPSidebar:
    """
    Create and render sidebar
    
    Args:
        session_state: Shared session state dictionary
        on_navigate: Callback for page navigation
        on_logout: Callback for logout
    
    Returns:
        ERPSidebar instance
    """
    if not is_authenticated():
        return None
    
    sidebar = ERPSidebar(
        session_state,
        on_navigate,
        on_logout
    )
    
    sidebar.render()
    
    return sidebar


# ==============================================================================
# PROFILE PAGE INTEGRATION
# ==============================================================================

def create_profile_section(
    session_state: Dict[str, Any],
    container: Any
):
    """Create profile page section with change password"""
    
    with container:
        with ui.card().classes('w-full max-w-md mx-auto'):
            ui.label('🔐 Change Password').classes('text-xl font-bold mb-4')
            
            old_password = ui.input(
                'Current Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-2')
            
            new_password = ui.input(
                'New Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-2')
            
            confirm_password = ui.input(
                'Confirm New Password',
                password=True,
                password_toggle_button=True
            ).classes('w-full mb-4')
            
            def handle_submit():
                _process_password_submit(
                    session_state,
                    old_password.value,
                    new_password.value,
                    confirm_password.value,
                    old_password,
                    new_password,
                    confirm_password
                )
            
            ui.button(
                '💾 Change Password',
                on_click=handle_submit
            ).classes('w-full bg-blue-500 text-white')


def _process_password_submit(
    session_state: Dict[str, Any],
    old_password: str,
    new_password: str,
    confirm_password: str,
    old_input: Any,
    new_input: Any,
    confirm_input: Any
):
    """Process password submission"""
    
    # Validation
    if not old_password:
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
    
    # Get current user ID
    user = session_state.get("user", {})
    user_id = user.get("id")
    
    if not user_id:
        ui.notify('Unable to identify the current user.', type='error', position='top')
        return
    
    # Change password
    success, message = change_password(
        user_id,
        old_password,
        new_password
    )
    
    # Show result
    if success:
        ui.notify(message, type='positive', position='top')
        ui.notify('🔐 Your password has been updated successfully.', type='info', position='top')
        
        # Clear inputs
        old_input.value = ''
        new_input.value = ''
        confirm_input.value = ''
    else:
        ui.notify(message, type='error', position='top')
