# ==============================================================================
# erp_core/exceptions.py
# ERP ENTERPRISE EXCEPTIONS v32 - NiceGUI Version
#
# Comprehensive exception hierarchy for ERP system
#
# ==============================================================================

from typing import Optional, Any, Dict, List
from datetime import datetime
import traceback


# ==============================================================================
# BASE EXCEPTIONS
# ==============================================================================

class ERPException(Exception):
    """
    Base exception for all ERP errors.
    
    Attributes:
        message: Human-readable error message
        code: Error code for client-side handling
        details: Additional error details
        cause: Original exception that caused this error
        timestamp: When the error occurred
    """
    
    def __init__(
        self,
        message: str = "ERP Error",
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        user_id: Optional[str] = None,
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now().isoformat()
        self.user_id = user_id
        
        # Build full error message
        error_parts = [message]
        if code:
            error_parts.append(f"[Code: {code}]")
        if user_id:
            error_parts.append(f"[User: {user_id}]")
        
        super().__init__(" | ".join(error_parts))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "traceback": traceback.format_exc() if self.cause else None,
        }
    
    def to_json(self) -> str:
        """Convert exception to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)


# ==============================================================================
# DATABASE ERRORS
# ==============================================================================

class DatabaseError(ERPException):
    """Base exception for database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass


class QueryError(DatabaseError):
    """Exception raised when a database query fails."""
    pass


class RecordNotFoundError(DatabaseError):
    """Exception raised when a record is not found."""
    
    def __init__(
        self,
        table: Optional[str] = None,
        record_id: Optional[str] = None,
        message: Optional[str] = None,
        **kwargs
    ):
        if message is None:
            message = f"Record not found"
            if table:
                message += f" in {table}"
            if record_id:
                message += f" with ID: {record_id}"
        
        super().__init__(
            message=message,
            details={"table": table, "record_id": record_id},
            **kwargs
        )


class DuplicateRecordError(DatabaseError):
    """Exception raised when a duplicate record is detected."""
    
    def __init__(
        self,
        table: Optional[str] = None,
        field: Optional[str] = None,
        value: Optional[str] = None,
        **kwargs
    ):
        message = "Duplicate record"
        if table:
            message += f" in {table}"
        if field and value:
            message += f": {field}='{value}'"
        
        super().__init__(
            message=message,
            details={"table": table, "field": field, "value": value},
            **kwargs
        )


class IntegrityError(DatabaseError):
    """Exception raised when database integrity is violated."""
    pass


# ==============================================================================
# VALIDATION ERRORS
# ==============================================================================

class ValidationError(ERPException):
    """Base exception for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation error",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraints: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        if constraints:
            details["constraints"] = constraints
        
        super().__init__(
            message=message,
            details=details,
            **kwargs
        )


class RequiredFieldError(ValidationError):
    """Exception raised when a required field is missing."""
    
    def __init__(self, field: str, **kwargs):
        super().__init__(
            message=f"Required field missing: {field}",
            field=field,
            **kwargs
        )


class InvalidFormatError(ValidationError):
    """Exception raised when data is in invalid format."""
    
    def __init__(
        self,
        field: str,
        value: Any,
        expected_format: Optional[str] = None,
        **kwargs
    ):
        message = f"Invalid format for {field}"
        if expected_format:
            message += f", expected: {expected_format}"
        
        super().__init__(
            message=message,
            field=field,
            value=value,
            constraints={"expected_format": expected_format},
            **kwargs
        )


class InvalidRangeError(ValidationError):
    """Exception raised when value is outside valid range."""
    
    def __init__(
        self,
        field: str,
        value: Any,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None,
        **kwargs
    ):
        message = f"Value out of range for {field}"
        if min_value is not None:
            message += f", min: {min_value}"
        if max_value is not None:
            message += f", max: {max_value}"
        
        super().__init__(
            message=message,
            field=field,
            value=value,
            constraints={"min": min_value, "max": max_value},
            **kwargs
        )


class InvalidChoiceError(ValidationError):
    """Exception raised when value is not in allowed choices."""
    
    def __init__(
        self,
        field: str,
        value: Any,
        choices: List[Any],
        **kwargs
    ):
        super().__init__(
            message=f"Invalid choice for {field}: {value}",
            field=field,
            value=value,
            constraints={"choices": choices},
            **kwargs
        )


# ==============================================================================
# PERMISSION ERRORS
# ==============================================================================

class PermissionDeniedError(ERPException):
    """Exception raised when permission is denied."""
    
    def __init__(
        self,
        message: str = "Permission denied",
        permission: Optional[str] = None,
        resource: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if permission:
            details["permission"] = permission
        if resource:
            details["resource"] = resource
        
        super().__init__(
            message=message,
            details=details,
            **kwargs
        )


class AuthenticationError(PermissionDeniedError):
    """Exception raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs
    ):
        super().__init__(message=message, **kwargs)


