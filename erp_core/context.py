# ==============================================================================
# erp_core/context.py
# ERP ENTERPRISE CONTEXT + CACHE MANAGER v31 - NiceGUI Version
#
# Responsibilities:
#
# - User Context
# - Warehouse Context
# - Transaction Context
# - ERP Global Cache Version Control
# - NiceGUI Session Management
#
# Used By:
#
# POS
# Inventory
# Pricing
# Settings
# Dashboard
#
# ==============================================================================

import uuid
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import os

# For NiceGUI, we'll use a custom session manager
# instead of Streamlit's st.session_state


# ==============================================================================
# SESSION STATE MANAGER FOR NICEGUI
# ==============================================================================

class NiceGUISession:
    """
    Simple session state manager for NiceGUI.
    Replaces Streamlit's st.session_state.
    """
    
    _sessions: Dict[str, Dict[str, Any]] = {}
    _current_session_id: Optional[str] = None
    
    @classmethod
    def init_session(cls, session_id: str = None) -> str:
        """Initialize a new session or get existing."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id not in cls._sessions:
            cls._sessions[session_id] = {}
        
        cls._current_session_id = session_id
        return session_id
    
    @classmethod
    def get_current_session(cls) -> Dict[str, Any]:
        """Get current session data."""
        if cls._current_session_id is None:
            cls.init_session()
        return cls._sessions.get(cls._current_session_id, {})
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a value from current session."""
        session = cls.get_current_session()
        return session.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set a value in current session."""
        session = cls.get_current_session()
        session[key] = value
        cls._sessions[cls._current_session_id] = session
    
    @classmethod
    def delete(cls, key: str) -> None:
        """Delete a value from current session."""
        session = cls.get_current_session()
        if key in session:
            del session[key]
            cls._sessions[cls._current_session_id] = session
    
    @classmethod
    def clear(cls) -> None:
        """Clear current session."""
        if cls._current_session_id:
            cls._sessions[cls._current_session_id] = {}
    
    @classmethod
    def clear_all(cls) -> None:
        """Clear all sessions."""
        cls._sessions.clear()
        cls._current_session_id = None
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all session data for current session."""
        return cls.get_current_session().copy()


# For backward compatibility with Streamlit
st = None  # Will be replaced by NiceGUISession


# ==============================================================================
# ERP CONTEXT
# ==============================================================================

@dataclass
class ERPContextData:
    """Data structure for ERP context."""
    user_id: Optional[str] = None
    warehouse_id: Optional[str] = None
    customer_id: Optional[str] = None
    supplier_id: Optional[str] = None
    transaction_id: str = None
    transaction_started_at: float = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.transaction_id is None:
            self.transaction_id = str(uuid.uuid4())
        if self.transaction_started_at is None:
            self.transaction_started_at = time.time()
        if self.permissions is None:
            self.permissions = []


