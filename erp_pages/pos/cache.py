# ==============================================================================
# erp_pages/pos/cache.py
# ERP ENTERPRISE POS CACHE CONTROLLER v13.0 - NiceGUI Version
#
# POS Cache
# Inventory Refresh
# Product Refresh
# NiceGUI Session Cache Control
# Real-time Updates
# WebSocket Support
#
# ==============================================================================

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import time
import json

from erp_core.context import CacheManager, NiceGUISession
from erp_core.loaders import invalidate_cache
from erp_core.exceptions import ERPException

# Try to import NiceGUI event bus for real-time updates
try:
    from nicegui import app
    HAS_NICEGUI = True
except ImportError:
    HAS_NICEGUI = False


# ==============================================================================
# CACHE KEYS
# ==============================================================================

class POSCacheKeys:
    """POS cache version keys."""
    
    INVENTORY = "inventory_version"
    PRODUCT = "product_version"
    SALES = "sales_version"
    PRICING = "pricing_version"
    CUSTOMER = "customer_version"
    SUPPLIER = "supplier_version"
    SETTINGS = "settings_version"
    
    # POS specific
    POS_CART = "pos_cart"
    POS_SESSION = "pos_session"
    POS_RECEIPT = "pos_receipt"
    POS_CHECKOUT = "pos_checkout"


# ==============================================================================
# CACHE INVALIDATOR
# ==============================================================================

class CacheInvalidator:
    """
    Cache invalidation system with event support.
    """
    
    _subscribers: Dict[str, List[Callable]] = {}
    
    @classmethod
    def invalidate(cls, cache_key: str, notify: bool = True) -> int:
        """
        Invalidate a specific cache.
        
        Args:
            cache_key: Cache version key
            notify: Whether to notify subscribers
        
        Returns:
            New version number
        """
        new_version = CacheManager.bump(cache_key)
        
        if notify:
            cls._notify_subscribers(cache_key, new_version)
        
        return new_version
    
    @classmethod
    def invalidate_all(cls) -> Dict[str, int]:
        """
        Invalidate all POS caches.
        
        Returns:
            Dictionary of updated versions
        """
        results = {}
        
        for key in [
            POSCacheKeys.INVENTORY,
            POSCacheKeys.PRODUCT,
            POSCacheKeys.SALES,
            POSCacheKeys.PRICING,
            POSCacheKeys.CUSTOMER,
            POSCacheKeys.SUPPLIER,
            POSCacheKeys.SETTINGS,
        ]:
            results[key] = cls.invalidate(key, notify=False)
        
        # Notify subscribers once
        cls._notify_subscribers("all", results)
        
        return results
    
    @classmethod
    def subscribe(cls, event: str, callback: Callable):
        """
        Subscribe to cache invalidation events.
        
        Args:
            event: Cache key or "all"
            callback: Function to call on invalidation
        """
        if event not in cls._subscribers:
            cls._subscribers[event] = []
        cls._subscribers[event].append(callback)
    
    @classmethod
    def unsubscribe(cls, event: str, callback: Callable):
        """Unsubscribe from cache invalidation events."""
        if event in cls._subscribers:
            cls._subscribers[event].remove(callback)
    
    @classmethod
    def _notify_subscribers(cls, event: str, data: Any):
        """Notify subscribers of invalidation."""
        # Notify specific event subscribers
        if event in cls._subscribers:
            for callback in cls._subscribers[event]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in cache subscriber: {e}")
        
        # Notify "all" subscribers
        if event != "all" and "all" in cls._subscribers:
            for callback in cls._subscribers["all"]:
                try:
                    callback({event: data})
                except Exception as e:
                    print(f"Error in cache subscriber: {e}")


# ==============================================================================
# INVENTORY CACHE
# ==============================================================================

def refresh_inventory(notify: bool = True) -> int:
    """
    Refresh inventory cache after sale/transfer/adjustment.
    
    Args:
        notify: Whether to notify subscribers
    
    Returns:
        New version number
    """
    return CacheInvalidator.invalidate(POSCacheKeys.INVENTORY, notify)


# ==============================================================================
# PRODUCT CACHE
# ==============================================================================

def refresh_products(notify: bool = True) -> int:
    """
    Refresh product cache after price/stock changes.
    
    Args:
        notify: Whether to notify subscribers
    
    Returns:
        New version number
    """
    return CacheInvalidator.invalidate(POSCacheKeys.PRODUCT, notify)


# ==============================================================================
# SALES CACHE
# ==============================================================================

def refresh_sales(notify: bool = True) -> int:
    """
    Refresh sales cache.
    
    Args:
        notify: Whether to notify subscribers
    
    Returns:
        New version number
    """
    return CacheInvalidator.invalidate(POSCacheKeys.SALES, notify)


# ==============================================================================
# PRICING CACHE
# ==============================================================================

def refresh_pricing(notify: bool = True) -> int:
    """
    Refresh pricing cache.
    
    Args:
        notify: Whether to notify subscribers
    
    Returns:
        New version number
    """
    return CacheInvalidator.invalidate(POSCacheKeys.PRICING, notify)


