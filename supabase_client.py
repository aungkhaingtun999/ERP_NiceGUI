# supabase_client.py
import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def get_supabase() -> Client:
    supabase_url = st.secrets["SUPABASE_URL"]
    
    # ✅ Force use service role key
    supabase_key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    
    if not supabase_url or not supabase_key:
        raise RuntimeError("Supabase credentials not found.")
    
    return create_client(supabase_url, supabase_key)
