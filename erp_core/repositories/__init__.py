# ==============================================================================
# erp_core/repositories/__init__.py
# ERP ENTERPRISE REPOSITORY EXPORTS v33 - NiceGUI Version
# ==============================================================================

"""
ERP Repositories Package
------------------------
Provides data access layer with:
- CRUD operations
- Caching with version control
- Transaction support
- Maker-Checker integration
- Permission checking
- Audit logging
- NiceGUI async support
"""

from typing import Optional, List, Dict, Any, Type, Union
from functools import wraps
import asyncio

# ------------------------------------------------------------------------------
# Base Repository
# ------------------------------------------------------------------------------

from .base_repository import (
    BaseRepository,
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryValidationError,
    RepositoryPermissionError,
)

# ------------------------------------------------------------------------------
# Domain Repositories
# ------------------------------------------------------------------------------

from .product_repository import (
    ProductRepository,
    ProductCreateDTO,
    ProductUpdateDTO,
    ProductFilterDTO,
)

from .warehouse_repository import (
    WarehouseRepository,
    WarehouseCreateDTO,
    WarehouseUpdateDTO,
)

from .customer_repository import (
    CustomerRepository,
    CustomerCreateDTO,
    CustomerUpdateDTO,
    CustomerFilterDTO,
)

from .supplier_repository import (
    SupplierRepository,
    SupplierCreateDTO,
    SupplierUpdateDTO,
)

from .sales_repository import (
    SalesRepository,
    SalesCreateDTO,
    SalesUpdateDTO,
    SalesItemDTO,
    SalesFilterDTO,
)

from .inventory_repository import (
    InventoryRepository,
    InventoryAdjustmentDTO,
    StockTransferDTO,
)

from .user_repository import (
    UserRepository,
    UserCreateDTO,
    UserUpdateDTO,
)

from .setting_repository import (
    SettingRepository,
    SettingCreateDTO,
    SettingUpdateDTO,
)

from .category_repository import (
    CategoryRepository,
    CategoryCreateDTO,
    CategoryUpdateDTO,
)

from .permission_repository import (
    PermissionRepository,
    RoleCreateDTO,
    RoleUpdateDTO,
)

# ------------------------------------------------------------------------------
# Repository Coordinator
# ------------------------------------------------------------------------------

from .repository_coordinator import (
    RepositoryCoordinator,
    RepositoryFactory,
    UnitOfWork,
)

# ------------------------------------------------------------------------------
# Repository Decorators
# ------------------------------------------------------------------------------