# ==============================================================================
# CUSTOMER CACHE
# ==============================================================================

def refresh_customers(notify: bool = True) -> int:
    """
    Refresh customer cache.
    
    Args:
        notify: Whether to notify subscribers
    
    Returns:
        New version number
    """
    return CacheInvalidator.invalidate(POSCacheKeys.CUSTOMER, notify)


# ==============================================================================
# SUPPLIER CACHE
# ==============================================================================

def refresh_suppliers(notify: bool = True) -> int:
    """
    Refresh supplier cache.
    
    Args:
        notify: Whether to notify subscribers
    
    Returns:
        New version number
    """
    return CacheInvalidator.invalidate(POSCacheKeys.SUPPLIER, notify)


# ==============================================================================
# SETTINGS CACHE
# ==============================================================================

def refresh_settings(notify: bool = True) -> int:
    """
    Refresh settings cache.
    
    Args:
        notify: Whether to notify subscribers
    
    Returns:
        New version number
    """
    return CacheInvalidator.invalidate(POSCacheKeys.SETTINGS, notify)


# ==============================================================================
# FULL POS REFRESH
# ==============================================================================

def refresh_pos(
    clear_session: bool = True,
    notify: bool = True
) -> Dict[str, Any]:
    """
    Full POS refresh after checkout success.
    
    Args:
        clear_session: Whether to clear POS session data
        notify: Whether to notify subscribers
    
    Returns:
        Dictionary with refresh results
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "cache_invalidations": {},
        "session_cleared": False,
        "success": True,
    }
    
    try:
        # Invalidate all caches
        result["cache_invalidations"] = CacheInvalidator.invalidate_all()
        
        # Clear POS session data
        if clear_session:
            clear_pos_session()
            result["session_cleared"] = True
        
        # Notify subscribers
        if notify:
            if HAS_NICEGUI:
                app.native.notify("POS refreshed", type="positive")
        
        result["success"] = True
        
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
    
    return result


def refresh_pos_async(clear_session: bool = True) -> None:
    """
    Async refresh POS (for NiceGUI background tasks).
    
    Args:
        clear_session: Whether to clear POS session data
    """
    import asyncio
    
    # Run refresh in background
    asyncio.create_task(
        _refresh_pos_background(clear_session)
    )


async def _refresh_pos_background(clear_session: bool = True):
    """Background task for POS refresh."""
    try:
        # Invalidate all caches
        CacheInvalidator.invalidate_all()
        
        # Clear POS session data
        if clear_session:
            clear_pos_session()
        
        # Notify via NiceGUI
        if HAS_NICEGUI:
            app.native.notify("POS refreshed in background", type="positive")
        
    except Exception as e:
        print(f"Error in background refresh: {e}")


# ==============================================================================
# GET CACHE VERSIONS
# ==============================================================================

def get_inventory_version() -> int:
    """Get current inventory cache version."""
    return CacheManager.get_version(POSCacheKeys.INVENTORY)


def get_product_version() -> int:
    """Get current product cache version."""
    return CacheManager.get_version(POSCacheKeys.PRODUCT)


def get_sales_version() -> int:
    """Get current sales cache version."""
    return CacheManager.get_version(POSCacheKeys.SALES)


def get_pricing_version() -> int:
    """Get current pricing cache version."""
    return CacheManager.get_version(POSCacheKeys.PRICING)


def get_customer_version() -> int:
    """Get current customer cache version."""
    return CacheManager.get_version(POSCacheKeys.CUSTOMER)


def get_supplier_version() -> int:
    """Get current supplier cache version."""
    return CacheManager.get_version(POSCacheKeys.SUPPLIER)


def get_settings_version() -> int:
    """Get current settings cache version."""
    return CacheManager.get_version(POSCacheKeys.SETTINGS)


def get_all_cache_versions() -> Dict[str, int]:
    """Get all cache versions."""
    return {
        "inventory": get_inventory_version(),
        "product": get_product_version(),
        "sales": get_sales_version(),
        "pricing": get_pricing_version(),
        "customer": get_customer_version(),
        "supplier": get_supplier_version(),
        "settings": get_settings_version(),
    }


# ==============================================================================
# CLEAR SESSION CART CACHE
# ==============================================================================

def clear_pos_session(keys: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    Clear POS session data from NiceGUI session.
    
    Args:
        keys: List of keys to clear. If None, clear all POS keys.
    
    Returns:
        Dictionary of cleared keys and success status
    """
    # Default POS session keys
    default_keys = [
        "cart",
        "sale_data",
        "show_receipt",
        "processing",
        "checkout_data",
        "payment_data",
        "receipt_data",
        "pos_cart_id",
        "pos_sale_id",
        "pos_customer_id",
    ]
    
    keys_to_clear = keys or default_keys
    results = {}
    
    for key in keys_to_clear:
        try:
            # Remove from session
            NiceGUISession.delete(key)
            
            # Also clear from any cached data
            if key in NiceGUISession._sessions:
                if NiceGUISession._current_session_id in NiceGUISession._sessions:
                    if key in NiceGUISession._sessions[NiceGUISession._current_session_id]:
                        del NiceGUISession._sessions[NiceGUISession._current_session_id][key]
            
            results[key] = True
        except Exception:
            results[key] = False
    
    return results


