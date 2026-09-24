import streamlit as st
import pandas as pd
import os
import csv
from datetime import datetime

# --- CONFIGURATION ---
USERS_FILE = "users.csv"
ATTENDANCE_FILE = "attendance.csv"
ADMIN_PASSWORD = "admin123"  # Change this to your preferred admin password

# --- INITIAL SETUP ---
def init_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Password", "Name", "Emp_ID", "Role"]) # Role = 'admin' or 'employee'
            # Create default admin account (optional, or just use hardcoded check)
            writer.writerow(["admin@company.com", ADMIN_PASSWORD, "System Admin", "ADM001", "admin"])

    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Emp_ID", "Name", "Date", "Check_in", "Check_out"])

# --- HELPER FUNCTIONS ---
def get_next_emp_id():
    """Generates a new ID (e.g., EMP101, EMP102) automatically."""
    if not os.path.exists(USERS_FILE):
        return "EMP100"
    
    df = pd.read_csv(USERS_FILE)
    # Filter only employees (exclude admins)
    employees = df[df['Role'] == 'employee']
    
    if employees.empty:
        return "EMP100"
    
    # Get last ID, strip 'EMP', convert to int, add 1
    last_id = employees['Emp_ID'].iloc[-1]
    try:
        num = int(last_id.replace("EMP", ""))
        return f"EMP{num + 1}"
    except:
        return "EMP100" # Fallback

def verify_login(identifier, password, role_type):
    """Verifies email OR Emp_ID matches password."""
    if not os.path.exists(USERS_FILE):
        return None

    df = pd.read_csv(USERS_FILE)
    
    # Check if identifier matches Email OR Emp_ID
    # AND Password matches
    # AND Role matches
    user = df[
        ((df['Email'] == identifier) | (df['Emp_ID'] == identifier)) & 
        (df['Password'] == password) & 
        (df['Role'] == role_type)
    ]
    
    if not user.empty:
        return user.iloc[0] # Return the user data row
    return None

def register_employee(email, password, name):
    """Saves new employee to CSV."""
    # Check if email already exists
    df = pd.read_csv(USERS_FILE)
    if email in df['Email'].values:
        return None, "Email already registered!"

    new_id = get_next_emp_id()
    
    with open(USERS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([email, password, name, new_id, "employee"])
    
    return new_id, "Success"

def mark_attendance(emp_id, name, action):
    today = datetime.now().strftime("%d-%m-%Y")
    now = datetime.now().strftime("%H:%M:%S")
    
    if action == "Check In":
        # Check duplicate
        with open(ATTENDANCE_FILE, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == emp_id and row[2] == today:
                    return False, "Already checked in today."
        
        with open(ATTENDANCE_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([emp_id, name, today, now, ""])
        return True, f"Checked in at {now}"

    elif action == "Check Out":
        rows = []
        found = False
        with open(ATTENDANCE_FILE, "r") as f:
            rows = list(csv.reader(f))
        
        for row in rows:
            if row and row[0] == emp_id and row[2] == today and row[4] == "":
                row[4] = now
                found = True
                break
        
        if found:
            with open(ATTENDANCE_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            return True, f"Checked out at {now}"
        return False, "No active check-in found."

# --- MAIN APP UI ---
st.set_page_config(page_title="Attendance Portal", page_icon="🏢")
init_files()

# Session State Management
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.session_state['role'] = None

# Logout Function
def logout():
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.rerun()

# --- 1. LOGIN / REGISTER SCREEN ---
if not st.session_state['logged_in']:
    st.title("🏢 Corporate Attendance System")
    
    tab1, tab2, tab3 = st.tabs(["Employee Login", "New Employee Registration", "Admin Login"])
    
    # --- Employee Login ---
    with tab1:
        st.subheader("Welcome Back")
        email_or_id = st.text_input("Email or Employee ID")
        password = st.text_input("Password", type="password")
        if st.button("Login", key="emp_login"):
            user = verify_login(email_or_id, password, "employee")
            if user is not None:
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = user
                st.session_state['role'] = "employee"
                st.rerun()
            else:
                st.error("Invalid credentials")

    # --- Employee Registration ---
    with tab2:
        st.subheader("First Time User?")
        new_name = st.text_input("Full Name")
        new_email = st.text_input("Email Address")
        new_pass = st.text_input("Create Password", type="password")
        
        if st.button("Register"):
            if new_name and new_email and new_pass:
                emp_id, msg = register_employee(new_email, new_pass, new_name)
                if emp_id:
                    st.success(f"✅ Account Created! Your Employee ID is **{emp_id}**.")
                    st.info("Please memorize this ID. You can use it to login.")
                else:
                    st.error(msg)
            else:
                st.warning("Please fill all fields.")

    # --- Admin Login ---
    with tab3:
        st.subheader("Admin Access")
        admin_user = st.text_input("Admin Username")
        admin_pass = st.text_input("Admin Password", type="password")
        if st.button("Admin Login"):
            # Simple check against CSV admin or hardcoded
            user = verify_login(admin_user, admin_pass, "admin")
            if user is not None:
                st.session_state['logged_in'] = True
                st.session_state['user_info'] = user
                st.session_state['role'] = "admin"
                st.rerun()
            else:
                st.error("Access Denied")

# --- 2. LOGGED IN DASHBOARD ---
else:
    user = st.session_state['user_info']
    role = st.session_state['role']

    # sidebar
    st.sidebar.write(f"Logged in as: **{user['Name']}**")
    if st.sidebar.button("Logout"):
        logout()

    # === EMPLOYEE VIEW ===
    if role == "employee":
        st.title(f"👋 Hello, {user['Name']}")
        st.write(f"Employee ID: **{user['Emp_ID']}**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check In 🟢", use_container_width=True):
                success, msg = mark_attendance(user['Emp_ID'], user['Name'], "Check In")
                if success: st.success(msg)
                else: st.warning(msg)
        
        with col2:
            if st.button("Check Out 🔴", use_container_width=True):
                success, msg = mark_attendance(user['Emp_ID'], user['Name'], "Check Out")
                if success: st.success(msg)
                else: st.warning(msg)

        st.divider()
        st.subheader("Your Attendance History")
        if os.path.exists(ATTENDANCE_FILE):
            df = pd.read_csv(ATTENDANCE_FILE)
            # Filter only this employee's data
            my_data = df[df['Emp_ID'] == user['Emp_ID']]
            st.dataframe(my_data, use_container_width=True)

    # === ADMIN VIEW ===
    elif role == "admin":
        st.title("🛠️ Admin Dashboard")
        st.metric("Total Employees", len(pd.read_csv(USERS_FILE)) - 1) # subtract header
        
        tab_view, tab_users = st.tabs(["Attendance Logs", "User Management"])
        
        with tab_view:
            st.subheader("All Attendance Records")
            if os.path.exists(ATTENDANCE_FILE):
                df = pd.read_csv(ATTENDANCE_FILE)
                st.dataframe(df, use_container_width=True)
                
                # Download Button
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Report", csv_data, "attendance.csv", "text/csv")
        
        with tab_users:
            st.subheader("Registered Employees")
            users_df = pd.read_csv(USERS_FILE)
            st.dataframe(users_df)