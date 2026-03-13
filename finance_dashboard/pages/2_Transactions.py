import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_transactions, add_transaction, update_transaction, delete_transaction

st.title("Transactions")

# Load data
df = get_transactions()

# --- Sidebar filters ---
st.sidebar.header("Filters")

if df is not None and not df.empty:
    # Category filter
    all_categories = sorted(df['category'].dropna().unique().tolist()) if 'category' in df.columns else []
    selected_categories = st.sidebar.multiselect("Category", options=all_categories, default=all_categories)

    # Type filter
    all_types = sorted(df['type'].dropna().unique().tolist()) if 'type' in df.columns else ['income', 'expense', 'transfer']
    selected_types = st.sidebar.multiselect("Type", options=all_types, default=all_types)

    # Date range filter
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
    else:
        min_date = date.today().replace(day=1)
        max_date = date.today()

    start_date = st.sidebar.date_input("Start Date", value=min_date)
    end_date = st.sidebar.date_input("End Date", value=max_date)

    # Apply filters
    filtered_df = df.copy()
    if 'category' in filtered_df.columns and selected_categories:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
    if 'type' in filtered_df.columns and selected_types:
        filtered_df = filtered_df[filtered_df['type'].isin(selected_types)]
    if 'date' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= start_date) &
            (filtered_df['date'].dt.date <= end_date)
        ]

    # --- Summary row ---
    total_amount = filtered_df['amount'].sum() if 'amount' in filtered_df.columns else 0.0
    st.write(f"**{len(filtered_df)} transactions** | Total amount: **${total_amount:,.2f}**")

    # --- Transactions table ---
    display_cols = [c for c in ['date', 'description', 'category', 'type', 'account', 'amount', 'notes'] if c in filtered_df.columns]
    if display_cols:
        st.dataframe(filtered_df[display_cols].sort_values('date', ascending=False) if 'date' in display_cols else filtered_df[display_cols],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No columns available to display.")

else:
    st.info("No transaction data found. Use the form below to add your first transaction.")
    filtered_df = pd.DataFrame()

st.divider()

# --- Category options shared across forms ---
CATEGORY_OPTIONS = ['Housing', 'Food', 'Transportation', 'Entertainment',
                    'Healthcare', 'Shopping', 'Income', 'Savings', 'Other']
TYPE_OPTIONS = ['expense', 'income', 'transfer']

# --- Add New Transaction ---
with st.expander("Add New Transaction"):
    with st.form("add_transaction_form"):
        st.subheader("Add New Transaction")
        new_date = st.date_input("Date", value=date.today(), key="add_date")
        new_description = st.text_input("Description", key="add_description")
        new_category = st.selectbox("Category", options=CATEGORY_OPTIONS, key="add_category")
        new_type = st.selectbox("Type", options=TYPE_OPTIONS, key="add_type")
        new_account = st.text_input("Account", key="add_account")
        new_amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f", key="add_amount")
        new_notes = st.text_area("Notes (optional)", key="add_notes")
        submitted = st.form_submit_button("Add Transaction")

    if submitted:
        if not new_description.strip():
            st.warning("Please enter a description for the transaction.")
        else:
            add_transaction(
                date=new_date,
                description=new_description.strip(),
                category=new_category,
                type=new_type,
                account=new_account.strip(),
                amount=new_amount,
                notes=new_notes.strip()
            )
            st.success(f"Transaction '{new_description}' added successfully.")
            st.rerun()

# --- Edit Transaction ---
with st.expander("Edit Transaction"):
    st.subheader("Edit Transaction")
    edit_id = st.number_input("Transaction ID to Edit", min_value=1, step=1, key="edit_id_input")
    load_clicked = st.button("Load Transaction", key="load_transaction_btn")

    if load_clicked:
        if df is not None and not df.empty and 'id' in df.columns:
            match = df[df['id'] == edit_id]
            if not match.empty:
                row = match.iloc[0]
                st.session_state['edit_row'] = row.to_dict()
                st.success(f"Transaction {edit_id} loaded.")
            else:
                st.warning(f"No transaction found with ID {edit_id}.")
        else:
            st.warning("No transactions available or 'id' column not found.")

    if 'edit_row' in st.session_state:
        row = st.session_state['edit_row']
        with st.form("edit_transaction_form"):
            row_date = row.get('date')
            if hasattr(row_date, 'date'):
                row_date = row_date.date()
            elif not isinstance(row_date, date):
                row_date = date.today()

            edit_date = st.date_input("Date", value=row_date, key="edit_date")
            edit_description = st.text_input("Description", value=row.get('description', ''), key="edit_description")

            cat_val = row.get('category', CATEGORY_OPTIONS[0])
            cat_index = CATEGORY_OPTIONS.index(cat_val) if cat_val in CATEGORY_OPTIONS else 0
            edit_category = st.selectbox("Category", options=CATEGORY_OPTIONS, index=cat_index, key="edit_category")

            type_val = row.get('type', TYPE_OPTIONS[0])
            type_index = TYPE_OPTIONS.index(type_val) if type_val in TYPE_OPTIONS else 0
            edit_type = st.selectbox("Type", options=TYPE_OPTIONS, index=type_index, key="edit_type")

            edit_account = st.text_input("Account", value=row.get('account', ''), key="edit_account")
            edit_amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f",
                                          value=float(row.get('amount', 0.0)), key="edit_amount")
            edit_notes = st.text_area("Notes (optional)", value=row.get('notes', ''), key="edit_notes")
            edit_submitted = st.form_submit_button("Save Changes")

        if edit_submitted:
            if not edit_description.strip():
                st.warning("Description cannot be empty.")
            else:
                update_transaction(
                    transaction_id=edit_id,
                    date=edit_date,
                    description=edit_description.strip(),
                    category=edit_category,
                    type=edit_type,
                    account=edit_account.strip(),
                    amount=edit_amount,
                    notes=edit_notes.strip()
                )
                del st.session_state['edit_row']
                st.success(f"Transaction {edit_id} updated successfully.")
                st.rerun()

# --- Delete Transaction ---
with st.expander("Delete Transaction"):
    st.subheader("Delete Transaction")
    delete_id = st.number_input("Transaction ID to Delete", min_value=1, step=1, key="delete_id_input")

    if 'confirm_delete' not in st.session_state:
        st.session_state['confirm_delete'] = False

    delete_clicked = st.button("Delete Transaction", key="delete_btn")

    if delete_clicked:
        if df is not None and not df.empty and 'id' in df.columns:
            match = df[df['id'] == delete_id]
            if not match.empty:
                st.session_state['confirm_delete'] = True
                st.session_state['pending_delete_id'] = delete_id
            else:
                st.warning(f"No transaction found with ID {delete_id}.")
        else:
            st.warning("No transactions available or 'id' column not found.")

    if st.session_state.get('confirm_delete') and st.session_state.get('pending_delete_id') == delete_id:
        st.warning(f"Are you sure you want to delete transaction ID {delete_id}? This cannot be undone.")
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button("Yes, Delete", key="confirm_delete_btn"):
                delete_transaction(transaction_id=delete_id)
                st.session_state['confirm_delete'] = False
                st.session_state.pop('pending_delete_id', None)
                st.success(f"Transaction {delete_id} deleted successfully.")
                st.rerun()
        with cancel_col:
            if st.button("Cancel", key="cancel_delete_btn"):
                st.session_state['confirm_delete'] = False
                st.session_state.pop('pending_delete_id', None)
                st.rerun()
