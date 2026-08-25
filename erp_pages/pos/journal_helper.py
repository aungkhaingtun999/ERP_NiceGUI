# ==============================================================================
# erp_pages/POS/journal_helper.py
# POS Journal Entry Helper for Double Entry System - NiceGUI Version
# Version v2.0
# ==============================================================================

"""
POS Journal Helper
------------------
Handles double-entry accounting for POS transactions.

Features:
- Automatic debit/credit posting
- Multiple payment methods support
- Error handling with NiceGUI notifications
- Transaction validation
- Audit trail
- Batch posting support
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from erp_core.base_repo import db, privileged_db, money_float
from erp_core.context import ERPContext
from erp_core.exceptions import (
    AccountingError,
    TransactionError,
    ValidationError,
    DatabaseError,
)
from erp_core.config import Tables, log_error
from erp_pages.pos.cache import refresh_sales


# ==============================================================================
# CONSTANTS
# ==============================================================================

class AccountType:
    """Account types for journal entries."""
    
    CASH = 1
    BANK = 2
    RECEIVABLE = 3
    REVENUE = 4
    COGS = 5
    INVENTORY = 6
    TAX = 7
    DISCOUNT = 8
    SALES_RETURN = 9
    PAYMENT = 10
    
    @classmethod
    def get_name(cls, account_id: int) -> str:
        """Get account name by ID."""
        names = {
            cls.CASH: "Cash",
            cls.BANK: "Bank",
            cls.RECEIVABLE: "Accounts Receivable",
            cls.REVENUE: "Sales Revenue",
            cls.COGS: "Cost of Goods Sold",
            cls.INVENTORY: "Inventory",
            cls.TAX: "Sales Tax Payable",
            cls.DISCOUNT: "Sales Discount",
            cls.SALES_RETURN: "Sales Return",
            cls.PAYMENT: "Payment",
        }
        return names.get(account_id, f"Account {account_id}")
    
    @classmethod
    def get_payment_account(cls, payment_method: str) -> int:
        """Get account ID for payment method."""
        method_map = {
            "CASH": cls.CASH,
            "BANK": cls.BANK,
            "CARD": cls.BANK,
            "MOBILE_PAYMENT": cls.BANK,
            "CREDIT": cls.RECEIVABLE,
            "CHECK": cls.BANK,
        }
        return method_map.get(payment_method.upper(), cls.CASH)


class JournalEntryType:
    """Journal entry types."""
    
    SALE = "sale"
    REFUND = "refund"
    PAYMENT = "payment"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"


# ==============================================================================
# JOURNAL ENTRY DATA CLASS
# ==============================================================================

from dataclasses import dataclass, field


@dataclass
class JournalEntry:
    """Journal entry data class."""
    
    sale_id: Optional[str] = None
    account_id: int = 0
    debit: float = 0.0
    credit: float = 0.0
    description: str = ""
    reference: Optional[str] = None
    entry_type: str = JournalEntryType.SALE
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate entry."""
        if self.debit < 0 or self.credit < 0:
            raise ValidationError("Debit and credit must be non-negative")
        
        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Entry cannot have both debit and credit")
        
        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Entry must have either debit or credit")
        
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database."""
        return {
            "sale_id": self.sale_id,
            "account_id": self.account_id,
            "debit": money_float(self.debit),
            "credit": money_float(self.credit),
            "description": self.description,
            "reference": self.reference,
            "entry_type": self.entry_type,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }


@dataclass
class JournalBatch:
    """Batch of journal entries."""
    
    entries: List[JournalEntry] = field(default_factory=list)
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    total_debit: float = 0.0
    total_credit: float = 0.0
    
    def add_entry(self, entry: JournalEntry):
        """Add entry to batch."""
        self.entries.append(entry)
        self.total_debit += entry.debit
        self.total_credit += entry.credit
    
    def validate(self) -> bool:
        """Validate batch (debits must equal credits)."""
        if not self.entries:
            raise ValidationError("Batch has no entries")
        
        if abs(self.total_debit - self.total_credit) > 0.01:
            raise BalanceError(
                f"Debit ({self.total_debit}) does not equal Credit ({self.total_credit})",
                debit_total=self.total_debit,
                credit_total=self.total_credit,
            )
        
        return True


# ==============================================================================
# JOURNAL HELPER
# ==============================================================================

class POSJournalHelper:
    """
    POS Journal Helper for double-entry accounting.
    """
    
    def __init__(self, use_privileged: bool = False):
        """
        Initialize journal helper.
        
        Args:
            use_privileged: Use privileged database connection
        """
        self.use_privileged = use_privileged
        self.client = privileged_db() if use_privileged else db()
        self.context = ERPContext.get_current()
    
    # --------------------------------------------------------------------------
    # Core Functions
    # --------------------------------------------------------------------------
    
    def post_sale_journal_entry(
        self,
        sale_id: Union[str, int],
        total_amount: float,
        payment_method: str = "CASH",
        tax_amount: float = 0.0,
        discount_amount: float = 0.0,
        customer_id: Optional[str] = None,
        sale_items: Optional[List[Dict]] = None,
    ) -> bool:
        """
        Post sale journal entry with double entry.
        
        Args:
            sale_id: Sale ID
            total_amount: Total sale amount
            payment_method: Payment method (CASH, CARD, BANK, CREDIT, etc.)
            tax_amount: Tax amount
            discount_amount: Discount amount
            customer_id: Customer ID for credit sales
            sale_items: Sale items for COGS posting
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate input
            if not sale_id:
                raise ValidationError("Sale ID is required")
            
            if total_amount <= 0:
                raise ValidationError(f"Invalid total amount: {total_amount}")
            
            # Create journal batch
            batch = self._create_sale_batch(
                sale_id=str(sale_id),
                total_amount=total_amount,
                payment_method=payment_method,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                customer_id=customer_id,
                sale_items=sale_items,
            )
            
            # Post batch
            return self.post_batch(batch)
            
        except Exception as e:
            log_error(
                message=f"Failed to post sale journal: {sale_id}",
                exception=e,
                payload={
                    "sale_id": sale_id,
                    "total_amount": total_amount,
                    "payment_method": payment_method,
                }
            )
            raise
    
    def post_refund_journal_entry(
        self,
        refund_id: Union[str, int],
        refund_amount: float,
        original_sale_id: Optional[str] = None,
        payment_method: str = "CASH",
    ) -> bool:
        """
        Post refund journal entry.
        
        Args:
            refund_id: Refund ID
            refund_amount: Refund amount
            original_sale_id: Original sale ID
            payment_method: Payment method for refund
        
        Returns:
            True if successful, False otherwise
        """
        try:
            batch = self._create_refund_batch(
                refund_id=str(refund_id),
                refund_amount=refund_amount,
                original_sale_id=original_sale_id,
                payment_method=payment_method,
            )
            
            return self.post_batch(batch)
            
        except Exception as e:
            log_error(
                message=f"Failed to post refund journal: {refund_id}",
                exception=e,
            )
            raise
    
    def post_payment_journal_entry(
        self,
        payment_id: Union[str, int],
        amount: float,
        payment_method: str = "CASH",
        customer_id: Optional[str] = None,
    ) -> bool:
        """
        Post payment journal entry.
        
        Args:
            payment_id: Payment ID
            amount: Payment amount
            payment_method: Payment method
            customer_id: Customer ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            batch = self._create_payment_batch(
                payment_id=str(payment_id),
                amount=amount,
                payment_method=payment_method,
                customer_id=customer_id,
            )
            
            return self.post_batch(batch)
            
        except Exception as e:
            log_error(
                message=f"Failed to post payment journal: {payment_id}",
                exception=e,
            )
            raise
    
    # --------------------------------------------------------------------------
    # Batch Creation
    # --------------------------------------------------------------------------
    
    def _create_sale_batch(
        self,
        sale_id: str,
        total_amount: float,
        payment_method: str,
        tax_amount: float = 0.0,
        discount_amount: float = 0.0,
        customer_id: Optional[str] = None,
        sale_items: Optional[List[Dict]] = None,
    ) -> JournalBatch:
        """
        Create journal batch for sale.
        
        Returns:
            JournalBatch instance
        """
        batch = JournalBatch()
        user_id = self.context.user_id
        
        # Calculate net amount
        net_amount = total_amount - tax_amount - discount_amount
        
        # Determine payment account
        payment_account = AccountType.get_payment_account(payment_method)
        
        # 1. Debit: Cash/Bank/Receivable (Payment account)
        if payment_method.upper() == "CREDIT":
            # Credit sale - debit receivable
            debit_account = AccountType.RECEIVABLE
            batch.add_entry(JournalEntry(
                sale_id=sale_id,
                account_id=debit_account,
                debit=total_amount,
                credit=0,
                description=f"Sale #{sale_id} - Credit sale to customer {customer_id or ''}",
                entry_type=JournalEntryType.SALE,
                created_by=user_id,
                metadata={"customer_id": customer_id, "payment_method": payment_method},
            ))
        else:
            # Cash sale - debit cash/bank
            batch.add_entry(JournalEntry(
                sale_id=sale_id,
                account_id=payment_account,
                debit=total_amount,
                credit=0,
                description=f"Sale #{sale_id} - Payment via {payment_method}",
                entry_type=JournalEntryType.SALE,
                created_by=user_id,
                metadata={"payment_method": payment_method},
            ))
        
        # 2. Credit: Sales Revenue
        batch.add_entry(JournalEntry(
            sale_id=sale_id,
            account_id=AccountType.REVENUE,
            debit=0,
            credit=net_amount,
            description=f"Sale #{sale_id} - Revenue",
            entry_type=JournalEntryType.SALE,
            created_by=user_id,
        ))
        
        # 3. Credit: Tax Payable (if tax amount > 0)
        if tax_amount > 0:
            batch.add_entry(JournalEntry(
                sale_id=sale_id,
                account_id=AccountType.TAX,
                debit=0,
                credit=tax_amount,
                description=f"Sale #{sale_id} - Sales Tax",
                entry_type=JournalEntryType.SALE,
                created_by=user_id,
                metadata={"tax_amount": tax_amount},
            ))
        
        # 4. Debit: Sales Discount (if discount amount > 0)
        if discount_amount > 0:
            batch.add_entry(JournalEntry(
                sale_id=sale_id,
                account_id=AccountType.DISCOUNT,
                debit=discount_amount,
                credit=0,
                description=f"Sale #{sale_id} - Discount",
                entry_type=JournalEntryType.SALE,
                created_by=user_id,
                metadata={"discount_amount": discount_amount},
            ))
        
        # 5. COGS and Inventory (if sale items provided)
        if sale_items:
            total_cogs = 0
            for item in sale_items:
                quantity = item.get('quantity', 0)
                cost = item.get('cost', 0)
                if quantity > 0 and cost > 0:
                    cogs_amount = quantity * cost
                    total_cogs += cogs_amount
            
            if total_cogs > 0:
                # Debit: COGS
                batch.add_entry(JournalEntry(
                    sale_id=sale_id,
                    account_id=AccountType.COGS,
                    debit=total_cogs,
                    credit=0,
                    description=f"Sale #{sale_id} - Cost of Goods Sold",
                    entry_type=JournalEntryType.SALE,
                    created_by=user_id,
                    metadata={"items_count": len(sale_items)},
                ))
                
                # Credit: Inventory
                batch.add_entry(JournalEntry(
                    sale_id=sale_id,
                    account_id=AccountType.INVENTORY,
                    debit=0,
                    credit=total_cogs,
                    description=f"Sale #{sale_id} - Inventory Reduction",
                    entry_type=JournalEntryType.SALE,
                    created_by=user_id,
                ))
        
        # Validate batch
        batch.validate()
        
        return batch
    
    def _create_refund_batch(
        self,
        refund_id: str,
        refund_amount: float,
        original_sale_id: Optional[str] = None,
        payment_method: str = "CASH",
    ) -> JournalBatch:
        """Create journal batch for refund."""
        batch = JournalBatch()
        user_id = self.context.user_id
        
        # Reverse the sale entries
        payment_account = AccountType.get_payment_account(payment_method)
        
        # 1. Credit: Cash/Bank (refund payment)
        batch.add_entry(JournalEntry(
            sale_id=original_sale_id,
            account_id=payment_account,
            debit=0,
            credit=refund_amount,
            description=f"Refund #{refund_id} - Refund via {payment_method}",
            entry_type=JournalEntryType.REFUND,
            created_by=user_id,
            metadata={"refund_id": refund_id, "original_sale_id": original_sale_id},
        ))
        
        # 2. Debit: Revenue (reverse revenue)
        batch.add_entry(JournalEntry(
            sale_id=original_sale_id,
            account_id=AccountType.REVENUE,
            debit=refund_amount,
            credit=0,
            description=f"Refund #{refund_id} - Revenue Reversal",
            entry_type=JournalEntryType.REFUND,
            created_by=user_id,
        ))
        
        # Validate batch
        batch.validate()
        
        return batch
    
    def _create_payment_batch(
        self,
        payment_id: str,
        amount: float,
        payment_method: str,
        customer_id: Optional[str] = None,
    ) -> JournalBatch:
        """Create journal batch for payment."""
        batch = JournalBatch()
        user_id = self.context.user_id
        
        payment_account = AccountType.get_payment_account(payment_method)
        
        # 1. Debit: Cash/Bank
        batch.add_entry(JournalEntry(
            sale_id=payment_id,
            account_id=payment_account,
            debit=amount,
            credit=0,
            description=f"Payment #{payment_id} - Received via {payment_method}",
            entry_type=JournalEntryType.PAYMENT,
            created_by=user_id,
            metadata={"payment_id": payment_id, "customer_id": customer_id},
        ))
        
        # 2. Credit: Receivable (if customer provided)
        if customer_id:
            batch.add_entry(JournalEntry(
                sale_id=payment_id,
                account_id=AccountType.RECEIVABLE,
                debit=0,
                credit=amount,
                description=f"Payment #{payment_id} - Customer payment",
                entry_type=JournalEntryType.PAYMENT,
                created_by=user_id,
                metadata={"payment_id": payment_id, "customer_id": customer_id},
            ))
        else:
            # Credit: Revenue (for over-the-counter payments)
            batch.add_entry(JournalEntry(
                sale_id=payment_id,
                account_id=AccountType.REVENUE,
                debit=0,
                credit=amount,
                description=f"Payment #{payment_id} - Revenue",
                entry_type=JournalEntryType.PAYMENT,
                created_by=user_id,
            ))
        
        # Validate batch
        batch.validate()
        
        return batch
    
    # --------------------------------------------------------------------------
    # Database Operations
    # --------------------------------------------------------------------------
    
    def post_batch(self, batch: JournalBatch) -> bool:
        """
        Post journal batch to database.
        
        Args:
            batch: Journal batch
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate batch
            batch.validate()
            
            # Convert entries to dict
            entries_data = [entry.to_dict() for entry in batch.entries]
            
            # Insert into database
            result = self.client.table("journal_entries").insert(entries_data).execute()
            
            # Check for errors
            if hasattr(result, 'error') and result.error:
                raise DatabaseError(f"Failed to insert journal entries: {result.error}")
            
            # Refresh sales cache
            refresh_sales()
            
            return True
            
        except Exception as e:
            log_error(
                message="Failed to post journal batch",
                exception=e,
                payload={
                    "transaction_id": batch.transaction_id,
                    "entries_count": len(batch.entries),
                }
            )
            raise
    
    def get_journal_entries(
        self,
        sale_id: Optional[str] = None,
        account_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get journal entries with filters.
        
        Args:
            sale_id: Filter by sale ID
            account_id: Filter by account ID
            date_from: Filter by date from
            date_to: Filter by date to
            limit: Limit results
            offset: Offset results
        
        Returns:
            List of journal entries
        """
        try:
            query = self.client.table("journal_entries").select("*")
            
            if sale_id:
                query = query.eq("sale_id", sale_id)
            
            if account_id:
                query = query.eq("account_id", account_id)
            
            if date_from:
                query = query.gte("created_at", date_from.isoformat())
            
            if date_to:
                query = query.lte("created_at", date_to.isoformat())
            
            query = query.order("created_at", desc=True)
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            
            if hasattr(result, 'error') and result.error:
                raise DatabaseError(f"Failed to get journal entries: {result.error}")
            
            return result.data if result else []
            
        except Exception as e:
            log_error(
                message="Failed to get journal entries",
                exception=e,
            )
            raise


# ==============================================================================
# LEGACY COMPATIBILITY
# ==============================================================================

def post_sale_journal_entry(
    sale_id: Union[str, int],
    total_amount: float,
    payment_method: str = "CASH",
) -> bool:
    """
    Legacy function for backward compatibility.
    
    Args:
        sale_id: Sale ID
        total_amount: Total sale amount
        payment_method: Payment method
    
    Returns:
        True if successful, False otherwise
    """
    helper = POSJournalHelper()
    return helper.post_sale_journal_entry(
        sale_id=sale_id,
        total_amount=total_amount,
        payment_method=payment_method,
    )


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Classes
    "JournalEntry",
    "JournalBatch",
    "POSJournalHelper",
    
    # Constants
    "AccountType",
    "JournalEntryType",
    
    # Legacy
    "post_sale_journal_entry",
]

print("ERP POS JOURNAL HELPER READY - NiceGUI Version")
