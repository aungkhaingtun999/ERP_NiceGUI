# ==============================================================================
# app.py
# ERP ENTERPRISE APPLICATION CONTROLLER
# SAFE PAGE ROUTER
# MULTI-TENANT READY
# NICE GUI VERSION
# ==============================================================================

import os
import sys
import importlib.util
from typing import Optional, Dict, Any

from nicegui import ui, app, Client
from nicegui.events import ValueChangeEventArguments

# ==============================================================================
# BASE PATH
# ==============================================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ==============================================================================
# ERP CORE
# ==============================================================================

import erp_core

# ==============================================================================
# AUTH
# ==============================================================================

from auth import (
    authenticate_user,
    get_current_user,
    logout_user,
)

# ==============================================================================
# PAGE ALIASES
# ==============================================================================

PAGE_ALIASES = {
    "PROFILE": "13_Profile",
    "__PROFILE__": "13_Profile",
}

# ==============================================================================
# SESSION MANAGEMENT
# ==============================================================================

class SessionState:
    """Manage per-client session state"""
    
    def __init__(self):
        self.user: Optional[Dict[str, Any]] = None
        self.active_page: str = "1_POS"
        self.language: str = "English"
        self.current_container: Optional[Any] = None
        self.sidebar_visible: bool = True

# Store session states per client
session_states: Dict[str, SessionState] = {}

def get_session(client: Client) -> SessionState:
    """Get or create session state for a client"""
    client_id = client.id
    if client_id not in session_states:
        session_states[client_id] = SessionState()
    return session_states[client_id]

# ==============================================================================
# PAGE LOADER
# ==============================================================================

def load_page(page_id: str, container: Any, session: SessionState):
    """Load and execute a page module"""
    
    # Normalize old page IDs
    page_id = PAGE_ALIASES.get(page_id, page_id)
    
    # Build page file path
    page_file = os.path.join(
        BASE_DIR,
        "erp_pages",
        f"{page_id}.py"
    )
    
    # File existence check
    if not os.path.exists(page_file):
        with container:
            ui.notify(
                f"Page file not found: {page_file}",
                type='error',
                position='top'
            )
        return
    
    try:
        module_name = f"erp_pages.dynamic_{page_id}"
        
        # Remove previous dynamic page module
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Load page specification
        spec = importlib.util.spec_from_file_location(module_name, page_file)
        
        if spec is None:
            raise ImportError(f"Cannot load page: {page_id}")
        
        # Create module
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        # Execute module
        spec.loader.exec_module(module)
        
        # Clear container
        container.clear()
        
        # Execute page with NiceGUI context
        with container:
            if hasattr(module, "run"):
                module.run()
            elif hasattr(module, "main"):
                module.main()
            else:
                ui.notify(
                    f"{page_id}.py has no run() or main()",
                    type='warning',
                    position='top'
                )
                
    except Exception as e:
        with container:
            ui.notify(
                f"Page Load Error: {e}",
                type='error',
                position='top'
            )
            with ui.expansion('Debug Trace', icon='bug_report').classes('w-full'):
                ui.code(str(e))

# ==============================================================================
# PAGE ROUTER
# ==============================================================================

def page_router(container: Any, session: SessionState):
    """Route to the appropriate page"""
    
    if not session.user:
        with container:
            ui.notify(
                "Please login first.",
                type='warning',
                position='top'
            )
        return
    
    # Current page
    page_id = session.active_page
    
    # Normalize legacy profile routes
    normalized_page = PAGE_ALIASES.get(page_id, page_id)
    
    if normalized_page != page_id:
        session.active_page = normalized_page
        page_id = normalized_page
    
    # Load normal ERP page
    load_page(page_id, container, session)

# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def create_login_page(container: Any, session: SessionState):
    """Create login page"""
    
    container.clear()
    
    with container:
        with ui.card().classes('w-96 mx-auto mt-20 p-6'):
            ui.label('Myanmar ERP Enterprise').classes('text-2xl font-bold text-center mb-4')
            ui.label('Login').classes('text-xl text-center mb-4')
            
            username_input = ui.input('Username').classes('w-full mb-2')
            password_input = ui.input('Password', password=True).classes('w-full mb-4')
            
            def handle_login():
                user = authenticate_user(
                    username_input.value,
                    password_input.value
                )
                
                if user:
                    session.user = user
                    ui.notify(
                        f"Welcome {user.get('name', 'User')}!",
                        type='positive',
                        position='top'
                    )
                    # Clear and show main app
                    main_container.clear()
                    create_main_app(main_container, session)
                else:
                    ui.notify(
                        "Invalid credentials",
                        type='error',
                        position='top'
                    )
            
            ui.button(
                'Login',
                on_click=handle_login
            ).classes('w-full bg-blue-500 text-white')

