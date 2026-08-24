# ============================================================
# supabase_client.py
# ERP ENTERPRISE SUPABASE CLIENT
# SERVER-SIDE SERVICE ROLE
# NICE GUI VERSION
# ============================================================

import os
from typing import Optional
from functools import lru_cache

from supabase import create_client, Client
from nicegui import app


# ==============================================================================
# CONFIGURATION LOADING
# ==============================================================================

def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get configuration value from multiple sources:
    1. Environment variables
    2. NiceGUI app.storage
    3. Streamlit-style secrets file (if exists)
    4. Default value
    """
    # Check environment variables first
    env_value = os.getenv(key)
    if env_value:
        return env_value
    
    # Check NiceGUI app storage
    try:
        if hasattr(app, 'storage') and app.storage:
            storage_value = app.storage.get(key)
            if storage_value:
                return storage_value
    except Exception:
        pass
    
    # Check for Streamlit-style secrets.toml
    try:
        import tomllib
        secrets_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '.streamlit',
            'secrets.toml'
        )
        
        if os.path.exists(secrets_path):
            with open(secrets_path, 'rb') as f:
                secrets = tomllib.load(f)
            
            # Handle nested keys (e.g., "SUPABASE.URL")
            if '.' in key:
                parts = key.split('.')
                value = secrets
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        return default
                return value if value else default
            
            return secrets.get(key, default)
    except Exception:
        pass
    
    return default


# ==============================================================================
# SUPABASE CLIENT CACHE
# ==============================================================================

@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """
    Get cached Supabase client with service role key.
    
    Uses lru_cache instead of st.cache_resource for caching.
    """
    
    # Try multiple configuration sources
    supabase_url = get_config_value("SUPABASE_URL")
    supabase_key = get_config_value("SUPABASE_SERVICE_ROLE_KEY")
    
    # Alternative key names
    if not supabase_url:
        supabase_url = get_config_value("SUPABASE.URL")
    
    if not supabase_key:
        supabase_key = get_config_value("SUPABASE.SERVICE_ROLE_KEY")
    
    # Validate configuration
    if not supabase_url:
        raise RuntimeError(
            "SUPABASE_URL is missing. "
            "Please set it in environment variables or secrets file."
        )
    
    if not supabase_key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY is missing. "
            "Please set it in environment variables or secrets file."
        )
    
    # Create and return client
    return create_client(supabase_url, supabase_key)


# ==============================================================================
# SUPABASE CLIENT WITH CUSTOM OPTIONS
# ==============================================================================

@lru_cache(maxsize=1)
def get_supabase_with_options(
    auto_refresh_token: bool = True,
    persist_session: bool = True,
    realtime_enabled: bool = True
) -> Client:
    """
    Get Supabase client with custom options.
    
    Args:
        auto_refresh_token: Automatically refresh token
        persist_session: Persist session between requests
        realtime_enabled: Enable realtime subscriptions
    
    Returns:
        Supabase Client instance
    """
    
    supabase_url = get_config_value("SUPABASE_URL")
    supabase_key = get_config_value("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase configuration is missing.")
    
    return create_client(
        supabase_url,
        supabase_key,
        options={
            "auto_refresh_token": auto_refresh_token,
            "persist_session": persist_session,
            "realtime_enabled": realtime_enabled,
        }
    )


# ==============================================================================
# SUPABASE ADMIN CLIENT (FOR USER MANAGEMENT)
# ==============================================================================

@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    """
    Get Supabase admin client with service role key.
    Used for user management operations.
    """
    
    supabase_url = get_config_value("SUPABASE_URL")
    service_role_key = get_config_value("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is missing.")
    
    if not service_role_key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is missing.")
    
    return create_client(supabase_url, service_role_key)


# ==============================================================================
# SUPABASE CLIENT FACTORY
# ==============================================================================

class SupabaseClientFactory:
    """
    Factory class for creating and managing Supabase clients.
    Provides dependency injection and testing support.
    """
    
    _instance: Optional[Client] = None
    _admin_instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance"""
        if cls._instance is None:
            cls._instance = get_supabase()
        return cls._instance
    
    @classmethod
    def get_admin_client(cls) -> Client:
        """Get or create Supabase admin client instance"""
        if cls._admin_instance is None:
            cls._admin_instance = get_supabase_admin()
        return cls._admin_instance
    
    @classmethod
    def reset(cls):
        """Reset cached clients (useful for testing)"""
        cls._instance = None
        cls._admin_instance = None
        get_supabase.cache_clear()
        get_supabase_with_options.cache_clear()
        get_supabase_admin.cache_clear()
    
    @classmethod
    def set_client(cls, client: Client):
        """Set custom client instance (for testing)"""
        cls._instance = client
    
    @classmethod
    def set_admin_client(cls, client: Client):
        """Set custom admin client instance (for testing)"""
        cls._admin_instance = client


