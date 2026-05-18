import datetime
import hashlib
import os
import secrets
import sqlite3

import streamlit as st

SALT = b"f9d2a3d7b5f1e6bc"
PASSWORD_HASH = "e58f90b3c2d2c1dd2ed8e22cecfc3f570c28f70f72a02add6b41bade777e13bb"
USERNAME = "vikalpsingh"
DB_FILE = os.path.join(os.path.dirname(__file__), "customer_data.db")


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a fixed salt."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), SALT, 200_000).hex()


def verify_password(password: str) -> bool:
    """Compare the entered password to the stored password hash."""
    return secrets.compare_digest(hash_password(password), PASSWORD_HASH)


@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    conn.commit()
    return conn


def add_customer(name: str) -> None:
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO customers (name, created_at) VALUES (?, ?)",
        (name.strip(), datetime.datetime.utcnow().isoformat()),
    )
    conn.commit()


def get_customers():
    conn = get_db_connection()
    cursor = conn.execute("SELECT id, name, created_at FROM customers ORDER BY id DESC")
    return cursor.fetchall()


def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""


def main() -> None:
    st.set_page_config(page_title="Customer Info App", page_icon="🧾", layout="centered")
    st.title("Customer Information Manager")
    st.write("Secure customer capture and display with lightweight storage.")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = ""

    if not st.session_state.authenticated:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Log in")

            if login_button:
                if username == USERNAME and verify_password(password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.info("Use your registered username and password to access the customer manager.")
        return

    st.sidebar.markdown(f"**Logged in as:** {st.session_state.username}")
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()

    tabs = st.tabs(["Add customer name", "Display customer name"])

    with tabs[0]:
        st.subheader("Add a new customer")
        customer_name = st.text_input("Customer name")
        if st.button("Save customer"):
            if not customer_name.strip():
                st.warning("Enter a customer name before saving.")
            else:
                add_customer(customer_name)
                st.success(f"Customer '{customer_name.strip()}' saved.")

    with tabs[1]:
        st.subheader("Customer list")
        customers = get_customers()
        if customers:
            st.write("Saved customer names:")
            st.table(
                [{"ID": row["id"], "Name": row["name"], "Added UTC": row["created_at"]} for row in customers]
            )
        else:
            st.info("No customers have been added yet.")


if __name__ == "__main__":
    main()
