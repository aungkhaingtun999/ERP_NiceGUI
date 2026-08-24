# ==========================================
# config.py
# Production Ready Configuration
# NICE GUI VERSION
# ==========================================

from pathlib import Path
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from nicegui import app

# Load environment variables
load_dotenv()

# ==============================================================================
# LOGGER SETUP
# ==============================================================================

logger = logging.getLogger(__name__)

# ==========================================
# APP INFORMATION
# ==========================================

APP_NAME = "AI POS System"
APP_VERSION = "1.0.0"

COMPANY_NAME = "My Store"

CURRENCY = "MMK"

TIMEZONE = "Asia/Yangon"

DATE_FORMAT = "%d-%m-%Y"

DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"

# ==========================================
# SUPABASE CONFIGURATION
# ==========================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-anon-key-here")

# ==========================================
# TIMEZONE MANAGEMENT
# ==========================================

TIMEZONE_OPTIONS = {
    "Myanmar 🇲🇲": "Asia/Yangon",
    "Thailand 🇹🇭": "Asia/Bangkok",
    "Mongolia 🇲🇳": "Asia/Ulaanbaatar",
    "Japan 🇯🇵": "Asia/Tokyo",
    "Singapore 🇸🇬": "Asia/Singapore",
    "China 🇨🇳": "Asia/Shanghai",
    "UTC 🌐": "UTC"
}

DEFAULT_TIMEZONE = "Asia/Yangon"

# Auto browser/device timezone
AUTO_TIMEZONE = True

# ==========================================
# ROOT PATH
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

PAGES_DIR = BASE_DIR / "pages"
UTILS_DIR = BASE_DIR / "utils"
SQL_DIR = BASE_DIR / "sql"
LOCALE_DIR = BASE_DIR / "locale"
RECEIPT_DIR = BASE_DIR / "receipts"
LOG_DIR = BASE_DIR / "logs"
EXPORT_DIR = BASE_DIR / "exports"
CONFIG_DIR = BASE_DIR / "config"

# Auto Create Folder
for folder in [RECEIPT_DIR, LOG_DIR, EXPORT_DIR, CONFIG_DIR]:
    folder.mkdir(exist_ok=True)

# ==========================================
# USER ROLES
# ==========================================

ROLE_ADMIN = "Admin"
ROLE_MANAGER = "Manager"
ROLE_CASHIER = "Cashier"

ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER]

# Role IDs (for database)
ROLE_IDS = {
    ROLE_ADMIN: 1,
    ROLE_MANAGER: 2,
    ROLE_CASHIER: 3,
}

# ==========================================
# LANGUAGES
# ==========================================

LANG_MY = "မြန်မာ"
LANG_EN = "English"

LANGUAGES = [LANG_MY, LANG_EN]

DEFAULT_LANGUAGE = LANG_EN

# ==========================================
# RECEIPT
# ==========================================

RECEIPT_PREFIX = "RCP"

STORE_FOOTER = "Thank you. Please come again."

# ==========================================
# INVENTORY
# ==========================================

DEFAULT_MINIMUM_STOCK = 5

LOW_STOCK_COLOR = "red"

# ==========================================
# SALES
# ==========================================

DEFAULT_TAX = 0.0

ALLOW_NEGATIVE_STOCK = False

DEFAULT_PAYMENT_METHOD = "CASH"

PAYMENT_METHODS = [
    "CASH",
    "KBZPay",
    "WavePay",
    "AYA Pay",
    "CB Pay",
    "Bank Transfer"
]

# ==========================================
# REPORTS
# ==========================================

TOP_PRODUCT_LIMIT = 10

RECENT_SALES_LIMIT = 20

# ==========================================
# DASHBOARD
# ==========================================

CHART_HEIGHT = 350

# ==========================================
# SESSION STATE MANAGEMENT
# ==========================================