# ==============================================================================
# HEALTH CHECK
# ==============================================================================

def check_supabase_connection() -> tuple[bool, str]:
    """
    Check Supabase connection health.
    
    Returns:
        (is_healthy: bool, message: str)
    """
    
    try:
        client = get_supabase()
        
        # Simple query to test connection
        result = client.table("users").select("id").limit(1).execute()
        
        if result:
            return True, "Supabase connection successful."
        else:
            return False, "Supabase connection failed."
    
    except Exception as e:
        return False, f"Supabase connection error: {str(e)}"


# ==============================================================================
# CONFIGURATION VALIDATION
# ==============================================================================

def validate_supabase_config() -> dict:
    """
    Validate Supabase configuration.
    
    Returns:
        Dictionary with validation results
    """
    
    config_status = {
        "has_url": False,
        "has_key": False,
        "url_source": None,
        "key_source": None,
        "is_valid": False,
        "message": "",
    }
    
    # Check URL
    supabase_url = get_config_value("SUPABASE_URL")
    if supabase_url:
        config_status["has_url"] = True
        config_status["url_source"] = "environment" if os.getenv("SUPABASE_URL") else "file"
    
    # Check Key
    supabase_key = get_config_value("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_key:
        config_status["has_key"] = True
        config_status["key_source"] = "environment" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "file"
    
    # Validate
    if config_status["has_url"] and config_status["has_key"]:
        config_status["is_valid"] = True
        config_status["message"] = "Supabase configuration is valid."
    else:
        missing = []
        if not config_status["has_url"]:
            missing.append("SUPABASE_URL")
        if not config_status["has_key"]:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        
        config_status["message"] = f"Missing: {', '.join(missing)}"
    
    return config_status


# ==============================================================================
# CONFIGURATION SETUP HELPER
# ==============================================================================

def setup_supabase_config(
    url: str,
    service_role_key: str,
    persist: bool = True
) -> bool:
    """
    Setup Supabase configuration programmatically.
    
    Args:
        url: Supabase project URL
        service_role_key: Supabase service role key
        persist: Whether to persist configuration
    
    Returns:
        Success status
    """
    
    try:
        # Set environment variables
        os.environ["SUPABASE_URL"] = url
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = service_role_key
        
        # Persist to NiceGUI app storage if requested
        if persist and hasattr(app, 'storage'):
            app.storage["SUPABASE_URL"] = url
            app.storage["SUPABASE_SERVICE_ROLE_KEY"] = service_role_key
        
        # Clear cache to force new client creation
        SupabaseClientFactory.reset()
        
        return True
    
    except Exception:
        return False


# ==============================================================================
# MAIN CLIENT GETTER (BACKWARD COMPATIBLE)
# ==============================================================================

def db() -> Client:
    """
    Get Supabase client (backward compatible function name).
    This is the main entry point used by other modules.
    """
    return SupabaseClientFactory.get_client()


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    "get_supabase",
    "get_supabase_with_options",
    "get_supabase_admin",
    "SupabaseClientFactory",
    "check_supabase_connection",
    "validate_supabase_config",
    "setup_supabase_config",
    "db",
]
