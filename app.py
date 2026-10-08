import sqlite3
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

DB_NAME = "jeevansetu.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# =============================================================
# 1. CORE HEALTH & STATUS ENDPOINTS
# =============================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "JeevanSetu AI Backend",
        "version": "1.0.0"
    }), 200

# =============================================================
# 2. AUTHENTICATION & ACCESS CONTROL
# =============================================================

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.get_json() or {}
    full_name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    role = data.get('role', 'PATIENT')

    if not all([full_name, email, phone, password]):
        return jsonify({"status": "error", "message": "Missing required registration parameters"}), 400

    hashed_pw = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (full_name, email, phone, hashed_pw, role))
        user_id = cursor.lastrowid
        conn.commit()
        return jsonify({
            "status": "success",
            "message": "User registered successfully",
            "user_id": user_id
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Email or Phone already registered"}), 409
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.get_json() or {}
    identifier = data.get('identifier')  # email or phone
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"status": "error", "message": "Missing credentials"}), 400

    conn = get_db_connection()
    user = conn.execute('''
        SELECT * FROM users WHERE email = ? OR phone = ?
    ''', (identifier, identifier)).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"status": "error", "message": "Invalid email/phone or password"}), 401

    return jsonify({
        "status": "success",
        "message": "Authentication successful",
        "user": {
            "id": user['id'],
            "name": user['full_name'],
            "email": user['email'],
            "phone": user['phone'],
            "role": user['role']
        }
    }), 200

# =============================================================
# 3. HOSPITALS & BED MANAGEMENT
# =============================================================

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    conn = get_db_connection()
    cursor = conn.cursor()
    hospitals = cursor.execute('''
        SELECT h.id, h.name, h.locality, h.distance_km, h.trauma_level, h.phone,
               b.icu_available, b.icu_total, b.oxygen_available
        FROM hospitals h
        LEFT JOIN hospital_beds b ON h.id = b.hospital_id
    ''').fetchall()
    conn.close()

    return jsonify({
        "status": "success",
        "hospitals": [dict(h) for h in hospitals]
    }), 200

@app.route('/api/hospitals/<int:hosp_id>/beds', methods=['PATCH'])
def update_hospital_beds(hosp_id):
    data = request.get_json() or {}
    icu_available = data.get('icu_available')
    oxygen_available = data.get('oxygen_available')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if icu_available is not None:
        cursor.execute('UPDATE hospital_beds SET icu_available = ? WHERE hospital_id = ?', (icu_available, hosp_id))
    if oxygen_available is not None:
        cursor.execute('UPDATE hospital_beds SET oxygen_available = ? WHERE hospital_id = ?', (oxygen_available, hosp_id))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Bed availability updated"}), 200

# =============================================================
# 4. EMERGENCY REQUESTS QUEUE
# =============================================================

@app.route('/api/emergency/create', methods=['POST'])
def create_emergency():
    data = request.get_json() or {}
    patient_name = data.get('patient_name', 'Anonymous Citizen')
    symptom = data.get('symptom', 'Critical Condition')
    priority = data.get('priority', 'CRITICAL')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO emergency_requests (patient_name, symptom, priority, status)
        VALUES (?, ?, ?, 'ACTIVE')
    ''', (patient_name, symptom, priority))
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Emergency dispatch request initiated",
        "request_id": request_id
    }), 201

@app.route('/api/emergencies', methods=['GET'])
def get_emergencies():
    conn = get_db_connection()
    emergencies = conn.execute('SELECT * FROM emergency_requests ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify({
        "status": "success",
        "emergencies": [dict(e) for e in emergencies]
    }), 200

# =============================================================
# 5. BLOOD BANK DIRECTORY & MOCK AI TRIAGE
# =============================================================

@app.route('/api/blood-banks', methods=['GET'])
def list_blood_banks():
    blood_banks = [
        {"name": "Hallet Blood Bank & Component Lab", "locality": "Swaroop Nagar", "units_available": {"O+": 14, "B+": 22, "AB+": 6, "A-": 3}, "phone": "+91-512-2534444"},
        {"name": "Rotary Blood Centre", "locality": "Mall Road Kanpur", "units_available": {"O+": 9, "B+": 18, "O-": 2, "A+": 12}, "phone": "+91-512-2300112"},
        {"name": "Regency Transfusion Center", "locality": "Govind Nagar", "units_available": {"O+": 25, "B+": 30, "AB-": 4, "A+": 18}, "phone": "+91-512-2211999"}
    ]
    return jsonify({"status": "success", "blood_banks": blood_banks}), 200

@app.route('/api/ai/triage', methods=['POST'])
def ai_triage_symptom():
    data = request.get_json() or {}
    symptom = (data.get('symptom') or "").lower()
    
    if any(k in symptom for k in ['chest pain', 'heart', 'unconscious', 'severe bleed', 'breath', 'stroke']):
        priority = "TIER_1_CRITICAL"
        recommended_facility = "Apex Emergency & Trauma Institute"
    elif any(k in symptom for k in ['fracture', 'burn', 'high fever', 'vomit', 'abdominal']):
        priority = "TIER_2_URGENT"
        recommended_facility = "Metro Heart & Critical Care Hub"
    else:
        priority = "TIER_3_STABLE"
        recommended_facility = "City Multi-Specialty Health Center"

    return jsonify({
        "status": "success",
        "triage_priority": priority,
        "recommended_facility": recommended_facility
    }), 200

# =============================================================
# 6. PATIENT PROFILE & EMERGENCY TELEMETRY (Phase 21.5)
# =============================================================

@app.route('/api/patient/profile/<int:user_id>', methods=['GET'])
def get_patient_profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user = cursor.execute('SELECT id, full_name, email, phone, role FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"status": "error", "message": "User not found"}), 404
        
    profile = cursor.execute('''
        SELECT blood_group, age, gender, emergency_contact_name, emergency_contact_phone, 
               medical_allergies, chronic_conditions, created_at 
        FROM patients WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    conn.close()
    
    profile_data = {
        "user_id": user["id"],
        "full_name": user["full_name"],
        "email": user["email"],
        "phone": user["phone"],
        "role": user["role"],
        "blood_group": profile["blood_group"] if profile else "",
        "age": profile["age"] if profile else None,
        "gender": profile["gender"] if profile else "",
        "emergency_contact_name": profile["emergency_contact_name"] if profile else "",
        "emergency_contact_phone": profile["emergency_contact_phone"] if profile else "",
        "medical_allergies": profile["medical_allergies"] if profile else "",
        "chronic_conditions": profile["chronic_conditions"] if profile else ""
    }
    
    return jsonify({"status": "success", "profile": profile_data}), 200

