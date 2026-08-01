# ==============================================================================
# ERP ENTERPRISE PAYMENT REPOSITORY v1.0
# MOBILE BANKING PAYMENT
# ==============================================================================

from erp_core import get_supabase

supabase = get_supabase()



# ==============================================================================
# CREATE PAYMENT TRANSACTION
# ==============================================================================

def create_payment_transaction(data: dict):

    result = (
        supabase
        .table("payment_transactions")
        .insert(data)
        .execute()
    )

    return result.data



# ==============================================================================
# GET PAYMENT BY ID
# ==============================================================================

def get_payment(payment_id):

    result = (
        supabase
        .table("payment_transactions")
        .select("*")
        .eq("id", payment_id)
        .single()
        .execute()
    )

    return result.data



# ==============================================================================
# GET PAYMENT BY SALE
# ==============================================================================

def get_payment_by_sale(sale_id):

    result = (
        supabase
        .table("payment_transactions")
        .select("*")
        .eq("sale_id", sale_id)
        .execute()
    )

    return result.data



# ==============================================================================
# UPDATE PAYMENT STATUS
# ==============================================================================

def update_payment_status(
    payment_id,
    status,
    verified_by=None,
    note=None
):

    payload = {
        "status": status
    }


    if verified_by:
        payload["verified_by"] = verified_by
        payload["verified_at"] = "now()"


    if note:
        payload["note"] = note


    result = (
        supabase
        .table("payment_transactions")
        .update(payload)
        .eq("id", payment_id)
        .execute()
    )

    return result.data



# ==============================================================================
# PENDING PAYMENT LIST
# ==============================================================================

def get_pending_payments():

    result = (
        supabase
        .table("payment_transactions")
        .select("*")
        .eq("status", "PENDING")
        .order("created_at", desc=True)
        .execute()
    )

    return result.data
