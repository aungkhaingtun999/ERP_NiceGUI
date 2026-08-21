# ============================================================
# supabase_client.py
# ============================================================

import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    """Get Supabase client with Service Role Key (full access)"""
    supabase_url = st.secrets["SUPABASE_URL"]
    
    # ✅ Use Service Role Key to bypass RLS
    supabase_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    
    # Fallback to anon key if service role not available
    if not supabase_key:
        supabase_key = st.secrets.get("SUPABASE_KEY")
    
    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is not set in secrets.")
    
    if not supabase_key:
        raise RuntimeError("SUPABASE_KEY or SUPABASE_SERVICE_ROLE_KEY is not set in secrets.")
    
    return create_client(supabase_url, supabase_key)