class ERPContext:
    """
    ERP Context Manager for NiceGUI.
    Manages user, warehouse, and transaction context.
    """
    
    SESSION_KEY = "erp_context"
    
    def __init__(
        self,
        user_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        self.data = ERPContextData(
            user_id=user_id,
            warehouse_id=warehouse_id,
            customer_id=customer_id,
            supplier_id=supplier_id,
            session_id=session_id or NiceGUISession._current_session_id,
        )
        self._save()
    
    def _save(self) -> None:
        """Save context to session."""
        NiceGUISession.set(self.SESSION_KEY, self)
    
    # --------------------------------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------------------------------
    
    @property
    def user_id(self) -> Optional[str]:
        return self.data.user_id
    
    @user_id.setter
    def user_id(self, value: Optional[str]) -> None:
        self.data.user_id = value
        self._save()
    
    @property
    def warehouse_id(self) -> Optional[str]:
        return self.data.warehouse_id
    
    @warehouse_id.setter
    def warehouse_id(self, value: Optional[str]) -> None:
        self.data.warehouse_id = value
        self._save()
    
    @property
    def customer_id(self) -> Optional[str]:
        return self.data.customer_id
    
    @customer_id.setter
    def customer_id(self, value: Optional[str]) -> None:
        self.data.customer_id = value
        self._save()
    
    @property
    def supplier_id(self) -> Optional[str]:
        return self.data.supplier_id
    
    @supplier_id.setter
    def supplier_id(self, value: Optional[str]) -> None:
        self.data.supplier_id = value
        self._save()
    
    @property
    def current_transaction_id(self) -> str:
        return self.data.transaction_id
    
    @property
    def transaction_started_at(self) -> float:
        return self.data.transaction_started_at
    
    @property
    def session_id(self) -> Optional[str]:
        return self.data.session_id
    
    @property
    def role(self) -> Optional[str]:
        return self.data.role
    
    @role.setter
    def role(self, value: Optional[str]) -> None:
        self.data.role = value
        self._save()
    
    @property
    def permissions(self) -> List[str]:
        return self.data.permissions
    
    @permissions.setter
    def permissions(self, value: List[str]) -> None:
        self.data.permissions = value
        self._save()
    
    # --------------------------------------------------------------------------
    # EXPORT CONTEXT
    # --------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Export context as dictionary."""
        return {
            "user_id": self.data.user_id,
            "warehouse_id": self.data.warehouse_id,
            "customer_id": self.data.customer_id,
            "supplier_id": self.data.supplier_id,
            "transaction_id": self.data.transaction_id,
            "transaction_started_at": self.data.transaction_started_at,
            "session_id": self.data.session_id,
            "role": self.data.role,
            "permissions": self.data.permissions,
        }
    
    def to_json(self) -> str:
        """Export context as JSON."""
        return json.dumps(self.to_dict(), default=str)
    
    # --------------------------------------------------------------------------
    # GET CURRENT CONTEXT
    # --------------------------------------------------------------------------
    
    @classmethod
    def get_current(cls) -> 'ERPContext':
        """Get current context from session."""
        context = NiceGUISession.get(cls.SESSION_KEY)
        
        if context is None:
            # Create new context
            context = cls(
                user_id=NiceGUISession.get("user_id"),
                warehouse_id=NiceGUISession.get("warehouse_id"),
                customer_id=NiceGUISession.get("customer_id"),
            )
            NiceGUISession.set(cls.SESSION_KEY, context)
        
        return context
    
    # --------------------------------------------------------------------------
    # SET CURRENT CONTEXT
    # --------------------------------------------------------------------------
    
    @classmethod
    def set_current(cls, context: 'ERPContext') -> None:
        """Set current context in session."""
        if isinstance(context, cls):
            NiceGUISession.set(cls.SESSION_KEY, context)
    
    # --------------------------------------------------------------------------
    # NEW TRANSACTION
    # --------------------------------------------------------------------------
    
    def rotate_transaction(self) -> str:
        """Generate a new transaction ID."""
        self.data.transaction_id = str(uuid.uuid4())
        self.data.transaction_started_at = time.time()
        self._save()
        return self.data.transaction_id
    
    # --------------------------------------------------------------------------
    # CONTEXT VALIDATION
    # --------------------------------------------------------------------------
    
    def is_valid(self) -> bool:
        """Check if context is valid."""
        return (
            self.data.user_id is not None and
            self.data.warehouse_id is not None
        )
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.data.permissions
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(p in self.data.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if user has all specified permissions."""
        return all(p in self.data.permissions for p in permissions)
    
    # --------------------------------------------------------------------------
    # CONTEXT FACTORY
    # --------------------------------------------------------------------------
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ERPContext':
        """Create context from dictionary."""
        context = cls(
            user_id=data.get("user_id"),
            warehouse_id=data.get("warehouse_id"),
            customer_id=data.get("customer_id"),
            supplier_id=data.get("supplier_id"),
        )
        if "role" in data:
            context.role = data["role"]
        if "permissions" in data:
            context.permissions = data["permissions"]
        return context


# ==============================================================================
# CACHE MANAGER
# ==============================================================================

class CacheVersion(str, Enum):
    """Cache version keys."""
    INVENTORY = "inventory_version"
    PRODUCT = "product_version"
    PRICING = "pricing_version"
    SETTINGS = "settings_version"
    SALES = "sales_version"
    CUSTOMER = "customer_version"
    SUPPLIER = "supplier_version"
    PURCHASE = "purchase_version"
    USER = "user_version"
    REPORT = "report_version"
    DASHBOARD = "dashboard_version"
    CATEGORY = "category_version"
    WAREHOUSE = "warehouse_version"


class CacheManager:
    """
    ERP Cache Manager for NiceGUI.
    Manages cache versioning for different domains.
    """
    
    VERSION_KEY = "erp_cache_versions"
    
    # Default versions
    DEFAULT_VERSIONS = {
        CacheVersion.INVENTORY: 1,
        CacheVersion.PRODUCT: 1,
        CacheVersion.PRICING: 1,
        CacheVersion.SETTINGS: 1,
        CacheVersion.SALES: 1,
        CacheVersion.CUSTOMER: 1,
        CacheVersion.SUPPLIER: 1,
        CacheVersion.PURCHASE: 1,
        CacheVersion.USER: 1,
        CacheVersion.REPORT: 1,
        CacheVersion.DASHBOARD: 1,
        CacheVersion.CATEGORY: 1,
        CacheVersion.WAREHOUSE: 1,
    }
    
    # --------------------------------------------------------------------------
    # INITIALIZE
    # --------------------------------------------------------------------------
    
    @classmethod
    def init(cls) -> None:
        """Initialize cache versions in session."""
        versions = NiceGUISession.get(cls.VERSION_KEY)
        
        if versions is None:
            versions = cls.DEFAULT_VERSIONS.copy()
            versions["updated_at"] = time.time()
            NiceGUISession.set(cls.VERSION_KEY, versions)
    
    # --------------------------------------------------------------------------
    # GET VERSION
    # --------------------------------------------------------------------------
    
    @classmethod
    def get_version(cls, key: str) -> int:
        """Get version for a specific cache key."""
        cls.init()
        versions = NiceGUISession.get(cls.VERSION_KEY)
        return versions.get(key, 1)
    
    @classmethod
    def get_all_versions(cls) -> Dict[str, Any]:
        """Get all cache versions."""
        cls.init()
        return NiceGUISession.get(cls.VERSION_KEY).copy()
    
    # --------------------------------------------------------------------------
    # INCREASE VERSION
    # --------------------------------------------------------------------------
    
    @classmethod
    def bump(cls, key: str) -> int:
        """Increment version for a specific cache key."""
        cls.init()
        versions = NiceGUISession.get(cls.VERSION_KEY)
        
        versions[key] = versions.get(key, 1) + 1
        versions["updated_at"] = time.time()
        
        NiceGUISession.set(cls.VERSION_KEY, versions)
        return versions[key]
    
    @classmethod
    def bump_version(cls, key: str) -> int:
        """Alias for bump."""
        return cls.bump(key)
    
    # --------------------------------------------------------------------------
    # DOMAIN-SPECIFIC CLEAR METHODS
    # --------------------------------------------------------------------------
    
    @classmethod
    def clear_inventory(cls) -> int:
        """Clear inventory cache."""
        return cls.bump(CacheVersion.INVENTORY)
    
    @classmethod
    def clear_products(cls) -> int:
        """Clear product cache."""
        return cls.bump(CacheVersion.PRODUCT)
    
    @classmethod
    def clear_pricing(cls) -> int:
        """Clear pricing cache."""
        return cls.bump(CacheVersion.PRICING)
    
    @classmethod
    def clear_settings(cls) -> int:
        """Clear settings cache."""
        return cls.bump(CacheVersion.SETTINGS)
    
    @classmethod
    def clear_sales(cls) -> int:
        """Clear sales cache."""
        return cls.bump(CacheVersion.SALES)
    
    @classmethod
    def clear_customers(cls) -> int:
        """Clear customer cache."""
        return cls.bump(CacheVersion.CUSTOMER)
    
    @classmethod
    def clear_suppliers(cls) -> int:
        """Clear supplier cache."""
        return cls.bump(CacheVersion.SUPPLIER)
    
    @classmethod
    def clear_purchases(cls) -> int:
        """Clear purchase cache."""
        return cls.bump(CacheVersion.PURCHASE)
    
    @classmethod
    def clear_users(cls) -> int:
        """Clear user cache."""
        return cls.bump(CacheVersion.USER)
    
    @classmethod
    def clear_reports(cls) -> int:
        """Clear report cache."""
        return cls.bump(CacheVersion.REPORT)
    
    @classmethod
    def clear_dashboard(cls) -> int:
        """Clear dashboard cache."""
        return cls.bump(CacheVersion.DASHBOARD)
    
    @classmethod
    def clear_categories(cls) -> int:
        """Clear category cache."""
        return cls.bump(CacheVersion.CATEGORY)
    
    @classmethod
    def clear_warehouses(cls) -> int:
        """Clear warehouse cache."""
        return cls.bump(CacheVersion.WAREHOUSE)
    
    # --------------------------------------------------------------------------
    # BULK CLEAR METHODS
    # --------------------------------------------------------------------------
    
    @classmethod
    def clear_all(cls) -> Dict[str, int]:
        """Clear all cache versions."""
        cls.init()
        versions = NiceGUISession.get(cls.VERSION_KEY)
        
        bumped = {}
        for key in cls.DEFAULT_VERSIONS:
            versions[key] = versions.get(key, 1) + 1
            bumped[key] = versions[key]
        
        versions["updated_at"] = time.time()
        NiceGUISession.set(cls.VERSION_KEY, versions)
        
        return bumped
    
    @classmethod
    def clear_domain(cls, domain: str) -> int:
        """Clear cache for a specific domain."""
        key_map = {
            "inventory": CacheVersion.INVENTORY,
            "product": CacheVersion.PRODUCT,
            "pricing": CacheVersion.PRICING,
            "settings": CacheVersion.SETTINGS,
            "sales": CacheVersion.SALES,
            "customer": CacheVersion.CUSTOMER,
            "supplier": CacheVersion.SUPPLIER,
            "purchase": CacheVersion.PURCHASE,
            "user": CacheVersion.USER,
            "report": CacheVersion.REPORT,
            "dashboard": CacheVersion.DASHBOARD,
            "category": CacheVersion.CATEGORY,
            "warehouse": CacheVersion.WAREHOUSE,
        }
        
        key = key_map.get(domain)
        if key:
            return cls.bump(key)
        return 0
    
    # --------------------------------------------------------------------------
    # CACHE KEY GENERATION
    # --------------------------------------------------------------------------
    
    @classmethod
    def generate_cache_key(cls, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key with version."""
        version = cls.get_version(prefix)
        key_parts = [prefix, str(version)]
        
        if args:
            key_parts.extend(str(arg) for arg in args)
        
        if kwargs:
            sorted_items = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_items)
        
        return "_".join(key_parts)
    
    @classmethod
    def is_valid(cls, key: str, prefix: str) -> bool:
        """Check if a cache key is still valid."""
        version = cls.get_version(prefix)
        return f"_{version}_" in key or key.startswith(f"{prefix}_{version}")


# ==============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ==============================================================================

def get_cache_version(key: str) -> int:
    """Legacy function to get cache version."""
    return CacheManager.get_version(key)


def bump_cache(key: str) -> int:
    """Legacy function to bump cache version."""
    return CacheManager.bump(key)


def bump_inventory_version() -> int:
    """Legacy function to bump inventory version."""
    return CacheManager.clear_inventory()


def bump_product_version() -> int:
    """Legacy function to bump product version."""
    return CacheManager.clear_products()


def bump_pricing_version() -> int:
    """Legacy function to bump pricing version."""
    return CacheManager.clear_pricing()


def bump_settings_version() -> int:
    """Legacy function to bump settings version."""
    return CacheManager.clear_settings()


def bump_sales_version() -> int:
    """Legacy function to bump sales version."""
    return CacheManager.clear_sales()


def bump_customer_version() -> int:
    """Legacy function to bump customer version."""
    return CacheManager.clear_customers()


def bump_supplier_version() -> int:
    """Legacy function to bump supplier version."""
    return CacheManager.clear_suppliers()


def bump_purchase_version() -> int:
    """Legacy function to bump purchase version."""
    return CacheManager.clear_purchases()


def bump_user_version() -> int:
    """Legacy function to bump user version."""
    return CacheManager.clear_users()


# ==============================================================================
# CONTEXT DECORATOR
# ==============================================================================

def with_context(func):
    """Decorator to ensure context is available."""
    def wrapper(*args, **kwargs):
        context = ERPContext.get_current()
        return func(context, *args, **kwargs)
    return wrapper


def require_permission(permission: str):
    """Decorator to require a specific permission."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            context = ERPContext.get_current()
            if not context.has_permission(permission):
                raise PermissionError(
                    f"Permission '{permission}' required"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    # Session Management
    "NiceGUISession",
    
    # ERP Context
    "ERPContext",
    "ERPContextData",
    
    # Cache Manager
    "CacheManager",
    "CacheVersion",
    
    # Legacy Functions
    "get_cache_version",
    "bump_cache",
    "bump_inventory_version",
    "bump_product_version",
    "bump_pricing_version",
    "bump_settings_version",
    "bump_sales_version",
    "bump_customer_version",
    "bump_supplier_version",
    "bump_purchase_version",
    "bump_user_version",
    
    # Decorators
    "with_context",
    "require_permission",
]

print("ERP CONTEXT + CACHE READY - NiceGUI Version")