class SessionManager:
    """Central session state manager for NiceGUI"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.defaults = SESSION_DEFAULTS.copy()
    
    def get_session(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Get or create session for client"""
        if client_id is None:
            # Try to get current client from NiceGUI context
            try:
                from nicegui import context
                client_id = context.client.id if context.client else "default"
            except Exception:
                client_id = "default"
        
        if client_id not in self._sessions:
            self._sessions[client_id] = self._create_default_session()
        
        return self._sessions[client_id]
    
    def _create_default_session(self) -> Dict[str, Any]:
        """Create new session with default values"""
        session = {}
        
        for key, value in self.defaults.items():
            if isinstance(value, list):
                session[key] = value.copy()
            elif isinstance(value, dict):
                session[key] = value.copy()
            else:
                session[key] = value
        
        return session
    
    def get(self, key: str, default: Any = None, client_id: Optional[str] = None) -> Any:
        """Get value from session"""
        session = self.get_session(client_id)
        return session.get(key, default)
    
    def set(self, key: str, value: Any, client_id: Optional[str] = None):
        """Set value in session"""
        session = self.get_session(client_id)
        session[key] = value
    
    def update(self, updates: Dict[str, Any], client_id: Optional[str] = None):
        """Update multiple values in session"""
        session = self.get_session(client_id)
        session.update(updates)
    
    def clear(self, client_id: Optional[str] = None):
        """Clear session"""
        session = self.get_session(client_id)
        session.clear()
        session.update(self._create_default_session())
    
    def reset(self, client_id: Optional[str] = None, keep_language: bool = True):
        """Reset session to defaults"""
        session = self.get_session(client_id)
        language = session.get("language", DEFAULT_LANGUAGE) if keep_language else DEFAULT_LANGUAGE
        
        session.clear()
        session.update(self._create_default_session())
        
        if keep_language:
            session["language"] = language
    
    def delete(self, client_id: str):
        """Delete session for client"""
        if client_id in self._sessions:
            del self._sessions[client_id]

# Global session manager instance
session_manager = SessionManager()

# ==========================================
# SESSION DEFAULTS
# ==========================================

SESSION_DEFAULTS = {
    "user": None,
    "role": ROLE_CASHIER,
    "language": DEFAULT_LANGUAGE,
    "cart": [],
    "receipt": None,
    "receipt_items": [],
    "sale_id": None,
    "logged_in": False,
    "theme": "light",
    "company": COMPANY_NAME,
    
    # Integrity Check Session States
    "integrity_results": None,
    "last_integrity_run": None,
    "active_page": "1_POS"
}

# Update session manager defaults
session_manager.defaults = SESSION_DEFAULTS.copy()

# ==========================================
# INIT SESSION
# ==========================================

def init_session(client_id: Optional[str] = None):
    """Initialize session for client"""
    return session_manager.get_session(client_id)

# ==========================================
# RESET SESSION
# ==========================================

def reset_session(client_id: Optional[str] = None):
    """Reset session for client"""
    session_manager.reset(client_id)

# ==========================================
# PAGE CONFIG
# ==========================================

PAGE_CONFIG = {
    "page_title": APP_NAME,
    "page_icon": "🛒",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "dark_mode": False,
}

# NiceGUI specific configuration
NICEGUI_CONFIG = {
    "title": APP_NAME,
    "favicon": "🛒",
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", 8080)),
    "reload": DEBUG,
    "show": True,
    "uvicorn_logging_level": "info" if DEBUG else "warning",
}

# ==========================================
# MENU
# ==========================================

ADMIN_MENU = [
    "Dashboard",
    "POS",
    "Inventory",
    "Receipt",
    "Reports",
    "Users",
    "Refund",
    "Integrity Check"
]

MANAGER_MENU = [
    "Dashboard",
    "POS",
    "Inventory",
    "Reports",
    "Integrity Check"
]

CASHIER_MENU = [
    "POS",
    "Receipt",
    "Refund",
    "Integrity Check"
]