class SessionExpiredError(PermissionDeniedError):
    """Exception raised when session has expired."""
    
    def __init__(
        self,
        message: str = "Session expired",
        **kwargs
    ):
        super().__init__(message=message, **kwargs)


class InsufficientRoleError(PermissionDeniedError):
    """Exception raised when user role is insufficient."""
    
    def __init__(
        self,
        required_role: str,
        current_role: Optional[str] = None,
        **kwargs
    ):
        message = f"Insufficient role"
        if required_role:
            message += f", required: {required_role}"
        if current_role:
            message += f", current: {current_role}"
        
        super().__init__(
            message=message,
            details={"required_role": required_role, "current_role": current_role},
            **kwargs
        )


# ==============================================================================
# TRANSACTION ERRORS
# ==============================================================================

class TransactionError(ERPException):
    """Base exception for transaction-related errors."""
    pass


class DuplicateTransactionError(TransactionError):
    """Exception raised for duplicate transactions."""
    
    def __init__(
        self,
        transaction_id: Optional[str] = None,
        **kwargs
    ):
        message = "Duplicate transaction"
        if transaction_id:
            message += f": {transaction_id}"
        
        super().__init__(
            message=message,
            details={"transaction_id": transaction_id},
            **kwargs
        )


class TransactionNotFoundError(TransactionError):
    """Exception raised when transaction is not found."""
    
    def __init__(
        self,
        transaction_id: Optional[str] = None,
        **kwargs
    ):
        message = "Transaction not found"
        if transaction_id:
            message += f": {transaction_id}"
        
        super().__init__(
            message=message,
            details={"transaction_id": transaction_id},
            **kwargs
        )


class TransactionRollbackError(TransactionError):
    """Exception raised when transaction rollback fails."""
    pass


class TransactionTimeoutError(TransactionError):
    """Exception raised when transaction times out."""
    pass


class TransactionLockError(TransactionError):
    """Exception raised when record is locked."""
    
    def __init__(
        self,
        record_id: Optional[str] = None,
        table: Optional[str] = None,
        **kwargs
    ):
        message = "Record is locked"
        if table:
            message += f" in {table}"
        if record_id:
            message += f" with ID: {record_id}"
        
        super().__init__(
            message=message,
            details={"table": table, "record_id": record_id},
            **kwargs
        )


# ==============================================================================
# ACCOUNTING ERRORS
# ==============================================================================

class AccountingError(ERPException):
    """Base exception for accounting-related errors."""
    pass


class AccountingPeriodClosedError(AccountingError):
    """Exception raised when accounting period is closed."""
    
    def __init__(
        self,
        period: Optional[str] = None,
        **kwargs
    ):
        message = "Accounting period is closed"
        if period:
            message += f": {period}"
        
        super().__init__(
            message=message,
            details={"period": period},
            **kwargs
        )


class AccountingPeriodNotFoundError(AccountingError):
    """Exception raised when accounting period is not found."""
    
    def __init__(
        self,
        period: Optional[str] = None,
        **kwargs
    ):
        message = "Accounting period not found"
        if period:
            message += f": {period}"
        
        super().__init__(
            message=message,
            details={"period": period},
            **kwargs
        )


class JournalEntryError(AccountingError):
    """Exception raised when journal entry is invalid."""
    
    def __init__(
        self,
        message: str = "Invalid journal entry",
        entries: Optional[List[Dict]] = None,
        **kwargs
    ):
        super().__init__(
            message=message,
            details={"entries": entries},
            **kwargs
        )


class BalanceError(AccountingError):
    """Exception raised when accounts don't balance."""
    
    def __init__(
        self,
        debit_total: Optional[float] = None,
        credit_total: Optional[float] = None,
        difference: Optional[float] = None,
        **kwargs
    ):
        message = "Debit and credit totals don't balance"
        if debit_total is not None and credit_total is not None:
            message += f" (Debit: {debit_total}, Credit: {credit_total})"
            difference = credit_total - debit_total
            message += f", Difference: {difference}"
        
        super().__init__(
            message=message,
            details={
                "debit_total": debit_total,
                "credit_total": credit_total,
                "difference": difference,
            },
            **kwargs
        )


# ==============================================================================
# CREDIT ERRORS
# ==============================================================================

class CreditLimitError(ERPException):
    """Base exception for credit limit errors."""
    pass


