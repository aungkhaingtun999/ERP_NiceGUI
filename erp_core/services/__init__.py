# ==============================================================================
# erp_core/services/__init__.py
# ERP ENTERPRISE SERVICE EXPORT v34 SAFE
# ==============================================================================


print("SERVICES PACKAGE START")



from .receipt_service import (
    ReceiptService
)



try:

    from .customer_service import (
        CustomerService
    )

except Exception:

    CustomerService = None




try:

    from .sales_service import (
        SalesService
    )

except Exception:

    SalesService = None




try:

    from .purchase_service import (
        PurchaseService
    )

except Exception:

    PurchaseService = None




try:

    from .inventory_service import (
        InventoryService
    )

except Exception:

    InventoryService = None




try:

    from .refund_service import (
        RefundService
    )

except Exception:

    RefundService = None




try:

    from .dashboard_service import (
        DashboardService
    )

except Exception:

    DashboardService = None




try:

    from .accounting_service import (
        AccountingLedgerService
    )

except Exception:

    AccountingLedgerService = None




try:

    from .audit_service import (
        AuditService,
        create_audit_log
    )

except Exception:


    AuditService = None


    def create_audit_log(*args, **kwargs):

        return None




try:

    from .helpers import (
        get_fifo_cogs
    )

except Exception:


    def get_fifo_cogs(*args, **kwargs):

        return 0





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

    "create_audit_log",

    "get_fifo_cogs"

]



print("SERVICES PACKAGE READY")
