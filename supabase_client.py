# supabase_client.py
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    """Get Supabase client with Service Role Key (full access)"""
    supabase_url = st.secrets["SUPABASE_URL"]
    
    # ✅ Use SERVICE ROLE KEY for full access
    supabase_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    
    # Fallback to normal key if service role not available
    if not supabase_key:
        supabase_key = st.secrets["SUPABASE_KEY"]
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase credentials not found in secrets.")
    
    return create_client(supabase_url, supabase_key)
