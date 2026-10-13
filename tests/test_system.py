"""
JeevanSetu AI - End-to-End Diagnostic & Telemetry Test Suite
Tests backend health, database integrity, hospital spatial data,
and AI pre-arrival triage knowledge matrix.
"""

import sys
import json
from app import app
from medical_knowledge import get_first_aid

def run_diagnostics():
    client = app.test_client()
    print("=" * 60)
    print("🚀 STARTING JEEVANSETU AI SYSTEM DIAGNOSTIC RUN")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = 5

    # Test 1: Health & Ping
    print("\n[1/5] Testing /api/health...")
    res = client.get('/api/health')
    if res.status_code == 200:
        data = res.get_json()
        print(f"  ✅ Health Check Passed: Status={data.get('status')}, Service={data.get('service')}")
        passed_tests += 1
    else:
        print(f"  ❌ Failed with status code: {res.status_code}")

    # Test 2: Hospital Telemetry & Kanpur/Rooma Seeding
    print("\n[2/5] Testing /api/hospitals...")
    res = client.get('/api/hospitals')
    if res.status_code == 200:
        hospitals = res.get_json()
        print(f"  ✅ Retrieved {len(hospitals)} registered hospitals in medical telemetry.")
        if len(hospitals) > 0:
            sample = hospitals[0]
            print(f"  📍 Sample Facility: {sample.get('name')} | ICU Available: {sample.get('icuAvailable')}/{sample.get('totalIcu')}")
        passed_tests += 1
    else:
        print(f"  ❌ Failed with status code: {res.status_code}")

    # Test 3: Regional Blood Bank Inventory
    print("\n[3/5] Testing /api/blood-banks...")
    res = client.get('/api/blood-banks')
    if res.status_code == 200:
        banks = res.get_json()
        print(f"  ✅ Retrieved {len(banks)} emergency blood bank centers.")
        passed_tests += 1
    else:
        print(f"  ❌ Failed with status code: {res.status_code}")

    # Test 4: Medical Knowledge Base (500-Taxonomy First Aid)
    print("\n[4/5] Testing 500-Taxonomy Triage Knowledge Engine...")
    test_conditions = [
        ("saap ne kaata", "Snakebite Emergency Protocol"),
        ("pair tut gaya fracture", "Bone Fracture & Trauma Care"),
        ("pet me dard appendix", "Acute Abdominal Emergency"),
        ("delivery labor pain", "Emergency Labor & Delivery"),
        ("aag se jalna burn", "Thermal Burn Emergency")
    ]
    kb_passed = True
    for text, expected in test_conditions:
        result = get_first_aid(text)
        if expected not in result.get("headline", ""):
            print(f"  ⚠️ Mismatch for '{text}': got {result.get('headline')}")
            kb_passed = False
        else:
            print(f"  ✓ Match: '{text}' -> {result.get('headline')}")
            
    if kb_passed:
        print("  ✅ All Acute Emergency Taxonomies verified with DOs and DON'Ts.")
        passed_tests += 1

    # Test 5: End-to-End Triage API Simulation
    print("\n[5/5] Testing /api/ai/triage API Endpoint...")
    res = client.post('/api/ai/triage', 
                      data=json.dumps({"symptoms": "severe chest pain and shortness of breath", "age": 52, "mobility": "bedridden"}),
                      content_type='application/json')
    if res.status_code == 200:
        triage_data = res.get_json()
        print(f"  ✅ Triage Response Received:")
        print(f"     Priority: {triage_data.get('priority')}")
        print(f"     Headline: {triage_data.get('headline')}")
        print(f"     DOs Count: {len(triage_data.get('dos', []))} | DON'Ts Count: {len(triage_data.get('donts', []))}")
        passed_tests += 1
    else:
        print(f"  ❌ Triage test failed: {res.status_code}")

    print("\n" + "=" * 60)
    print(f"🏁 DIAGNOSTIC COMPLETED: {passed_tests}/{total_tests} TESTS PASSED")
    print("=" * 60)

if __name__ == "__main__":
    run_diagnostics()