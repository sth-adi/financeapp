import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.database import get_goals, add_goal, update_goal, delete_goal
from utils.charts import goal_progress_chart
from utils.mobile import inject_mobile_css

st.set_page_config(page_title="Savings Goals", page_icon="🎯", layout="centered", initial_sidebar_state="collapsed")
inject_mobile_css()

st.title("Savings Goals")

# --- Load Goals ---
df_goals = get_goals()

goals_empty = df_goals is None or (isinstance(df_goals, pd.DataFrame) and df_goals.empty)

if goals_empty:
    st.info("No goals yet. Add your first goal below!")
else:
    st.markdown(f"You have **{len(df_goals)}** active goal(s).")

    MONTHLY_SAVINGS_RATE = 500.0  # default estimate

    for _, goal in df_goals.iterrows():
        goal_name = goal.get("name", goal.get("goal_name", "Unnamed Goal"))
        current_amount = float(goal.get("current_amount", 0.0))
        target_amount = float(goal.get("target_amount", 1.0))
        target_date_raw = goal.get("target_date", None)
        goal_type = goal.get("goal_type", goal.get("type", "savings"))
        goal_id = goal.get("id", goal.get("goal_id", None))

        # Parse target date
        target_date = None
        days_remaining = None
        if target_date_raw is not None:
            try:
                if isinstance(target_date_raw, str):
                    target_date = datetime.strptime(target_date_raw, "%Y-%m-%d").date()
                elif isinstance(target_date_raw, (datetime,)):
                    target_date = target_date_raw.date()
                elif isinstance(target_date_raw, date):
                    target_date = target_date_raw
                days_remaining = (target_date - date.today()).days
            except Exception:
                target_date = None
                days_remaining = None

        remaining = max(target_amount - current_amount, 0.0)
        pct_complete = min(current_amount / target_amount, 1.0) if target_amount > 0 else 0.0

        with st.container():
            st.subheader(f"{goal_name}")

            # Progress bar
            st.progress(pct_complete)

            # Metrics rows (2+2 for better mobile layout)
            m1, m2 = st.columns(2)
            m1.metric("Current Amount", f"${current_amount:,.2f}")
            m2.metric("Target Amount", f"${target_amount:,.2f}")
            m3, m4 = st.columns(2)
            m3.metric("Remaining", f"${remaining:,.2f}")
            m4.metric("Progress", f"{pct_complete * 100:.1f}%")

            # Date row
            date_col, track_col = st.columns(2)
            with date_col:
                if target_date:
                    st.markdown(f"**Target Date:** {target_date.strftime('%B %d, %Y')}")
                    if days_remaining is not None:
                        if days_remaining < 0:
                            st.markdown(f"**Status:** Overdue by {abs(days_remaining)} day(s)")
                        else:
                            st.markdown(f"**Days Remaining:** {days_remaining}")
                else:
                    st.markdown("**Target Date:** Not set")

            with track_col:
                if remaining > 0 and MONTHLY_SAVINGS_RATE > 0:
                    months_remaining_est = remaining / MONTHLY_SAVINGS_RATE
                    if days_remaining is not None and days_remaining > 0:
                        months_available = days_remaining / 30.44
                        if months_remaining_est <= months_available:
                            st.success(f"On track — estimated {months_remaining_est:.1f} month(s) to complete.")
                        else:
                            st.warning(
                                f"Behind schedule — needs {months_remaining_est:.1f} month(s) at "
                                f"${MONTHLY_SAVINGS_RATE:,.0f}/mo, but only {months_available:.1f} month(s) available."
                            )
                    else:
                        st.info(f"Estimated completion: {months_remaining_est:.1f} month(s) at ${MONTHLY_SAVINGS_RATE:,.0f}/mo.")
                elif remaining <= 0:
                    st.success("Goal achieved!")

            # Plotly chart
            try:
                fig = goal_progress_chart(goal_name, current_amount, target_amount)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.caption(f"Chart unavailable: {e}")

            st.divider()

