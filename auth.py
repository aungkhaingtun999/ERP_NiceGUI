# ============================================================
# auth.py - FIXED (ပြုပြင်ပြီး)
# ============================================================

import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import streamlit as st

from erp_core.base_repo import db

# ✅ IMPORTANT: Get Supabase client with schema
supabase = db()

# ==================================================
# USER QUERY - FIXED
# ==================================================

def get_user_by_username(username):
    """Get user by username - Fixed with schema"""
    try:
        # ✅ Use schema('public') explicitly
        result = supabase.schema('public').table('users').select('*').eq('username', username.strip()).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        # If not found, get all and filter
        all_result = supabase.schema('public').table('users').select('*').execute()
        
        if all_result.data:
            username_lower = username.strip().lower()
            for user in all_result.data:
                if user.get('username', '').lower() == username_lower:
                    return user
        
        return None
        
    except Exception as e:
        print(f"Get user error: {e}")
        return None

# ==================================================
# LOGIN UI - WITH DEBUG
# ==================================================

def login_page():
    st.title("🔐 ERP Enterprise Login")
    
    # DEBUG
    with st.expander("🔍 Database Debug (Click to expand)"):
        try:
            # ✅ Test with schema('public')
            result = supabase.schema('public').table('users').select('*').execute()
            st.write(f"📋 Users found: {len(result.data) if result.data else 0}")
            if result.data:
                st.dataframe(result.data)
            else:
                st.warning("⚠️ No users found in database.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        if not username or not password:
            st.error("Username and password required")
        else:
            success, msg = login_user(username, password)
            if success:
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error(f"❌ {msg}")
