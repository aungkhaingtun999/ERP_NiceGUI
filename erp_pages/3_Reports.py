from datetime import date, timedelta
from io import BytesIO
import json
from database import db
from utils.notification import toast_success  # Enterprise notification engine
from utils.ui import show_table
import pandas as pd
import streamlit as st


def run():
  st.set_page_config(
      page_title="ERP Executive Analytics & Reports v3.5", layout="wide"
  )

  st.title("📊 ERP Executive Analytics & Reports v3.5")

  # =====================================================
  # DATE FILTER
  # =====================================================

  c1, c2, c3 = st.columns([2, 2, 6])
  start_date = c1.date_input("Start Date", value=date.today())
  end_date = c2.date_input("End Date", value=date.today())

  start_iso = start_date.isoformat()
  end_iso = (end_date + timedelta(days=1)).isoformat()

  # =====================================================
  # FETCH SALES (Joined with users table - UUID kept for RLS & Audit Trail)
  # =====================================================

  @st.cache_data(ttl=60)
  def get_sales(start_iso, end_iso):
    try:
      return (
          db()
          .table("sales")
          .select(
              """
                id,
                total,
                discount,
                tax,
                subtotal,
                paid_amount,
                payment_method,
                created_at,
                cashier_id,
                users(
                    username,
                    employee_code
                )
                """
          )
          .gte("created_at", start_iso)
          .lt("created_at", end_iso)
          .order("created_at", desc=True)
          .execute()
          .data
          or []
      )
    except Exception as e:
      st.error(f"Error fetching data: {e}")
      return []

  sales = get_sales(start_iso, end_iso)
  df = pd.DataFrame(sales)

  if df.empty:
    st.warning("No sales data found.")
    return

  # =====================================================
  # NORMALIZE DATA
  # =====================================================

  numeric_cols = [
      "total",
      "discount",
      "tax",
      "subtotal",
      "paid_amount",
  ]
  for col in numeric_cols:
    if col in df.columns:
      df[col] = pd.to_numeric(df[col].fillna(0))
    else:
      df[col] = 0

  # =====================================================
# MYANMAR TIMEZONE CONVERSION
# =====================================================

df["created_at"] = pd.to_datetime(
    df["created_at"],
    utc=True
)

df["created_at"] = (
    df["created_at"]
    .dt.tz_convert("Asia/Yangon")
    .dt.tz_localize(None)
)

  # =====================================================
  # CASHIER DISPLAY NAME (Safe check & Professional naming)
  # =====================================================

  def format_cashier(user):
    if isinstance(user, dict):
      code = user.get("employee_code", "UNKNOWN")
      name = user.get("username", "")
      return f"{code} ({name})"
    return "SYSTEM"

  if "users" in df.columns:
    df["Cashier"] = df["users"].apply(format_cashier)
  else:
    df["Cashier"] = "SYSTEM"

  df["Cashier Name"] = df["Cashier"]  # For professional Excel export

  # =====================================================
  # FILTER PANEL (Odoo Style Flow)
  # =====================================================

  st.sidebar.markdown("### 🔎 Report Filters")
  cashier_list = ["All"] + sorted(df["Cashier"].unique().tolist())
  selected_cashier = st.sidebar.selectbox("👨‍💼 Cashier Filter", cashier_list)

  if selected_cashier != "All":
    df = df[df["Cashier"] == selected_cashier]

  if df.empty:
    st.warning("No sales data found for the selected filter.")
    return

  # =====================================================
  # KPI (Standard Total Calculation)
  # =====================================================

  revenue = df["total"].sum()
  discount = df["discount"].sum()
  tax = df["tax"].sum()
  bills = len(df)

  k1, k2, k3, k4 = st.columns(4)
  k1.metric("💰 Revenue", f"{revenue:,.0f} MMK")
  k2.metric("🧾 Bills", bills)
  k3.metric("🏷 Discount", f"{discount:,.0f}")
  k4.metric("🧮 Tax", f"{tax:,.0f}")

  st.divider()

  # =====================================================
  # TABS
  # =====================================================

  tab1, tab2, tab3, tab4 = st.tabs([
      "📈 Sales Summary",
      "👨‍💼 Cashier Report",
      "💳 Payment Report",
      "📥 Export Center",
  ])

  with tab1:
    st.subheader("Daily Sales")
    daily = df.groupby(df["created_at"].dt.date)["total"].sum().reset_index()
    show_table(daily)

    st.subheader("Monthly Sales")
    monthly = (
        df.groupby(df["created_at"].dt.to_period("M").astype(str))["total"]
        .sum()
        .reset_index()
    )
    show_table(monthly)

  with tab2:
    st.subheader("👨‍💼 Cashier Performance")
    cashier = (
        df.groupby("Cashier")
        .agg(Bills=("id", "count"), Sales=("total", "sum"))
        .reset_index()
    )
    show_table(cashier)

  with tab3:
    st.subheader("💳 Payment Methods")
    payment = (
        df.groupby("payment_method")
        .agg(Bills=("id", "count"), Amount=("total", "sum"))
        .reset_index()
    )
    show_table(payment)

  with tab4:
    st.subheader("📥 Export Reports")

    # --- DATA CLEANING FOR EXCEL ---
    export_df = df.copy()

    # Drop UUID, users relation, and old Cashier column, keeping "Cashier Name"
    export_df = export_df.drop(
        columns=["cashier_id", "users", "Cashier"], errors="ignore"
    )

    # 1. Convert Complex Objects (Dicts/Lists) to JSON Strings
    for col in export_df.columns:
      if export_df[col].dtype == "object":
        export_df[col] = export_df[col].apply(
            lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
        )

    # 2. Remove timezone for Excel compatibility (Safe Approach)
    for col in export_df.columns:
      try:
        if isinstance(export_df[col].dtype, pd.DatetimeTZDtype):
          export_df[col] = export_df[col].dt.tz_convert(None).astype(str)
        elif pd.api.types.is_datetime64_dtype(export_df[col]):
          export_df[col] = export_df[col].astype(str)
      except Exception:
        pass

    for col in export_df.columns:
      if isinstance(export_df[col].dtype, pd.DatetimeTZDtype):
        export_df[col] = export_df[col].dt.tz_localize(None)

    # 3. Replace NaN values with empty strings
    export_df = export_df.fillna("")

    # CSV Download
    csv = export_df.to_csv(index=False).encode("utf-8")
    if st.download_button(
        "⬇ Download CSV", csv, "sales_report.csv", "text/csv"
    ):
      toast_success("CSV exported successfully")

    # Excel Download
    try:
      output = BytesIO()
      with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Sales")
      if st.download_button(
          "⬇ Download Excel",
          output.getvalue(),
          "ERP_Sales_Report.xlsx",
          (
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          ),
      ):
        toast_success("Excel report exported successfully")
    except Exception as e:
      st.error(f"Excel Export Error: {e}")


if __name__ == "__main__":
  run()
