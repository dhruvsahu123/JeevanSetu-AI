import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_db_connection, init_db
from google import genai

app = Flask(__name__)
# Enable CORS for all incoming client origins
CORS(app, resources={r"/*": {"origins": "*"}})

# 1. Gemini Client Setup
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# -------------------------------------------------------------
# 1. SYSTEM HEALTH
# -------------------------------------------------------------
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "service": "JeevanSetu AI Full Stack Engine",
        "gemini_active": bool(client)
    }), 200

# -------------------------------------------------------------
# 2. USER AUTHENTICATION (REGISTER & LOGIN)
# -------------------------------------------------------------
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.get_json() or {}
    name = data.get('full_name')
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password')
    role = data.get('role', 'PATIENT').strip().upper()

    if not (name and email and phone and password):
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, phone, password, role))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return jsonify({
            "message": "Account created successfully",
            "user_id": user_id,
            "role": role
        }), 201
    except Exception:
        conn.close()
        return jsonify({"error": "Email or Phone already registered"}), 409

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not (email and password):
        return jsonify({"error": "Email and Password are required"}), 400

    conn = get_db_connection()
    user = conn.execute('''
        SELECT id, full_name, email, role, password_hash 
        FROM users 
        WHERE LOWER(email) = ?
    ''', (email,)).fetchone()
    conn.close()

    if user and user['password_hash'] == password:
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["full_name"],
                "email": user["email"],
                "role": user["role"].upper()
            }
        }), 200
    
    return jsonify({"error": "Invalid email or password"}), 401

# -------------------------------------------------------------
# 3. HOSPITALS & BED MANAGEMENT
# -------------------------------------------------------------
@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    conn = get_db_connection()
    query = '''
        SELECT h.id, h.name, h.locality, h.distance_km, h.trauma_level, h.phone, h.lat, h.lng,
               b.icu_available, b.icu_total, b.oxygen_available
        FROM hospitals h
        LEFT JOIN hospital_beds b ON h.id = b.hospital_id
    '''
    rows = conn.execute(query).fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "name": r["name"],
            "location": r["locality"],
            "distanceKm": r["distance_km"],
            "traumaLevel": r["trauma_level"],
            "phone": r["phone"],
            "lat": r["lat"],
            "lng": r["lng"],
            "icuAvailable": r["icu_available"] if r["icu_available"] is not None else 0,
            "totalIcu": r["icu_total"] if r["icu_total"] is not None else 0,
            "oxygenBeds": r["oxygen_available"] if r["oxygen_available"] is not None else 0
        })
    return jsonify(results), 200

@app.route('/api/hospitals/<int:hosp_id>/beds', methods=['PATCH'])
def update_beds(hosp_id):
    data = request.get_json() or {}
    icu_change = data.get('icu_change', 0)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE hospital_beds 
        SET icu_available = MAX(0, icu_available + ?) 
        WHERE hospital_id = ?
    ''', (icu_change, hosp_id))
    conn.commit()

    updated = cursor.execute('''
        SELECT icu_available, icu_total FROM hospital_beds WHERE hospital_id = ?
    ''', (hosp_id,)).fetchone()
    conn.close()

    if updated:
        return jsonify({
            "hospital_id": hosp_id,
            "icu_available": updated["icu_available"],
            "icu_total": updated["icu_total"]
        }), 200
    return jsonify({"error": "Hospital not found"}), 404

# -------------------------------------------------------------
# 4. EMERGENCY SOS DISPATCH & QUEUE
# -------------------------------------------------------------
@app.route('/api/emergency/create', methods=['POST'])
def create_emergency():
    data = request.get_json() or {}
    patient_name = data.get('patient_name', 'Emergency Alert')
    symptom = data.get('symptom', 'Critical Condition')
    priority = data.get('priority', 'TIER_1_CRITICAL')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO emergency_requests (patient_name, symptom, priority)
        VALUES (?, ?, ?)
    ''', (patient_name, symptom, priority))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "incident_id": f"#JS-EM-{new_id}",
        "message": "Emergency Alert Dispatched Successfully",
        "eta": "6-8 Mins"
    }), 201

@app.route('/api/emergencies', methods=['GET'])
def get_emergencies():
    conn = get_db_connection()
    emergencies = conn.execute('''
        SELECT id, patient_name, symptom, priority, created_at
        FROM emergency_requests
        ORDER BY id DESC
        LIMIT 10
    ''').fetchall()
    conn.close()

    results = []
    for em in emergencies:
        results.append({
            "id": em["id"],
            "ticket": f"#JS-EM-{em['id']}",
            "patient_name": em["patient_name"],
            "symptom": em["symptom"],
            "priority": em["priority"],
            "time": em["created_at"]
        })
    return jsonify(results), 200

