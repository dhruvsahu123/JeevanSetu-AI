import sqlite3

DB_NAME = "jeevansetu.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
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

    # 2. Patients Profile Table
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
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 3. Hospitals Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            locality TEXT NOT NULL,
            distance_km REAL NOT NULL,
            trauma_level INTEGER NOT NULL,
            phone TEXT NOT NULL,
            latitude REAL DEFAULT 26.4499,
            longitude REAL DEFAULT 80.3319,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Hospital Beds Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_beds (
            hospital_id INTEGER PRIMARY KEY,
            icu_available INTEGER NOT NULL DEFAULT 0,
            icu_total INTEGER NOT NULL DEFAULT 0,
            oxygen_available INTEGER NOT NULL DEFAULT 0,
            oxygen_total INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
        )
    ''')

    # 5. Ambulances Fleet Table
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

    # 6. Emergency Requests Queue
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            symptom TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Geolocation Migration Check
    cursor.execute("PRAGMA table_info(hospitals);")
    cols = [col[1] for col in cursor.fetchall()]
    if 'latitude' not in cols:
        cursor.execute("ALTER TABLE hospitals ADD COLUMN latitude REAL DEFAULT 26.4499;")
    if 'longitude' not in cols:
        cursor.execute("ALTER TABLE hospitals ADD COLUMN longitude REAL DEFAULT 80.3319;")

    # Seed Kanpur Hospitals if empty
    cursor.execute("SELECT COUNT(*) FROM hospitals;")
    if cursor.fetchone()[0] == 0:
        hospitals = [
            ("Apex Emergency & Trauma Institute", "Civil Lines", 2.4, 1, "+91-512-2550101", 26.4735, 80.3506),
            ("Metro Heart & Critical Care Hub", "Swaroop Nagar", 4.1, 1, "+91-512-2550202", 26.4350, 80.2980),
            ("SPM Trauma Centre", "Rooma NH-19 Bypass", 6.8, 2, "+91-512-2550303", 26.3785, 80.4421)
        ]
        cursor.executemany('''
            INSERT INTO hospitals (name, locality, distance_km, trauma_level, phone, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', hospitals)

        beds = [
            (1, 8, 12, 15, 20),
            (2, 4, 10, 10, 15),
            (3, 5, 8, 12, 16)
        ]
        cursor.executemany('''
            INSERT INTO hospital_beds (hospital_id, icu_available, icu_total, oxygen_available, oxygen_total)
            VALUES (?, ?, ?, ?, ?)
        ''', beds)

    # Seed Ambulances if empty
    cursor.execute("SELECT COUNT(*) FROM ambulances;")
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

    conn.commit()
    conn.close()
    print("Database schema initialized cleanly.")

if __name__ == '__main__':
    init_db()
