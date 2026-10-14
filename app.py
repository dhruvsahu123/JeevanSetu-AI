import os
import shutil
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Writable SQLite setup for Vercel Serverless
if os.environ.get("VERCEL") or os.path.exists("/tmp"):
    DB_PATH = "/tmp/jeevansetu.db"
    src_db = os.path.join(BASE_DIR, "database.db")
    if not os.path.exists(DB_PATH) and os.path.exists(src_db):
        try:
            shutil.copyfile(src_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    # Timeout 20 seconds, WAL mode removed to avoid serverless filesystem crash
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

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

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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

        cursor.execute(
            'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
            (name, email, password, role)
        )
        conn.commit()
        return jsonify({"message": "User registered successfully", "status": "success"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# Login API Route
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        
        user = cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()

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
    finally:
        if conn:
            conn.close()

# Hospital Update API Route (Fixes locality, zone, and all NOT NULL constraints)
# Hospital Update API Route (Auto-fills ALL SQLite NOT NULL columns)
@app.route('/api/hospital/update', methods=['POST'])
@app.route('/api/hospitals/update', methods=['POST'])
@app.route('/api/hospitals', methods=['POST'])
def update_hospital_data():
    data = request.get_json() or {}
    hospital_name = data.get('hospital_name') or data.get('name')
    
    icu_available = data.get('icu_beds') or data.get('available_icu', 0)
    oxygen_available = data.get('oxygen_beds') or data.get('available_oxygen', 0)
    ventilators = data.get('ventilators') or data.get('active_ventilators', 0)
    contact_number = data.get('contact') or data.get('emergency_contact') or data.get('emergency_contact_no', '')
    address = data.get('address') or data.get('location', '') or 'Kanpur'

    if not hospital_name:
        return jsonify({"error": "Hospital name is required"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Table columns and schema info
        cursor.execute("PRAGMA table_info(hospitals);")
        columns_info = cursor.fetchall()
        existing_cols = {col['name']: col for col in columns_info}

        # Form data mapping
        fields_to_update = {}
        if 'name' in existing_cols: fields_to_update['name'] = hospital_name
        if 'icu_beds' in existing_cols: fields_to_update['icu_beds'] = icu_available
        if 'oxygen_beds' in existing_cols: fields_to_update['oxygen_beds'] = oxygen_available
        if 'ventilators' in existing_cols: fields_to_update['ventilators'] = ventilators
        if 'active_ventilators' in existing_cols: fields_to_update['active_ventilators'] = ventilators
        if 'contact' in existing_cols: fields_to_update['contact'] = contact_number
        if 'emergency_contact' in existing_cols: fields_to_update['emergency_contact'] = contact_number
        if 'address' in existing_cols: fields_to_update['address'] = address
        if 'location' in existing_cols: fields_to_update['location'] = address
        if 'locality' in existing_cols: fields_to_update['locality'] = address

        # Universal NOT NULL Failsafe:
        # Table me jitne bhi NOT NULL columns hain jinki value abhi tak assign nahi hui,
        # unhe automatically unke data type ke hisaab se default value de dega.
        for col_name, info in existing_cols.items():
            is_not_null = info['notnull']
            has_no_default = info['dflt_value'] is None
            is_not_primary_key = not info['pk']

            if is_not_null and has_no_default and is_not_primary_key:
                if col_name not in fields_to_update:
                    col_type = (info['type'] or '').upper()
                    if 'INT' in col_type:
                        fields_to_update[col_name] = 1
                    elif 'REAL' in col_type or 'FLOA' in col_type or 'DOUB' in col_type:
                        fields_to_update[col_name] = 0.0
                    else:
                        # For text fields like trauma_tier, zone, city, etc.
                        if 'tier' in col_name:
                            fields_to_update[col_name] = 'Tier-1'
                        elif 'zone' in col_name:
                            fields_to_update[col_name] = 'Central'
                        else:
                            fields_to_update[col_name] = 'Standard'

        # Check existing hospital record
        row = cursor.execute("SELECT id FROM hospitals WHERE name = ?", (hospital_name,)).fetchone()
        
        if row:
            # Update fields excluding primary key / name if needed
            update_data = {k: v for k, v in fields_to_update.items() if k != 'name'}
            set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values()) + [hospital_name]
            cursor.execute(f"UPDATE hospitals SET {set_clause} WHERE name = ?", values)
        else:
            cols_clause = ", ".join(fields_to_update.keys())
            placeholders = ", ".join(["?"] * len(fields_to_update))
            values = list(fields_to_update.values())
            cursor.execute(f"INSERT INTO hospitals ({cols_clause}) VALUES ({placeholders})", values)

        conn.commit()
        return jsonify({"message": f"{hospital_name} data updated successfully!", "status": "success"}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()
# Root Route: Serves index.html
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Universal Dynamic Route Handler for frontend pages, subfolders, CSS and JS
@app.route('/<path:path>')
def serve_files(path):
    direct_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(direct_path) and os.path.isfile(direct_path):
        return send_from_directory(FRONTEND_DIR, path)

    target_filename = os.path.basename(path)
    for root, dirs, files in os.walk(FRONTEND_DIR):
        if target_filename in files:
            return send_from_directory(root, target_filename)

    if not target_filename.endswith('.html'):
        target_html = target_filename + '.html'
        for root, dirs, files in os.walk(FRONTEND_DIR):
            if target_html in files:
                return send_from_directory(root, target_html)

    fallback_404 = os.path.join(FRONTEND_DIR, '404.html')
    if os.path.exists(fallback_404):
        return send_from_directory(FRONTEND_DIR, '404.html'), 404

    abort(404)

if __name__ == '__main__':
    app.run(debug=True, port=5000)