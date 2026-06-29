import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# ---------------- APP CONFIGURATION ---------------- #
st.set_page_config(page_title="Monthly Expenses Tracker", page_icon="💰", layout="wide")

# Initialize Session State
defaults = {
    "logged_in": False, "user_id": None, "username": "", 
    "dark_theme": True, "monthly_budget": 50000.0, "active_quick_amt": 0.0
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------- DATABASE STORAGE ---------------- #
def get_db_connection():
    return sqlite3.connect("expense_tracker.db", check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, monthly_budget REAL DEFAULT 50000.00)")
    cursor.execute("CREATE TABLE IF NOT EXISTS expenses (expense_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, expense_date TEXT, category TEXT, amount REAL, note TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS income (income_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, income_date TEXT, source TEXT, amount REAL, FOREIGN KEY(user_id) REFERENCES users(user_id))")
    cursor.execute("CREATE TABLE IF NOT EXISTS custom_categories (category_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, category_name TEXT, UNIQUE(user_id, category_name))")
    conn.commit()
    conn.close()

init_db()

# --- Helper Functions ---
def get_monthly_financial_totals(user_id, month_str):
    conn = get_db_connection()
    inc = pd.read_sql_query("SELECT IFNULL(SUM(amount), 0) FROM income WHERE user_id=? AND strftime('%Y-%m', income_date)=?", conn, params=(user_id, month_str)).iloc[0, 0]
    exp = pd.read_sql_query("SELECT IFNULL(SUM(amount), 0) FROM expenses WHERE user_id=? AND strftime('%Y-%m', expense_date)=?", conn, params=(user_id, month_str)).iloc[0, 0]
    conn.close()
    return float(inc), float(exp)

def get_user_categories(user_id):
    defaults = ["🍔 Food", "🚗 Travel", "🛍️ Shopping", "💡 Bills", "🎬 Entertainment", "✨ Others"]
    conn = get_db_connection()
    custom = pd.read_sql_query("SELECT category_name FROM custom_categories WHERE user_id=?", conn, params=(user_id,))
    conn.close()
    return defaults + custom['category_name'].tolist()

# ---------------- SIDEBAR & AUTH ---------------- #
with st.sidebar:
    st.title("💰 Expense Tracker")
    if not st.session_state.logged_in:
        mode = st.radio("Access", ["Log In", "Create Account"])
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Submit"):
            conn = get_db_connection()
            if mode == "Create Account":
                try:
                    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pwd))
                    conn.commit()
                    st.success("Account created!")
                except: st.error("User exists.")
            else:
                res = conn.execute("SELECT user_id, monthly_budget FROM users WHERE username=? AND password=?", (user, pwd)).fetchone()
                if res:
                    st.session_state.update({"logged_in": True, "user_id": res[0], "username": user, "monthly_budget": res[1]})
                    st.rerun()
            conn.close()
    else:
        st.write(f"Hello, **{st.session_state.username}**")
        menu = st.radio("Navigation", ["Dashboard", "Log Expense", "Log Income", "Settings"])
        if st.button("Log Out"):
            for key in defaults: st.session_state[key] = defaults[key]
            st.rerun()

# ---------------- MAIN CONTENT ---------------- #
if not st.session_state.logged_in:
    st.info("Please log in from the sidebar.")
else:
    if menu == "Dashboard":
        st.header("📊 Dashboard")
        month = st.date_input("Select Month", datetime.now()).strftime("%Y-%m")
        inc, exp = get_monthly_financial_totals(st.session_state.user_id, month)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"₹{inc:,.0f}")
        c2.metric("Expenses", f"₹{exp:,.0f}")
        c3.metric("Balance", f"₹{inc-exp:,.0f}")

    elif menu == "Log Expense":
        st.header("📤 Log Expense")
        with st.form("exp_form"):
            date = st.date_input("Date")
            cat = st.selectbox("Category", get_user_categories(st.session_state.user_id))
            amt = st.number_input("Amount", min_value=0.0)
            note = st.text_input("Note")
            if st.form_submit_button("Add"):
                conn = get_db_connection()
                conn.execute("INSERT INTO expenses (user_id, expense_date, category, amount, note) VALUES (?,?,?,?,?)", 
                             (st.session_state.user_id, date, cat, amt, note))
                conn.commit()
                conn.close()
                st.success("Logged!")

    elif menu == "Settings":
        st.header("⚙️ Settings")
        new_budget = st.number_input("Update Monthly Budget", value=st.session_state.monthly_budget)
        if st.button("Save Budget"):
            conn = get_db_connection()
            conn.execute("UPDATE users SET monthly_budget=? WHERE user_id=?", (new_budget, st.session_state.user_id))
            conn.commit()
            conn.close()
            st.session_state.monthly_budget = new_budget
            st.success("Budget Updated!")
        
        new_cat = st.text_input("Add Custom Category")
        if st.button("Add Category"):
            conn = get_db_connection()
            try:
                conn.execute("INSERT INTO custom_categories (user_id, category_name) VALUES (?,?)", (st.session_state.user_id, new_cat))
                conn.commit()
            except: st.error("Category exists.")
            conn.close()
            st.rerun()