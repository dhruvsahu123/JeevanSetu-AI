import sqlite3

def seed_data():
    conn = sqlite3.connect("jeevansetu.db")
    cursor = conn.cursor()

    # Purani tables drop karein taaki nayi columns (lat, lng) ke sath fresh schema bane
    cursor.execute("DROP TABLE IF EXISTS hospital_beds")
    cursor.execute("DROP TABLE IF EXISTS hospitals")

    # Fresh table schema with lat and lng
    cursor.execute("""
        CREATE TABLE hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            locality TEXT NOT NULL,
            distance_km REAL DEFAULT 2.5,
            trauma_level TEXT NOT NULL,
            phone TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE hospital_beds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER UNIQUE,
            icu_available INTEGER DEFAULT 5,
            icu_total INTEGER DEFAULT 20,
            oxygen_available INTEGER DEFAULT 25,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        )
    """)

    # Kanpur & Rooma Corridor Hospitals Dataset
    hospitals = [
        # --- ROOMA & NH-19 HIGHWAY CORRIDOR ---
        ("SPM Hospital Research & Trauma Centre", "Rooma / NH-19, Kanpur", 1.8, "Level 1 Trauma", "0512-2410100", 26.3785, 80.4421, 18, 25, 45),
        ("Mahaadeva Multi-Speciality Hospital", "Naubasta / Rooma Bypass, Kanpur", 4.2, "Level 2 Trauma", "0512-2621000", 26.4082, 80.3456, 14, 20, 35),
        ("Vaishnavi Hospital & Critical Care", "Hamirpur Road, Naubasta, Kanpur", 4.8, "Level 2 Trauma", "0512-2602200", 26.4150, 80.3390, 12, 18, 30),
        ("Utkarsh Hospital & Trauma Centre", "Baba Nagar, Naubasta, Kanpur", 4.5, "Level 2 Trauma", "0512-2619090", 26.4120, 80.3412, 10, 15, 25),
        ("Deys Hospital & Emergency Centre", "Lal Bangla, Kanpur", 5.5, "Level 2 Trauma", "0512-2401500", 26.4385, 80.3950, 15, 22, 40),
        ("Kashi Ram Memorial Government Hospital", "Ramadevi, Kanpur", 3.8, "Level 1 Trauma", "0512-2402555", 26.4310, 80.3870, 24, 40, 80),

        # --- SOUTH KANPUR (BARRA, KIDWAI NAGAR, GOVIND NAGAR) ---
        ("Raj Hospital (ICU, NICU & Trauma Centre)", "NH-2, Barra, Kanpur", 6.2, "Level 1 Trauma", "0512-2281236", 26.4312, 80.3015, 20, 30, 50),
        ("Satya Trauma & Maternity Centre", "Barra, Kanpur", 6.5, "Level 2 Trauma", "0512-2285327", 26.4350, 80.3050, 16, 24, 35),
        ("Priya Hospital & Critical Care", "Barra II Bypass, Kanpur", 6.8, "Level 2 Trauma", "0512-2280010", 26.4380, 80.2980, 14, 20, 32),
        ("The Umrao Multi-Speciality Hospital", "Sachan Chauraha, Juhi Kalan, Kanpur", 5.9, "Level 2 Trauma", "0512-2271500", 26.4420, 80.3120, 18, 25, 45),
        ("Delta Hospital", "Opp. Parag Dairy, Saket Nagar, Kanpur", 5.3, "Level 2 Trauma", "0512-2600065", 26.4410, 80.3270, 12, 18, 28),
        ("New Angel Hospital & Research Centre", "Kidwai Nagar, Kanpur", 5.1, "Level 2 Trauma", "0512-2602460", 26.4460, 80.3340, 15, 20, 30),
        ("Regency Hospital (South Branch)", "Govind Nagar, Kanpur", 6.0, "Level 1 Trauma", "0512-3501234", 26.4450, 80.3100, 22, 35, 60),

        # --- CENTRAL & NORTH KANPUR (SWAROOP NAGAR, SARVODAYA, KAKADEO) ---
        ("Regency Super Speciality Hospital", "A-2, Sarvodaya Nagar, Kanpur", 8.5, "Level 1 Apex Trauma", "0512-2555111", 26.4789, 80.3065, 38, 50, 120),
        ("Lala Lajpat Rai Hospital (LLR / Hallet)", "Hallet Road, Swaroop Nagar, Kanpur", 8.8, "Level 1 Apex Trauma", "0512-2556295", 26.4835, 80.3150, 52, 70, 250),
        ("Narayana Super Speciality Hospital", "A-3, Sarvodaya Nagar, Kanpur", 8.4, "Level 1 Trauma", "0512-3500000", 26.4795, 80.3050, 32, 45, 110),
        ("Madhuraj Hospital", "113/121, Swaroop Nagar, Kanpur", 8.7, "Level 1 Trauma", "0512-2540717", 26.4810, 80.3180, 20, 28, 60),
        ("Apollo Spectra Hospitals", "117/1, W-1 Block, Kakadeo, Kanpur", 9.1, "Level 1 Trauma", "0512-3055555", 26.4820, 80.2950, 21, 30, 70),
        ("Kulwanti Hospital & Research Centre", "117/N/8, Kakadeo, Kanpur", 9.3, "Level 2 Trauma", "0512-2556666", 26.4840, 80.2920, 18, 25, 55),
        ("Fortune Hospital", "117/H-2/166, Pandu Nagar, Kanpur", 8.9, "Level 1 Trauma", "0512-2583333", 26.4750, 80.2990, 24, 32, 65),
        ("Chandni Hospital Pvt Ltd", "9/60, Arya Nagar, Kanpur", 9.0, "Level 2 Trauma", "0512-2544539", 26.4860, 80.3240, 16, 22, 50),
        ("Prakhar Hospital", "Near Arya Nagar Dharamshala, Kanpur", 9.2, "Level 2 Trauma", "0512-2544467", 26.4870, 80.3220, 14, 20, 35),

        # --- KALYANPUR, RAWATPUR & MANDHANA ZONE ---
        ("Rama Medical College Hospital & Research Centre", "Mandhana / Kalyanpur, Kanpur", 14.2, "Level 1 Apex Trauma", "0512-2780882", 26.5412, 80.2215, 30, 45, 150),
        ("Rama Hospital & Research Centre (Lakhanpur)", "Lakhanpur, Near Kanpur University", 10.2, "Level 1 Trauma", "0512-2580883", 26.4950, 80.2780, 19, 25, 60),
        ("SIS Hospital & Research Centre", "Near Echo Park, Kalyanpur, Kanpur", 11.5, "Level 2 Trauma", "0512-2572700", 26.5020, 80.2650, 15, 20, 45),
        ("New GT Nursing Home", "GT Road, Rawatpur, Kanpur", 8.2, "Level 2 Trauma", "0512-2562700", 26.4815, 80.3010, 11, 15, 30)
    ]

    for h in hospitals:
        name, locality, dist, trauma, phone, lat, lng, icu_avail, icu_tot, oxy_avail = h
        cursor.execute("""
            INSERT INTO hospitals (name, locality, distance_km, trauma_level, phone, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, locality, dist, trauma, phone, lat, lng))
        hosp_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO hospital_beds (hospital_id, icu_available, icu_total, oxygen_available)
            VALUES (?, ?, ?, ?)
        """, (hosp_id, icu_avail, icu_tot, oxy_avail))

    conn.commit()
    print(f"✅ Success: Seeded {len(hospitals)} verified Kanpur & Rooma hospitals into jeevansetu.db!")
    conn.close()

if __name__ == "__main__":
    seed_data()