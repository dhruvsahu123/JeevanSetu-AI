import sqlite3
import json
from app import app

def run_tests():
    print("=" * 50)
    print("JEEVANSETU AI - PHASE 21.5 VERIFICATION SUITE")
    print("=" * 50)

    # 1. Database Schema Check
    conn = sqlite3.connect('jeevansetu.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients';")
    patient_table = cursor.fetchone()
    assert patient_table is not None, "Failed: 'patients' table does not exist in jeevansetu.db"
    print(" [PASS] 1. SQLite 'patients' table exists")

    # Ensure a test user exists
    cursor.execute("SELECT id FROM users WHERE id = 1;")
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (id, full_name, email, phone, password_hash, role) VALUES (1, 'Test Patient', 'test@jeevansetu.in', '9876543210', 'dummyhash', 'PATIENT');")
        conn.commit()
    conn.close()

    client = app.test_client()

    # 2. Existing Route Non-regression Check
    res_health = client.get('/api/health')
    assert res_health.status_code == 200, f"Failed: /api/health returned {res_health.status_code}"
    print(" [PASS] 2. Baseline API (/api/health) is functional")

    # 3. GET Profile Endpoint Test
    res_get = client.get('/api/patient/profile/1')
    assert res_get.status_code == 200, f"Failed: GET /api/patient/profile/1 returned {res_get.status_code}"
    data_get = json.loads(res_get.data)
    assert data_get.get('status') == 'success', "Failed: status is not success"
    print(" [PASS] 3. GET /api/patient/profile/1 responds successfully")

    # 4. POST/PUT Update Profile Endpoint Test
    payload = {
        "blood_group": "B+",
        "age": 24,
        "gender": "MALE",
        "emergency_contact_name": "Emergency Relative",
        "emergency_contact_phone": "+91-9988776655",
        "medical_allergies": "Penicillin",
        "chronic_conditions": "Mild Asthma"
    }
    res_post = client.post('/api/patient/profile/1', data=json.dumps(payload), content_type='application/json')
    assert res_post.status_code == 200, f"Failed: POST /api/patient/profile/1 returned {res_post.status_code}"
    print(" [PASS] 4. POST /api/patient/profile/1 updates record successfully")

    # 5. Persisted Data Round-trip Verification
    res_verify = client.get('/api/patient/profile/1')
    data_verify = json.loads(res_verify.data)['profile']
    assert data_verify['blood_group'] == "B+", "Failed: blood_group not persisted"
    assert data_verify['medical_allergies'] == "Penicillin", "Failed: allergies not persisted"
    print(" [PASS] 5. Round-trip data persistence verified")

    print("\n All Phase 21.5 verifications passed successfully!")

if __name__ == '__main__':
    run_tests()