@app.route('/api/patient/profile/<int:user_id>', methods=['POST', 'PUT'])
def update_patient_profile(user_id):
    data = request.get_json() or {}
    
    blood_group = data.get('blood_group')
    age = data.get('age')
    gender = data.get('gender')
    emergency_contact_name = data.get('emergency_contact_name')
    emergency_contact_phone = data.get('emergency_contact_phone')
    medical_allergies = data.get('medical_allergies')
    chronic_conditions = data.get('chronic_conditions')

    conn = get_db_connection()
    cursor = conn.cursor()

    user = cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"status": "error", "message": "User not found"}), 404

    existing = cursor.execute('SELECT id FROM patients WHERE user_id = ?', (user_id,)).fetchone()
    if existing:
        cursor.execute('''
            UPDATE patients SET
                blood_group = ?, age = ?, gender = ?,
                emergency_contact_name = ?, emergency_contact_phone = ?,
                medical_allergies = ?, chronic_conditions = ?
            WHERE user_id = ?
        ''', (blood_group, age, gender, emergency_contact_name, emergency_contact_phone, medical_allergies, chronic_conditions, user_id))
    else:
        cursor.execute('''
            INSERT INTO patients (user_id, blood_group, age, gender, emergency_contact_name, emergency_contact_phone, medical_allergies, chronic_conditions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, blood_group, age, gender, emergency_contact_name, emergency_contact_phone, medical_allergies, chronic_conditions))

    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Patient profile updated successfully"}), 200

# =============================================================
# 7. AMBULANCE FLEET & LIVE TELEMETRY (Phase 22)
# =============================================================

@app.route('/api/ambulances', methods=['GET'])
def list_ambulances():
    conn = get_db_connection()
    ambulances = conn.execute('SELECT * FROM ambulances').fetchall()
    conn.close()
    return jsonify({
        "status": "success",
        "ambulances": [dict(amb) for amb in ambulances]
    }), 200

@app.route('/api/ambulances/<int:amb_id>/location', methods=['PATCH'])
def update_ambulance_location(amb_id):
    data = request.get_json() or {}
    lat = data.get('latitude')
    lng = data.get('longitude')
    status = data.get('status', 'AVAILABLE')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE ambulances
        SET current_latitude = ?, current_longitude = ?, operational_status = ?
        WHERE id = ?
    ''', (lat, lng, status, amb_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Location updated"}), 200

# =============================================================
# TRIAGE ENGINE & ATOMIC DISPATCH PIPELINE (Phase 23/27)
# =============================================================

@app.route('/api/dispatch/triage', methods=['POST'])
def triage_and_dispatch():
    data = request.get_json() or {}
    patient_name = data.get('patient_name', 'Emergency Casualty')
    symptom = data.get('symptom', 'Trauma/Unspecified')
    priority = data.get('priority', 'TIER_1_CRITICAL')
    p_lat = float(data.get('latitude', 26.4499))
    p_lng = float(data.get('longitude', 80.3319))
    requires_icu = data.get('requires_icu', True)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Fetch hospitals that have bed availability
        bed_col = 'icu_available' if requires_icu else 'oxygen_available'
        query = f'''
            SELECT h.id, h.name, h.locality, h.phone, h.latitude, h.longitude, b.{bed_col}
            FROM hospitals h
            JOIN hospital_beds b ON h.id = b.hospital_id
            WHERE b.{bed_col} > 0
        '''
        candidate_hospitals = cursor.execute(query).fetchall()

        if not candidate_hospitals:
            conn.close()
            return jsonify({
                "status": "error",
                "message": "No critical care beds available across the emergency corridor"
            }), 409

        # Sort hospitals by dynamic Haversine distance from patient
        sorted_hospitals = sorted(
            candidate_hospitals,
            key=lambda h: haversine_km(p_lat, p_lng, h['latitude'], h['longitude'])
        )
        selected_hosp = sorted_hospitals[0]
        hosp_dist = haversine_km(p_lat, p_lng, selected_hosp['latitude'], selected_hosp['longitude'])

        # 2. Select closest available ambulance
        available_ambs = cursor.execute('''
            SELECT id, vehicle_number, driver_name, driver_phone, current_latitude, current_longitude
            FROM ambulances
            WHERE operational_status = 'AVAILABLE'
        ''').fetchall()

        selected_amb = None
        amb_dist = None
        if available_ambs:
            sorted_ambs = sorted(
                available_ambs,
                key=lambda a: haversine_km(p_lat, p_lng, a['current_latitude'], a['current_longitude'])
            )
            selected_amb = sorted_ambs[0]
            amb_dist = haversine_km(p_lat, p_lng, selected_amb['current_latitude'], selected_amb['current_longitude'])

        # 3. Atomically reserve bed and lock ambulance
        cursor.execute(f'''
            UPDATE hospital_beds
            SET {bed_col} = {bed_col} - 1
            WHERE hospital_id = ?
        ''', (selected_hosp['id'],))

        if selected_amb:
            cursor.execute('''
                UPDATE ambulances
                SET operational_status = 'DISPATCHED'
                WHERE id = ?
            ''', (selected_amb['id'],))

        # 4. Insert Emergency Incident Record
        cursor.execute('''
            INSERT INTO emergency_requests (patient_name, symptom, priority, status)
            VALUES (?, ?, ?, 'ACTIVE')
        ''', (patient_name, symptom, priority))
        emergency_id = cursor.lastrowid

        conn.commit()
        conn.close()

        # Approximate ETA at 40 km/h emergency speed
        amb_eta_mins = max(2, round((amb_dist / 40.0) * 60)) if amb_dist is not None else "Queued"

        return jsonify({
            "status": "success",
            "incident_id": emergency_id,
            "patient_name": patient_name,
            "priority": priority,
            "patient_coordinates": {"latitude": p_lat, "longitude": p_lng},
            "assigned_hospital": {
                "id": selected_hosp['id'],
                "name": selected_hosp['name'],
                "locality": selected_hosp['locality'],
                "contact": selected_hosp['phone'],
                "distance_km": hosp_dist
            },
            "assigned_ambulance": {
                "id": selected_amb['id'] if selected_amb else None,
                "vehicle_number": selected_amb['vehicle_number'] if selected_amb else "Queued",
                "driver": selected_amb['driver_name'] if selected_amb else "Pending Assignment",
                "phone": selected_amb['driver_phone'] if selected_amb else "108",
                "distance_km": amb_dist,
                "eta_minutes": amb_eta_mins
            }
        }), 201

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

# Check and add latitude/longitude to hospitals if missing
cursor.execute("PRAGMA table_info(hospitals);")
cols = [col[1] for col in cursor.fetchall()]

if 'latitude' not in cols:
    cursor.execute("ALTER TABLE hospitals ADD COLUMN latitude REAL DEFAULT 26.4499;")
if 'longitude' not in cols:
    cursor.execute("ALTER TABLE hospitals ADD COLUMN longitude REAL DEFAULT 80.3319;")

# Seed standard coordinates for key Kanpur medical hubs
hosp_coords = [
    (1, 26.4735, 80.3506),  # Apex / GSVM Medical College area
    (2, 26.4350, 80.2980),  # Regency / Govind Nagar corridor
    (3, 26.3785, 80.4421)   # SPM Hospital / Rooma NH-19 corridor
]

for hid, lat, lng in hosp_coords:
    cursor.execute("UPDATE hospitals SET latitude = ?, longitude = ? WHERE id = ?;", (lat, lng, hid))

conn.commit()
print("✓ Hospital coordinates successfully migrated!")
conn.close()
'@ | Set-Content migrate_coords.py; python migrate_coords.py; Remove-Item migrate_coords.py
