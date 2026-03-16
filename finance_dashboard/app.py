import streamlit as st
from utils.database import init_db
from utils.mobile import inject_mobile_css

st.set_page_config(
    page_title="Personal Finance Dashboard",
    layout="centered",
    page_icon="💰",
    initial_sidebar_state="collapsed",
)

inject_mobile_css()
init_db()

st.sidebar.title("Navigation")
st.sidebar.info(
    "Use the pages listed above to navigate between sections:\n\n"
    "- **Dashboard** – spending overview and charts\n"
    "- **Transactions** – add and manage transactions\n"
    "- **Simulator** – model future financial scenarios\n"
    "- **Goals** – track savings and financial goals"
)

st.title("Welcome to Your Personal Finance Dashboard")
st.markdown(
    """
    This app helps you track your income, expenses, and financial goals all in one place.

    **Getting started:**
    - Head to **Transactions** to log income and expenses.
    - Visit the **Dashboard** to see spending breakdowns and trends.
    - Use the **Simulator** to project future balances based on your habits.
    - Set and monitor targets on the **Goals** page.

    Use the sidebar to navigate between pages. Your data is stored locally in a SQLite
    database (`data/finance.db`) and sample data is loaded automatically on first run.
    """
)
