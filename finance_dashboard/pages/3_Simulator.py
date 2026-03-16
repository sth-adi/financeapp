import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from utils.database import get_transactions, get_recurring_items
from utils.calculations import get_current_month_summary, get_recurring_monthly_cost
from utils.simulator import simulate_scenario
from utils.mobile import inject_mobile_css

st.set_page_config(page_title="Financial Simulator", page_icon="🔮", layout="centered", initial_sidebar_state="collapsed")
inject_mobile_css()

st.title("Financial Simulator")
st.markdown("Simulate financial decisions without affecting your real data")

# --- Load current financial state ---
df = get_transactions()
df_rec = get_recurring_items()
summary = get_current_month_summary(df)
current_balance = 5000.0

monthly_income = summary.get("income", 0.0)
monthly_spending = summary.get("expenses", 0.0)
net_balance = summary.get("net", monthly_income - monthly_spending)

# --- Current Financial State expander ---
with st.expander("Current Financial State", expanded=False):
    col1, col2, col3 = st.columns(3)
    col1.metric("Monthly Income", f"${monthly_income:,.2f}")
    col2.metric("Monthly Spending", f"${monthly_spending:,.2f}")
    col3.metric("Net Balance", f"${net_balance:,.2f}", delta=f"${net_balance:,.2f}")

st.divider()

# --- Simulator Section ---
st.subheader("Configure Scenario")

scenario_label_to_type = {
    "One-Time Expense": "one_time_expense",
    "New Recurring Monthly Cost": "recurring_monthly_cost",
    "Increase Monthly Savings": "additional_savings",
    "Reduce Monthly Savings": "reduced_savings",
    "Extra Monthly Income": "extra_income",
}

col_left, col_right = st.columns([1, 1])

with col_left:
    scenario_label = st.selectbox(
        "Scenario Type",
        options=list(scenario_label_to_type.keys()),
    )
    scenario_type = scenario_label_to_type[scenario_label]

with col_right:
    amount = st.number_input(
        "Amount ($)",
        min_value=0.0,
        step=10.0,
        format="%.2f",
    )

# Optional: save scenario as transaction
save_option = st.checkbox(
    "Save this scenario as a transaction",
    value=False,
    help="Only available for One-Time Expense and Extra Monthly Income scenarios.",
)

run_col, save_col = st.columns([1, 5])
run_button = run_col.button("Run Simulation", type="primary")

# --- Run Simulation ---
if run_button:
    if amount <= 0.0:
        st.warning("Please enter an amount greater than $0.00 to run a simulation.")
    else:
        result = simulate_scenario(
            scenario_type=scenario_type,
            amount=amount,
            current_balance=current_balance,
            monthly_income=monthly_income,
            monthly_spending=monthly_spending,
        )

        verdict = result.get("verdict", "").lower()
        immediate_impact = result.get("immediate_impact", 0.0)
        monthly_impact = result.get("monthly_impact", 0.0)
        annual_impact = result.get("annual_impact", 0.0)
        details = result.get("details", "")

        # Verdict banner
        verdict_message = f"**Verdict: {result.get('verdict', 'Unknown')}**"
        if verdict in ("good", "positive", "recommended"):
            st.success(verdict_message)
        elif verdict in ("bad", "negative", "risky", "warning"):
            st.warning(verdict_message)
        else:
            st.info(verdict_message)

        # Impact metrics
        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Immediate Impact",
            f"${immediate_impact:,.2f}",
            delta=f"${immediate_impact:,.2f}" if immediate_impact != 0 else None,
        )
        m2.metric(
            "Monthly Impact",
            f"${monthly_impact:,.2f}",
            delta=f"${monthly_impact:,.2f}" if monthly_impact != 0 else None,
        )
        m3.metric(
            "Annual Impact (12 months)",
            f"${annual_impact:,.2f}",
            delta=f"${annual_impact:,.2f}" if annual_impact != 0 else None,
        )

        if details:
            st.caption(details)

        st.divider()

        # What this means section
        st.markdown("### What this means:")

        if scenario_type == "one_time_expense":
            st.markdown(
                f"- A one-time expense of **${amount:,.2f}** will immediately reduce your balance by that amount.\n"
                f"- Your balance after this expense: **${current_balance + immediate_impact:,.2f}**\n"
                f"- Over 12 months, accounting for this single cost, the total impact is **${annual_impact:,.2f}**."
            )
        elif scenario_type == "recurring_monthly_cost":
            st.markdown(
                f"- Adding a recurring cost of **${amount:,.2f}/month** will reduce your monthly net by **${abs(monthly_impact):,.2f}**.\n"
                f"- Over a full year this adds up to **${abs(annual_impact):,.2f}** in additional spending.\n"
                f"- Your new estimated monthly net would be **${net_balance + monthly_impact:,.2f}**."
            )
        elif scenario_type == "additional_savings":
            st.markdown(
                f"- Increasing monthly savings by **${amount:,.2f}** means you set aside more each month.\n"
                f"- Over 12 months you would accumulate an additional **${annual_impact:,.2f}** in savings.\n"
                f"- Ensure your monthly income can support this commitment."
            )
        elif scenario_type == "reduced_savings":
            st.markdown(
                f"- Reducing monthly savings by **${amount:,.2f}** frees up **${abs(monthly_impact):,.2f}** per month for spending.\n"
                f"- Over 12 months you save **${abs(annual_impact):,.2f}** less than your current plan.\n"
                f"- Consider whether this aligns with your long-term financial goals."
            )
        elif scenario_type == "extra_income":
            st.markdown(
                f"- An extra **${amount:,.2f}/month** in income improves your monthly net by **${monthly_impact:,.2f}**.\n"
                f"- Over 12 months this adds **${annual_impact:,.2f}** to your finances.\n"
                f"- Consider directing this extra income toward savings or debt repayment."
            )
        else:
            st.markdown(f"- This scenario results in a net annual impact of **${annual_impact:,.2f}**.")

        # Optional save
        if save_option:
            if scenario_type in ("one_time_expense", "extra_income"):
                if st.button("Save as Transaction"):
                    try:
                        from utils.database import add_transaction
                        txn_amount = -amount if scenario_type == "one_time_expense" else amount
                        txn_category = "Simulated Expense" if scenario_type == "one_time_expense" else "Simulated Income"
                        add_transaction(
                            amount=txn_amount,
                            description=f"[Simulated] {scenario_label}",
                            category=txn_category,
                        )
                        st.success("Transaction saved successfully!")
                    except Exception as e:
                        st.error(f"Could not save transaction: {e}")
            else:
                st.info(
                    "Saving is only supported for 'One-Time Expense' and 'Extra Monthly Income' scenarios."
                )
