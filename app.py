import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Database Connection Helper ---
def get_db_connection():
    # Use environment variable or default local settings
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode='require')
    return psycopg2.connect(
        dbname="postgres", 
        user="postgres", 
        password="asifa07", 
        host="localhost", 
        port="5432"
    )

# --- App Configuration ---
st.set_page_config(page_title="MotoFix Pro-Hub", layout="wide")
st.title("🔧 MotoFix Pro-Hub: Advanced Garage Management")

# Initialize Session State for tabs
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Stock Ledger"

# Sidebar Navigation
nav = st.sidebar.radio("Navigation", ["Stock Ledger", "Service Analytics", "Bookings", "Emergency SOS"])

# --- TAB 1: Stock Ledger ---
if nav == "Stock Ledger":
    st.header("📦 Inventory Management")
    conn = get_db_connection()
    cur = conn.cursor()

    # Metrics Row
    cur.execute("SELECT SUM(cost_price * available_units) FROM inventory;")
    valuation = cur.fetchone()[0] or 0
    
    col1, col2 = st.columns(2)
    col1.metric("On-Shelf Valuation", f"₹{valuation:,.2f}")
    
    # Add New Item
    with st.expander("📥 Log New Spares Cargo"):
        with st.form("add_part"):
            name = st.text_input("Part Name")
            code = st.text_input("Part Code")
            cat = st.text_input("Category")
            price = st.number_input("Cost Price (₹)", min_value=0.0)
            qty = st.number_input("Quantity", min_value=0)
            if st.form_submit_button("Add To Shelf"):
                cur.execute("INSERT INTO inventory (part_name, part_code, category, cost_price, available_units) VALUES (%s, %s, %s, %s, %s);", 
                            (name, code, cat, price, qty))
                conn.commit()
                st.rerun()

    # Display Inventory Table
    cur.execute("SELECT part_name, part_code, category, cost_price, available_units FROM inventory;")
    items = cur.fetchall()
    
    for item in items:
        cols = st.columns([3, 1, 1, 1, 1])
        cols[0].write(f"**{item[0]}** ({item[1]})")
        cols[1].write(item[2])
        cols[2].write(f"₹{item[3]}")
        cols[3].write(f"{item[4]} units")
        if cols[4].button("Delete", key=f"del_{item[1]}"):
            cur.execute("DELETE FROM inventory WHERE part_code = %s;", (item[1],))
            conn.commit()
            st.rerun()
    cur.close()
    conn.close()

# --- TAB 2: Analytics ---
elif nav == "Service Analytics":
    st.header("📊 Vehicle Diagnostic Overhaul")
    pre = st.number_input("Baseline Factory Output (BHP)", value=120)
    post = st.number_input("Post-Tune Target (BHP)", value=175)
    
    if st.button("Run Evaluation Logic"):
        gain = ((post - pre) / pre) * 100
        st.success(f"Evaluation Matrix Complete: Tuning map gained +{gain:.1f}%!")
        st.bar_chart({"Baseline": pre, "Post-Tune": post})

# --- TAB 3: Bookings ---
elif nav == "Bookings":
    st.header("📅 Advanced Booking Block")
    conn = get_db_connection()
    cur = conn.cursor()
    
    with st.form("booking_form"):
        name = st.text_input("Owner Name")
        plate = st.text_input("License Plate")
        service = st.selectbox("Service Type", ["Full Engine Tuning", "Brake Calibration", "Electrical Rewire"])
        date = st.date_input("Date")
        if st.form_submit_button("Confirm Appointment"):
            cur.execute("INSERT INTO bookings (name, plate, service_type, booking_date) VALUES (%s, %s, %s, %s);", (name, plate, service, date))
            conn.commit()
            st.rerun()
    
    st.subheader("Current Appointments")
    cur.execute("SELECT name, plate, service_type, booking_date FROM bookings;")
    for row in cur.fetchall():
        st.write(f"**{row[0]}** | {row[1]} | {row[2]} | {row[3]}")
    cur.close()
    conn.close()

# --- TAB 4: Emergency ---
elif nav == "Emergency SOS":
    st.header("🚨 Roadside Assistance")
    if st.button("TRIGGER EMERGENCY DISPATCH"):
        st.error("DISPATCHED: Technician Vikram Rathore. ETA: 20 mins.")