# -------------------------------------------------------------
# 5. REGIONAL BLOOD BANK DIRECTORY & INVENTORY
# -------------------------------------------------------------
@app.route('/api/blood-banks', methods=['GET'])
def get_blood_banks():
    blood_banks = [
        {
            "id": 1,
            "name": "LLR / Hallet Hospital Regional Blood Bank",
            "location": "Swaroop Nagar, Kanpur",
            "phone": "0512-2556295",
            "distanceKm": 8.8,
            "inventory": { "O_pos": 24, "O_neg": 4, "A_pos": 18, "B_pos": 32, "AB_pos": 9, "AB_neg": 2 }
        },
        {
            "id": 2,
            "name": "SPM Trauma Center Emergency Blood Unit",
            "location": "Rooma / NH-19, Kanpur",
            "phone": "0512-2410100",
            "distanceKm": 1.8,
            "inventory": { "O_pos": 14, "O_neg": 2, "A_pos": 8, "B_pos": 16, "AB_pos": 5, "AB_neg": 1 }
        },
        {
            "id": 3,
            "name": "Red Cross Society Blood Centre",
            "location": "Civil Lines, Kanpur",
            "phone": "0512-2304567",
            "distanceKm": 7.5,
            "inventory": { "O_pos": 30, "O_neg": 6, "A_pos": 22, "B_pos": 40, "AB_pos": 12, "AB_neg": 3 }
        },
        {
            "id": 4,
            "name": "Kashi Ram Government Hospital Blood Bank",
            "location": "Ramadevi, Kanpur",
            "phone": "0512-2402555",
            "distanceKm": 3.8,
            "inventory": { "O_pos": 16, "O_neg": 1, "A_pos": 10, "B_pos": 20, "AB_pos": 6, "AB_neg": 0 }
        }
    ]
    return jsonify(blood_banks), 200

