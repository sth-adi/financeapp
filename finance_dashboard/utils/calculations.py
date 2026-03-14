"""
calculations.py
---------------
Pure calculation functions for the personal finance dashboard.

All functions accept pandas DataFrames as input and never touch the database
directly. This makes them easy to test in isolation.

Expected DataFrame schemas
--------------------------
df_transactions columns: date (str YYYY-MM-DD), description, category,
    type ('income' | 'expense'), account, amount (float), notes

df_recurring columns: description, category, amount (float),
    frequency ('monthly' | 'weekly' | 'yearly' | 'bi-weekly'), next_due_date
"""

import datetime
import pandas as pd


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _filter_by_period(
    df: pd.DataFrame,
    year: int,
    month: int,
) -> pd.DataFrame:
    """Return only the rows whose date column matches *year* and *month*.

    The date column is expected to contain strings in YYYY-MM-DD format.
    """
    # Parse once to a datetime column for reliable comparisons
    dates = pd.to_datetime(df["date"], errors="coerce")
    mask = (dates.dt.year == year) & (dates.dt.month == month)
    return df[mask]


# ---------------------------------------------------------------------------
# Monthly summary
# ---------------------------------------------------------------------------

def get_monthly_summary(
    df_transactions: pd.DataFrame,
    year: int,
    month: int,
) -> dict:
    """Return income, spending, net and savings rate for a given month.

    Parameters
    ----------
    df_transactions:
        Full transactions DataFrame.
    year:
        4-digit year, e.g. 2026.
    month:
        Integer month, 1–12.

    Returns
    -------
    dict with keys:
        income      – total income for the period (float)
        spending    – total expenses for the period (float, always positive)
        net         – income minus spending (float)
        savings_rate – net / income as a percentage (float, 0 if income == 0)
    """
    df_period = _filter_by_period(df_transactions, year, month)

    income = df_period.loc[df_period["type"] == "income", "amount"].sum()
    spending = df_period.loc[df_period["type"] == "expense", "amount"].sum()
    net = income - spending
    savings_rate = get_savings_rate(income, spending)

    return {
        "income": round(float(income), 2),
        "spending": round(float(spending), 2),
        "net": round(float(net), 2),
        "savings_rate": round(float(savings_rate), 2),
    }


def get_current_month_summary(df_transactions: pd.DataFrame) -> dict:
    """Convenience wrapper – returns get_monthly_summary for today's month."""
    today = datetime.date.today()
    return get_monthly_summary(df_transactions, today.year, today.month)


# ---------------------------------------------------------------------------
# Spending by category
# ---------------------------------------------------------------------------

def get_spending_by_category(
    df_transactions: pd.DataFrame,
    year: int = None,
    month: int = None,
) -> pd.DataFrame:
    """Return total spending grouped by category.

    Only 'expense' rows are included. If *year* and *month* are both provided,
    results are filtered to that period; otherwise all available data is used.

    Returns
    -------
    pd.DataFrame with columns: category (str), amount (float)
        Sorted by amount descending.
    """
    df = df_transactions.copy()

    # Optionally filter to a specific period
    if year is not None and month is not None:
        df = _filter_by_period(df, year, month)

    # Keep only expense rows
    df_expenses = df[df["type"] == "expense"]

    if df_expenses.empty:
        return pd.DataFrame(columns=["category", "amount"])

    result = (
        df_expenses.groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
        .reset_index(drop=True)
    )
    result["amount"] = result["amount"].round(2)
    return result


# ---------------------------------------------------------------------------
# Monthly totals (all months in dataset)
# ---------------------------------------------------------------------------

def get_monthly_totals(df_transactions: pd.DataFrame) -> pd.DataFrame:
    """Return income, spending and net aggregated by calendar month.

    Returns
    -------
    pd.DataFrame with columns:
        month   – string in YYYY-MM format, sorted ascending
        income  – float
        spending – float
        net     – float
    """
    if df_transactions.empty:
        return pd.DataFrame(columns=["month", "income", "spending", "net"])

    df = df_transactions.copy()
    # Derive a YYYY-MM string column for grouping
    df["month"] = pd.to_datetime(df["date"], errors="coerce").dt.to_period("M").astype(str)

    # Pivot income and expenses separately then merge
    income_df = (
        df[df["type"] == "income"]
        .groupby("month", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "income"})
    )
    spending_df = (
        df[df["type"] == "expense"]
        .groupby("month", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "spending"})
    )

    # Outer join so months that have only income or only expenses are included
    result = pd.merge(income_df, spending_df, on="month", how="outer").fillna(0)
    result["net"] = result["income"] - result["spending"]
    result = result.sort_values("month").reset_index(drop=True)

    # Round for display
    for col in ("income", "spending", "net"):
        result[col] = result[col].round(2)

    return result


# ---------------------------------------------------------------------------
# Recurring cost helper
# ---------------------------------------------------------------------------

# Conversion factors to a monthly equivalent
_FREQUENCY_TO_MONTHLY = {
    "weekly":    52 / 12,   # ~4.33 weeks per month
    "bi-weekly": 26 / 12,   # ~2.17 per month
    "monthly":   1.0,
    "yearly":    1 / 12,
}


def get_recurring_monthly_cost(df_recurring: pd.DataFrame) -> float:
    """Return the total monthly-equivalent cost of all recurring items.

    Rows with an unrecognised frequency are treated as monthly.

    Returns
    -------
    float – total monthly cost, rounded to 2 decimal places.
    """
    if df_recurring.empty:
        return 0.0

    total = 0.0
    for _, row in df_recurring.iterrows():
        freq = str(row.get("frequency", "monthly")).lower()
        factor = _FREQUENCY_TO_MONTHLY.get(freq, 1.0)
        total += float(row["amount"]) * factor

    return round(total, 2)


# ---------------------------------------------------------------------------
# Safe spending
# ---------------------------------------------------------------------------

def get_safe_spending(
    monthly_income: float,
    monthly_spending: float,
    savings_target: float,
    upcoming_recurring: float,
) -> float:
    """Calculate how much discretionary money is available to spend safely.

    Safe spending = income - committed spending - savings target
                  - upcoming recurring costs not already in spending.

    Parameters
    ----------
    monthly_income:
        Expected income for the month.
    monthly_spending:
        Spending already recorded for the month.
    savings_target:
        The amount the user wants to save each month.
    upcoming_recurring:
        Monthly-equivalent total of recurring items not yet paid this month.

    Returns
    -------
    float – safe discretionary spend (may be negative if over-budget).
    """
    safe = monthly_income - monthly_spending - savings_target - upcoming_recurring
    return round(safe, 2)


# ---------------------------------------------------------------------------
# Savings rate
# ---------------------------------------------------------------------------

def get_savings_rate(income: float, spending: float) -> float:
    """Return the savings rate as a percentage (0–100).

    Returns 0.0 when income is zero to avoid division errors.
    """
    if income <= 0:
        return 0.0
    net = income - spending
    return round((net / income) * 100, 2)
