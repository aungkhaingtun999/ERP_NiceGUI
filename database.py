"""
==============================================================================
database.py
ERP ENTERPRISE DATABASE GATEWAY v34
Legacy Compatibility Bridge
NICE GUI VERSION

Legacy pages:
    from database import ...

New architecture:
    erp_core/

This module only re-exports ERP Core APIs.
==============================================================================
"""

import logging
from typing import Optional, Any, Dict, List, Tuple
from functools import lru_cache

# ==============================================================================
# LOGGER SETUP
# ==============================================================================

logger = logging.getLogger(__name__)

# ==============================================================================
# ERP CORE IMPORT
# ==============================================================================

from erp_core import (
    # ------------------------------------------------------------------
    # DATABASE
    # ------------------------------------------------------------------
    db,
    get_supabase,
    get_connection,
    DatabaseHealth,
    database_health_check,
    
    # ------------------------------------------------------------------
    # LOADERS
    # ------------------------------------------------------------------
    get_setting,
    get_products,
    get_inventory_view,
    get_warehouses,
    get_default_warehouse_id,
    get_categories,
    get_suppliers,
    get_customers,
    
    # ------------------------------------------------------------------
    # RECEIPT
    # ------------------------------------------------------------------
    get_receipt,
    get_sale_items,
    search_receipts,
    
    # ------------------------------------------------------------------
    # RPC
    # ------------------------------------------------------------------
    checkout_sale_rpc,
    purchase_receive_rpc,
    refund_sale_rpc,
    stock_adjustment_rpc,
    update_product_rpc,
    request_product_create_rpc,
    request_product_bulk_create_rpc,
    approve_product_create_rpc,
    
    # ------------------------------------------------------------------
    # SERVICES
    # ------------------------------------------------------------------
    SalesService,
    PurchaseService,
    InventoryService,
    RefundService,
    ReceiptService,
    PaymentService,
    PaymentQRService,
    
    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    get_fifo_cogs,
    create_audit_log,
    
    # ------------------------------------------------------------------
    # UTILITIES
    # ------------------------------------------------------------------
    money,
    money_float,
    validate_uuid,
    serialize_json,
    safe_execute,
)


ERP_DATABASE_VERSION = "34.0 Legacy Gateway (NiceGUI)"


# ==============================================================================
# SERVICE FACTORIES WITH CACHING
# ==============================================================================

@lru_cache(maxsize=8)
def get_sales_service() -> SalesService:
    """Get cached SalesService instance"""
    return SalesService(db())


@lru_cache(maxsize=8)
def get_purchase_service() -> PurchaseService:
    """Get cached PurchaseService instance"""
    return PurchaseService(db())


@lru_cache(maxsize=8)
def get_inventory_service() -> InventoryService:
    """Get cached InventoryService instance"""
    return InventoryService(db())


@lru_cache(maxsize=8)
def get_refund_service() -> RefundService:
    """Get cached RefundService instance"""
    return RefundService(db())


@lru_cache(maxsize=8)
def get_receipt_service() -> ReceiptService:
    """Get cached ReceiptService instance"""
    return ReceiptService(db())


# ==============================================================================
# PAYMENT HELPERS
# ==============================================================================

