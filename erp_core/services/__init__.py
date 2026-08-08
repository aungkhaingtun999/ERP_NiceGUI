# ==============================================================================
# erp_core/services/__init__.py
# ERP ENTERPRISE SERVICES
#
# CI/CD SAFE SERVICE EXPORTS
#
# IMPORTANT:
# Do NOT import every service here.
#
# Importing every service can trigger repositories which initialize Supabase
# during module import. That breaks isolated pytest / CI environments.
# ==============================================================================


# ==============================================================================
# CORE SERVICES
# ==============================================================================

from .inventory_service import InventoryService


# ==============================================================================
# OPTIONAL SERVICES
#
# Import these directly from their own modules when needed:
#
# from erp_core.services.sales_service import SalesService
# from erp_core.services.purchase_service import PurchaseService
# from erp_core.services.payment_service import PaymentService
# from erp_core.services.refund_service import RefundService
# from erp_core.services.receipt_service import ReceiptService
# from erp_core.services.settings_service import SettingsService
# ==============================================================================


__all__ = [
    "InventoryService",
]
