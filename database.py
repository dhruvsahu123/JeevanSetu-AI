import sqlite3
import os

DB_NAME = "jeevansetu.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'PATIENT',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Patients Profile Table (Phase 21.5)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            blood_group TEXT,
            age INTEGER,
            gender TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            medical_allergies TEXT,
            chronic_conditions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # 3. Hospitals Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            locality TEXT NOT NULL,
            distance_km REAL NOT NULL,
            trauma_level INTEGER DEFAULT 2,
            phone TEXT NOT NULL
        )
    ''')

    # 4. Hospital Beds Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_beds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            icu_available INTEGER DEFAULT 0,
            icu_total INTEGER DEFAULT 10,
            oxygen_available INTEGER DEFAULT 0,
            FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
        )
    ''')

    # 5. Emergency Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            symptom TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed Initial Hospitals Data if table is empty
    cursor.execute('SELECT COUNT(*) FROM hospitals')
    if cursor.fetchone()[0] == 0:
        hospitals_data = [
            ("Apex Emergency & Trauma Institute", "Civil Lines Central", 1.8, 1, "+91-512-2550101"),
            ("Metro Heart & Critical Care Hub", "Swaroop Nagar Bypass", 3.2, 2, "+91-512-2550102"),
            ("City Multi-Specialty Health Center", "Govind Nagar West", 4.5, 2, "+91-512-2550103"),
            ("Divine Lifeline Super-Specialty", "Kalyanpur Health Corridor", 5.1, 1, "+91-512-2550104"),
            ("Shanti Memorial General Hospital", "Kidwai Nagar Block B", 6.8, 3, "+91-512-2550105")
        ]
        cursor.executemany('''
            INSERT INTO hospitals (name, locality, distance_km, trauma_level, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', hospitals_data)

        beds_data = [
            (1, 4, 16, 12),
            (2, 2, 10, 8),
            (3, 0, 8, 15),
            (4, 7, 20, 24),
            (5, 1, 6, 4)
        ]
        cursor.executemany('''
            INSERT INTO hospital_beds (hospital_id, icu_available, icu_total, oxygen_available)
            VALUES (?, ?, ?, ?)
        ''', beds_data)

    conn.commit()
    conn.close()
    print("✓ SQLite Database (jeevansetu.db) schema verified and updated successfully!")

if __name__ == "__main__":
    init_db() 
    # 6. Ambulances Fleet Table (Phase 22)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ambulances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL,
            fleet_type TEXT NOT NULL DEFAULT 'BLS',
            driver_name TEXT NOT NULL,
            driver_phone TEXT NOT NULL,
            current_latitude REAL NOT NULL,
            current_longitude REAL NOT NULL,
            operational_status TEXT NOT NULL DEFAULT 'AVAILABLE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed Initial Kanpur Ambulances if table is empty
    cursor.execute('SELECT COUNT(*) FROM ambulances')
    if cursor.fetchone()[0] == 0:
        ambulance_fleet = [
            ("UP-78-AG-1021", "ALS", "Ramesh Kumar", "+91-9876500001", 26.4520, 80.3350, "AVAILABLE"),
            ("UP-78-BG-2042", "BLS", "Suresh Yadav", "+91-9876500002", 26.4735, 80.3150, "AVAILABLE"),
            ("UP-78-CG-3099", "ALS", "Mohit Verma", "+91-9876500003", 26.4380, 80.3010, "AVAILABLE")
        ]
        cursor.executemany('''
            INSERT INTO ambulances (vehicle_number, fleet_type, driver_name, driver_phone, current_latitude, current_longitude, operational_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ambulance_fleet)
        # In init_db() inside database.py:

cursor.execute('''
    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        locality TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        trauma_level INTEGER NOT NULL DEFAULT 1,
        phone TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')