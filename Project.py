import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# ---------------- APP CONFIGURATION ---------------- #
st.set_page_config(page_title="Monthly Expenses Tracker", page_icon="💰", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "dark_theme" not in st.session_state:
    st.session_state.dark_theme = True
if "monthly_budget" not in st.session_state:
    st.session_state.monthly_budget = 50000.00
if "active_quick_amt" not in st.session_state:
    st.session_state.active_quick_amt = 0.0

# ---------------- DATABASE STORAGE ---------------- #
def get_db_connection():
    return sqlite3.connect("expense_tracker.db", check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE, 
            password TEXT,
            monthly_budget REAL DEFAULT 50000.00
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, expense_date TEXT,
            category TEXT, amount REAL, payment_mode TEXT, note TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            income_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, income_date TEXT,
            source TEXT, amount REAL, note TEXT, FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, category_name TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id), UNIQUE(user_id, category_name)
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN monthly_budget REAL DEFAULT 50000.00")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

init_db()

def get_monthly_financial_totals(user_id, month_str):
    conn = get_db_connection()
    inc_query = "SELECT IFNULL(SUM(amount), 0) as total FROM income WHERE user_id=? AND strftime('%Y-%m', income_date)=?"
    exp_query = "SELECT IFNULL(SUM(amount), 0) as total FROM expenses WHERE user_id=? AND strftime('%Y-%m', expense_date)=?"
    
    df_inc = pd.read_sql_query(inc_query, conn, params=(user_id, month_str))
    df_exp = pd.read_sql_query(exp_query, conn, params=(user_id, month_str))
    conn.close()
    return float(df_inc["total"].iloc[0]), float(df_exp["total"].iloc[0])

def get_all_transaction_years(user_id):
    conn = get_db_connection()
    query = """
        SELECT DISTINCT strftime('%Y', expense_date) as year FROM expenses WHERE user_id=?
        UNION
        SELECT DISTINCT strftime('%Y', income_date) as year FROM income WHERE user_id=?
    """
    df = pd.read_sql_query(query, conn, params=(user_id, user_id))
    conn.close()
    
    years = df['year'].dropna().tolist()
    years = sorted([int(y) for y in years if y.isdigit()], reverse=True)
    
    current_year = datetime.today().year
    if current_year not in years:
        years.insert(0, current_year)
    return years

def get_user_categories(user_id):
    default_cats = ["🍔 Food & Dining", "🚗 Travel & Transport", "🛍️ Shopping", "💡 Bills & Utilities", "🎬 Fun & Entertainment", "✨ Others"]
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT category_name FROM custom_categories WHERE user_id=?", conn, params=(user_id,))
    conn.close()
    if not df.empty:
        return default_cats + df['category_name'].tolist()
    return default_cats

# ---------------- STYLE SETTING ---------------- #
if st.session_state.dark_theme:
    st.markdown("""
        <style>
            .stApp { background-color: #0B0F19; color: #F8FAFC; }
            h1, h2, h3, h4, h5, h6, .content-card h4, .content-card h5 { color: #FFFFFF !important; font-weight: 700; }
            p, span, label, [data-testid="stMarkdownContainer"] p { color: #F8FAFC !important; }
            
            .dashboard-metric {
                border-radius: 14px; padding: 20px; margin-bottom: 15px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25); background: #111827; border: 1px solid #1E293B;
            }
            .m-income { border-top: 4px solid #3B82F6; }
            .m-expense { border-top: 4px solid #EF4444; }
            .m-balance { border-top: 4px solid #10B981; }
            .m-budget { border-top: 4px solid #F59E0B; }
            .metric-lbl { font-size: 13px; color: #94A3B8 !important; font-weight: 500; text-transform: uppercase; }
            .metric-val { font-size: 26px; font-weight: 700; color: #FFFFFF !important; margin-top: 5px; }
            
            section[data-testid="stSidebar"] { background-color: #0D1527 !important; border-right: 1px solid #1E293B; }
            section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #FFFFFF !important; }
            
            .content-card { background-color: #111827; padding: 25px; border-radius: 14px; border: 1px solid #1E293B; margin-bottom: 25px; }
            
            .stButton>button, .stButton>button p, .stButton>button span { color: #FFFFFF !important; font-weight: 600 !important; }
            .stButton>button { background-color: #1F2937 !important; border: 1px solid #374151 !important; border-radius: 8px !important; }
            .stButton>button:hover { background-color: #374151 !important; }
        </style>
    """, unsafe_allow_html=True)
    chart_bg = '#111827'
    chart_text = '#94A3B8'
    chart_grid = '#1E293B'
    pie_text_color = '#FFFFFF'
else:
    st.markdown("""
        <style>
            .stApp { background-color: #F8FAFC; color: #0F172A; }
            h1, h2, h3, h4, h5, h6, .content-card h4, .content-card h5 { color: #0F172A !important; font-weight: 700; }
            p, span, label, [data-testid="stMarkdownContainer"] p { color: #334155 !important; }
            
            .dashboard-metric {
                border-radius: 14px; padding: 20px; margin-bottom: 15px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); background: #FFFFFF; border: 1px solid #E2E8F0;
            }
            .m-income { border-top: 4px solid #2563EB; }
            .m-expense { border-top: 4px solid #DC2626; }
            .m-balance { border-top: 4px solid #16A34A; }
            .m-budget { border-top: 4px solid #EA580C; }
            .metric-lbl { font-size: 13px; color: #64748B !important; font-weight: 500; text-transform: uppercase; }
            .metric-val { font-size: 26px; font-weight: 700; color: #0F172A !important; margin-top: 5px; }
            
            section[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
            section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #0F172A !important; }
            
            .content-card { background-color: #FFFFFF; padding: 25px; border-radius: 14px; border: 1px solid #E2E8F0; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
            
            .stButton>button, .stButton>button p, .stButton>button span { color: #0F172A !important; font-weight: 600 !important; }
            .stButton>button { background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 8px !important; }
            .stButton>button:hover { background-color: #F1F5F9 !important; border-color: #94A3B8 !important; }
        </style>
    """, unsafe_allow_html=True)
    chart_bg = '#FFFFFF'
    chart_text = '#475569'
    chart_grid = '#E2E8F0'
    pie_text_color = '#0F172A'

# ---------------- SIDEBAR MENU ---------------- #
menu = "📊 Dashboard Overview" 

with st.sidebar:
    st.markdown("<h2 style='text-align: center; font-weight:800; margin-bottom:5px;'>💰 MONTHLY EXPENSES TRACKER</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size:12px; margin-bottom:25px;'>Track Money Simply</p>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        st.markdown("<h4 style='margin-bottom:2px;'>Welcome! 👋</h4>", unsafe_allow_html=True)
        auth_mode = st.radio("What do you want to do?", ["Log In", "Create Account"], horizontal=True)
        
        username_input = st.text_input("Your Username", key="auth_username")
        password_input = st.text_input("Your Password", type="password", key="auth_password")
        
        if st.button("START NOW", type="primary", use_container_width=True):
            if username_input.strip() and password_input.strip():
                conn = get_db_connection()
                cursor = conn.cursor()
                if auth_mode == "Log In":
                    cursor.execute("SELECT user_id, username, monthly_budget FROM users WHERE username=? AND password=?", (username_input.strip(), password_input.strip()))
                    user = cursor.fetchone()
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.monthly_budget = user[2]
                        conn.close() 
                        st.rerun()
                    else:
                        st.error("Wrong username or password. Please try again!")
                elif auth_mode == "Create Account":
                    try:
                        cursor.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username_input.strip(), password_input.strip()))
                        conn.commit()
                        st.success("🎉 Success! Now switch to 'Log In' above to enter.")
                    except sqlite3.IntegrityError:
                        st.error("This username is already taken!")
                conn.close()
    else:
        st.markdown(f"<p style='color:#94A3B8; margin-bottom: 2px;'>Hello,</p><h4 style='margin-top:0px;'>👤 {st.session_state.username}</h4>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("MENU", ["📊 Dashboard Overview", "📤 Log an Expense", "📥 Log an Income", "⚙️ App Settings"])
        
        st.markdown("---")
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""
            st.rerun()

# ---------------- MAIN WINDOW DISPLAY ---------------- #
if not st.session_state.logged_in:
    st.info("← Please log in or create an account in the sidebar to start tracking your money!")
else:
    conn = get_db_connection()
    available_categories = get_user_categories(st.session_state.user_id)
    
    # Header & Date Filters
    t_col1, t_col2, t_col3 = st.columns([3, 2, 1])
    with t_col1:
        st.title(menu)
    
    with t_col2:
        years_pool = get_all_transaction_years(st.session_state.user_id)
        months_pool = [("Jan", "01"), ("Feb", "02"), ("Mar", "03"), ("Apr", "04"), ("May", "05"), ("Jun", "06"), 
                       ("Jul", "07"), ("Aug", "08"), ("Sep", "09"), ("Oct", "10"), ("Nov", "11"), ("Dec", "12")]
        
        y_col, m_col = st.columns(2)
        sel_year = y_col.selectbox("Choose Year", years_pool, index=0)
        sel_month_tuple = m_col.selectbox("Choose Month", months_pool, index=datetime.today().month - 1, format_func=lambda x: x[0])
        
        selected_month_str = f"{sel_year}-{sel_month_tuple[1]}"
        selected_month_display = f"{sel_month_tuple[0]} {sel_year}"
        
    with t_col3:
        st.write(" ")
        theme_toggle = st.toggle("🌙 Dark View", value=st.session_state.dark_theme)
        if theme_toggle != st.session_state.dark_theme:
            st.session_state.dark_theme = theme_toggle
            conn.close()
            st.rerun()
            
    total_income, total_expense = get_monthly_financial_totals(st.session_state.user_id, selected_month_str)
    net_balance = total_income - total_expense
    budget_pct = (total_expense / st.session_state.monthly_budget * 100) if st.session_state.monthly_budget > 0 else 0
    
    # ---------------- VIEW 1: DASHBOARD OVERVIEW ---------------- #
    if menu == "📊 Dashboard Overview":
        st.markdown("### 💡 Monthly Summary Snapshot")
        st.caption("Here is your total cash summary card for the selected month.")
        
        # Summary KPI Cards Row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='dashboard-metric m-income'><div class='metric-lbl'>Total Income</div><div class='metric-val'>₹ {total_income:,.0f}</div></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='dashboard-metric m-expense'><div class='metric-lbl'>Total Spent</div><div class='metric-val'>₹ {total_expense:,.0f}</div></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='dashboard-metric m-balance'><div class='metric-lbl'>Net Savings</div><div class='metric-val'>₹ {net_balance:,.0f}</div></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='dashboard-metric m-budget'><div class='metric-lbl'>Budget Limit</div><div class='metric-val'>₹ {st.session_state.monthly_budget:,.0f}</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        
        col_g1, col_g2 = st.columns([3, 2])
        
        with col_g1:
            st.markdown("<div class='content-card'><h3>📈 Monthly Budget Progress Status</h3>", unsafe_allow_html=True)
            st.write(f"**💰 Total Money Earned:** ₹ {total_income:,.2f}")
            st.progress(1.0 if total_income > 0 else 0.0)
            
            expense_to_income_ratio = min(total_expense / total_income, 1.0) if total_income > 0 else 0.0
            st.write(f"**📉 Total Money Spent:** ₹ {total_expense:,.2f} ({expense_to_income_ratio * 100:.1f}% of income used)")
            st.progress(expense_to_income_ratio)
            
            if total_expense > total_income:
                st.error("⚠️ Warning: Your monthly expenses have completely crossed your total income!")
            elif total_income > 0:
                st.success(f"🌱 Perfect! You successfully saved ₹ {net_balance:,.2f} of your earnings this month.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_g2:
            st.markdown("<div class='content-card'><h3>🍰 Spend Category Share</h3>", unsafe_allow_html=True)
            df_cat = pd.read_sql_query(
                "SELECT category, SUM(amount) as total FROM expenses WHERE user_id=? AND strftime('%Y-%m', expense_date)=? GROUP BY category", 
                conn, params=(st.session_state.user_id, selected_month_str)
            )
            if not df_cat.empty:
                fig2, ax2 = plt.subplots(figsize=(4.5, 3.5))
                fig2.patch.set_facecolor(chart_bg)
                ax2.set_facecolor(chart_bg)
                ax2.pie(df_cat['total'], labels=df_cat['category'], autopct='%1.0f%%', startangle=140,
                        textprops={'color': pie_text_color, 'fontsize': 10, 'weight': 'bold'}, 
                        colors=['#38BDF8', '#F43F5E', '#10B981', '#F59E0B', '#A855F7', '#EC4899', '#6366F1'])
                ax2.axis('equal')
                st.pyplot(fig2)
            else:
                st.info(f"No payments logged for {selected_month_display} yet.")
            st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown("---")
        
        # Recent History Logs Block
        b_col1, b_col2 = st.columns([3, 2])
        with b_col1:
            st.markdown("<div class='content-card'><h3>⏱️ Last 3 Entries Added</h3>", unsafe_allow_html=True)
            query = '''
SELECT expense_date AS Date,'Expense' AS Type,category AS Category,amount AS Amount,note AS Details
FROM expenses WHERE user_id=?
UNION ALL
SELECT income_date AS Date,'Income' AS Type,source AS Category,amount AS Amount,note AS Details
FROM income WHERE user_id=?
ORDER BY Date DESC
LIMIT 3
'''
            df_rec = pd.read_sql_query(query, conn,
                params=(st.session_state.user_id, st.session_state.user_id))
            if not df_rec.empty:
                for _, row in df_rec.iterrows():
                    if row["Type"]=="Income":
                        st.success(f"💰 Income: ₹{row['Amount']:,.2f} | {row['Category']} | {row['Date']}")
                    else:
                        st.error(f"💸 Expense: ₹{row['Amount']:,.2f} | {row['Category']} | {row['Date']}")
            else:
                st.caption("Your recent transactions history log is completely clear.")
            st.markdown("</div>", unsafe_allow_html=True)
                
        with b_col2:
            st.markdown("<div class='content-card'><h3>💾 Export and Save Reports</h3>", unsafe_allow_html=True)
            st.write("Download your full transactions database log into an Excel-friendly CSV file format instantly.")
            export_query = '''
SELECT expense_date AS Date,'Expense' AS Type,category AS Category,amount,note
FROM expenses WHERE user_id=?
UNION ALL
SELECT income_date,'Income',source,amount,note
FROM income WHERE user_id=?
ORDER BY Date DESC
'''
            df_export = pd.read_sql_query(export_query, conn,
                params=(st.session_state.user_id, st.session_state.user_id))
            csv_data = df_export.to_csv(index=False).encode('utf-8') if not df_export.empty else b""
            
            st.download_button(
                label="🧾 Download full CSV Sheet",
                data=csv_data,
                file_name=f"my_money_records.csv",
                mime="text/csv",
                use_container_width=True,
                disabled=df_export.empty
            )
            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- VIEW 2: LOG AN EXPENSE ---------------- #
    elif menu == "📤 Log an Expense":
        st.markdown("### 🔍 Manage or Add Your Spending Records")
        st.caption("This section allows you to log new expense entries or review, edit, and delete existing entries.")
        
        df_exp = pd.read_sql_query(
            "SELECT expense_id, expense_date as Date, category as Category, amount as Amount, note as Details FROM expenses WHERE user_id=? ORDER BY expense_id DESC", 
            conn, params=(st.session_state.user_id,)
        )
        
        selected_exp_id = None
        default_date = datetime.today()
        default_cat_idx = 0
        default_note = ""
        
        # Form block 1: Selection Editor Matrix Table
        st.markdown("<div class='content-card'><h3>📋 Step 1: Select a Record to Edit or Delete (Optional)</h3>", unsafe_allow_html=True)
        if not df_exp.empty:
            st.caption("To update or delete an entry, check the checkbox box next to it first.")
            df_exp_editor = df_exp.copy()
            df_exp_editor.insert(0, "Select ✅", False)
            
            edited_df = st.data_editor(
                df_exp_editor,
                use_container_width=True,
                hide_index=True,
                disabled=["expense_id", "Date", "Category", "Amount", "Details"],
                key="exp_editor"
            )
            
            selected_rows = edited_df[edited_df["Select ✅"] == True]
            if not selected_rows.empty:
                matched_row = selected_rows.iloc[0]
                selected_exp_id = int(matched_row['expense_id'])
                
                try:
                    default_date = datetime.strptime(matched_row['Date'], "%Y-%m-%d")
                except:
                    default_date = datetime.today()
                    
                if matched_row['Category'] in available_categories:
                    default_cat_idx = available_categories.index(matched_row['Category'])
                st.session_state.active_quick_amt = float(matched_row['Amount'])
                default_note = str(matched_row['Details'])
                st.info(f"Selected Record Reference ID: {selected_exp_id}")
        else:
            st.info("No expense entries found in your account yet.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Form block 2: Expense Creation/Modification fields
        st.markdown("<div class='content-card'><h3>📝 Step 2: Enter Expense Details</h3>", unsafe_allow_html=True)
        st.caption("Quick Amount Shortcuts:")
        q1, q2, q3, q4 = st.columns(4)
        if q1.button("+ ₹100"): st.session_state.active_quick_amt = 100.0
        if q2.button("+ ₹200"): st.session_state.active_quick_amt = 200.0
        if q3.button("+ ₹500"): st.session_state.active_quick_amt = 500.0
        if q4.button("+ ₹1,000"): st.session_state.active_quick_amt = 1000.0
        
        with st.form("expense_management_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            d_in = c1.date_input("Date of Transaction", value=default_date)
            cat_in = c2.selectbox("Category Group", available_categories, index=default_cat_idx)
            amt_in = c3.number_input("Amount Paid (₹)", min_value=0.0, value=st.session_state.active_quick_amt)
            
            note_in = st.text_input("Transaction Description Notes", value=default_note)
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            add_submitted = btn_col1.form_submit_button("📤 LOG NEW ENTRY", use_container_width=True)
            update_submitted = btn_col2.form_submit_button("💾 SAVE CHANGES TO SELECTED", use_container_width=True)
            delete_submitted = btn_col3.form_submit_button("🗑️ DELETE SELECTED ENTRY", use_container_width=True)
            
            if not note_in.strip():
                note_in = f"Paid for {cat_in}"
                
            cursor = conn.cursor()
            if add_submitted:
                if amt_in > 0:
                    cursor.execute("INSERT INTO expenses(user_id, expense_date, category, amount, payment_mode, note) VALUES(?,?,?,?,?,?)",
                                   (st.session_state.user_id, str(d_in), cat_in, amt_in, "UPI", note_in))
                    conn.commit()
                    st.success("Logged successfully!")
                    st.session_state.active_quick_amt = 0.0
                    conn.close()
                    st.rerun()
                else:
                    st.error("Please enter an amount greater than 0.")
                    
            elif update_submitted:
                if selected_exp_id:
                    cursor.execute("UPDATE expenses SET expense_date=?, category=?, amount=?, note=? WHERE expense_id=? AND user_id=?", 
                                   (str(d_in), cat_in, amt_in, note_in, selected_exp_id, st.session_state.user_id))
                    conn.commit()
                    st.success("Record updated successfully!")
                    st.session_state.active_quick_amt = 0.0
                    conn.close()
                    st.rerun()
                else:
                    st.warning("Please check the 'Select ✅' checkbox in the table box above first.")
                    
            elif delete_submitted:
                if selected_exp_id:
                    cursor.execute("DELETE FROM expenses WHERE expense_id=? AND user_id=?", (selected_exp_id, st.session_state.user_id))
                    conn.commit()
                    st.success("Record deleted successfully!")
                    st.session_state.active_quick_amt = 0.0
                    conn.close()
                    st.rerun()
                else:
                    st.warning("Please check the 'Select ✅' checkbox in the table box above first.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- VIEW 3: LOG AN INCOME ---------------- #
    elif menu == "📥 Log an Income":
        st.markdown("### 🔍 Manage or Add Your Income Streams")
        st.caption("This section allows you to track incoming earnings and salary credits or review historical earnings.")
        
        df_inc = pd.read_sql_query(
            "SELECT income_id, income_date as Date, source as Source, amount as Amount FROM income WHERE user_id=? ORDER BY income_id DESC", 
            conn, params=(st.session_state.user_id,)
        )
        
        selected_inc_id = None
        default_inc_date = datetime.today()
        default_src = ""
        default_inc_amount = 0.0
        
        # Form block 1: Income Selection Row
        st.markdown("<div class='content-card'><h3>📋 Step 1: Select an Income Entry to Edit/Delete (Optional)</h3>", unsafe_allow_html=True)
        if not df_inc.empty:
            df_inc_editor = df_inc.copy()
            df_inc_editor.insert(0, "Select ✅", False)
            
            edited_inc_df = st.data_editor(
                df_inc_editor,
                use_container_width=True,
                hide_index=True,
                disabled=["income_id", "Date", "Source", "Amount"],
                key="inc_editor"
            )
            
            selected_inc_rows = edited_inc_df[edited_inc_df["Select ✅"] == True]
            if not selected_inc_rows.empty:
                matched_inc_row = selected_inc_rows.iloc[0]
                selected_inc_id = int(matched_inc_row['income_id'])
                
                try:
                    default_inc_date = datetime.strptime(matched_inc_row['Date'], "%Y-%m-%d")
                except:
                    default_inc_date = datetime.today()
                default_src = str(matched_inc_row['Source'])
                default_inc_amount = float(matched_inc_row['Amount'])
                st.info(f"Selected Income Reference ID: {selected_inc_id}")
        else:
            st.info("No recorded earnings entries found in your account history log.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Form block 2: Income input layout
        st.markdown("<div class='content-card'><h3>📝 Step 2: Enter Earning Details</h3>", unsafe_allow_html=True)
        with st.form("income_management_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            d_inc_in = c1.date_input("Date Received", value=default_inc_date)
            src_in = c2.text_input("Source/Sender Name (e.g., Salary, Freelance)", value=default_src)
            val_in = c3.number_input("Amount Deposited (₹)", min_value=0.0, value=default_inc_amount)
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            add_inc_submitted = btn_col1.form_submit_button("📥 LOG NEW INCOME", use_container_width=True)
            update_inc_submitted = btn_col2.form_submit_button("💾 SAVE CHANGES TO SELECTED", use_container_width=True)
            delete_inc_submitted = btn_col3.form_submit_button("🗑️ DELETE SELECTED INCOME", use_container_width=True)
            
            cursor = conn.cursor()
            if add_inc_submitted:
                if val_in > 0 and src_in.strip():
                    cursor.execute("INSERT INTO income(user_id, income_date, source, amount, note) VALUES(?,?,?,?,?)",
                                   (st.session_state.user_id, str(d_inc_in), src_in.strip(), val_in, ""))
                    conn.commit()
                    st.success("Income logged successfully!")
                    conn.close()
                    st.rerun()
                else:
                    st.error("Please add both a valid source name and a value higher than 0.")
                    
            elif update_inc_submitted:
                if selected_inc_id:
                    cursor.execute("UPDATE income SET income_date=?, source=?, amount=? WHERE income_id=? AND user_id=?", 
                                   (str(d_inc_in), src_in.strip(), val_in, selected_inc_id, st.session_state.user_id))
                    conn.commit()
                    st.success("Income record fixed cleanly!")
                    conn.close()
                    st.rerun()
                else:
                    st.warning("Please check the 'Select ✅' checkbox in the table box above first.")
                    
            elif delete_inc_submitted:
                if selected_inc_id:
                    cursor.execute("DELETE FROM income WHERE income_id=? AND user_id=?", (selected_inc_id, st.session_state.user_id))
                    conn.commit()
                    st.success("Income record erased successfully!")
                    conn.close()
                    st.rerun()
                else:
                    st.warning("Please check the 'Select ✅' checkbox in the table box above first.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- VIEW 4: APP SETTINGS ---------------- #
    elif menu == "⚙️ App Settings":
        st.markdown("### 👤 Account Configuration & Parameters")
        st.caption("Customize your goal limit targets, personal tracking labels, and adjust profile security info.")
        
        # Status Metric Gamification Element Block
        st.markdown("<div class='content-card'><h3>🏅 Profile Standing Score</h3>", unsafe_allow_html=True)
        if total_income > 0:
            savings_rate = ((total_income - total_expense) / total_income) * 100
        else:
            savings_rate = 0.0
            
        if total_expense == 0 and total_income == 0:
            badge_title = "🌱 Fresh Starter"
            badge_desc = "Add your first transaction entries to calculate your pocket standing level."
            badge_color = "#38BDF8"
        elif budget_pct > 100:
            badge_title = "⚠️ Target Crossed"
            badge_desc = "You have completely exceeded your goal target budget limit for this month!"
            badge_color = "#EF4444"
        elif savings_rate >= 40:
            badge_title = "👑 Wealth Master"
            badge_desc = "Phenomenal discipline! You are saving over 40% of your current income streams."
            badge_color = "#10B981"
        elif savings_rate >= 20:
            badge_title = "🛡️ Smart Saver"
            badge_desc = "Terrific work! Your financial savings path stays healthy and protected."
            badge_color = "#F59E0B"
        else:
            badge_title = "🏃 Active Tracker"
            badge_desc = "Excellent tracking habits. Try minimizing luxury expenses to grow your score."
            badge_color = "#A855F7"

        st.markdown(f"""
        <div style='background-color: {chart_bg}; padding: 15px; border-radius: 10px; border-left: 6px solid {badge_color};'>
            <h4 style='margin: 0px; color: {badge_color} !important;'>{badge_title}</h4>
            <p style='margin: 5px 0 0 0; font-size: 14px; color: #94A3B8;'>{badge_desc}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Organized Tab Layout Configurations
        profile_tab1, profile_tab2, profile_tab3 = st.tabs(["🎯 Spending Target Goal", "🏷️ Custom Categories Selection", "🔒 Security Access Info"])
        
        with profile_tab1:
            st.markdown("<div class='content-card'><h3>Set Your Maximum Monthly Budget Limit Goal</h3>", unsafe_allow_html=True)
            st.write(f"**Current Progress:** You have spent ₹ {total_expense:,.0f} out of your ₹ {st.session_state.monthly_budget:,.0f} cap.")
            clamped_pct = min(float(budget_pct / 100.0), 1.0) if budget_pct > 0 else 0.0
            st.progress(clamped_pct)
            
            with st.form("budget_limit_form"):
                new_budget = st.number_input("Enter New Monthly Spend Limit (₹)", min_value=1.0, value=st.session_state.monthly_budget)
                if st.form_submit_button("💾 UPDATE MY GOAL LIMIT"):
                    st.session_state.monthly_budget = new_budget
                    
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET monthly_budget=? WHERE user_id=?", (new_budget, st.session_state.user_id))
                    conn.commit() 
                    st.success("🎯 Budget limit goal updated successfully!")
                    conn.close()
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
        with profile_tab2:
            st.markdown("<div class='content-card'><h3>✨ Create Custom Expense Categories</h3>", unsafe_allow_html=True)
            st.write("Add your own custom tracking tags to tailor the application to your lifestyle needs.")
            
            cursor = conn.cursor()
            cursor.execute("SELECT category_name FROM custom_categories WHERE user_id=?", (st.session_state.user_id,))
            custom_cats = [row[0] for row in cursor.fetchall()]
            
            if custom_cats:
                st.write("**Your Custom Categories:** " + ", ".join([f"`{c}`" for c in custom_cats]))
            else:
                st.caption("You haven't added any custom categories yet. The default setup is currently active.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("custom_category_form", clear_on_submit=True):
                new_cat_name = st.text_input("New Category Name (e.g., 🦄 Hobbies, 🍼 Baby Care)")
                if st.form_submit_button("➕ ADD CUSTOM TAG"):
                    cleaned_cat = new_cat_name.strip()
                    if cleaned_cat:
                        try:
                            cursor.execute("INSERT INTO custom_categories(user_id, category_name) VALUES(?, ?)", (st.session_state.user_id, cleaned_cat))
                            conn.commit()
                            st.success(f"🎉 '{cleaned_cat}' added to your categories pool!")
                            conn.close()
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("This category label already exists in your account profile!")
                    else:
                        st.warning("Please enter a valid category label name.")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with profile_tab3:
            st.markdown("<div class='content-card'><h3>🔒 Update Profile Security Key</h3>", unsafe_allow_html=True)
            st.write("Modify your security password parameters below to ensure complete data integrity.")
            
            with st.form("security_update_form", clear_on_submit=True):
                new_password = st.text_input("Enter New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("🔐 CHANGE MY PASSWORD"):
                    if new_password.strip() == "":
                        st.error("Password string fields cannot be left empty!")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match! Please check your entry values.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET password=? WHERE user_id=?", (new_password.strip(), st.session_state.user_id))
                        conn.commit()
                        st.success("🔒 Security access password modified cleanly!")
            st.markdown("</div>", unsafe_allow_html=True)

    # Global connection cleanup closure safely handled at the end of lifecycle
    conn.close()