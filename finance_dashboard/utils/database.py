"""
database.py
-----------
Handles all SQLite database operations for the personal finance dashboard.
The database file lives at data/finance.db, relative to the project root
(finance_dashboard/).

All public functions either return a pandas DataFrame or perform a write
operation with no return value (unless noted otherwise).
"""

import os
import sqlite3
import pandas as pd

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

# Resolve the project root directory (finance_dashboard/) regardless of where
# the script is imported from.
_HERE = os.path.dirname(os.path.abspath(__file__))          # utils/
_PROJECT_ROOT = os.path.dirname(_HERE)                       # finance_dashboard/
DB_PATH = os.path.join(_PROJECT_ROOT, "data", "finance.db")


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Return a sqlite3 connection to the finance database.

    The row_factory is set to sqlite3.Row so that rows can be accessed by
    column name as well as by index.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

_CREATE_TRANSACTIONS = """
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT    NOT NULL,
    description TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    type        TEXT    NOT NULL,   -- 'income' or 'expense'
    account     TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    notes       TEXT
)
"""

_CREATE_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name    TEXT    NOT NULL,
    account_type    TEXT    NOT NULL,
    current_balance REAL    NOT NULL
)
"""

_CREATE_GOALS = """
CREATE TABLE IF NOT EXISTS goals (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_name      TEXT    NOT NULL,
    target_amount  REAL    NOT NULL,
    current_amount REAL    NOT NULL,
    target_date    TEXT    NOT NULL,
    goal_type      TEXT    NOT NULL
)
"""

_CREATE_RECURRING = """
CREATE TABLE IF NOT EXISTS recurring_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    description   TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    amount        REAL    NOT NULL,
    frequency     TEXT    NOT NULL,  -- e.g. 'monthly', 'weekly', 'yearly'
    next_due_date TEXT    NOT NULL
)
"""


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

_SAMPLE_ACCOUNTS = [
    ("Checking",     "checking", 5000.00),
    ("Savings",      "savings",  15000.00),
    ("Credit Card",  "credit",   -800.00),
]

_SAMPLE_TRANSACTIONS = [
    # (date, description, category, type, account, amount, notes)
    ("2026-01-03", "Monthly Salary",        "income",        "income",  "Checking",    5500.00, "January paycheck"),
    ("2026-01-05", "Rent Payment",          "housing",       "expense", "Checking",    1500.00, "January rent"),
    ("2026-01-10", "Grocery Store",         "groceries",     "expense", "Checking",     220.00, None),
    ("2026-01-15", "Electric Bill",         "utilities",     "expense", "Checking",      95.00, None),
    ("2026-01-18", "Netflix",               "entertainment", "expense", "Credit Card",   15.00, "Streaming subscription"),
    ("2026-02-03", "Monthly Salary",        "income",        "income",  "Checking",    5500.00, "February paycheck"),
    ("2026-02-05", "Rent Payment",          "housing",       "expense", "Checking",    1500.00, "February rent"),
    ("2026-02-12", "Grocery Store",         "groceries",     "expense", "Checking",     185.00, None),
    ("2026-02-20", "Gym Membership",        "health",        "expense", "Credit Card",   50.00, None),
    ("2026-02-25", "Restaurant Dinner",     "dining",        "expense", "Credit Card",   68.00, "Night out"),
    # March 2026 (current month) — gives the Dashboard real data to display
    ("2026-03-03", "Monthly Salary",        "income",        "income",  "Checking",    5500.00, "March paycheck"),
    ("2026-03-05", "Rent Payment",          "housing",       "expense", "Checking",    1500.00, "March rent"),
    ("2026-03-08", "Grocery Store",         "groceries",     "expense", "Checking",     210.00, None),
    ("2026-03-10", "Netflix",               "entertainment", "expense", "Credit Card",   15.00, "Streaming subscription"),
    ("2026-03-12", "Coffee Shop",           "dining",        "expense", "Credit Card",   24.00, None),
]

_SAMPLE_GOALS = [
    # (goal_name, target_amount, current_amount, target_date, goal_type)
    ("Emergency Fund", 20000.00, 15000.00, "2026-12-31", "savings"),
    ("Vacation",        3000.00,   800.00, "2026-08-01", "savings"),
]

_SAMPLE_RECURRING = [
    # (description, category, amount, frequency, next_due_date)
    ("Rent",    "housing",       1500.00, "monthly", "2026-04-01"),
    ("Netflix", "entertainment",   15.00, "monthly", "2026-04-01"),
    ("Gym",     "health",          50.00, "monthly", "2026-04-01"),
]


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables (if they do not already exist) and seed sample data.

    Sample data is only inserted when each table is empty, so repeated calls
    to init_db() are idempotent.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Create tables
    cur.execute(_CREATE_TRANSACTIONS)
    cur.execute(_CREATE_ACCOUNTS)
    cur.execute(_CREATE_GOALS)
    cur.execute(_CREATE_RECURRING)
    conn.commit()

    # Seed accounts
    if cur.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO accounts (account_name, account_type, current_balance) VALUES (?, ?, ?)",
            _SAMPLE_ACCOUNTS,
        )

    # Seed transactions
    if cur.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 0:
        cur.executemany(
            """INSERT INTO transactions
               (date, description, category, type, account, amount, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            _SAMPLE_TRANSACTIONS,
        )

    # Seed goals
    if cur.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0:
        cur.executemany(
            """INSERT INTO goals
               (goal_name, target_amount, current_amount, target_date, goal_type)
               VALUES (?, ?, ?, ?, ?)""",
            _SAMPLE_GOALS,
        )

    # Seed recurring items
    if cur.execute("SELECT COUNT(*) FROM recurring_items").fetchone()[0] == 0:
        cur.executemany(
            """INSERT INTO recurring_items
               (description, category, amount, frequency, next_due_date)
               VALUES (?, ?, ?, ?, ?)""",
            _SAMPLE_RECURRING,
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def get_transactions() -> pd.DataFrame:
    """Return all transactions as a DataFrame, ordered by date descending."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM transactions ORDER BY date DESC",
        conn,
    )
    conn.close()
    return df


def add_transaction(
    date: str,
    description: str,
    category: str,
    type: str,
    account: str,
    amount: float,
    notes: str,
) -> None:
    """Insert a new transaction row."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO transactions
           (date, description, category, type, account, amount, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (date, description, category, type, account, amount, notes),
    )
    conn.commit()
    conn.close()


def update_transaction(
    id: int,
    date: str,
    description: str,
    category: str,
    type: str,
    account: str,
    amount: float,
    notes: str,
) -> None:
    """Update an existing transaction identified by its primary key."""
    conn = get_connection()
    conn.execute(
        """UPDATE transactions
           SET date=?, description=?, category=?, type=?, account=?, amount=?, notes=?
           WHERE id=?""",
        (date, description, category, type, account, amount, notes, id),
    )
    conn.commit()
    conn.close()


def delete_transaction(id: int) -> None:
    """Delete the transaction with the given primary key."""
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id=?", (id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

def get_accounts() -> pd.DataFrame:
    """Return all accounts as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM accounts ORDER BY account_name", conn)
    conn.close()
    return df


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

def get_goals() -> pd.DataFrame:
    """Return all goals as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM goals ORDER BY target_date", conn)
    conn.close()
    return df


def add_goal(
    goal_name: str,
    target_amount: float,
    current_amount: float,
    target_date: str,
    goal_type: str,
) -> None:
    """Insert a new savings/financial goal."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO goals
           (goal_name, target_amount, current_amount, target_date, goal_type)
           VALUES (?, ?, ?, ?, ?)""",
        (goal_name, target_amount, current_amount, target_date, goal_type),
    )
    conn.commit()
    conn.close()


def update_goal(
    id: int,
    goal_name: str,
    target_amount: float,
    current_amount: float,
    target_date: str,
    goal_type: str,
) -> None:
    """Update an existing goal identified by its primary key."""
    conn = get_connection()
    conn.execute(
        """UPDATE goals
           SET goal_name=?, target_amount=?, current_amount=?, target_date=?, goal_type=?
           WHERE id=?""",
        (goal_name, target_amount, current_amount, target_date, goal_type, id),
    )
    conn.commit()
    conn.close()


def delete_goal(id: int) -> None:
    """Delete the goal with the given primary key."""
    conn = get_connection()
    conn.execute("DELETE FROM goals WHERE id=?", (id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Recurring items
# ---------------------------------------------------------------------------

def get_recurring_items() -> pd.DataFrame:
    """Return all recurring items as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM recurring_items ORDER BY next_due_date",
        conn,
    )
    conn.close()
    return df
