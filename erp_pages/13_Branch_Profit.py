import streamlit as st
import pandas as pd
from database import get_supabase

st.set_page_config(page_title='Branch Profit', layout='wide')

supabase = get_supabase()

st.title('🏢 Branch Profit Dashboard')

# Load data
res = supabase.table('branch_profit_report').select('*').execute()
df = pd.DataFrame(res.data)

if df.empty:
    st.warning('No branch profit data found.')
    st.stop()

# Branch filter
branches = ['All'] + sorted(df['branch_name'].dropna().unique().tolist())
branch = st.selectbox('Select Branch', branches)

if branch != 'All':
    df = df[df['branch_name'] == branch]

# KPI
revenue = float(df['revenue'].sum())
cogs = float(df['cogs'].sum())
profit = float(df['gross_profit'].sum())

col1, col2, col3 = st.columns(3)
col1.metric('Revenue', f'{revenue:,.2f}')
col2.metric('COGS', f'{cogs:,.2f}')
col3.metric('Gross Profit', f'{profit:,.2f}')

st.divider()

# Table
st.subheader('Product Profit')
st.dataframe(
    df[
        [
            'branch_name',
            'product_name',
            'sold_qty',
            'revenue',
            'cogs',
            'gross_profit',
            'profit_margin_percent'
        ]
    ],
    use_container_width=True
)

# Chart
chart_df = (
    df.groupby('product_name', as_index=False)['gross_profit']
      .sum()
      .sort_values('gross_profit', ascending=False)
)

st.subheader('Gross Profit by Product')
st.bar_chart(chart_df.set_index('product_name')['gross_profit'])