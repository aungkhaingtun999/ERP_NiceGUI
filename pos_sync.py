pos_sync.py (Production Safe Version)

# ==============================================================================
# pos_sync.py
# ERP POS PRODUCT CACHE ENGINE
# Production Safe Version
# ==============================================================================

import streamlit as st


# ==============================================================================
# FETCH PRODUCTS
# ==============================================================================

def fetch_products_from_supabase(client):

    try:

        response = (
            client
            .table("products")
            .select("*")
            .eq("is_active", True)
            .execute()
        )

        return response.data or []

    except Exception as e:

        st.error(f"Product sync failed : {e}")

        return []


# ==============================================================================
# INIT CACHE
# ==============================================================================

def init_pos_cache(client):

    if "products_cache" not in st.session_state:

        st.session_state.products_cache = fetch_products_from_supabase(client)


# ==============================================================================
# GET CACHED PRODUCTS
# ==============================================================================

def get_cached_products(client):

    init_pos_cache(client)

    return st.session_state.products_cache


# ==============================================================================
# SIDEBAR CONTROL
# ==============================================================================

def render_pos_sync_sidebar(client):

    with st.sidebar:

        st.divider()

        st.subheader("⚙️ POS Control Panel")

        st.caption(
            "Refresh product cache after purchase / transfer / stock update."
        )

        if st.button(
            "🔄 Sync / Refresh Products",
            type="primary",
            use_container_width=True
        ):

            with st.spinner("Refreshing products..."):

                st.session_state.products_cache = fetch_products_from_supabase(client)

            st.success("Product cache updated")

            st.rerun()
