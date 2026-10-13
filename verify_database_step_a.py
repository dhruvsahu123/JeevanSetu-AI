import sqlite3
import os

DB_FILE = "database.db" if os.path.exists("database.db") else "jeevansetu.db"
print(f"=== VERIFYING DATABASE: {DB_FILE} ===")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

tables_expected = {
    'hospitals': 100,
    'hospital_beds': 1000,
    'doctors': 500,
    'ambulances': 50,
    'blood_banks': 100,
    'blood_stock': 800,
    'clinical_conditions': 1000,
    'medicines': 500,
    'synthetic_patients': 200,
    'emergency_incidents': 200,
    'treatment_pricing': 100,
    'diagnostic_centres': 100
}

all_passed = True
for table, min_expected in tables_expected.items():
    c.execute(f"SELECT COUNT(*) FROM {table} WHERE is_demo = 1 AND data_source = 'SYNTHETIC'")
    synthetic_count = c.fetchone()[0]

    c.execute(f"SELECT COUNT(*) FROM {table} WHERE is_demo = 0")
    live_count = c.fetchone()[0]

    status = "OK" if synthetic_count >= min_expected else "FAIL"
    print(f"[{status}] Table '{table:<22}': Synthetic Demo={synthetic_count:<5} (Expected: {min_expected}) | Live Records={live_count}")
    if synthetic_count < min_expected:
        all_passed = False

# Foreign key integrity check
c.execute("PRAGMA foreign_key_check;")
fk_errors = c.fetchall()
if not fk_errors:
    print("[OK] Foreign Key constraints: 100% Valid (Zero Orphaned Records)")
else:
    print(f"[FAIL] Foreign Key violations detected: {len(fk_errors)}")
    all_passed = False

conn.close()

if all_passed:
    print("\n>>> STEP A DATABASE INTEGRITY: 100% VERIFIED & PASSED <<<")
else:
    print("\n>>> STEP A VERIFICATION FAILED <<<")
