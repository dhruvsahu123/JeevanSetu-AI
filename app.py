import os
import shutil
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Base path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Vercel Serverless Writable Storage Fix
if os.environ.get("VERCEL") or os.path.exists("/tmp"):
    DB_PATH = "/tmp/jeevansetu.db"
    src_db = os.path.join(BASE_DIR, "database.db")
    if not os.path.exists(DB_PATH) and os.path.exists(src_db):
        shutil.copyfile(src_db, DB_PATH)
else:
    DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Database initialize & schema auto-migrate
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'patient',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Hospitals Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icu_beds INTEGER DEFAULT 0,
            oxygen_beds INTEGER DEFAULT 0,
            ventilators INTEGER DEFAULT 0,
            active_ventilators INTEGER DEFAULT 0,
            emergency_contact TEXT,
            contact TEXT,
            location TEXT,
            address TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Auto-add missing columns to avoid SQLite OperationalErrors
    cols = [
        ("icu_beds", "INTEGER DEFAULT 0"),
        ("oxygen_beds", "INTEGER DEFAULT 0"),
        ("ventilators", "INTEGER DEFAULT 0"),
        ("active_ventilators", "INTEGER DEFAULT 0"),
        ("emergency_contact", "TEXT"),
        ("contact", "TEXT"),
        ("location", "TEXT"),
        ("address", "TEXT")
    ]
    for col_name, col_type in cols:
        try:
            cursor.execute(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_type};")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()

# Start hone par DB setup chalega
init_db()

# Health Check API
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "JeevanSetu-AI"}), 200

# Registration API Route
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'patient')

    if not email or not password or not name:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
            (name, email, password, role)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully", "status": "success"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Login API Route
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()

        if user:
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email'],
                    "role": user['role']
                }
            }), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Hospital Update API Route (Handles both endpoint paths & form keys)
@app.route('/api/hospital/update', methods=['POST'])
@app.route('/api/hospitals/update', methods=['POST'])
@app.route('/api/hospitals', methods=['POST'])
def update_hospital_data():
    data = request.get_json() or {}
    hospital_name = data.get('hospital_name') or data.get('name')
    
    icu_available = data.get('icu_beds') or data.get('available_icu', 0)
    oxygen_available = data.get('oxygen_beds') or data.get('available_oxygen', 0)
    
    # Ventilators handles both naming conventions
    ventilators = data.get('ventilators') or data.get('active_ventilators', 0)
    
    # Contact and Location handles both naming conventions
    contact_number = data.get('contact') or data.get('emergency_contact') or data.get('emergency_contact_no', '')
    address = data.get('address') or data.get('location', '')

    if not hospital_name:
        return jsonify({"error": "Hospital name is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO hospitals (name, icu_beds, oxygen_beds, ventilators, active_ventilators, contact, emergency_contact, location, address, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                icu_beds = excluded.icu_beds,
                oxygen_beds = excluded.oxygen_beds,
                ventilators = excluded.ventilators,
                active_ventilators = excluded.active_ventilators,
                contact = excluded.contact,
                emergency_contact = excluded.emergency_contact,
                location = excluded.location,
                address = excluded.address,
                updated_at = CURRENT_TIMESTAMP
        ''', (hospital_name, icu_available, oxygen_available, ventilators, ventilators, contact_number, contact_number, address, address))

        conn.commit()
        conn.close()
        return jsonify({"message": f"{hospital_name} data updated successfully!", "status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Root Route: Serves index.html
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Universal Dynamic Route Handler for frontend pages, subfolders, CSS and JS
@app.route('/<path:path>')
def serve_files(path):
    # 1. Exact path match in frontend
    direct_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(direct_path) and os.path.isfile(direct_path):
        return send_from_directory(FRONTEND_DIR, path)

    # 2. Match direct filename inside frontend subdirectories
    target_filename = os.path.basename(path)
    for root, dirs, files in os.walk(FRONTEND_DIR):
        if target_filename in files:
            return send_from_directory(root, target_filename)

    # 3. Match filename without .html extension
    if not target_filename.endswith('.html'):
        target_html = target_filename + '.html'
        for root, dirs, files in os.walk(FRONTEND_DIR):
            if target_html in files:
                return send_from_directory(root, target_html)

    # 4. Fallback if 404 page exists
    fallback_404 = os.path.join(FRONTEND_DIR, '404.html')
    if os.path.exists(fallback_404):
        return send_from_directory(FRONTEND_DIR, '404.html'), 404

    abort(404)

if __name__ == '__main__':
    app.run(debug=True, port=5000)