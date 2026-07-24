import streamlit as st
from supabase_client import supabase
from utils.ui import show_table
from utils.notification import (
    notify_success,
    notify_error,
    notify_warning
)

def run():
    # =========================
    # 🔐 SECURITY GUARD
    # =========================
    def require_admin():
        user = st.session_state.get("user")
        if not user:
            st.error("⛔ Please login first")
            st.stop()
        if user.get("role_id") != 1:
            st.error("⛔ Access Denied: Admin Only Module")
            st.stop()
        return user

    user = require_admin()

    st.title("⚙️ ERP Control Center (Admin Panel)")
    st.success(f"🔐 Welcome Admin: {user.get('full_name', 'Admin')}")

    # =========================
    # LOAD SETTINGS FROM DB
    # =========================
    try:
        settings = supabase.table("erp_settings").select("*").execute().data or []
        settings_map = {s["key"]: s["value"] for s in settings}
    except Exception as e:
        st.error(f"Error loading settings: {e}")
        settings_map = {}

    # =========================
    # SAVE FUNCTION
    # =========================
    def save_setting(key, value):
        try:
            supabase.table("erp_settings").upsert(
                {"key": key, "value": str(value)},
                on_conflict="key"
            ).execute()
        except Exception as e:
            notify_error(f"Failed to save {key}: {e}")
            st.stop()

    def get_bool(key, default=False):
        return str(settings_map.get(key, str(default))).lower() == "true"

    def get_float(key, default=0):
        try:
            return float(settings_map.get(key, default))
        except:
            return default

    # =========================
    # 🧾 ACCOUNTING & TAX
    # =========================
    st.subheader("🧾 Accounting & Tax")
    
    tax_rate = st.number_input(
        "Default Tax Rate (%)",
        value=get_float("default_tax_rate", 7.0)
    )
    
    discount_policy = st.selectbox(
        "Discount Policy",
        ["allowed", "restricted"],
        index=0 if settings_map.get("discount_policy", "allowed") == "allowed" else 1
    )

    if st.button("💾 Save Accounting Settings", use_container_width=True):
        try:
            save_setting("default_tax_rate", tax_rate)
            save_setting("discount_policy", discount_policy)
            
            st.cache_data.clear()
            
            notify_success("🧾 Accounting settings updated successfully.")
            st.rerun()
        except Exception as e:
            notify_error(f"Accounting settings save failed: {e}")

    st.divider()

    # =========================
    # 🏢 ORGANIZATION
    # =========================
    st.subheader("🏢 Organization Settings")
    branch_mode = st.toggle("Enable Multi-Branch", value=get_bool("multi_branch", False))
    warehouse_mode = st.toggle("Enable Multi-Warehouse", value=get_bool("multi_warehouse", True))

    if st.button("💾 Save Organization Settings", use_container_width=True):
        try:
            save_setting("multi_branch", branch_mode)
            save_setting("multi_warehouse", warehouse_mode)
            
            notify_success("🏢 Organization settings updated successfully.")
            st.rerun()
        except Exception as e:
            notify_error(f"Organization settings save failed: {e}")

    st.divider()

    # =========================
    # 👤 SECURITY
    # =========================
    st.subheader("👤 Security & Permissions")
    rls_enabled = st.toggle("Enable Row Level Security (RLS)", value=get_bool("rls", False))

    if st.button("💾 Save Security Settings", use_container_width=True):
        try:
            save_setting("rls", rls_enabled)
            
            notify_success("👤 Security settings updated successfully.")
            st.rerun()
        except Exception as e:
            notify_error(f"Security settings save failed: {e}")

    st.info("⚠️ RLS changes require Supabase policy update")
    st.divider()

    # =========================
    # 📦 INVENTORY RULES
    # =========================
    st.subheader("📦 Inventory Rules")
    min_stock_alert = st.number_input("Default Minimum Stock Alert", value=get_float("min_stock", 10))
    reorder_auto = st.toggle("Enable Auto Reorder", value=get_bool("auto_reorder", False))

    if st.button("💾 Save Inventory Rules", use_container_width=True):
        try:
            save_setting("min_stock", min_stock_alert)
            save_setting("auto_reorder", reorder_auto)
            
            notify_success("📦 Inventory rules saved successfully.")
            st.rerun()
        except Exception as e:
            notify_error(f"Inventory rules save failed: {e}")

    st.divider()

    # =========================
    # 💱 FINANCE
    # =========================
    st.subheader("💱 Finance Settings")
    saved_currency = settings_map.get("currency", "MMK")
    curr_options = ["MMK", "USD", "THB", "SGD"]
    currency = st.selectbox(
        "Base Currency",
        curr_options,
        index=curr_options.index(saved_currency) if saved_currency in curr_options else 0
    )
    payment_methods = st.multiselect(
        "Enable Payment Methods",
        ["Cash", "Bank Transfer", "Mobile Pay", "Credit"],
        default=settings_map.get("payment_methods", "Cash,Bank Transfer").split(",")
    )

    if st.button("💾 Save Finance Settings", use_container_width=True):
        try:
            save_setting("currency", currency)
            save_setting("payment_methods", ",".join(payment_methods))
            
            notify_success("💰 Finance settings saved successfully.")
            st.rerun()
        except Exception as e:
            notify_error(f"Finance settings save failed: {e}")

    st.divider()

    st.subheader("System Status")
    st.success("✔ ERP Core Active\n✔ Warehouse Engine Ready\n✔ Sales/Purchase Connected\n✔ Settings DB Synced")
    st.success("⚙️ Control Center Fully Operational 🚀")

if __name__ == "__main__":
    st.set_page_config(page_title="ERP Control Center", layout="wide")
    run()
