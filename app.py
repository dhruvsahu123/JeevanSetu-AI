import os
import time
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from flask import Flask, render_template, request, jsonify, send_from_directory

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


# --- PWA STATIC ASSETS ROUTING ---
@app.route('/sw.js')
def serve_sw():
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('.', 'manifest.json', mimetype='application/json')


# --- BLOOD BANK INTELLIGENCE & COMPATIBILITY MATRIX ---
BLOOD_COMPATIBILITY = {
    'O-': ['O-'],
    'O+': ['O-', 'O+'],
    'A-': ['O-', 'A-'],
    'A+': ['O-', 'O+', 'A-', 'A+'],
    'B-': ['O-', 'B-'],
    'B+': ['O-', 'O+', 'B-', 'B+'],
    'AB-': ['O-', 'A-', 'B-', 'AB-'],
    'AB+': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
    'BOMBAY_HH': ['BOMBAY_HH']
}

@app.route('/api/blood/match', methods=['POST'])
def match_blood():
    data = request.get_json() or {}
    patient_group = data.get('blood_group', 'O-').strip().upper()
    component = data.get('component', 'PRBC').strip().upper()
    units_needed = int(data.get('units_needed', 2))

    compatible_groups = BLOOD_COMPATIBILITY.get(patient_group, [patient_group])

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM blood_banks ORDER BY id ASC')
    blood_banks = [dict(r) for r in cursor.fetchall()]
    conn.close()

    matches = []
    total_compatible_units = 0

    for b in blood_banks:
        avail_breakdown = {
            'O-': b.get('units_o_negative', 0),
            'AB-': b.get('units_ab_negative', 0),
            'B-': b.get('units_b_negative', 0),
            'O+': b.get('units_o_positive', 0),
            'B+': b.get('units_b_positive', 0)
        }
        
        bank_compatible_units = sum(avail_breakdown.get(grp, 0) for grp in compatible_groups)
        total_compatible_units += bank_compatible_units

        matches.append({
            'facility_id': b['id'],
            'facility_name': b['facility_name'],
            'locality': b['locality'],
            'phone': b['contact_phone'],
            'compatible_units_available': bank_compatible_units,
            'breakdown': {grp: avail_breakdown.get(grp, 0) for grp in compatible_groups if grp in avail_breakdown}
        })

    matches.sort(key=lambda x: x['compatible_units_available'], reverse=True)

    is_rare = patient_group in ['O-', 'AB-', 'B-', 'BOMBAY_HH']
    critical_shortage = total_compatible_units < units_needed

    return jsonify({
        'status': 'success',
        'patient_group': patient_group,
        'component_type': component,
        'units_requested': units_needed,
        'compatible_donor_groups': compatible_groups,
        'is_rare_phenotype': is_rare,
        'critical_shortage': critical_shortage,
        'total_available_in_grid': total_compatible_units,
        'facilities_ranked': matches,
        'advisory': 'Initiate intra-city inter-bank emergency component relay.' if critical_shortage else 'Direct dispatch possible from top matching center.'
    })


