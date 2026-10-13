import requests
import sys

BASE_URL = 'http://127.0.0.1:5000'

def test_endpoint(name, url, method='GET', data=None):
    try:
        if method == 'GET':
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=data, timeout=5)
        
        if r.status_code in [200, 201]:
            print(f'✅ [PASS] {name} (HTTP {r.status_code})')
            return True
        else:
            print(f'❌ [FAIL] {name} (HTTP {r.status_code}): {r.text[:80]}')
            return False
    except Exception as e:
        print(f'❌ [ERR]  {name}: {str(e)}')
        return False

print("="*55)
print("🚑 JEEVANSETU AI - CLINICAL SYSTEM HEALTH CHECK")
print("="*55)

tests = [
    ('Landing Page UI', f'{BASE_URL}/', 'GET', None),
    ('Hospital Bed Grid API', f'{BASE_URL}/api/beds', 'GET', None),
    ('ER Queue Live Feed', f'{BASE_URL}/api/er/queue', 'GET', None),
    ('Traffic Corridors API', f'{BASE_URL}/api/traffic/corridors', 'GET', None),
    ('Command Analytics API', f'{BASE_URL}/api/analytics/summary', 'GET', None),
    ('Trauma Audit Logs API', f'{BASE_URL}/api/audit/logs', 'GET', None),
    ('Rare Blood Matcher (AB-)', f'{BASE_URL}/api/blood/match', 'POST', {'blood_group': 'AB-', 'units_needed': 2}),
    ('En-Route Vitals Relay', f'{BASE_URL}/api/teleconsult/vitals', 'POST', {'heart_rate': 110, 'spo2': 88}),
    ('Cost Estimator Engine', f'{BASE_URL}/api/cost/estimate', 'POST', {'procedure_key': 'CARDIAC_PCI', 'hospital_tier': 'PRIVATE'})
]

passed = 0
for name, url, m, d in tests:
    if test_endpoint(name, url, m, d):
        passed += 1

print("="*55)
print(f'System Score: {passed}/{len(tests)} Endpoints Verified')
print("="*55)