# --- Add New Goal ---
with st.expander("Add New Goal"):
    with st.form("add_goal_form", clear_on_submit=True):
        goal_name_input = st.text_input("Goal Name", placeholder="e.g. Emergency Fund")
        target_amount_input = st.number_input("Target Amount ($)", min_value=0.01, step=50.0, format="%.2f")
        current_amount_input = st.number_input("Current Amount ($)", min_value=0.0, step=50.0, format="%.2f", value=0.0)
        target_date_input = st.date_input("Target Date", value=date.today().replace(year=date.today().year + 1))
        goal_type_input = st.selectbox(
            "Goal Type",
            options=["savings", "debt_payoff", "investment", "other"],
        )
        submitted = st.form_submit_button("Add Goal", type="primary")

        if submitted:
            if not goal_name_input.strip():
                st.error("Please enter a goal name.")
            elif target_amount_input <= 0:
                st.error("Target amount must be greater than $0.")
            elif current_amount_input > target_amount_input:
                st.warning("Current amount exceeds target amount — the goal is already complete!")
            else:
                try:
                    add_goal(
                        name=goal_name_input.strip(),
                        target_amount=target_amount_input,
                        current_amount=current_amount_input,
                        target_date=target_date_input.strftime("%Y-%m-%d"),
                        goal_type=goal_type_input,
                    )
                    st.success(f"Goal '{goal_name_input.strip()}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not add goal: {e}")

# --- Update Goal Progress ---
with st.expander("Update Goal Progress"):
    if goals_empty:
        st.info("No goals available to update.")
    else:
        goal_names = df_goals.apply(
            lambda r: r.get("name", r.get("goal_name", "Unnamed Goal")), axis=1
        ).tolist()

        selected_goal_name = st.selectbox("Select Goal", options=goal_names, key="update_select")

        selected_row = df_goals[
            df_goals.apply(
                lambda r: r.get("name", r.get("goal_name", "")) == selected_goal_name, axis=1
            )
        ]

        if not selected_row.empty:
            selected_goal = selected_row.iloc[0]
            goal_id = selected_goal.get("id", selected_goal.get("goal_id", None))
            prefill_current = float(selected_goal.get("current_amount", 0.0))

            with st.form("update_goal_form"):
                new_current = st.number_input(
                    "Updated Current Amount ($)",
                    min_value=0.0,
                    step=50.0,
                    format="%.2f",
                    value=prefill_current,
                )
                update_submitted = st.form_submit_button("Update Goal", type="primary")

                if update_submitted:
                    try:
                        update_goal(goal_id=goal_id, current_amount=new_current)
                        st.success(f"Goal '{selected_goal_name}' updated to ${new_current:,.2f}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not update goal: {e}")

# --- Delete Goal ---
with st.expander("Delete Goal"):
    if goals_empty:
        st.info("No goals available to delete.")
    else:
        goal_names_del = df_goals.apply(
            lambda r: r.get("name", r.get("goal_name", "Unnamed Goal")), axis=1
        ).tolist()

        selected_del_name = st.selectbox("Select Goal to Delete", options=goal_names_del, key="delete_select")

        selected_del_row = df_goals[
            df_goals.apply(
                lambda r: r.get("name", r.get("goal_name", "")) == selected_del_name, axis=1
            )
        ]

        if not selected_del_row.empty:
            selected_del_goal = selected_del_row.iloc[0]
            del_goal_id = selected_del_goal.get("id", selected_del_goal.get("goal_id", None))

            st.warning(f"Are you sure you want to delete **'{selected_del_name}'**? This action cannot be undone.")
            if st.button("Confirm Delete", type="primary", key="confirm_delete"):
                try:
                    delete_goal(goal_id=del_goal_id)
                    st.success(f"Goal '{selected_del_name}' deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not delete goal: {e}")