def create_mobile_payment(
    sale_id: str,
    provider: str,
    transaction_id: str,
    amount: float,
    cashier_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create mobile payment record.
    
    Args:
        sale_id: Sale transaction ID
        provider: Payment provider name
        transaction_id: Mobile transaction ID
        amount: Payment amount
        cashier_id: Cashier user ID
    
    Returns:
        Payment record dictionary
    """
    try:
        return PaymentService.create_mobile_payment(
            sale_id=sale_id,
            provider=provider,
            transaction_id=transaction_id,
            amount=amount,
            cashier_id=cashier_id
        )
    except Exception as e:
        logger.error(f"Error creating mobile payment: {e}")
        raise


def verify_payment(
    payment_id: str,
    verified_by: str
) -> Dict[str, Any]:
    """
    Verify mobile payment.
    
    Args:
        payment_id: Payment record ID
        verified_by: Verifier user ID
    
    Returns:
        Updated payment record
    """
    try:
        return PaymentService.verify_payment(payment_id, verified_by)
    except Exception as e:
        logger.error(f"Error verifying payment: {e}")
        raise


def reject_payment(
    payment_id: str,
    verified_by: str,
    reason: str
) -> Dict[str, Any]:
    """
    Reject mobile payment.
    
    Args:
        payment_id: Payment record ID
        verified_by: Verifier user ID
        reason: Rejection reason
    
    Returns:
        Updated payment record
    """
    try:
        return PaymentService.reject_payment(payment_id, verified_by, reason)
    except Exception as e:
        logger.error(f"Error rejecting payment: {e}")
        raise


def get_pending_payments() -> List[Dict[str, Any]]:
    """
    Get all pending mobile payments.
    
    Returns:
        List of pending payment records
    """
    try:
        return PaymentService.pending_payments()
    except Exception as e:
        logger.error(f"Error getting pending payments: {e}")
        raise


def generate_payment_qr(
    provider: str = "",
    account_name: str = "",
    account_no: str = "",
    amount: float = 0,
    sale_id: str = "",
    raw_payload: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate payment QR code.
    
    Args:
        provider: Payment provider (KBZ, Wave, etc.)
        account_name: Merchant account name
        account_no: Merchant account number
        amount: Payment amount
        sale_id: Sale transaction ID
        raw_payload: Additional payload data
    
    Returns:
        QR code data dictionary
    """
    try:
        return PaymentQRService.generate_qr(
            provider=provider,
            account_name=account_name,
            account_no=account_no,
            amount=amount,
            sale_id=sale_id,
            raw_payload=raw_payload
        )
    except Exception as e:
        logger.error(f"Error generating payment QR: {e}")
        raise


# ==============================================================================
# DATABASE HEALTH CHECK (ASYNC-FRIENDLY)
# ==============================================================================

async def check_database_health_async() -> Tuple[bool, str]:
    """
    Async database health check.
    
    Returns:
        (is_healthy: bool, message: str)
    """
    try:
        result = database_health_check()
        
        if isinstance(result, DatabaseHealth):
            return result.is_healthy, result.message
        elif isinstance(result, dict):
            return result.get("healthy", False), result.get("message", "")
        else:
            return bool(result), str(result)
    
    except Exception as e:
        return False, f"Database health check failed: {e}"


def check_database_health() -> Tuple[bool, str]:
    """
    Synchronous database health check.
    
    Returns:
        (is_healthy: bool, message: str)
    """
    try:
        result = database_health_check()
        
        if isinstance(result, DatabaseHealth):
            return result.is_healthy, result.message
        elif isinstance(result, dict):
            return result.get("healthy", False), result.get("message", "")
        else:
            return bool(result), str(result)
    
    except Exception as e:
        return False, f"Database health check failed: {e}"


# ==============================================================================
# SERVICE RESET (FOR TESTING / RECONNECTION)
# ==============================================================================

def reset_service_cache():
    """Reset all cached service instances"""
    get_sales_service.cache_clear()
    get_purchase_service.cache_clear()
    get_inventory_service.cache_clear()
    get_refund_service.cache_clear()
    get_receipt_service.cache_clear()
    
    logger.info("Service cache cleared")


# ==============================================================================
# CONNECTION UTILITIES
# ==============================================================================

def test_connection() -> Tuple[bool, str]:
    """
    Test database connection.
    
    Returns:
        (is_connected: bool, message: str)
    """
    try:
        client = get_connection()
        
        # Simple test query
        result = client.table("users").select("id").limit(1).execute()
        
        if result is not None:
            return True, "Database connection successful"
        else:
            return False, "Database connection failed"
    
    except Exception as e:
        return False, f"Database connection error: {e}"


def get_database_info() -> Dict[str, Any]:
    """
    Get database information and statistics.
    
    Returns:
        Dictionary with database info
    """
    info = {
        "version": ERP_DATABASE_VERSION,
        "type": "Supabase",
        "is_connected": False,
        "message": "",
    }
    
    try:
        is_healthy, message = check_database_health()
        info["is_connected"] = is_healthy
        info["message"] = message
        
        # Get table counts
        client = db()
        
        tables = [
            "users",
            "products",
            "inventory",
            "sales",
            "sale_items",
            "purchases",
            "customers",
            "suppliers",
        ]
        
        info["table_counts"] = {}
        
        for table in tables:
            try:
                count = client.table(table).select("id", count="exact").execute()
                info["table_counts"][table] = count.count if hasattr(count, 'count') else len(count.data or [])
            except Exception:
                info["table_counts"][table] = 0
        
    except Exception as e:
        info["message"] = f"Error getting database info: {e}"
    
    return info


# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================

__all__ = [
    # DATABASE
    "db",
    "get_supabase",
    "get_connection",
    "DatabaseHealth",
    "database_health_check",
    "check_database_health",
    "check_database_health_async",
    "test_connection",
    "get_database_info",
    
    # LOADERS
    "get_setting",
    "get_products",
    "get_inventory_view",
    "get_warehouses",
    "get_default_warehouse_id",
    "get_categories",
    "get_suppliers",
    "get_customers",
    
    # RECEIPT
    "get_receipt",
    "get_sale_items",
    "search_receipts",
    
    # RPC
    "checkout_sale_rpc",
    "purchase_receive_rpc",
    "refund_sale_rpc",
    "stock_adjustment_rpc",
    "update_product_rpc",
    "request_product_create_rpc",
    "request_product_bulk_create_rpc",
    "approve_product_create_rpc",
    
    # SERVICES
    "SalesService",
    "PurchaseService",
    "InventoryService",
    "RefundService",
    "ReceiptService",
    "PaymentService",
    "PaymentQRService",
    
    # PAYMENT
    "create_mobile_payment",
    "verify_payment",
    "reject_payment",
    "get_pending_payments",
    "generate_payment_qr",
    
    # SERVICE FACTORIES
    "get_sales_service",
    "get_purchase_service",
    "get_inventory_service",
    "get_refund_service",
    "get_receipt_service",
    "reset_service_cache",
    
    # HELPERS
    "get_fifo_cogs",
    "create_audit_log",
    
    # UTILITIES
    "money",
    "money_float",
    "validate_uuid",
    "serialize_json",
    "safe_execute",
]


# ==============================================================================
# MODULE INITIALIZATION LOG
# ==============================================================================

logger.info("ERP DATABASE GATEWAY v34 LOADED (NiceGUI Version)")

# Remove print statement to avoid console clutter
# Use logger instead for proper logging
