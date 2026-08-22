# ============================================================
# supabase_client.py
# ERP ENTERPRISE SUPABASE CLIENT
# SERVER-SIDE SERVICE ROLE
# ============================================================

import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:

    supabase_url = st.secrets.get("SUPABASE_URL")
    supabase_key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url:
        raise RuntimeError("SUPABASE_URL is missing.")

    if not supabase_key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY is missing."
        )

    return create_client(
        supabase_url,
        supabase_key
    )
