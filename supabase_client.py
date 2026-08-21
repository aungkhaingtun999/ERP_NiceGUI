# ============================================================
# supabase_client.py
# ERP ENTERPRISE SUPABASE CLIENT
# Centralized Supabase connection
# ============================================================

import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    """Get Supabase client with caching"""
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase credentials not found in secrets.")
    
    return create_client(supabase_url, supabase_key)