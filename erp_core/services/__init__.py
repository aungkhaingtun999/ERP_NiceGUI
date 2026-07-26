# ==============================================================================
# erp_core/services/__init__.py
# ERP ENTERPRISE SERVICE LAYER v30.12
# SAFE SERVICE EXPORT PACKAGE
# ==============================================================================


"""
ERP Service Layer Package

Structure:

erp_core
 |
 └── services
        |
        ├── __init__.py
        ├── sales_service.py
        ├── customer_service.py
        ├── purchase_service.py
        ├── inventory_service.py
        ├── refund_service.py
        ├── dashboard_service.py
        └── audit_service.py


Only exports service classes.
"""


print(
    "SERVICES PACKAGE START"
)



# ==============================================================================
# CORE IMPORTS
# ==============================================================================

from .receipt_service import (
    ReceiptService
)
from erp_core.exceptions import *


from erp_core.config import (

    log_error

)




# ==============================================================================
# CUSTOMER
# ==============================================================================


from .customer_service import (

    CustomerService

)




# ==============================================================================
# SALES
# ==============================================================================


from .sales_service import (

    SalesService

)




# ==============================================================================
# PURCHASE
# ==============================================================================


from .purchase_service import (

    PurchaseService

)




# ==============================================================================
# INVENTORY
# ==============================================================================


from .inventory_service import (

    InventoryService

)




# ==============================================================================
# REFUND
# ==============================================================================


from .refund_service import (

    RefundService

)




# ==============================================================================
# DASHBOARD
# ==============================================================================


from .dashboard_service import (

    DashboardService

)




# ==============================================================================
# ACCOUNTING
# ==============================================================================


from .accounting_service import (

    AccountingLedgerService

)




# ==============================================================================
# AUDIT
# ==============================================================================
from .audit_service import create_audit_log

from .audit_service import (

    AuditService

)



# ==============================================================================
# RECEIPT
# ==============================================================================


from .receipt_service import (

    ReceiptService

)
# ==============================================================================
# HELPERS
# ==============================================================================


from .helpers import (

    get_fifo_cogs,

    create_audit_log

)




# ==============================================================================
# PUBLIC EXPORTS
# ==============================================================================


__all__ = [

    "SalesService",

    "CustomerService",

    "PurchaseService",

    "InventoryService",

    "RefundService",

    "DashboardService",

    "AccountingLedgerService",

    "AuditService",
    "ReceiptService",

    "get_fifo_cogs",

    "create_audit_log"

]



print(
    "SERVICES PACKAGE READY"
)
