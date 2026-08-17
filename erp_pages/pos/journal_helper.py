# ==============================================================================
# erp_pages/POS/journal_helper.py
# POS Journal Entry Helper for Double Entry System
# ==============================================================================

import datetime
import streamlit as st
from supabase_client import get_supabase

def post_sale_journal_entry(sale_id: int, total_amount: float, payment_method: str = "CASH"):
    """
    အရောင်းအဝယ် (Sale) ပြီးမြောက်ပါက journal_entries ဇယားသို့ 
    Double Entry (Debit နှင့် Credit) အလိုအလျောက် ထည့်သွင်းပေးသည်။
    """
    try:
        supabase = get_supabase()
        if not supabase:
            st.error("Journal Error: Supabase connection failed.")
            return False

        if total_amount <= 0:
            return True

        debit_account_id = 1 if "CASH" in payment_method.upper() else 2  
        credit_account_id = 4  

        journal_rows = [
            {
                "sale_id": int(sale_id),
                "account_id": int(debit_account_id),
                "debit": float(total_amount),
                "credit": 0.00,
                "description": f"Sale #{sale_id} - Payment via {payment_method}",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            },
            {
                "sale_id": int(sale_id),
                "account_id": int(credit_account_id),
                "debit": 0.00,
                "credit": float(total_amount),
                "description": f"Sale #{sale_id} - Revenue",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        ]

        # Supabase သို့ insert လုပ်ခြင်းနှင့် Error တက်ပါက တိုက်ရိုက်ဖော်ပြရန်
        response = supabase.table("journal_entries").insert(journal_rows).execute()
        
        # Supabase v2 တွင် error ရှိမရှိ စစ်ဆေးခြင်း
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase Journal Insert Error: {response.error}")
            return False

        if response.data:
            return True
        else:
            st.warning(f"Journal inserted but no data returned: {response}")
            return False

    except Exception as e:
        st.error(f"Exception in post_sale_journal_entry: {str(e)}")
        return False
