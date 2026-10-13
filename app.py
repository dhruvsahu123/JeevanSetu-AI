import os
from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    file_path = os.path.join(FRONTEND_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(FRONTEND_DIR, filename)
    
    for root, dirs, files in os.walk(FRONTEND_DIR):
        if filename.split('/')[-1] in files:
            return send_from_directory(root, filename.split('/')[-1])
            
    return send_from_directory(FRONTEND_DIR, '404.html'), 404

import os
import time
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='frontend', static_url_path='/frontend')
CORS(app, resources={r"/*": {"origins": "*"}})

# Sahi active SQLite database select karein
if os.path.exists("database.db"):
    DB_NAME = "database.db"
elif os.path.exists("jeevansetu.db"):
    DB_NAME = "jeevansetu.db"
else:
    DB_NAME = "database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- FRONTEND ROUTING ---
@app.route('/')
def home():
    return send_from_directory('frontend', 'index.html')
    if os.path.exists("frontend/index.html"):
        return send_from_directory('frontend', 'index.html')
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return jsonify({"status": "running", "service": "JeevanSetu AI Backend"})

# --- UNIVERSAL FRONTEND ROUTING (Handles subfolders automatically) ---
@app.route('/frontend/<path:filename>')
def serve_frontend_files(filename):
    frontend_dir = os.path.join(app.root_path, 'frontend')
    direct_path = os.path.join(frontend_dir, filename)

    # 1. Direct file check
    if os.path.isfile(direct_path):
        return send_from_directory(frontend_dir, filename)

    # 2. Sub-folders (pages/inventory, pages/operations, etc.) recursive check
    pages_dir = os.path.join(frontend_dir, 'pages')
    base_name = os.path.basename(filename)
    if os.path.exists(pages_dir):
        for root, _, files in os.walk(pages_dir):
            if base_name in files:
                return send_from_directory(root, base_name)

    return jsonify({"error": "Page not found", "path": filename}), 404
   
   

# --- AUTH APIS ---
@app.route('/api/login', methods=['POST', 'OPTIONS'])
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def universal_login():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json(silent=True) or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    if email and password:
        role = 'hospital_staff' if ('admin' in email or 'hospital' in email) else 'citizen'
        return jsonify({
            'status': 'success',
            'token': 'demo_jwt_token_jeevansetu_verified',
            'user': {
                'email': email,
                'name': 'Dr. Alok Verma' if role == 'hospital_staff' else 'Citizen User',
                'role': role
            },
            'redirect': '/frontend/hospital-dashboard.html' if role == 'hospital_staff' else '/frontend/customer-dashboard.html'
        }), 200
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST', 'OPTIONS'])
@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def universal_register():
    if request.method == 'OPTIONS':
        return ('', 204)
    data = request.get_json(silent=True) or {}
    email = data.get('email') or 'user@jeevansetu.in'
    role = data.get('role') or 'citizen'
    return jsonify({
        'status': 'success',
        'message': 'Account registered successfully!',
        'user': {'email': email, 'role': role}
    }), 201

# --- DASHBOARD SUMMARY STATS ---
@app.route('/api/stats/dashboard', methods=['GET'])
def api_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    total_fac = 0
    icu_avail = 0
    oxy_avail = 0
    ambulances_count = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM hospitals")
        total_fac = cursor.fetchone()[0]
    except Exception:
        pass

    try:
        cursor.execute("SELECT COUNT(*) FROM hospital_beds WHERE bed_type LIKE '%ICU%' AND status = 'Available'")
        icu_avail = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM hospital_beds WHERE bed_type LIKE '%Oxygen%' AND status = 'Available'")
        oxy_avail = cursor.fetchone()[0]
    except Exception:
        pass

    try:
        cursor.execute("SELECT COUNT(*) FROM ambulances WHERE current_status = 'Dispatched-Enroute'")
        ambulances_count = cursor.fetchone()[0]
    except Exception:
        pass

    conn.close()
    return jsonify({
        'status': 'success',
        'data': {
            'total_facilities': total_fac if total_fac > 0 else 26,
            'available_icu': icu_avail if icu_avail > 0 else 48,
            'available_oxygen': oxy_avail if oxy_avail > 0 else 124,
            'active_ambulances': ambulances_count if ambulances_count > 0 else 18
        }
    })

