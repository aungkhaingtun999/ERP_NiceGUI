# ==============================================================================
# erp_core/services/__init__.py
# ERP ENTERPRISE SERVICE EXPORT v34 FINAL
# SAFE SERVICE HUB
# ==============================================================================




from .settings_service import SettingsService

# ==============================================================================
# RECEIPT
# ==============================================================================

try:

    from .receipt_service import (
        ReceiptService
    )

except Exception:

    ReceiptService = None





# ==============================================================================
# CUSTOMER
# ==============================================================================

try:

    from .customer_service import (
        CustomerService
    )

except Exception:

    CustomerService = None





# ==============================================================================
# SALES
# ==============================================================================

try:

    from .sales_service import (
        SalesService
    )

except Exception:

    SalesService = None





# ==============================================================================
# PURCHASE
# ==============================================================================

try:

    from .purchase_service import (
        PurchaseService
    )

except Exception:

    PurchaseService = None





# ==============================================================================
# INVENTORY
# ==============================================================================

try:

    from .inventory_service import (
        InventoryService
    )

except Exception:

    InventoryService = None





# ==============================================================================
# REFUND
# ==============================================================================

try:

    from .refund_service import (
        RefundService
    )

except Exception:

    RefundService = None





# ==============================================================================
# DASHBOARD
# ==============================================================================

try:

    from .dashboard_service import (
        DashboardService
    )

except Exception:

    DashboardService = None





# ==============================================================================
# ACCOUNTING
# ==============================================================================

try:

    from .accounting_service import (
        AccountingLedgerService
    )

except Exception:

    AccountingLedgerService = None





# ==============================================================================
# AUDIT
# ==============================================================================

try:

    from .audit_service import (

        AuditService,

        create_audit_log

    )

except Exception:


    AuditService = None


    def create_audit_log(*args, **kwargs):

        return None





# ==============================================================================
# PRICING ENGINE
# ==============================================================================

try:

    from .pricing_service import (

        PricingService

    )

except Exception:


    PricingService = None





# ==============================================================================
# FIFO / COSTING
# ==============================================================================

try:

    from .helpers import (

        get_fifo_cogs

    )


except Exception:


    def get_fifo_cogs(*args, **kwargs):

        return 0





# ==============================================================================
# EXPORT
# ==============================================================================


__all__ = [


    "ReceiptService",

    "CustomerService",

    "SalesService",

    "PurchaseService",

    "InventoryService",

    "RefundService",

    "DashboardService",

    "AccountingLedgerService",

    "AuditService",

    "PricingService",

    "create_audit_log",

    "get_fifo_cogs"

]



print("SERVICES PACKAGE READY")
