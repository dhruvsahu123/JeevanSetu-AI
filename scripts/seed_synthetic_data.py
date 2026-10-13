import sqlite3
import sys
import os
import shutil
import json
import random
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")

def backup_database():
    if os.path.exists(DB_FILE):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = os.path.join(BASE_DIR, f"database.db.backup_{timestamp}")
        shutil.copy2(DB_FILE, backup_name)
        print(f"[SAFETY BACKUP] Created local database backup: {backup_name}")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def run_migrations(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        cols = [c[1] for c in cursor.fetchall()]
        if "is_demo" not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN is_demo INTEGER DEFAULT 0;")
        if "data_source" not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN data_source TEXT DEFAULT 'LIVE';")
    conn.commit()

def init_schema(conn):
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_uid TEXT UNIQUE,
        name TEXT NOT NULL,
        locality TEXT NOT NULL,
        zone TEXT NOT NULL,
        trauma_tier TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hospital_beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bed_uid TEXT UNIQUE,
        hospital_uid TEXT NOT NULL,
        bed_type TEXT NOT NULL,
        status TEXT NOT NULL,
        ward_number TEXT,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE',
        FOREIGN KEY (hospital_uid) REFERENCES hospitals(hospital_uid) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_uid TEXT UNIQUE,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        qualification TEXT NOT NULL,
        hospital_uid TEXT NOT NULL,
        is_on_duty INTEGER DEFAULT 1,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE',
        FOREIGN KEY (hospital_uid) REFERENCES hospitals(hospital_uid) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ambulances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_number TEXT UNIQUE,
        ambulance_type TEXT NOT NULL,
        driver_name TEXT NOT NULL,
        driver_contact TEXT NOT NULL,
        base_zone TEXT NOT NULL,
        current_status TEXT NOT NULL,
        current_speed_kmh REAL DEFAULT 0.0,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blood_banks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_uid TEXT UNIQUE,
        name TEXT NOT NULL,
        locality TEXT NOT NULL,
        zone TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blood_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_uid TEXT UNIQUE,
        bank_uid TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        component_type TEXT NOT NULL,
        units_available INTEGER DEFAULT 0,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE',
        FOREIGN KEY (bank_uid) REFERENCES blood_banks(bank_uid) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinical_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condition_code TEXT UNIQUE,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        severity_grade TEXT NOT NULL,
        dos_json TEXT NOT NULL,
        donts_json TEXT NOT NULL,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_code TEXT UNIQUE,
        brand_name TEXT NOT NULL,
        generic_formula TEXT NOT NULL,
        dosage_form TEXT NOT NULL,
        category TEXT NOT NULL,
        standard_unit_cost REAL NOT NULL,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS synthetic_patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_uid TEXT UNIQUE,
        full_name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        blood_group TEXT NOT NULL,
        mock_abha_id TEXT NOT NULL,
        emergency_contact TEXT NOT NULL,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS emergency_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_code TEXT UNIQUE,
        patient_uid TEXT NOT NULL,
        corridor TEXT NOT NULL,
        triage_category TEXT NOT NULL,
        condition_summary TEXT NOT NULL,
        assigned_ambulance TEXT,
        destination_hospital TEXT,
        incident_status TEXT NOT NULL,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS treatment_pricing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        procedure_code TEXT UNIQUE,
        procedure_name TEXT NOT NULL,
        clinical_department TEXT NOT NULL,
        pmjay_package_code TEXT NOT NULL,
        private_hospital_rate REAL NOT NULL,
        pmjay_cashless_rate REAL NOT NULL,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diagnostic_centres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        centre_uid TEXT UNIQUE,
        name TEXT NOT NULL,
        locality TEXT NOT NULL,
        imaging_capabilities TEXT NOT NULL,
        contact_phone TEXT NOT NULL,
        is_demo INTEGER DEFAULT 0,
        data_source TEXT DEFAULT 'LIVE'
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_directory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        serial_no INTEGER,
        full_name TEXT NOT NULL,
        email_address TEXT NOT NULL UNIQUE,
        program TEXT NOT NULL,
        student_identifier TEXT UNIQUE,
        account_status TEXT DEFAULT 'PENDING_AUTHORIZATION',
        record_source TEXT DEFAULT 'USER_PROVIDED',
        is_demo INTEGER DEFAULT 1
    );
    """)

    conn.commit()

def reset_demo_only(conn):
    cursor = conn.cursor()
    tables = [
        "hospital_beds", "doctors", "hospitals", "blood_stock", "blood_banks",
        "clinical_conditions", "medicines", "synthetic_patients", "emergency_incidents",
        "treatment_pricing", "diagnostic_centres", "ambulances", "student_directory"
    ]
    purged = 0
    for t in tables:
        try:
            cursor.execute(f"DELETE FROM {t} WHERE is_demo = 1;")
            purged += cursor.rowcount
        except sqlite3.OperationalError:
            pass
    conn.commit()
    print(f"[RESET DEMO ONLY] Purged {purged} synthetic records safely. Live records remain intact.")

def seed_all(conn):
    cursor = conn.cursor()
    random.seed(42)

    zones = ["Rooma NH-19 Corridor", "Civil Lines Apex", "Swaroop Nagar Hub", "Barra South Bypass", "Kalyanpur West GT Road", "Chakeri Airport Corridor", "Govind Nagar Central", "Mandhana Outer Cut"]
    localities = ["NH-19 Expressway Mile 12", "GT Road Sector 4", "Mall Road Radial", "Industrial Area Gate 2", "Panki Bypass Link", "Kanpur Ring Road Node 3"]
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    blood_components = ["Packed Red Blood Cells (PRBC)", "Single Donor Platelets (SDP)", "Fresh Frozen Plasma (FFP)", "Cryoprecipitate"]

    print("[1/11] Seeding 100 Synthetic Hospitals...")
    tiers = ["Level-1 Apex Trauma", "Level-2 Emergency Care", "Level-3 Rapid Transit", "Super Specialty Grid"]
    hosp_uids = []
    for i in range(1, 101):
        uid = f"HOSP-SYN-{i:03d}"
        hosp_uids.append(uid)
        name = f"Demo Trauma Centre {i:03d}"
        zone = zones[i % len(zones)]
        loc = localities[i % len(localities)]
        tier = tiers[i % len(tiers)]
        phone = f"+91-512-29{i:04d}"
        cursor.execute("""
            INSERT OR IGNORE INTO hospitals (hospital_uid, name, locality, zone, trauma_tier, contact_phone, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (uid, name, loc, zone, tier, phone))

    print("[2/11] Seeding 1,000 Synthetic Hospital Beds...")
    bed_types = ["ICU Ventilator", "Oxygen High-Flow", "Trauma Resuscitation Bay", "Step-Down HDU", "Post-Op Observation"]
    bed_statuses = ["Available", "Occupied", "Sanitizing", "Reserved-Enroute"]
    for i in range(1, 1001):
        b_uid = f"BED-SYN-{i:04d}"
        h_uid = hosp_uids[(i - 1) % len(hosp_uids)]
        b_type = bed_types[i % len(bed_types)]
        b_status = bed_statuses[i % len(bed_statuses)]
        ward = f"Ward-{chr(65 + (i % 6))}"
        cursor.execute("""
            INSERT OR IGNORE INTO hospital_beds (bed_uid, hospital_uid, bed_type, status, ward_number, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (b_uid, h_uid, b_type, b_status, ward))

    print("[3/11] Seeding 500 Fictional Doctors...")
    specialties = ["Trauma Surgeon", "Neurosurgeon", "Critical Care Intensivist", "Emergency Physician", "Interventional Cardiologist", "Orthopedic Trauma Specialist"]
    qualifications = ["MS, MCh (Trauma Surgery)", "MD (Emergency Medicine)", "MD (Anaesthesia & Critical Care)", "MS (Orthopaedics)", "DM (Cardiology)"]
    for i in range(1, 501):
        d_uid = f"DOC-SYN-{i:03d}"
        name = f"Dr. S. K. Demo Specialist {i:03d}"
        spec = specialties[i % len(specialties)]
        qual = qualifications[i % len(qualifications)]
        h_uid = hosp_uids[i % len(hosp_uids)]
        on_duty = 1 if (i % 3 != 0) else 0
        cursor.execute("""
            INSERT OR IGNORE INTO doctors (doctor_uid, name, specialty, qualification, hospital_uid, is_on_duty, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (d_uid, name, spec, qual, h_uid, on_duty))

    print("[4/11] Seeding 50 Fictional Ambulances...")
    for i in range(1, 51):
        v_num = f"UP78-SIM-{i:04d}"
        a_type = "Advanced Life Support (ALS)" if (i % 2 == 0) else "Basic Life Support (BLS)"
        d_name = f"Simulated Paramedic Pilot {i:02d}"
        d_phone = f"+91-9839{i:06d}"
        base = zones[i % len(zones)]
        status = "Dispatched-Enroute" if (i % 4 == 0) else "Standing-By"
        speed = round(random.uniform(42.0, 78.5), 1) if status == "Dispatched-Enroute" else 0.0
        cursor.execute("""
            INSERT OR IGNORE INTO ambulances (vehicle_number, ambulance_type, driver_name, driver_contact, base_zone, current_status, current_speed_kmh, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (v_num, a_type, d_name, d_phone, base, status, speed))

    print("[5/11] Seeding 100 Blood Banks & 800 Blood Stock Inventories...")
    for i in range(1, 101):
        b_uid = f"BB-SYN-{i:03d}"
        name = f"Demo Blood Bank Facility {i:03d}"
        loc = localities[i % len(localities)]
        zone = zones[i % len(zones)]
        phone = f"+91-512-27{i:04d}"
        cursor.execute("""
            INSERT OR IGNORE INTO blood_banks (bank_uid, name, locality, zone, contact_phone, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (b_uid, name, loc, zone, phone))

        for grp in blood_groups:
            stock_uid = f"STK-{b_uid}-{grp}"
            comp = blood_components[hash(grp) % len(blood_components)]
            units = (i * 7 + hash(grp)) % 25 + 3
            cursor.execute("""
                INSERT OR IGNORE INTO blood_stock (stock_uid, bank_uid, blood_group, component_type, units_available, is_demo, data_source)
                VALUES (?, ?, ?, ?, ?, 1, 'SYNTHETIC')
            """, (stock_uid, b_uid, grp, comp, units))

    print("[6/11] Seeding 1,000 Clinical Conditions (Evidence-Based 4 DOs & 4 DON'Ts)...")
    cats = ["Trauma & Resuscitation", "Cardiovascular Crisis", "Neurotrauma & CVA", "Respiratory Failure", "Thermal & Chemical Burns", "Toxicology & Envenomation", "Orthopedic Emergencies", "Pediatric Resuscitation"]
    for i in range(1, 1001):
        code = f"PROT-SYN-{i:04d}"
        cat = cats[i % len(cats)]
        name = f"{cat.split(' ')[0]} Emergency Protocol #{i:04d} [ATLS Grade {(i % 4) + 1}]"
        grade = f"Grade-{(i % 4) + 1}"
        dos = [
            "Maintain cervical spine inline stabilization and align airway.",
            "Administer high-flow humidified oxygen targeting SpO2 > 95%.",
            "Establish dual large-bore IV access (16G/18G).",
            "Pre-notify apex receiving trauma bay via telemetry link."
        ]
        donts = [
            "Do NOT remove helmet forcibly in suspected cervical spine trauma.",
            "Do NOT administer oral fluids to an unconscious or drowsy patient.",
            "Do NOT delay emergency transport for secondary non-critical checks.",
            "Do NOT infuse cold, un-warmed fluids in hemorrhagic shock."
        ]
        cursor.execute("""
            INSERT OR IGNORE INTO clinical_conditions (condition_code, name, category, severity_grade, dos_json, donts_json, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (code, name, cat, grade, json.dumps(dos), json.dumps(donts)))

    print("[7/11] Seeding 500 Emergency Medicines...")
    med_cats = ["Emergency ACLS Drug", "Vasoactive Inotrope", "Hemostatic Agent", "Analgesic & Sedative", "Antidote & Reversal", "Bronchodilator"]
    forms = ["IV Ampoule", "Prefilled Syringe", "IV Infusion Bag 100 mL", "Inhalation Respule", "Sublingual Tablet"]
    for i in range(1, 501):
        m_code = f"MED-SYN-{i:03d}"
        b_name = f"Demo Pharmacopeia Compound {i:03d}"
        g_name = f"Generic Active Reference Formulation #{i:03d}"
        f_form = forms[i % len(forms)]
        c_cat = med_cats[i % len(med_cats)]
        cost = round((i * 12.5) % 450 + 25.0, 2)
        cursor.execute("""
            INSERT OR IGNORE INTO medicines (medicine_code, brand_name, generic_formula, dosage_form, category, standard_unit_cost, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (m_code, b_name, g_name, f_form, c_cat, cost))

    print("[8/11] Seeding 200 Synthetic Patients & 200 Emergency Incidents...")
    first_names = ["Aarav", "Vivaan", "Aditya", "Reyansh", "Diya", "Ananya", "Ishaan", "Tanvi", "Kabir", "Rhea", "Ayaan", "Myra"]
    last_names = ["DemoSharma", "DemoVerma", "DemoPatel", "DemoGupta", "DemoSingh", "DemoYadav", "DemoMishra", "DemoPandey"]
    for i in range(1, 201):
        p_uid = f"PAT-SYN-{i:03d}"
        p_name = f"{first_names[i % len(first_names)]} {last_names[(i // len(first_names)) % len(last_names)]} #{i:03d}"
        age = (i * 3) % 65 + 12
        gender = "Male" if (i % 2 == 0) else "Female"
        bg = blood_groups[i % len(blood_groups)]
        mock_abha = f"TEST-ABHA-{i:04d}-{random.randint(1000, 9999)}"
        phone = f"+91-9163{i:06d}"
        cursor.execute("""
            INSERT OR IGNORE INTO synthetic_patients (patient_uid, full_name, age, gender, blood_group, mock_abha_id, emergency_contact, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (p_uid, p_name, age, gender, bg, mock_abha, phone))

        inc_code = f"INC-SYN-{i:04d}"
        corr = localities[i % len(localities)]
        triage = "Red (Immediate)" if (i % 3 == 0) else ("Yellow (Delayed)" if (i % 3 == 1) else "Green (Minor)")
        summary = f"Simulated Trauma Scenario #{i:03d}: Highway Incident Telemetry Dispatch"
        amb = f"UP78-SIM-{(i % 50) + 1:04d}"
        hosp = f"Demo Trauma Centre {(i % 100) + 1:03d}"
        status = "Enroute-To-Bay" if (i % 2 == 0) else "Admitted-Triage-Complete"
        cursor.execute("""
            INSERT OR IGNORE INTO emergency_incidents (incident_code, patient_uid, corridor, triage_category, condition_summary, assigned_ambulance, destination_hospital, incident_status, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (inc_code, p_uid, corr, triage, summary, amb, hosp, status))

    print("[9/11] Seeding 100 Treatment Pricing Packages...")
    dept = ["Consultation", "Hospital room", "ICU", "Nursing", "Laboratory tests", "Imaging", "Procedures", "Medicines", "Consumables", "Surgery", "Delivery", "Post-treatment care"]
    for i in range(1, 101):
        proc_code = f"PROC-SYN-{i:03d}"
        proc_name = f"Synthetic Estimate: {dept[i % len(dept)]} Tier-{((i % 4) + 1)} Care Package"
        pmjay_code = f"PMJAY-UP-SIM-{i:03d}"
        priv_rate = round((i * 1200) % 95000 + 15000.0, 2)
        pmjay_rate = round(priv_rate * 0.42, 2)
        cursor.execute("""
            INSERT OR IGNORE INTO treatment_pricing (procedure_code, procedure_name, clinical_department, pmjay_package_code, private_hospital_rate, pmjay_cashless_rate, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (proc_code, proc_name, dept[i % len(dept)], pmjay_code, priv_rate, pmjay_rate))

    print("[10/11] Seeding 100 Diagnostic Centres...")
    caps = ["CT 128-Slice & Digital X-Ray", "E-FAST Ultrasound & CT Angiography", "3T MRI & Emergency Trauma Lab", "Sonography & Bedside Radiography"]
    for i in range(1, 101):
        diag_uid = f"DIAG-SYN-{i:03d}"
        d_name = f"Demo Diagnostic Imaging Centre {i:03d}"
        loc = localities[i % len(localities)]
        cap = caps[i % len(caps)]
        phone = f"+91-512-26{i:04d}"
        cursor.execute("""
            INSERT OR IGNORE INTO diagnostic_centres (centre_uid, name, locality, imaging_capabilities, contact_phone, is_demo, data_source)
            VALUES (?, ?, ?, ?, ?, 1, 'SYNTHETIC')
        """, (diag_uid, d_name, loc, cap, phone))

    conn.commit()
    print("[11/11] [SUCCESS] All 11 synthetic modules seeded idempotently with ZERO live data impact.")

if __name__ == "__main__":
    backup_database()
    conn = get_connection()
    run_migrations(conn)
    init_schema(conn)
    if len(sys.argv) > 1 and sys.argv[1] == "--reset-demo-only":
        reset_demo_only(conn)
    else:
        seed_all(conn)
    conn.close()