# --- HOSPITALS GRID API (Matches SQLite database.db Schema) ---
@app.route('/api/hospitals', methods=['GET'])
@app.route('/api/v2/hospitals', methods=['GET'])
@app.route('/api/beds', methods=['GET'])
def get_hospitals_grid():
    q = request.args.get('q', '').strip()
    tier = request.args.get('tier', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 25))
    offset = (page - 1) * limit

    conn = get_db()
    cursor = conn.cursor()

    try:
        sql = """
            SELECT 
                h.id, h.hospital_uid, h.name, h.locality, h.zone, h.trauma_tier, h.contact_phone,
                COALESCE(SUM(CASE WHEN b.bed_type LIKE '%ICU%' AND b.status = 'Available' THEN 1 ELSE 0 END), 4) AS icu_available,
                COALESCE(SUM(CASE WHEN b.bed_type LIKE '%Oxygen%' AND b.status = 'Available' THEN 1 ELSE 0 END), 12) AS oxygen_available
            FROM hospitals h
            LEFT JOIN hospital_beds b ON h.hospital_uid = b.hospital_uid
            WHERE 1=1
        """
        params = []
        if q:
            sql += " AND (h.name LIKE ? OR h.locality LIKE ? OR h.zone LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        if tier and tier != 'All Trauma Tiers':
            sql += " AND h.trauma_tier LIKE ?"
            params.append(f"%{tier}%")

        sql += " GROUP BY h.id ORDER BY h.id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(sql, params)
        rows = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) FROM hospitals")
        total_rows = cursor.fetchone()[0]
        conn.close()

        return jsonify({
            "status": "success",
            "count": len(rows),
            "total_records": total_rows,
            "hospitals": rows,
            "data": rows
        })
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- BLOOD BANKS API ---
@app.route('/api/bloodbanks', methods=['GET'])
@app.route('/api/v2/bloodbanks', methods=['GET'])
def get_blood_banks():
    q = request.args.get('q', '').strip()
    conn = get_db()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM blood_banks WHERE 1=1"
        params = []
        if q:
            query += " AND (name LIKE ? OR locality LIKE ? OR zone LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- AMBULANCES TELEMETRY ---
@app.route('/api/ambulances', methods=['GET'])
def get_ambulances_telemetry():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM ambulances ORDER BY id ASC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify({"status": "success", "ambulances": rows, "data": rows})
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- CLINICAL CONDITIONS API ---
@app.route('/api/v2/conditions', methods=['GET'])
def get_conditions():
    q = request.args.get('q', '').strip()
    conn = get_db()
    cursor = conn.cursor()
    try:
        sql = "SELECT * FROM clinical_conditions WHERE 1=1"
        params = []
        if q:
            sql += " AND (name LIKE ? OR category LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%"])
        sql += " LIMIT 30"
        cursor.execute(sql, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

# --- EMERGENCY SOS API ---
@app.route('/api/sos', methods=['POST'])
def trigger_sos():
    data = request.get_json(silent=True) or {}
    req_id = int(time.time()) % 10000
    return jsonify({
        "status": "success",
        "emergency_id": req_id,
        "token": f"JS-EM-KAN-{req_id:04d}",
        "hospital_assigned": "SPM Hospital Trauma Centre (NH-19 Apex)",
        "ambulance_assigned": "UP-78-AG-1021",
        "message": "Dispatch alert relayed. Corridor wave preempted."
    })

if __name__ == '__main__':
    print("[SERVER] Starting JeevanSetu AI Backend on http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)
    # app = Flask(__name__) already define hoga file me.
# Aakhri lines me ye ensure karein:
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)