class CreditLimitExceededError(CreditLimitError):
    """Exception raised when credit limit is exceeded."""
    
    def __init__(
        self,
        customer_id: Optional[str] = None,
        limit: Optional[float] = None,
        current_balance: Optional[float] = None,
        **kwargs
    ):
        message = "Credit limit exceeded"
        if customer_id:
            message += f" for customer: {customer_id}"
        if limit is not None:
            message += f", Limit: {limit}"
        if current_balance is not None:
            message += f", Balance: {current_balance}"
        
        super().__init__(
            message=message,
            details={
                "customer_id": customer_id,
                "limit": limit,
                "current_balance": current_balance,
            },
            **kwargs
        )


class CreditLimitNotSetError(CreditLimitError):
    """Exception raised when credit limit is not set."""
    
    def __init__(
        self,
        customer_id: Optional[str] = None,
        **kwargs
    ):
        message = "Credit limit not set"
        if customer_id:
            message += f" for customer: {customer_id}"
        
        super().__init__(
            message=message,
            details={"customer_id": customer_id},
            **kwargs
        )


# ==============================================================================
# RPC ERRORS
# ==============================================================================

class RPCError(ERPException):
    """Base exception for RPC-related errors."""
    
    def __init__(
        self,
        message: str = "RPC error",
        rpc_name: Optional[str] = None,
        params: Optional[Dict] = None,
        **kwargs
    ):
        details = kwargs.pop("details", {})
        if rpc_name:
            details["rpc_name"] = rpc_name
        if params:
            details["params"] = params
        
        super().__init__(
            message=message,
            details=details,
            **kwargs
        )


class RPCTimeoutError(RPCError):
    """Exception raised when RPC times out."""
    
    def __init__(
        self,
        timeout: Optional[int] = None,
        **kwargs
    ):
        message = "RPC timeout"
        if timeout:
            message += f" after {timeout}s"
        
        super().__init__(
            message=message,
            details={"timeout": timeout},
            **kwargs
        )


class RPCNotFoundError(RPCError):
    """Exception raised when RPC is not found."""
    
    def __init__(
        self,
        rpc_name: Optional[str] = None,
        **kwargs
    ):
        message = "RPC not found"
        if rpc_name:
            message += f": {rpc_name}"
        
        super().__init__(
            message=message,
            rpc_name=rpc_name,
            **kwargs
        )


class RPCInvalidParamsError(RPCError):
    """Exception raised when RPC parameters are invalid."""
    
    def __init__(
        self,
        param: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        message = "Invalid RPC parameters"
        if param:
            message += f" for parameter: {param}"
        
        super().__init__(
            message=message,
            details={"param": param, "value": value},
            **kwargs
        )


class RPCPermissionError(RPCError, PermissionDeniedError):
    """Exception raised when RPC permission is denied."""
    
    def __init__(
        self,
        rpc_name: Optional[str] = None,
        permission: Optional[str] = None,
        **kwargs
    ):
        message = "RPC permission denied"
        if rpc_name:
            message += f" for: {rpc_name}"
        
        super().__init__(
            message=message,
            rpc_name=rpc_name,
            permission=permission,
            **kwargs
        )


# ==============================================================================
# INVENTORY ERRORS
# ==============================================================================

class InventoryError(ERPException):
    """Base exception for inventory-related errors."""
    pass


class InsufficientStockError(InventoryError):
    """Exception raised when stock is insufficient."""
    
    def __init__(
        self,
        product_id: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        requested: Optional[float] = None,
        available: Optional[float] = None,
        **kwargs
    ):
        message = "Insufficient stock"
        if product_id:
            message += f" for product: {product_id}"
        if warehouse_id:
            message += f" at warehouse: {warehouse_id}"
        if requested is not None:
            message += f", Requested: {requested}"
        if available is not None:
            message += f", Available: {available}"
        
        super().__init__(
            message=message,
            details={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "requested": requested,
                "available": available,
            },
            **kwargs
        )


class ProductNotFoundError(InventoryError):
    """Exception raised when product is not found."""
    
    def __init__(
        self,
        product_id: Optional[str] = None,
        sku: Optional[str] = None,
        **kwargs
    ):
        message = "Product not found"
        if sku:
            message += f" with SKU: {sku}"
        elif product_id:
            message += f" with ID: {product_id}"
        
        super().__init__(
            message=message,
            details={"product_id": product_id, "sku": sku},
            **kwargs
        )


class WarehouseNotFoundError(InventoryError):
    """Exception raised when warehouse is not found."""
    
    def __init__(
        self,
        warehouse_id: Optional[str] = None,
        **kwargs
    ):
        message = "Warehouse not found"
        if warehouse_id:
            message += f": {warehouse_id}"
        
        super().__init__(
            message=message,
            details={"warehouse_id": warehouse_id},
            **kwargs
        )


# ==============================================================================
# SETTINGS ERRORS
# ==============================================================================

class SettingsError(ERPException):
    """Base exception for settings-related errors."""
    pass


class SettingsNotFoundError(SettingsError):
    """Exception raised when setting is not found."""
    
    def __init__(
        self,
        key: Optional[str] = None,
        **kwargs
    ):
        message = "Setting not found"
        if key:
            message += f": {key}"
        
        super().__init__(
            message=message,
            details={"key": key},
            **kwargs
        )


class SettingsInvalidValueError(SettingsError):
    """Exception raised when setting value is invalid."""
    
    def __init__(
        self,
        key: Optional[str] = None,
        value: Optional[Any] = None,
        expected_type: Optional[str] = None,
        **kwargs
    ):
        message = "Invalid setting value"
        if key:
            message += f" for: {key}"
        if expected_type:
            message += f", expected type: {expected_type}"
        
        super().__init__(
            message=message,
            details={"key": key, "value": value, "expected_type": expected_type},
            **kwargs
        )


class SettingsChangeNotAllowedError(SettingsError):
    """Exception raised when settings change is not allowed."""
    
    def __init__(
        self,
        key: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ):
        message = "Settings change not allowed"
        if key:
            message += f" for: {key}"
        if reason:
            message += f" ({reason})"
        
        super().__init__(
            message=message,
            details={"key": key, "reason": reason},
            **kwargs
        )


# ==============================================================================
# MAKER-CHECKER ERRORS
# ==============================================================================

class MakerCheckerError(ERPException):
    """Base exception for maker-checker related errors."""
    pass


class ApprovalRequiredError(MakerCheckerError):
    """Exception raised when approval is required."""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        request_type: Optional[str] = None,
        **kwargs
    ):
        message = "Approval required"
        if request_type:
            message += f" for: {request_type}"
        if request_id:
            message += f" (Request ID: {request_id})"
        
        super().__init__(
            message=message,
            details={"request_id": request_id, "request_type": request_type},
            **kwargs
        )


