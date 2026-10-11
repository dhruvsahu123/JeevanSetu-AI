import sqlite3
import os
import json

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_summary():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM hospitals")
    hosp_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM hospital_beds WHERE bed_type LIKE '%ICU%' AND status = 'Available'")
    icu_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM hospital_beds WHERE bed_type LIKE '%Oxygen%' AND status = 'Available'")
    oxy_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ambulances WHERE current_status != 'Maintenance'")
    amb_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM clinical_conditions")
    cond_cnt = c.fetchone()[0]
    conn.close()
    return {
        "total_facilities": hosp_cnt,
        "available_icu_beds": icu_cnt,
        "available_oxygen_beds": oxy_cnt,
        "active_ambulances": amb_cnt,
        "indexed_protocols": cond_cnt,
        "data_mode": "SYNTHETIC_HYBRID"
    }

get_dashboard_stats = get_dashboard_summary

def fetch_hospitals(search_query=None, tier_filter=None, page=1, limit=15, demo_only=False, q=None, tier=None):
    search_query = q if q is not None else search_query
    tier_filter = tier if tier is not None else tier_filter
    
    offset = (page - 1) * limit
    conn = get_db()
    c = conn.cursor()
    where = ["1=1"]
    params = []
    
    if demo_only:
        where.append("h.is_demo = 1")
    if search_query:
        where.append("(h.name LIKE ? OR h.locality LIKE ? OR h.zone LIKE ?)")
        term = f"%{search_query}%"
        params.extend([term, term, term])
    if tier_filter:
        where.append("h.trauma_tier = ?")
        params.append(tier_filter)
        
    where_sql = " AND ".join(where)
    c.execute(f"SELECT COUNT(*) FROM hospitals h WHERE {where_sql}", params)
    total_count = c.fetchone()[0]
    
    sql = f"""
    SELECT h.hospital_uid, h.name, h.locality, h.zone, h.trauma_tier, h.contact_phone, h.is_demo, h.data_source,
           COALESCE(SUM(CASE WHEN b.bed_type LIKE '%ICU%' AND b.status = 'Available' THEN 1 ELSE 0 END), 0) AS icu_count,
           COALESCE(SUM(CASE WHEN b.bed_type LIKE '%Oxygen%' AND b.status = 'Available' THEN 1 ELSE 0 END), 0) AS oxy_count
    FROM hospitals h
    LEFT JOIN hospital_beds b ON h.hospital_uid = b.hospital_uid
    WHERE {where_sql}
    GROUP BY h.hospital_uid
    ORDER BY h.id ASC
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    c.execute(sql, params)
    rows = c.fetchall()
    
    items = []
    for r in rows:
        items.append({
            "uid": r["hospital_uid"],
            "name": r["name"],
            "area": f"{r['locality']} ({r['zone']})",
            "trauma_tier": r["trauma_tier"],
            "icu": r["icu_count"],
            "oxy": r["oxy_count"],
            "contact": r["contact_phone"],
            "is_demo": bool(r["is_demo"]),
            "data_source": r["data_source"]
        })
    conn.close()
    return {"total": total_count, "page": page, "limit": limit, "items": items}

get_hospitals_data = fetch_hospitals

def fetch_blood_banks(search_query=None, q=None):
    search_query = q if q is not None else search_query
    conn = get_db()
    c = conn.cursor()
    where = "1=1"
    params = []
    if search_query:
        where = "(name LIKE ? OR locality LIKE ? OR zone LIKE ?)"
        term = f"%{search_query}%"
        params = [term, term, term]
        
    c.execute(f"SELECT bank_uid, name, locality, zone, contact_phone, is_demo, data_source FROM blood_banks WHERE {where} LIMIT 50", params)
    banks = c.fetchall()
    results = []
    for b in banks:
        c.execute("SELECT blood_group, units_available FROM blood_stock WHERE bank_uid = ?", (b["bank_uid"],))
        stocks = c.fetchall()
        o_neg = sum(s["units_available"] for s in stocks if s["blood_group"] == "O-")
        platelets = sum(s["units_available"] for s in stocks if s["blood_group"] in ["O+", "A+", "B+"]) // 2
        results.append({
            "uid": b["bank_uid"],
            "name": b["name"],
            "area": f"{b['locality']} ({b['zone']})",
            "contact": b["contact_phone"],
            "o_neg": o_neg,
            "platelets": platelets,
            "is_demo": bool(b["is_demo"]),
            "data_source": b["data_source"]
        })
    conn.close()
    return results

get_blood_banks_data = fetch_blood_banks

def fetch_conditions(search_query=None, category=None, page=1, limit=24, q=None, cat=None):
    search_query = q if q is not None else search_query
    category = cat if cat is not None else category
    
    conn = get_db()
    c = conn.cursor()
    offset = (page - 1) * limit
    where = ["1=1"]
    params = []
    if search_query:
        where.append("(name LIKE ? OR category LIKE ?)")
        term = f"%{search_query}%"
        params.extend([term, term])
    if category:
        where.append("category = ?")
        params.append(category)
        
    where_sql = " AND ".join(where)
    c.execute(f"SELECT COUNT(*) FROM clinical_conditions WHERE {where_sql}", params)
    total_count = c.fetchone()[0]
    
    c.execute(f"""
        SELECT condition_code, name, category, severity_grade, dos_json, donts_json, is_demo, data_source
        FROM clinical_conditions
        WHERE {where_sql}
        ORDER BY id ASC
        LIMIT ? OFFSET ?
    """, params + [limit, offset])
    rows = c.fetchall()
    
    items = []
    for r in rows:
        items.append({
            "code": r["condition_code"],
            "name": r["name"],
            "category": r["category"],
            "severity": r["severity_grade"],
            "dos": json.loads(r["dos_json"]),
            "donts": json.loads(r["donts_json"]),
            "is_demo": bool(r["is_demo"]),
            "data_source": r["data_source"]
        })
    conn.close()
    return {"total": total_count, "page": page, "limit": limit, "items": items}

get_conditions_data = fetch_conditions

def fetch_treatment_pricing(search_query=None, dept=None):
    conn = get_db()
    c = conn.cursor()
    where = ["1=1"]
    params = []
    if search_query:
        where.append("(procedure_name LIKE ? OR pmjay_package_code LIKE ?)")
        term = f"%{search_query}%"
        params.extend([term, term])
    if dept:
        where.append("clinical_department = ?")
        params.append(dept)
    where_sql = " AND ".join(where)
    c.execute(f"SELECT * FROM treatment_pricing WHERE {where_sql} LIMIT 100", params)
    rows = c.fetchall()
    items = [dict(r) for r in rows]
    conn.close()
    return items
