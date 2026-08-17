# ============================================================
# erp_pages/POS/journal_helper.py
# POS Journal Entry Helper for Double Entry System
# ============================================================

import datetime
from supabase_client import get_supabase

def post_sale_journal_entry(sale_id: int, total_amount: float, payment_method: str = "CASH"):
    """
    အရောင်းအဝယ် (Sale) ပြီးမြောက်ပါက journal_entries ဇယားသို့ 
    Double Entry (Debit နှင့် Credit) အလိုအလျောက် ထည့်သွင်းပေးသည်။
    """
    try:
        supabase = get_supabase()
        if not supabase:
            print("Supabase connection failed.")
            return False

        if total_amount <= 0:
            return True

        # ငွေပေးချေမှုပုံစံအလိုက် Account ID သတ်မှတ်ခြင်း (လိုအပ်ပါက မိမိစနစ်အလျောက် ပြင်ရန်)
        debit_account_id = 1 if "CASH" in payment_method.upper() else 2  # 1: Cash, 2: Accounts Receivable
        credit_account_id = 4  # Sales Revenue

        journal_rows = [
            {
                "sale_id": sale_id,
                "account_id": debit_account_id,
                "debit": total_amount,
                "credit": 0.00,
                "description": f"Sale #{sale_id} - Payment via {payment_method}",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            {
                "sale_id": sale_id,
                "account_id": credit_account_id,
                "debit": 0.00,
                "credit": total_amount,
                "description": f"Sale #{sale_id} - Revenue",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        ]

        response = supabase.table("journal_entries").insert(journal_rows).execute()
        
        if response.data:
            print(f"Successfully posted journal entries for Sale #{sale_id}")
            return True
        else:
            print(f"Failed to post journal entries: {response}")
            return False

    except Exception as e:
        print(f"Error posting journal entry: {str(e)}")
        return False
