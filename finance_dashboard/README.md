# Personal Finance Dashboard

A Streamlit app for tracking personal income, expenses, savings goals, and running financial simulations.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py
   ```

## Usage

| Page | Description |
|------|-------------|
| **Dashboard** | Overview charts showing spending by category, income vs. expenses, and monthly trends. |
| **Transactions** | Log new income or expense transactions and browse/filter transaction history. |
| **Simulator** | Model future account balances by adjusting income, spending, and savings rate assumptions. |
| **Goals** | Create savings targets and track progress toward each goal over time. |

## File Structure

```
finance_dashboard/
├── app.py                  # Main entry point and landing page
├── requirements.txt        # Python dependencies
├── README.md
├── pages/
│   ├── 1_Dashboard.py
│   ├── 2_Transactions.py
│   ├── 3_Simulator.py
│   └── 4_Goals.py
├── utils/
│   └── database.py         # DB init, schema, and query helpers
└── data/
    └── finance.db          # SQLite database (auto-created on first run)
```

## Notes

- Data is stored locally in `data/finance.db` (SQLite) — no external services required.
- Sample data is loaded automatically on the first run so you can explore the app immediately.
- All pages are discovered automatically by Streamlit via the `pages/` folder.