class ApprovalNotFoundError(MakerCheckerError):
    """Exception raised when approval request is not found."""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        **kwargs
    ):
        message = "Approval request not found"
        if request_id:
            message += f": {request_id}"
        
        super().__init__(
            message=message,
            details={"request_id": request_id},
            **kwargs
        )


class ApprovalAlreadyProcessedError(MakerCheckerError):
    """Exception raised when approval is already processed."""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs
    ):
        message = "Approval already processed"
        if request_id:
            message += f": {request_id}"
        if status:
            message += f" (Status: {status})"
        
        super().__init__(
            message=message,
            details={"request_id": request_id, "status": status},
            **kwargs
        )


class ApprovalPermissionError(MakerCheckerError, PermissionDeniedError):
    """Exception raised when user cannot approve."""
    
    def __init__(
        self,
        request_id: Optional[str] = None,
        required_role: Optional[str] = None,
        **kwargs
    ):
        message = "You don't have permission to approve this request"
        if required_role:
            message += f", required role: {required_role}"
        
        super().__init__(
            message=message,
            details={"request_id": request_id, "required_role": required_role},
            **kwargs
        )


# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    # Base
    "ERPException",
    
    # Database
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    "IntegrityError",
    
    # Validation
    "ValidationError",
    "RequiredFieldError",
    "InvalidFormatError",
    "InvalidRangeError",
    "InvalidChoiceError",
    
    # Permission
    "PermissionDeniedError",
    "AuthenticationError",
    "SessionExpiredError",
    "InsufficientRoleError",
    
    # Transaction
    "TransactionError",
    "DuplicateTransactionError",
    "TransactionNotFoundError",
    "TransactionRollbackError",
    "TransactionTimeoutError",
    "TransactionLockError",
    
    # Accounting
    "AccountingError",
    "AccountingPeriodClosedError",
    "AccountingPeriodNotFoundError",
    "JournalEntryError",
    "BalanceError",
    
    # Credit
    "CreditLimitError",
    "CreditLimitExceededError",
    "CreditLimitNotSetError",
    
    # RPC
    "RPCError",
    "RPCTimeoutError",
    "RPCNotFoundError",
    "RPCInvalidParamsError",
    "RPCPermissionError",
    
    # Inventory
    "InventoryError",
    "InsufficientStockError",
    "ProductNotFoundError",
    "WarehouseNotFoundError",
    
    # Settings
    "SettingsError",
    "SettingsNotFoundError",
    "SettingsInvalidValueError",
    "SettingsChangeNotAllowedError",
    
    # Maker-Checker
    "MakerCheckerError",
    "ApprovalRequiredError",
    "ApprovalNotFoundError",
    "ApprovalAlreadyProcessedError",
    "ApprovalPermissionError",
]

print("ERP EXCEPTIONS READY - NiceGUI Version")
