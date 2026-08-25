# ==============================================================================
# erp_core/loaders/__init__.py
# ERP ENTERPRISE LOADERS PACKAGE v33 - NiceGUI Version
# ==============================================================================

"""
ERP Loaders Package
-------------------
Provides cached data loading functions for all major ERP domains.

Features:
- Automatic caching with version control
- Type hints for better IDE support
- Async support for NiceGUI
- Error handling with detailed exceptions
- Pagination and filtering support
"""

from typing import Optional, List, Dict, Any, Union, Callable
from functools import wraps

# ------------------------------------------------------------------------------
# Loader Imports
# ------------------------------------------------------------------------------

from .settings_loader import (
    get_setting,
    get_settings_batch,
    get_all_settings,
    SettingsLoader,
)

from .product_loader import (
    get_products,
    get_active_products,
    get_product_by_id,
    get_product_by_sku,
    get_products_by_category,
    search_products,
    ProductLoader,
)

from .warehouse_loader import (
    get_warehouses,
    get_default_warehouse_id,
    get_warehouse_by_id,
    get_active_warehouses,
    WarehouseLoader,
)

from .customer_loader import (
    get_customers,
    get_customer_by_id,
    search_customers,
    get_active_customers,
    CustomerLoader,
)

from .supplier_loader import (
    get_suppliers,
    get_supplier_by_id,
    search_suppliers,
    get_active_suppliers,
    SupplierLoader,
)

from .inventory_loader import (
    get_inventory_view,
    get_inventory_by_warehouse,
    get_inventory_by_product,
    get_stock_levels,
    InventoryLoader,
)

from .receipt_loader import (
    get_receipt,
    get_sale_items,
    search_receipts,
    get_receipt_by_number,
    get_receipts_by_customer,
    ReceiptLoader,
)

# ------------------------------------------------------------------------------
# New Loaders for NiceGUI
# ------------------------------------------------------------------------------

from .category_loader import (
    get_categories,
    get_category_by_id,
    get_category_tree,
    get_subcategories,
    CategoryLoader,
)

from .report_loader import (
    get_sales_report,
    get_inventory_report,
    get_customer_report,
    get_supplier_report,
    ReportLoader,
)

from .user_loader import (
    get_users,
    get_user_by_id,
    get_user_by_email,
    get_users_by_role,
    UserLoader,
)

from .permission_loader import (
    get_permissions,
    get_user_permissions,
    get_role_permissions,
    PermissionLoader,
)

from .currency_loader import (
    get_currency_rates,
    get_currency_rate,
    CurrencyLoader,
)

from .audit_loader import (
    get_audit_logs,
    get_audit_by_user,
    get_audit_by_action,
    AuditLoader,
)

# ------------------------------------------------------------------------------
# Utility Loaders
# ------------------------------------------------------------------------------

from .utils import (
    load_cache_manager,
    invalidate_cache,
    clear_all_caches,
    get_cache_stats,
    CacheStats,
)

# ------------------------------------------------------------------------------
# Loader Factory
# ------------------------------------------------------------------------------

class LoaderFactory:
    """
    Factory for creating and managing loaders.
    Provides unified access to all loaders.
    """
    
    _loaders: Dict[str, Any] = {}
    
    @classmethod
    def get_loader(cls, loader_type: str) -> Any:
        """Get a specific loader instance."""
        loader_map = {
            "settings": SettingsLoader,
            "product": ProductLoader,
            "warehouse": WarehouseLoader,
            "customer": CustomerLoader,
            "supplier": SupplierLoader,
            "inventory": InventoryLoader,
            "receipt": ReceiptLoader,
            "category": CategoryLoader,
            "report": ReportLoader,
            "user": UserLoader,
            "permission": PermissionLoader,
            "currency": CurrencyLoader,
            "audit": AuditLoader,
        }
        
        loader_class = loader_map.get(loader_type)
        if not loader_class:
            raise ValueError(f"Unknown loader type: {loader_type}")
        
        if loader_type not in cls._loaders:
            cls._loaders[loader_type] = loader_class()
        
        return cls._loaders[loader_type]
    
    @classmethod
    def get_all_loaders(cls) -> Dict[str, Any]:
        """Get all loader instances."""
        loaders = [
            "settings", "product", "warehouse", "customer",
            "supplier", "inventory", "receipt", "category",
            "report", "user", "permission", "currency", "audit"
        ]
        
        for loader_type in loaders:
            if loader_type not in cls._loaders:
                cls.get_loader(loader_type)
        
        return cls._loaders
    
    @classmethod
    def clear_cache(cls, loader_type: Optional[str] = None) -> None:
        """Clear cache for specific loader or all loaders."""
        if loader_type:
            if loader_type in cls._loaders:
                loader = cls._loaders[loader_type]
                if hasattr(loader, 'clear_cache'):
                    loader.clear_cache()
        else:
            for loader in cls._loaders.values():
                if hasattr(loader, 'clear_cache'):
                    loader.clear_cache()
    
    @classmethod
    def reload_all(cls) -> None:
        """Reload all loaders."""
        cls.clear_cache()
        cls._loaders.clear()


# ------------------------------------------------------------------------------
# Cache Decorator for NiceGUI
# ------------------------------------------------------------------------------

