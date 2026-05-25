import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='/')
# Enable CORS for all routes so your frontend can communicate smoothly
CORS(app)

def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    DATABASE_URL = os.environ.get('DATABASE_URL')
    try:
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            return psycopg2.connect(
                dbname="postgres", 
                user="postgres", 
                password="asifa07", 
                host="localhost", 
                port="5432"
            )
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    return app.send_static_file('index.html')

# --- 1. ESSENTIAL SHOP (INVENTORY) ROUTES ---

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    # Using RealDictCursor lets us fetch rows directly as dictionaries
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, part_name, part_code, category, cost_price, available_units, alert_limit 
            FROM inventory 
            ORDER BY id DESC;
        """)
        items = cursor.fetchall()
        # Ensure cost_price is serialized cleanly as a float
        for item in items:
            item['cost_price'] = float(item['cost_price'])
        return jsonify(items), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/inventory', methods=['POST'])
def add_inventory_item():
    data = request.get_json() or {}
    required_fields = ['part_name', 'part_code', 'category', 'cost_price', 'available_units', 'alert_limit']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required data fields"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO inventory (part_name, part_code, category, cost_price, available_units, alert_limit) 
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (data['part_name'], data['part_code'], data['category'], data['cost_price'], data['available_units'], data['alert_limit']))
        conn.commit()
        return jsonify({"message": "Part added successfully"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/inventory/update', methods=['POST', 'PUT'])
def update_inventory_item():
    data = request.get_json() or {}
    if 'part_code' not in data:
        return jsonify({"error": "part_code is required to perform an update"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE inventory 
            SET part_name=%s, category=%s, cost_price=%s, available_units=%s, alert_limit=%s 
            WHERE part_code=%s;
        """, (data.get('part_name'), data.get('category'), data.get('cost_price'), data.get('available_units'), data.get('alert_limit'), data['part_code']))
        conn.commit()
        return jsonify({"message": "Updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/inventory/update-qty', methods=['POST'])
def update_quantity():
    data = request.get_json() or {}
    if 'part_code' not in data or 'change' not in data:
        return jsonify({"error": "part_code and change metrics are required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE inventory 
            SET available_units = GREATEST(0, available_units + %s) 
            WHERE part_code = %s;
        """, (data['change'], data['part_code']))
        conn.commit()
        return jsonify({"message": "Quantity adjusted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/inventory/delete', methods=['POST', 'DELETE'])
def delete_inventory_item():
    data = request.get_json() or {}
    if 'part_code' not in data:
        return jsonify({"error": "part_code is required to delete an item"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM inventory WHERE part_code = %s;", (data['part_code'],))
        conn.commit()
        return jsonify({"message": "Purged successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- 2. SERVICE ANALYTICS ROUTE ---

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_metrics():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SUM(cost_price * available_units) FROM inventory;")
        result = cursor.fetchone()
        val = result[0] if result and result[0] is not None else 0
        return jsonify({"network_financial_value": float(val)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- 3. BOOK APPOINTMENT ROUTES ---

@app.route('/api/bookings', methods=['GET', 'POST'])
def manage_bookings():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            required_fields = ['name', 'plate', 'type', 'date', 'time']
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing required booking details"}), 400

            cursor.execute("""
                INSERT INTO bookings (name, plate, type, date, time) 
                VALUES (%s, %s, %s, %s, %s);
            """, (data['name'], data['plate'], data['type'], data['date'], data['time']))
            conn.commit()
        
        # Always return the updated list of bookings for clean frontend sync
        cursor.execute("SELECT id, name, plate, type, date, time FROM bookings ORDER BY id DESC;")
        rows = cursor.fetchall()
        for r in rows:
            r['date'] = str(r['date'])
            r['time'] = str(r['time'])
            
        return jsonify(rows), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    """Deletes an appointment based directly on its true database ID."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM bookings WHERE id = %s;", (booking_id,))
        conn.commit()
        return jsonify({"message": "Booking canceled successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- EMERGENCY ROUTE ---

@app.route('/api/emergency/sos', methods=['POST'])
def trigger_emergency_dispatch():
    return jsonify({
        "status": "Dispatched",
        "technician": "Vikram Rathore",
        "unit": "Interceptor 4",
        "contact": "+91 98765 43210",
        "distance_km": "5.2 km",
        "eta_minutes": "20 mins"
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
