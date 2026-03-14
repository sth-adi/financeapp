import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_transactions, get_recurring_items
from utils.calculations import (get_current_month_summary, get_spending_by_category,
                                get_monthly_totals, get_recurring_monthly_cost,
                                get_safe_spending, get_savings_rate)
from utils.charts import spending_by_category_chart, income_vs_spending_chart

st.title("Dashboard")
st.subheader(datetime.now().strftime("%B %Y"))

# Load data
df_transactions = get_transactions()
df_recurring = get_recurring_items()

# Calculate summary values
if df_transactions is not None and not df_transactions.empty:
    summary = get_current_month_summary(df_transactions)
    recurring_cost = get_recurring_monthly_cost(df_recurring) if df_recurring is not None and not df_recurring.empty else 0.0
    savings_target = 500
    safe_spending = get_safe_spending(summary['income'], summary['spending'], savings_target, recurring_cost)

    # --- Top metrics row ---
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="Total Income",
            value=f"${summary['income']:,.2f}"
        )

    with col2:
        st.metric(
            label="Total Spending",
            value=f"${summary['spending']:,.2f}"
        )

    with col3:
        net = summary['net']
        st.metric(
            label="Net Balance",
            value=f"${abs(net):,.2f}",
            delta=f"${net:,.2f}",
            delta_color="normal"
        )

    with col4:
        st.metric(
            label="Recurring Costs",
            value=f"${recurring_cost:,.2f}"
        )

    with col5:
        if safe_spending >= 0:
            st.markdown(
                f"**Safe to Spend**\n\n"
                f"<span style='color: green; font-size: 1.5rem; font-weight: bold;'>${safe_spending:,.2f}</span>",
                unsafe_allow_html=True
            )
        else:
            st.metric(
                label="Safe to Spend",
                value=f"${safe_spending:,.2f}"
            )

    st.divider()

    # --- Two-column layout ---
    left_col, right_col = st.columns(2)

    with left_col:
        # Recent Transactions
        st.subheader("Recent Transactions")
        display_cols = [c for c in ['date', 'description', 'category', 'amount'] if c in df_transactions.columns]
        if display_cols:
            recent = df_transactions.sort_values('date', ascending=False).head(5)[display_cols]
            st.dataframe(recent, use_container_width=True, hide_index=True)
        else:
            st.info("No transaction columns available to display.")

        # Top Spending Categories
        st.subheader("Top Spending Categories")
        now = datetime.now()
        df_category = get_spending_by_category(df_transactions, now.year, now.month)
        if df_category is not None and not df_category.empty:
            top5 = df_category.head(5)
            st.dataframe(top5, use_container_width=True, hide_index=True)
        else:
            st.info("No category spending data available for this month.")

    with right_col:
        # Spending by Category pie chart
        now = datetime.now()
        df_category = get_spending_by_category(df_transactions, now.year, now.month)
        if df_category is not None and not df_category.empty:
            fig_pie = spending_by_category_chart(df_category)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No spending category data available to display chart.")

        # Income vs Spending bar chart
        df_monthly = get_monthly_totals(df_transactions)
        if df_monthly is not None and not df_monthly.empty:
            fig_bar = income_vs_spending_chart(df_monthly)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No monthly totals data available to display chart.")

else:
    st.info("No transaction data found. Add some transactions to get started.")