class LoaderCache:
    """
    Cache decorator for loader functions.
    Supports version-based invalidation.
    """
    
    _cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def cache(
        cls,
        ttl: int = 300,  # 5 minutes default
        key_prefix: Optional[str] = None,
        version_key: Optional[str] = None,
    ):
        """Cache decorator with TTL and version support."""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                from erp_core.context import CacheManager
                
                # Generate cache key
                cache_key = cls._generate_key(
                    func.__name__,
                    args,
                    kwargs,
                    key_prefix,
                    version_key
                )
                
                # Check version if specified
                if version_key:
                    current_version = CacheManager.get_version(version_key)
                    cache_key = f"{cache_key}_v{current_version}"
                
                # Check cache
                cached = cls._get(cache_key)
                if cached is not None:
                    return cached
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                cls._set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator
    
    @classmethod
    def _generate_key(cls, func_name: str, args: tuple, kwargs: dict, 
                      key_prefix: Optional[str], version_key: Optional[str]) -> str:
        """Generate a unique cache key."""
        key_parts = []
        
        if key_prefix:
            key_parts.append(key_prefix)
        else:
            key_parts.append(func_name)
        
        # Add args
        if args:
            key_parts.extend(str(arg) for arg in args)
        
        # Add kwargs (sorted for consistency)
        if kwargs:
            sorted_items = sorted(kwargs.items())
            key_parts.extend(f"{k}={v}" for k, v in sorted_items if v is not None)
        
        return "_".join(key_parts)
    
    @classmethod
    def _get(cls, key: str) -> Optional[Any]:
        """Get value from cache."""
        import time
        
        cache_data = cls._cache.get(key)
        if cache_data:
            value, expiry = cache_data
            if time.time() < expiry:
                return value
            else:
                # Remove expired entry
                del cls._cache[key]
        return None
    
    @classmethod
    def _set(cls, key: str, value: Any, ttl: int) -> None:
        """Set value in cache with TTL."""
        import time
        cls._cache[key] = (value, time.time() + ttl)
    
    @classmethod
    def clear(cls, pattern: Optional[str] = None) -> None:
        """Clear cache entries matching pattern."""
        if pattern:
            keys_to_delete = [k for k in cls._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del cls._cache[key]
        else:
            cls._cache.clear()
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get cache statistics."""
        import time
        now = time.time()
        total_entries = len(cls._cache)
        expired_entries = sum(
            1 for v in cls._cache.values() 
            if v[1] < now
        )
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "memory_usage": cls._estimate_memory(),
        }
    
    @classmethod
    def _estimate_memory(cls) -> str:
        """Estimate cache memory usage."""
        import sys
        total_size = sum(sys.getsizeof(v) for v in cls._cache.values())
        
        if total_size < 1024:
            return f"{total_size} B"
        elif total_size < 1024 * 1024:
            return f"{total_size / 1024:.2f} KB"
        else:
            return f"{total_size / (1024 * 1024):.2f} MB"


# ------------------------------------------------------------------------------
# Loader Decorators
# ------------------------------------------------------------------------------

def cache_result(
    ttl: int = 300,
    version_key: Optional[str] = None,
):
    """Alias for LoaderCache.cache decorator."""
    return LoaderCache.cache(ttl=ttl, version_key=version_key)


def invalidates_cache(*version_keys: str):
    """Decorator to invalidate cache versions after function execution."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            from erp_core.context import CacheManager
            
            for key in version_keys:
                CacheManager.bump(key)
            
            return result
        return wrapper
    return decorator


# ------------------------------------------------------------------------------
# API Exports
# ------------------------------------------------------------------------------

__all__ = [
    # Settings
    "get_setting",
    "get_settings_batch",
    "get_all_settings",
    "SettingsLoader",
    
    # Products
    "get_products",
    "get_active_products",
    "get_product_by_id",
    "get_product_by_sku",
    "get_products_by_category",
    "search_products",
    "ProductLoader",
    
    # Warehouses
    "get_warehouses",
    "get_default_warehouse_id",
    "get_warehouse_by_id",
    "get_active_warehouses",
    "WarehouseLoader",
    
    # Customers
    "get_customers",
    "get_customer_by_id",
    "search_customers",
    "get_active_customers",
    "CustomerLoader",
    
    # Suppliers
    "get_suppliers",
    "get_supplier_by_id",
    "search_suppliers",
    "get_active_suppliers",
    "SupplierLoader",
    
    # Inventory
    "get_inventory_view",
    "get_inventory_by_warehouse",
    "get_inventory_by_product",
    "get_stock_levels",
    "InventoryLoader",
    
    # Receipts
    "get_receipt",
    "get_sale_items",
    "search_receipts",
    "get_receipt_by_number",
    "get_receipts_by_customer",
    "ReceiptLoader",
    
    # Categories
    "get_categories",
    "get_category_by_id",
    "get_category_tree",
    "get_subcategories",
    "CategoryLoader",
    
    # Reports
    "get_sales_report",
    "get_inventory_report",
    "get_customer_report",
    "get_supplier_report",
    "ReportLoader",
    
    # Users
    "get_users",
    "get_user_by_id",
    "get_user_by_email",
    "get_users_by_role",
    "UserLoader",
    
    # Permissions
    "get_permissions",
    "get_user_permissions",
    "get_role_permissions",
    "PermissionLoader",
    
    # Currency
    "get_currency_rates",
    "get_currency_rate",
    "CurrencyLoader",
    
    # Audit
    "get_audit_logs",
    "get_audit_by_user",
    "get_audit_by_action",
    "AuditLoader",
    
    # Cache Management
    "LoaderCache",
    "LoaderFactory",
    "cache_result",
    "invalidates_cache",
    "load_cache_manager",
    "invalidate_cache",
    "clear_all_caches",
    "get_cache_stats",
    "CacheStats",
]

print("ERP LOADERS READY - NiceGUI Version")