# Menu with page IDs for routing
MENU_WITH_ROUTES = {
    ROLE_ADMIN: [
        ("Dashboard", "3_Admin_Dashboard"),
        ("POS", "1_POS"),
        ("Inventory", "2_Inventory"),
        ("Receipt", "2_Receipt"),
        ("Reports", "3_Reports"),
        ("Users", "4_Users"),
        ("Refund", "5_Refund"),
        ("Integrity Check", "14_Integrity"),
    ],
    ROLE_MANAGER: [
        ("Dashboard", "3_Admin_Dashboard"),
        ("POS", "1_POS"),
        ("Inventory", "2_Inventory"),
        ("Reports", "3_Reports"),
        ("Integrity Check", "14_Integrity"),
    ],
    ROLE_CASHIER: [
        ("POS", "1_POS"),
        ("Receipt", "2_Receipt"),
        ("Refund", "5_Refund"),
        ("Integrity Check", "14_Integrity"),
    ],
}

# ==========================================
# INTEGRITY CHECK CONFIGURATION
# ==========================================

# FIFO Cost Alert Threshold
FIFO_DEFAULT_COST_ALERT = 1.00

# Max days to check for FIFO data quality
FIFO_CHECK_DAYS = 30

# Enable/Disable specific checks
ENABLE_DOUBLE_ENTRY_CHECK = True
ENABLE_SALES_PAYMENTS_CHECK = True
ENABLE_STOCK_LEDGER_CHECK = True
ENABLE_FIFO_STOCK_CHECK = True
ENABLE_SALES_ITEMS_CHECK = True
ENABLE_FIFO_DATA_QUALITY_CHECK = True

# ==========================================
# DEBUG
# ==========================================

DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# ==========================================
# GET SUPABASE CONFIG
# ==========================================

def get_supabase_config() -> Dict[str, str]:
    """Return Supabase configuration"""
    return {
        "url": SUPABASE_URL,
        "key": SUPABASE_KEY
    }

# ==========================================
# VALIDATE CONFIG
# ==========================================

def validate_config() -> List[str]:
    """Validate configuration settings"""
    errors = []
    
    if not SUPABASE_URL or SUPABASE_URL == "https://your-project.supabase.co":
        errors.append("SUPABASE_URL is not configured")
    
    if not SUPABASE_KEY or SUPABASE_KEY == "your-supabase-anon-key-here":
        errors.append("SUPABASE_KEY is not configured")
    
    return errors

# ==========================================
# CONFIGURATION FILE MANAGEMENT
# ==========================================

def save_config_to_file(config: Dict[str, Any], filename: str = "app_config.json"):
    """Save configuration to JSON file"""
    config_path = CONFIG_DIR / filename
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def load_config_from_file(filename: str = "app_config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    config_path = CONFIG_DIR / filename
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

# ==========================================
# THEME MANAGEMENT
# ==========================================

THEMES = {
    "light": {
        "primary": "#1976D2",
        "secondary": "#26A69A",
        "accent": "#9C27B0",
        "dark": False,
    },
    "dark": {
        "primary": "#90CAF9",
        "secondary": "#80CBC4",
        "accent": "#CE93D8",
        "dark": True,
    },
}

def get_theme(theme_name: str = "light") -> Dict[str, Any]:
    """Get theme configuration"""
    return THEMES.get(theme_name, THEMES["light"])

# ==========================================
# PRINT CONFIG (Debug only)
# ==========================================

if DEBUG:
    logger.info("=" * 50)
    logger.info("📋 ERP CONFIGURATION")
    logger.info("=" * 50)
    logger.info(f"✅ APP_NAME: {APP_NAME}")
    logger.info(f"✅ SUPABASE_URL: {SUPABASE_URL[:30]}..." if SUPABASE_URL else "❌ SUPABASE_URL: Not Set")
    logger.info(f"✅ SUPABASE_KEY: {SUPABASE_KEY[:15]}..." if SUPABASE_KEY else "❌ SUPABASE_KEY: Not Set")
    logger.info(f"✅ DEBUG: {DEBUG}")
    logger.info("=" * 50)
