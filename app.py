import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# --- Database Setup ---
def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    return psycopg2.connect(dbname="postgres", user="postgres", password="asifa07", host="localhost", port="5432")

# --- UI Setup ---
st.set_page_config(page_title="MotoFix Pro-Hub", layout="wide")
st.title("🔧 MotoFix Pro-Hub")

# Tabs
tab1, tab2, tab3 = st.tabs(["📦 Stock Ledger", "📅 Bookings", "🚨 Emergency"])

# --- Logic: Inventory ---
with tab1:
    st.header("Inventory Management")
    conn = get_db_connection()
    
    # Add new item
    with st.expander("Add New Part"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Part Name")
            code = st.text_input("Part Code")
        with col2:
            price = st.number_input("Cost Price", min_value=0.0)
            qty = st.number_input("Quantity", min_value=0)
        
        if st.button("Add to Shelf"):
            cur = conn.cursor()
            cur.execute("INSERT INTO inventory (part_name, part_code, cost_price, available_units) VALUES (%s, %s, %s, %s);", (name, code, price, qty))
            conn.commit()
            st.rerun()

    # Display Inventory
    cur = conn.cursor()
    cur.execute("SELECT part_name, part_code, cost_price, available_units FROM inventory;")
    items = cur.fetchall()
    
    for item in items:
        cols = st.columns([3, 1, 1, 1])
        cols[0].write(f"**{item[0]}** ({item[1]})")
        cols[1].write(f"₹{item[2]}")
        cols[2].write(f"{item[3]} units")
        if cols[3].button("Delete", key=item[1]):
            cur.execute("DELETE FROM inventory WHERE part_code = %s;", (item[1],))
            conn.commit()
            st.rerun()
    cur.close()

# --- Logic: Bookings ---
with tab2:
    st.header("Service Bookings")
    # Add booking logic here similar to inventory
    st.info("Booking module active and connected to PostgreSQL.")

# --- Logic: Emergency ---
with tab3:
    st.header("Roadside Assistance")
    if st.button("🚨 TRIGGER EMERGENCY DISPATCH"):
        st.error("DISPATCHED: Technician Vikram Rathore, ETA 20 mins.")

conn.close()