# -------------------------------------------------------------
# 6. GEMINI AI CLINICAL TRIAGE
# -------------------------------------------------------------
@app.route('/api/ai/triage', methods=['POST'])
def ai_triage():
    data = request.get_json() or {}
    symptoms = data.get('symptoms', '')
    age = data.get('age', 'Unknown')
    mobility = data.get('mobility', 'Ambulatory')

    if not symptoms:
        return jsonify({"error": "Symptoms are required"}), 400

    if not client:
        return jsonify({
            "priority": "CRITICAL PRIORITY (TIER 1)",
            "headline": "Immediate Medical Attention Advised",
            "advice": "High risk detected. Proceed directly to nearest emergency trauma unit.",
            "ambulance_needed": True,
            "required_facility": "Cardiac / Level 1 Trauma ICU"
        }), 200

    triage_prompt = f"""
    You are the clinical emergency triage AI for 'JeevanSetu AI'.
    Evaluate this emergency scenario:
    - Symptoms: {symptoms}
    - Patient Age: {age}
    - Mobility State: {mobility}

    Respond STRICTLY with a valid JSON object matching this structure:
    {{
      "priority": "CRITICAL PRIORITY (TIER 1)",
      "headline": "Short 4-6 word clinical summary",
      "advice": "Two sentences of direct, life-saving advice for the patient/bystander while waiting.",
      "ambulance_needed": true,
      "required_facility": "e.g., Cath Lab / Neuro ICU / General Emergency"
    }}
    Do not include markdown blocks or extra text, only raw JSON.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=triage_prompt
        )
        cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
        result_json = json.loads(cleaned_text)
        return jsonify(result_json), 200
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({
            "priority": "URGENT EVALUATION (TIER 2)",
            "headline": "Rapid Emergency Assessment",
            "advice": "Keep patient calm and seated. Dispatching ambulance for emergency monitoring.",
            "ambulance_needed": True,
            "required_facility": "Emergency Casualty Bay"
        }), 200

def auto_seed_if_empty():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS hospitals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, locality TEXT, distance_km REAL, trauma_level TEXT, phone TEXT, lat REAL, lng REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS hospital_beds (id INTEGER PRIMARY KEY AUTOINCREMENT, hospital_id INTEGER UNIQUE, icu_available INTEGER, icu_total INTEGER, oxygen_available INTEGER)")
    count = cursor.execute("SELECT COUNT(*) FROM hospitals").fetchone()[0]
    conn.close()
    if count == 0:
        print("🌱 Seeding Kanpur & Rooma hospitals into cloud database...")
        from seed_kanpur_hospitals import seed_data
        seed_data()

if __name__ == '__main__':
    init_db()
    try:
        auto_seed_if_empty()
    except Exception as e:
        print(f"Auto-seed warning: {e}")
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 JeevanSetu AI Server running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
    # -------------------------------------------------------------
# 6. GEMINI AI CLINICAL TRIAGE WITH FIRST-AID ADVISORY (DOs & DONTs)
# -------------------------------------------------------------
@app.route('/api/ai/triage', methods=['POST'])
def ai_triage():
    data = request.get_json() or {}
    symptoms = data.get('symptoms', '')
    age = data.get('age', 'Unknown')
    mobility = data.get('mobility', 'Ambulatory')

    if not symptoms:
        return jsonify({"error": "Symptoms are required"}), 400

    # Offline / Instant Rules Database (Agar network issue ya lag ho)
    symptom_lower = symptoms.lower()
    fallback_dos = ["Patient ko shaant aur sthir rakhein.", "Tight kapde dheele karein aur emergency hotline 108 par call karein."]
    fallback_donts = ["Ghabrahat me mariz ko daudayein ya chalayein nahi.", "Bina doctori salah ke koi dawai na dein."]

    if "snake" in symptom_lower or "saap" in symptom_lower:
        fallback_dos = [
            "Kaate hue ang ko dil ke level se neeche rakhein aur mariz ko bilkul sthir (still) rakhein.",
            "Ghaav ko saaf paani se halka dhoyein aur ghadi/chudi/ring turant nikal dein taaki sujan aane par rukawat na ho."
        ]
        fallback_donts = [
            "Ghaav par cheer/cut na lagayein aur muh se zehar choosne ki galti KABHI na karein.",
            "Rassi ya tourniquet ko itna tight na baandhein ki khoon ka bahav bilkul ruk jaye, aur barf (ice) na lagayein."
        ]
    elif "chest" in symptom_lower or "heart" in symptom_lower or "dard" in symptom_lower:
        fallback_dos = [
            "Mariz ko aaram se aadhi baithi hui (semi-upright) halat me bithayein.",
            "Agar pehle se doctor ne Sorbitrate ya Aspirin suggest ki ho toh le sakte hain aur shant rahein."
        ]
        fallback_donts = [
            "Mariz ko chalkar ya seedhiyan chadhkar jane na dein.",
            "Bhari khana ya peena na dein."
        ]

    if not client:
        return jsonify({
            "priority": "CRITICAL PRIORITY (TIER 1)",
            "headline": "Immediate First-Aid Protocol Active",
            "advice": "Ambulance deploy ho rahi hai. Neeche diye gaye life-saving steps turant follow karein.",
            "dos": fallback_dos,
            "donts": fallback_donts,
            "ambulance_needed": True
        }), 200

    triage_prompt = f"""
    You are an emergency emergency medical specialist AI for JeevanSetu.
    A patient has this acute emergency:
    - Condition/Symptoms: {symptoms}
    - Age: {age}
    - Mobility: {mobility}

    The ambulance is on the way (arrival 6-8 mins). Give critical pre-arrival FIRST-AID guidance in simple Hinglish/English.
    Respond STRICTLY with raw JSON matching this schema:
    {{
      "priority": "CRITICAL PRIORITY (TIER 1)",
      "headline": "Short 4-5 words condition summary",
      "advice": "1 concise sentence reassuring the attendant.",
      "dos": [
        "First critical DO instruction",
        "Second critical DO instruction"
      ],
      "donts": [
        "First lethal mistake NOT to do (e.g. do not cut snakebite or tourniquet tightly)",
        "Second mistake NOT to do"
      ],
      "voice_speech": "A concise 2-sentence voice instruction in simple Hindi/Hinglish to be read aloud immediately."
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=triage_prompt
        )
        cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
        result_json = json.loads(cleaned_text)
        return jsonify(result_json), 200
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({
            "priority": "CRITICAL PRIORITY (TIER 1)",
            "headline": "Emergency First-Aid Protocol",
            "advice": "Ambulance en route. Follow these life-saving precautions immediately.",
            "dos": fallback_dos,
            "donts": fallback_donts,
            "voice_speech": "Mariz ko shaant rakhein aur sthir rakhein. Ghaav par koi cheer ya tight patti na baandhein."
        }), 200