# --- REAL-TIME EMERGENCY ANALYTICS API ---
@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM emergency_requests')
    total_sos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM emergency_requests WHERE status = 'ADMITTED'")
    admitted = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(icu_available), SUM(icu_total), SUM(oxygen_available), SUM(oxygen_total) FROM hospital_beds')
    beds = cursor.fetchone()
    icu_avail, icu_tot, oxy_avail, oxy_tot = beds[0] or 0, beds[1] or 1, beds[2] or 0, beds[3] or 1

    cursor.execute('SELECT SUM(units_o_negative + units_ab_negative + units_b_negative + units_o_positive + units_b_positive) FROM blood_banks')
    total_blood_units = cursor.fetchone()[0] or 0

    conn.close()

    icu_occupancy = round(((icu_tot - icu_avail) / icu_tot) * 100, 1)
    oxy_occupancy = round(((oxy_tot - oxy_avail) / oxy_tot) * 100, 1)
    golden_hour_compliance = 94.2

    return jsonify({
        'status': 'success',
        'total_sos_dispatched': total_sos,
        'admissions_completed': admitted,
        'golden_hour_rate': f'{golden_hour_compliance}%',
        'icu_occupancy_pct': icu_occupancy,
        'oxygen_occupancy_pct': oxy_occupancy,
        'blood_reserve_units': total_blood_units,
        'corridor_hotspots': [
            {'zone': 'NH-19 Rooma Bypass', 'incidents': max(12, total_sos // 2), 'status': 'CRITICAL'},
            {'zone': 'Ramadevi Chauraha', 'incidents': max(8, total_sos // 3), 'status': 'HIGH_TRAFFIC'},
            {'zone': 'Govind Nagar Bridge', 'incidents': max(5, total_sos // 4), 'status': 'MODERATE'}
        ]
    })


# --- HOSPITAL TREATMENT & TRAUMA COST ESTIMATOR API ---
PROCEDURE_BASE_RATES = {
    'CARDIAC_PCI': {'name': 'Primary Angioplasty (PCI / Stent)', 'base_govt': 15000, 'base_pvt': 145000, 'icu_days': 2},
    'POLYTRAUMA': {'name': 'Polytrauma Resuscitation & Ortho Fixation', 'base_govt': 8000, 'base_pvt': 95000, 'icu_days': 3},
    'NEURO_TRAUMA': {'name': 'Severe Head Injury / Craniotomy', 'base_govt': 20000, 'base_pvt': 185000, 'icu_days': 4},
    'STROKE_THROMBOLYSIS': {'name': 'Acute Ischemic Stroke Thrombolysis (r-tPA)', 'base_govt': 5000, 'base_pvt': 65000, 'icu_days': 2},
    'RESPIRATORY_VENT': {'name': 'ARDS / Ventilator Support & ICU', 'base_govt': 4000, 'base_pvt': 45000, 'icu_days': 3}
}

@app.route('/api/cost/estimate', methods=['POST'])
def estimate_cost():
    data = request.get_json() or {}
    proc_key = data.get('procedure_key', 'CARDIAC_PCI')
    tier = data.get('hospital_tier', 'PRIVATE')  # GOVT, TRUST, PRIVATE
    has_pmjay = bool(data.get('ayushman_covered', False))
    icu_stay_days = int(data.get('icu_days', 2))

    proc = PROCEDURE_BASE_RATES.get(proc_key, PROCEDURE_BASE_RATES['CARDIAC_PCI'])
    
    # Base estimation
    if tier == 'GOVT':
        base_fee = proc['base_govt']
        icu_per_day = 1200
        nursing_consumables = 3500
    elif tier == 'TRUST':
        base_fee = int(proc['base_pvt'] * 0.45)
        icu_per_day = 4500
        nursing_consumables = 8000
    else:  # PRIVATE Tertiary
        base_fee = proc['base_pvt']
        icu_per_day = 12500
        nursing_consumables = 18000

    icu_total = icu_stay_days * icu_per_day
    gross_total = base_fee + icu_total + nursing_consumables

    covered_amount = 0
    if has_pmjay:
        covered_amount = gross_total
        patient_payable = 0
        status_note = '100% Cashless under Ayushman Bharat PM-JAY (Government Empanelled Rates)'
    else:
        patient_payable = gross_total
        status_note = 'Standard Estimated Out-of-Pocket Tariff'

    return jsonify({
        'status': 'success',
        'procedure': proc['name'],
        'hospital_tier': tier,
        'breakdown': {
            'procedure_base_fee': base_fee,
            'icu_charges': icu_total,
            'icu_days': icu_stay_days,
            'consumables_medicines': nursing_consumables
        },
        'gross_estimated_total': gross_total,
        'pmjay_coverage_amount': covered_amount,
        'patient_estimated_payable': patient_payable,
        'coverage_note': status_note
    })


# --- EN-ROUTE VITALS TELEMETRY & PRE-ARRIVAL ADVISORY API ---
@app.route('/api/teleconsult/vitals', methods=['POST'])
def relay_vitals():
    data = request.get_json() or {}
    ambulance_id = data.get('ambulance_id', 'UP-78-AG-1021')
    hr = int(data.get('heart_rate', 110))
    bp = data.get('blood_pressure', '90/60')
    spo2 = int(data.get('spo2', 89))
    gcs = int(data.get('gcs_score', 12))  # Glasgow Coma Scale 3-15
    ecg_status = data.get('ecg_status', 'Sinus Tachycardia / ST Elevation')

    # Clinical Priority Scoring
    is_critical = spo2 < 90 or gcs < 9 or hr > 120 or 'Elevation' in ecg_status
    advisory = []

    if spo2 < 90:
        advisory.append('Prepare High Flow Nasal Cannula (HFNC) / Rapid Sequence Intubation')
    if 'Elevation' in ecg_status:
        advisory.append('Activate Cath Lab Team - Code STEMI Pre-Alert')
    if gcs < 9:
        advisory.append('Severe Neuro Trauma Protocol - Secure Airway Immediate CT Scan')
    if not advisory:
        advisory.append('Patient vitals stabilized en-route. Maintain IV access.')

    return jsonify({
        'status': 'success',
        'ambulance_id': ambulance_id,
        'triage_alert': 'CODE_RED_CRITICAL' if is_critical else 'CODE_YELLOW_STABLE',
        'timestamp': time.strftime('%H:%M:%S IST'),
        'vitals_received': {
            'heart_rate': f'{hr} bpm',
            'bp': bp,
            'spo2': f'{spo2}%',
            'gcs_score': f'{gcs}/15',
            'ecg': ecg_status
        },
        'er_pre_arrival_actions': advisory,
        'assigned_hospital': 'SPM Hospital Trauma Centre / Hallet Apex Grid'
    })


# --- KANPUR TRAFFIC GREEN CORRIDOR & SIGNAL PREEMPTION API ---
ACTIVE_CORRIDORS = [
    {'corridor_id': 'GC-NH19-01', 'name': 'NH-19 Rooma to Hallet Trauma Apex', 'length_km': 14.2, 'chokepoints': ['Rooma Cut', 'Ramadevi Roundabout', 'Tatmill Chauraha', 'Mariampur Crossing'], 'status': 'STANDBY'},
    {'corridor_id': 'GC-GT-02', 'name': 'GT Road Kalyanpur to LLR ER Bay', 'length_km': 9.8, 'chokepoints': ['Kalyanpur Crossing', 'Rawatpur Bus Depot', 'Medical College Gate'], 'status': 'STANDBY'},
    {'corridor_id': 'GC-VIP-03', 'name': 'Civil Lines to Regency Super-Specialty', 'length_km': 6.5, 'chokepoints': ['Bada Chauraha', 'Phoolbagh', 'Sarvodaya Nagar Gate'], 'status': 'STANDBY'}
]

@app.route('/api/traffic/corridors', methods=['GET'])
def get_corridors():
    return jsonify({'status': 'success', 'corridors': ACTIVE_CORRIDORS})

@app.route('/api/traffic/preempt/<corridor_id>', methods=['POST'])
def preempt_signals(corridor_id):
    matched = None
    for c in ACTIVE_CORRIDORS:
        if c['corridor_id'] == corridor_id:
            c['status'] = 'GREEN_LOCKED'
            matched = c
            break

    if not matched:
        return jsonify({'status': 'error', 'message': 'Corridor not found'}), 404

    return jsonify({
        'status': 'success',
        'corridor_id': corridor_id,
        'corridor_name': matched['name'],
        'signal_status': 'ALL_SIGNALS_GREEN_PREEMPTED',
        'duration_cleared': '18 Minutes Wave Cleared',
        'traffic_police_units_alerted': len(matched['chokepoints']) * 2,
        'advisory': f"Police bike outriders and intersection wardens locked on {matched['name']}. Traffic cleared for en-route ALS units."
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)