def clear_cart_cache() -> bool:
    """Clear cart data from session."""
    result = clear_pos_session(["cart", "pos_cart_id"])
    return all(result.values())


def clear_sale_data() -> bool:
    """Clear sale data from session."""
    result = clear_pos_session(["sale_data", "pos_sale_id"])
    return all(result.values())


def clear_receipt_data() -> bool:
    """Clear receipt data from session."""
    result = clear_pos_session(["receipt_data", "show_receipt"])
    return all(result.values())


# ==============================================================================
# POS CACHE MANAGER
# ==============================================================================

class POSCacheManager:
    """
    Advanced POS cache manager with statistics and monitoring.
    """
    
    _cache_stats = {
        "hits": 0,
        "misses": 0,
        "invalidations": 0,
        "last_invalidation": None,
        "cache_size": 0,
    }
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            **cls._cache_stats,
            "hit_ratio": cls._calculate_hit_ratio(),
            "timestamp": datetime.now().isoformat(),
        }
    
    @classmethod
    def _calculate_hit_ratio(cls) -> float:
        """Calculate cache hit ratio."""
        total = cls._cache_stats["hits"] + cls._cache_stats["misses"]
        if total == 0:
            return 0.0
        return cls._cache_stats["hits"] / total
    
    @classmethod
    def record_hit(cls):
        """Record a cache hit."""
        cls._cache_stats["hits"] += 1
    
    @classmethod
    def record_miss(cls):
        """Record a cache miss."""
        cls._cache_stats["misses"] += 1
    
    @classmethod
    def record_invalidation(cls):
        """Record a cache invalidation."""
        cls._cache_stats["invalidations"] += 1
        cls._cache_stats["last_invalidation"] = datetime.now().isoformat()
    
    @classmethod
    def reset_stats(cls):
        """Reset cache statistics."""
        cls._cache_stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "last_invalidation": None,
            "cache_size": 0,
        }


# ==============================================================================
# REAL-TIME CACHE UPDATES (WebSocket)
# ==============================================================================

class RealTimeCache:
    """
    Real-time cache updates via WebSocket (NiceGUI).
    """
    
    _clients = set()
    
    @classmethod
    def register_client(cls, client_id: str):
        """Register a client for real-time updates."""
        cls._clients.add(client_id)
    
    @classmethod
    def unregister_client(cls, client_id: str):
        """Unregister a client."""
        cls._clients.discard(client_id)
    
    @classmethod
    async def broadcast_update(cls, cache_key: str, version: int):
        """Broadcast cache update to all clients."""
        if not HAS_NICEGUI:
            return
        
        try:
            from nicegui import app
            data = {
                "type": "cache_update",
                "key": cache_key,
                "version": version,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Broadcast via app.native if available
            if hasattr(app, 'native') and hasattr(app.native, 'broadcast'):
                app.native.broadcast(json.dumps(data))
            
        except Exception as e:
            print(f"Error broadcasting cache update: {e}")
    
    @classmethod
    def broadcast_update_sync(cls, cache_key: str, version: int):
        """Synchronous broadcast wrapper."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(cls.broadcast_update(cache_key, version))
            else:
                loop.run_until_complete(cls.broadcast_update(cache_key, version))
        except Exception as e:
            print(f"Error in sync broadcast: {e}")


# ==============================================================================
# LEGACY COMPATIBILITY (Streamlit)
# ==============================================================================

# For backward compatibility, we keep the old function names
# but they now work with NiceGUI session


# ==============================================================================
# DECORATORS
# ==============================================================================

def invalidate_on_success(*cache_keys: str):
    """
    Decorator to invalidate caches after successful function execution.
    
    Example:
        @invalidate_on_success("inventory_version", "product_version")
        def process_sale(sale_data):
            # Sale processing logic
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate specified caches
            for key in cache_keys:
                CacheInvalidator.invalidate(key)
            
            return result
        return wrapper
    return decorator


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Cache keys
    "POSCacheKeys",
    
    # Refresh functions
    "refresh_inventory",
    "refresh_products",
    "refresh_sales",
    "refresh_pricing",
    "refresh_customers",
    "refresh_suppliers",
    "refresh_settings",
    "refresh_pos",
    "refresh_pos_async",
    
    # Get version functions
    "get_inventory_version",
    "get_product_version",
    "get_sales_version",
    "get_pricing_version",
    "get_customer_version",
    "get_supplier_version",
    "get_settings_version",
    "get_all_cache_versions",
    
    # Session management
    "clear_pos_session",
    "clear_cart_cache",
    "clear_sale_data",
    "clear_receipt_data",
    
    # Cache invalidation
    "CacheInvalidator",
    
    # Cache manager
    "POSCacheManager",
    
    # Real-time updates
    "RealTimeCache",
    
    # Decorators
    "invalidate_on_success",
]

print("ERP POS CACHE READY - NiceGUI Version")
