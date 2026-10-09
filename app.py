from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__, static_folder='frontend', static_url_path='/frontend')
CORS(app)

DB_NAME = "jeevansetu.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- STATIC & ROUTING ---
@app.route('/')
def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return send_from_directory('frontend', 'index.html')

# --- HOSPITALS API ---
@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, h.name, h.locality, h.distance_km, h.trauma_level, h.phone,
               h.latitude, h.longitude,
               b.icu_available, b.icu_total, b.oxygen_available, b.oxygen_total
        FROM hospitals h
        LEFT JOIN hospital_beds b ON h.id = b.hospital_id
        ORDER BY h.distance_km ASC
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"status": "success", "count": len(rows), "hospitals": rows})

# --- AMBULANCES TELEMETRY API ---
@app.route('/api/ambulances', methods=['GET'])
def get_ambulances():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ambulances ORDER BY id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"status": "success", "ambulances": rows})

# --- BLOOD BANKS API ---
@app.route('/api/blood_banks', methods=['GET'])
def get_blood_banks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blood_banks ORDER BY id ASC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({"status": "success", "blood_banks": rows})

# --- EMERGENCY SOS TRIGGER API ---
@app.route('/api/sos', methods=['POST'])
def trigger_sos():
    data = request.get_json() or {}
    patient_name = data.get('patient_name', 'Anonymous Citizen')
    symptom = data.get('symptom', 'Critical Emergency')
    priority = data.get('priority', 'CRITICAL')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO emergency_requests (patient_name, symptom, priority, allocated_hospital_id, allocated_ambulance_id)
        VALUES (?, ?, ?, 1, 1)
    """, (patient_name, symptom, priority))
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "emergency_id": req_id,
        "token": f"JS-EM-KAN-{req_id:04d}",
        "hospital_assigned": "SPM Hospital Research & Trauma Centre",
        "ambulance_assigned": "UP-78-AG-1021",
        "message": "Emergency pass generated. Dispatch unit alerted."
    })

# --- CLINICAL KNOWLEDGE SEARCH (ICD-10 DISEASES) ---
@app.route('/api/search/diseases', methods=['GET'])
def search_diseases():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    severity = request.args.get('severity', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    sql = "SELECT * FROM diseases WHERE 1=1"
    params = []

    if query:
        sql += " AND (disease_name LIKE ? OR symptoms_keywords LIKE ? OR icd_code LIKE ?)"
        wildcard = f"%{query}%"
        params.extend([wildcard, wildcard, wildcard])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if severity:
        sql += " AND severity_level = ?"
        params.append(severity)

    sql += " ORDER BY CASE severity_level WHEN 'CRITICAL' THEN 1 WHEN 'MODERATE' THEN 2 ELSE 3 END LIMIT 50"

    cursor.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"status": "success", "count": len(rows), "results": rows})

# --- MEDICINES & FORMULATIONS SEARCH ---
@app.route('/api/search/medicines', methods=['GET'])
def search_medicines():
    query = request.args.get('q', '').strip()
    conn = get_db()
    cursor = conn.cursor()

    if query:
        wildcard = f"%{query}%"
        cursor.execute("""
            SELECT * FROM medicines 
            WHERE generic_name LIKE ? OR brand_name LIKE ? OR primary_indications LIKE ?
            LIMIT 50
        """, (wildcard, wildcard, wildcard))
    else:
        cursor.execute("SELECT * FROM medicines LIMIT 30")

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify({"status": "success", "count": len(rows), "results": rows})


# --- HOSPITAL ER STAFF & ADMIN AUTHENTICATION API ---
@app.route('/api/auth/login', methods=['POST'])
def staff_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()

    # Default authorized triage desk credentials for testing
    if email == 'admin@jeevansetu.in' and password == 'kanpur123':
        return jsonify({
            'status': 'success',
            'token': 'JS-AUTH-JWT-DEMO-KAN-2026',
            'user': {
                'name': 'Dr. Alok Verma',
                'role': 'ER Triage In-Charge',
                'hospital': 'SPM Hospital Research & Trauma Centre'
            }
        })

    return jsonify({'status': 'error', 'message': 'Invalid medical ID or password'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
