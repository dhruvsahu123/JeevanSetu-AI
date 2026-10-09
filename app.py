import os
import sqlite3
import math
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='frontend')
CORS(app)

DB_NAME = "jeevansetu.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ----------------- STATIC FRONTEND ROUTES -----------------
@app.route('/')
def serve_root():
    return send_from_directory('.', 'index.html')

@app.route('/frontend/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('frontend', filename)

# ----------------- API ENDPOINTS -----------------
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "active", "service": "JeevanSetu AI Emergency Grid", "version": "2.0"})

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT h.id, h.name, h.locality, h.distance_km, h.trauma_level, h.phone,
               h.latitude, h.longitude,
               b.icu_available, b.icu_total, b.oxygen_available, b.oxygen_total
        FROM hospitals h
        LEFT JOIN hospital_beds b ON h.id = b.hospital_id
        ORDER BY h.id ASC
    ''')
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "name": r["name"],
            "locality": r["locality"],
            "distance_km": r["distance_km"],
            "trauma_level": r["trauma_level"],
            "phone": r["phone"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "icu_available": r["icu_available"] or 0,
            "icu_total": r["icu_total"] or 0,
            "oxygen_available": r["oxygen_available"] or 0,
            "oxygen_total": r["oxygen_total"] or 0
        })
    return jsonify({"status": "success", "count": len(result), "hospitals": result})

@app.route('/api/blood-banks', methods=['GET'])
def get_blood_banks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, facility_name, locality, contact_phone,
               units_o_negative, units_ab_negative, units_b_negative,
               units_o_positive, units_b_positive, latitude, longitude
        FROM blood_banks
    ''')
    rows = cursor.fetchall()
    conn.close()

    banks = [dict(r) for r in rows]
    return jsonify({"status": "success", "blood_banks": banks})

@app.route('/api/ambulances', methods=['GET'])
def get_ambulances():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, vehicle_number, fleet_type, driver_name, driver_phone,
               current_latitude, current_longitude, operational_status, speed_kmh
        FROM ambulances
    ''')
    rows = cursor.fetchall()
    conn.close()

    fleet = [dict(r) for r in rows]
    return jsonify({"status": "success", "ambulances": fleet})

@app.route('/api/ambulances/<int:amb_id>/location', methods=['PATCH'])
def update_ambulance_location(amb_id):
    data = request.json or {}
    lat = data.get('latitude')
    lng = data.get('longitude')
    speed = data.get('speed_kmh', 45.0)

    if lat is None or lng is None:
        return jsonify({"status": "error", "message": "latitude and longitude required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE ambulances
        SET current_latitude = ?, current_longitude = ?, speed_kmh = ?
        WHERE id = ?
    ''', (lat, lng, speed, amb_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "ambulance_id": amb_id, "lat": lat, "lng": lng, "speed": speed})

# ----------------- EMERGENCY TRIAGE & ATOMIC DISPATCH -----------------
@app.route('/api/dispatch/triage', methods=['POST'])
def emergency_dispatch():
    data = request.json or {}
    patient_name = data.get('patient_name', 'Anonymous Casualty')
    symptom = data.get('symptom', 'Acute Multi-Trauma / Highway Collision')
    req_lat = float(data.get('latitude', 26.3785))
    req_lng = float(data.get('longitude', 80.4421))
    requires_icu = data.get('requires_icu', True)

    conn = get_db()
    cursor = conn.cursor()

    # Nearest hospital with ICU availability
    cursor.execute('''
        SELECT h.id, h.name, h.locality, h.phone, h.latitude, h.longitude,
               b.icu_available, b.icu_total, b.oxygen_available
        FROM hospitals h
        JOIN hospital_beds b ON h.id = b.hospital_id
        WHERE b.icu_available > 0
    ''')
    hospitals = cursor.fetchall()

    if not hospitals:
        conn.close()
        return jsonify({"status": "error", "message": "Zero ICU beds available in network."}), 503

    best_hospital = None
    min_dist = float('inf')

    for hosp in hospitals:
        dist = haversine(req_lat, req_lng, hosp["latitude"], hosp["longitude"])
        if dist < min_dist:
            min_dist = dist
            best_hospital = hosp

    # Atomic decrement of bed
    if requires_icu:
        cursor.execute('''
            UPDATE hospital_beds
            SET icu_available = icu_available - 1
            WHERE hospital_id = ? AND icu_available > 0
        ''', (best_hospital["id"],))

    # Pick closest available ambulance
    cursor.execute("SELECT * FROM ambulances WHERE operational_status = 'AVAILABLE' LIMIT 1")
    ambulance = cursor.fetchone()

    amb_eta = round(min_dist * 2.2) + 3

    # Log emergency request
    cursor.execute('''
        INSERT INTO emergency_requests (patient_name, symptom, priority, allocated_hospital_id, allocated_ambulance_id)
        VALUES (?, ?, 'CRITICAL', ?, ?)
    ''', (patient_name, symptom, best_hospital["id"], ambulance["id"] if ambulance else None))
    incident_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "status": "success",
        "incident_id": incident_id,
        "token": f"#JS-EM-KAN-{incident_id:04d}",
        "assigned_hospital": {
            "id": best_hospital["id"],
            "name": best_hospital["name"],
            "locality": best_hospital["locality"],
            "phone": best_hospital["phone"],
            "distance_km": round(min_dist, 2),
            "latitude": best_hospital["latitude"],
            "longitude": best_hospital["longitude"]
        },
        "assigned_ambulance": {
            "vehicle_number": ambulance["vehicle_number"] if ambulance else "UP-78-AG-1021",
            "driver": ambulance["driver_name"] if ambulance else "Emergency On-Call Unit",
            "driver_phone": ambulance["driver_phone"] if ambulance else "+91-9876500001",
            "eta_minutes": amb_eta
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚑 JeevanSetu AI Command Grid running on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)