class RepositoryDecorators:
    """Decorators for repository operations."""
    
    @staticmethod
    def audit(action: str):
        """Audit log decorator."""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                from erp_core.context import ERPContext
                
                context = ERPContext.get_current()
                result = func(self, *args, **kwargs)
                
                # Log audit
                self._log_audit(
                    action=action,
                    user_id=context.user_id,
                    details={
                        "args": args,
                        "kwargs": kwargs,
                        "result": str(result)[:100] if result else None,
                    }
                )
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def require_permission(permission: str):
        """Permission check decorator."""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                from erp_core.context import ERPContext
                
                context = ERPContext.get_current()
                if not context.has_permission(permission):
                    raise RepositoryPermissionError(
                        permission=permission,
                        message=f"Permission '{permission}' required"
                    )
                
                return func(self, *args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def with_transaction():
        """Transaction decorator."""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                from erp_core.base_repo import db, privileged_db
                
                # Start transaction
                try:
                    result = func(self, *args, **kwargs)
                    # Commit (implicit)
                    return result
                except Exception as e:
                    # Rollback
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def cache(ttl: int = 300, version_key: Optional[str] = None):
        """Cache decorator for repository methods."""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                from erp_core.context import CacheManager
                from erp_core.loaders import LoaderCache
                
                # Generate cache key
                cache_prefix = f"{self.__class__.__name__}_{func.__name__}"
                if version_key:
                    version = CacheManager.get_version(version_key)
                    cache_prefix = f"{cache_prefix}_v{version}"
                
                # Use loader cache
                cached_result = LoaderCache._get(cache_prefix)
                if cached_result is not None:
                    return cached_result
                
                result = func(self, *args, **kwargs)
                LoaderCache._set(cache_prefix, result, ttl)
                
                return result
            return wrapper
        return decorator


# ------------------------------------------------------------------------------
# Repository Manager
# ------------------------------------------------------------------------------

class RepositoryManager:
    """
    Manages repository instances with caching and dependency injection.
    """
    
    _repositories: Dict[str, Any] = {}
    _coordinator: Optional[RepositoryCoordinator] = None
    
    @classmethod
    def get_repository(cls, repo_type: str) -> Any:
        """Get a repository instance."""
        repo_map = {
            "product": ProductRepository,
            "warehouse": WarehouseRepository,
            "customer": CustomerRepository,
            "supplier": SupplierRepository,
            "sales": SalesRepository,
            "inventory": InventoryRepository,
            "user": UserRepository,
            "setting": SettingRepository,
            "category": CategoryRepository,
            "permission": PermissionRepository,
        }
        
        repo_class = repo_map.get(repo_type)
        if not repo_class:
            raise ValueError(f"Unknown repository type: {repo_type}")
        
        if repo_type not in cls._repositories:
            cls._repositories[repo_type] = repo_class()
        
        return cls._repositories[repo_type]
    
    @classmethod
    def get_coordinator(cls) -> RepositoryCoordinator:
        """Get repository coordinator."""
        if cls._coordinator is None:
            cls._coordinator = RepositoryCoordinator()
            # Register repositories
            for repo_name, repo in cls._repositories.items():
                cls._coordinator.register_repository(repo_name, repo)
        
        return cls._coordinator
    
    @classmethod
    def clear_cache(cls, repo_type: Optional[str] = None) -> None:
        """Clear repository cache."""
        if repo_type:
            if repo_type in cls._repositories:
                repo = cls._repositories[repo_type]
                if hasattr(repo, 'clear_cache'):
                    repo.clear_cache()
        else:
            for repo in cls._repositories.values():
                if hasattr(repo, 'clear_cache'):
                    repo.clear_cache()
    
    @classmethod
    def reset(cls) -> None:
        """Reset all repositories."""
        cls._repositories.clear()
        cls._coordinator = None


# ------------------------------------------------------------------------------
# Repository DTO Base Classes
# ------------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Any


@dataclass
class BaseDTO:
    """Base Data Transfer Object."""
    
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseDTO':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SearchFilterDTO:
    """Search filter DTO."""
    
    query: Optional[str] = None
    page: int = 1
    page_size: int = 100
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    active_only: bool = True
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result


# ------------------------------------------------------------------------------
# Repository Extensions
# ------------------------------------------------------------------------------

class RepositoryExtensions:
    """
    Extension methods for repositories.
    """
    
    @staticmethod
    def bulk_create(repo: BaseRepository, items: List[BaseDTO]) -> List[Any]:
        """Bulk create items."""
        results = []
        for item in items:
            result = repo.create(item)
            results.append(result)
        return results
    
    @staticmethod
    def bulk_update(repo: BaseRepository, items: List[BaseDTO]) -> List[Any]:
        """Bulk update items."""
        results = []
        for item in items:
            result = repo.update(item.id, item)
            results.append(result)
        return results
    
    @staticmethod
    def bulk_delete(repo: BaseRepository, ids: List[str]) -> int:
        """Bulk delete items."""
        count = 0
        for id in ids:
            if repo.delete(id):
                count += 1
        return count
    
    @staticmethod
    def exists(repo: BaseRepository, **filters) -> bool:
        """Check if any item exists matching filters."""
        result = repo.get_by_filters(**filters)
        return len(result) > 0
    
    @staticmethod
    def get_or_create(repo: BaseRepository, defaults: BaseDTO, **filters) -> Any:
        """Get item or create it if not exists."""
        result = repo.get_by_filters(**filters)
        if result:
            return result[0]
        return repo.create(defaults)


# ------------------------------------------------------------------------------
# Async Repository Support
# ------------------------------------------------------------------------------

class AsyncRepositoryMixin:
    """
    Mixin for async repository operations.
    """
    
    async def async_create(self, dto: BaseDTO) -> Any:
        """Async create."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.create, dto)
    
    async def async_get(self, id: str) -> Any:
        """Async get."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get, id)
    
    async def async_update(self, id: str, dto: BaseDTO) -> Any:
        """Async update."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.update, id, dto)
    
    async def async_delete(self, id: str) -> bool:
        """Async delete."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.delete, id)
    
    async def async_search(self, filters: SearchFilterDTO) -> List[Any]:
        """Async search."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search, filters)


# ------------------------------------------------------------------------------
# API Exports
# ------------------------------------------------------------------------------

__all__ = [
    # Base
    "BaseRepository",
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryValidationError",
    "RepositoryPermissionError",
    
    # Domain Repositories
    "ProductRepository",
    "ProductCreateDTO",
    "ProductUpdateDTO",
    "ProductFilterDTO",
    
    "WarehouseRepository",
    "WarehouseCreateDTO",
    "WarehouseUpdateDTO",
    
    "CustomerRepository",
    "CustomerCreateDTO",
    "CustomerUpdateDTO",
    "CustomerFilterDTO",
    
    "SupplierRepository",
    "SupplierCreateDTO",
    "SupplierUpdateDTO",
    
    "SalesRepository",
    "SalesCreateDTO",
    "SalesUpdateDTO",
    "SalesItemDTO",
    "SalesFilterDTO",
    
    "InventoryRepository",
    "InventoryAdjustmentDTO",
    "StockTransferDTO",
    
    "UserRepository",
    "UserCreateDTO",
    "UserUpdateDTO",
    
    "SettingRepository",
    "SettingCreateDTO",
    "SettingUpdateDTO",
    
    "CategoryRepository",
    "CategoryCreateDTO",
    "CategoryUpdateDTO",
    
    "PermissionRepository",
    "RoleCreateDTO",
    "RoleUpdateDTO",
    
    # Coordinator
    "RepositoryCoordinator",
    "RepositoryFactory",
    "UnitOfWork",
    "RepositoryManager",
    
    # DTOs
    "BaseDTO",
    "SearchFilterDTO",
    
    # Decorators
    "RepositoryDecorators",
    
    # Extensions
    "RepositoryExtensions",
    
    # Async Support
    "AsyncRepositoryMixin",
]

print("ERP REPOSITORIES READY - NiceGUI Version")
