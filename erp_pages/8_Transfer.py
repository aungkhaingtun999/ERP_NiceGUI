# ==============================================================================
# erp_core/loaders/product_loader.py
# ERP ENTERPRISE PRODUCT LOADER v10
# ==============================================================================

from typing import Any, Dict, List
import streamlit as st

from erp_core.base_repo import db, log_error
from ..context import CacheManager
from ..repositories import RepositoryCoordinator


@st.cache_data(ttl=300)
def _get_active_products_cached(version: int) -> List[Dict[str, Any]]:
    """Fetch active products ordered by name with caching."""
    try:
        # Assuming your RepositoryCoordinator exposes a products repository
        with RepositoryCoordinator(db()) as coord:
            # If using Supabase directly via a repository method or client:
            return coord.products.get_active_products()
    except Exception as e:
        log_error(f"product loader error: {e}")
        return []


def get_active_products() -> List[Dict[str, Any]]:
    """Retrieve active products using the current product cache version."""
    return _get_active_products_cached(
        CacheManager.get_version("product_version")
    )


def render_product_selector() -> Any:
    """Render a Streamlit selectbox for active products."""
    products = get_active_products()
    
    if not products:
        st.warning("No active products available.")
        return None

    product_options = {p["id"]: p["name"] for p in products}
    
    selected_id = st.selectbox(
        "Select Product",
        options=list(product_options.keys()),
        format_func=lambda x: product_options[x]
    )
    
    return selected_id