def create_sidebar(session: SessionState):
    """Create sidebar navigation"""
    
    # Define navigation pages
    pages = [
        ("1_POS", "Point of Sale", "point_of_sale"),
        ("2_Inventory", "Inventory", "inventory"),
        ("3_Sales", "Sales", "trending_up"),
        ("4_Purchase", "Purchase", "shopping_cart"),
        ("5_Finance", "Finance", "account_balance"),
        ("6_HR", "Human Resources", "people"),
        ("7_CRM", "CRM", "contacts"),
        ("8_Reports", "Reports", "assessment"),
        ("9_Settings", "Settings", "settings"),
        ("13_Profile", "Profile", "person"),
    ]
    
    # Create sidebar content
    with ui.left_drawer(value=session.sidebar_visible).classes('bg-gray-100') as drawer:
        with ui.column().classes('w-full p-2'):
            # Logo/Title
            ui.label('ERP Enterprise').classes('text-xl font-bold text-center w-full mb-4')
            
            # Navigation buttons
            for page_id, title, icon in pages:
                is_active = session.active_page == page_id
                
                button_classes = 'w-full text-left mb-1 p-2 rounded'
                if is_active:
                    button_classes += ' bg-blue-500 text-white'
                else:
                    button_classes += ' hover:bg-gray-200'
                
                ui.button(
                    title,
                    icon=icon,
                    on_click=lambda pid=page_id: navigate_to(pid, session)
                ).props('flat').classes(button_classes)
            
            ui.separator()
            
            # User info
            if session.user:
                with ui.card().classes('w-full p-2'):
                    ui.label(f"User: {session.user.get('name', 'Unknown')}")
                    ui.label(f"Role: {session.user.get('role', 'Unknown')}")
            
            # Logout button
            ui.button(
                'Logout',
                icon='logout',
                on_click=lambda: handle_logout(session)
            ).classes('w-full bg-red-500 text-white mt-4')

def navigate_to(page_id: str, session: SessionState):
    """Navigate to a specific page"""
    session.active_page = page_id
    
    # Clear main container and reload page
    if session.current_container:
        session.current_container.clear()
        page_router(session.current_container, session)

def handle_logout(session: SessionState):
    """Handle logout"""
    logout_user()
    session.user = None
    
    # Clear main container
    if session.current_container:
        session.current_container.clear()
        create_login_page(session.current_container, session)

# ==============================================================================
# MAIN APP
# ==============================================================================

# Global main container reference
main_container = None

def create_main_app(container: Any, session: SessionState):
    """Create main application layout"""
    
    session.current_container = container
    
    # Create sidebar
    create_sidebar(session)
    
    # Create main content area
    with container:
        with ui.column().classes('w-full h-full'):
            # Top bar
            with ui.row().classes('w-full items-center p-2 bg-white shadow'):
                ui.button(
                    icon='menu',
                    on_click=lambda: toggle_sidebar(session)
                ).props('flat')
                
                ui.label('Myanmar ERP Enterprise').classes('text-xl font-bold')
                
                ui.space()
                
                # Language selector
                ui.select(
                    ['English', 'Myanmar'],
                    value=session.language,
                    on_change=lambda e: change_language(e, session)
                ).classes('w-32')
            
            # Page content
            page_container = ui.column().classes('w-full p-4 flex-1')
            page_router(page_container, session)

def toggle_sidebar(session: SessionState):
    """Toggle sidebar visibility"""
    session.sidebar_visible = not session.sidebar_visible

def change_language(e: ValueChangeEventArguments, session: SessionState):
    """Change application language"""
    session.language = e.value
    # Reload current page with new language
    if session.current_container:
        session.current_container.clear()
        page_router(session.current_container, session)

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

@ui.page('/')
def main_page(client: Client):
    """Main application page"""
    
    # Get session state
    session = get_session(client)
    
    # Create main container
    global main_container
    main_container = ui.column().classes('w-full min-h-screen')
    
    # Check authentication
    if not session.user:
        create_login_page(main_container, session)
    else:
        create_main_app(main_container, session)

@ui.page('/login')
def login_page_route(client: Client):
    """Login page route"""
    
    session = get_session(client)
    
    # Create login container
    with ui.column().classes('w-full min-h-screen bg-gray-100'):
        create_login_page(ui.column(), session)

# ==============================================================================
# CLIENT CONNECTION HANDLING
# ==============================================================================

@app.on_connect
def handle_connect(client: Client):
    """Handle client connection"""
    # Initialize session state
    get_session(client)
    
    # Check for existing session/token
    current_user = get_current_user()
    if current_user:
        session = get_session(client)
        session.user = current_user

@app.on_disconnect
def handle_disconnect(client: Client):
    """Handle client disconnect"""
    # Clean up session state
    client_id = client.id
    if client_id in session_states:
        del session_states[client_id]

# ==============================================================================
# START SERVER
# ==============================================================================

if __name__ in {"__main__", "__mp_main__"}:
    # Configure NiceGUI
    ui.run(
        title='Myanmar ERP Enterprise',
        favicon='🏭',
        host='0.0.0.0',
        port=8080,
        reload=False,
        show=True,
        uvicorn_logging_level='info',
        dark=False,
    )
