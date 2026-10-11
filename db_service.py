import sqlite3
import json

DB_FILE = "database.db"

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        r = cur.fetchall()
        return (r[0] if r else None) if one else r
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return [] if not one else None
    finally:
        conn.close()

def get_hospitals_data(q=None, tier=None, page=1, limit=25):
    offset = (page - 1) * limit
    params = []
    where_clauses = ["1=1"]
    
    if q:
        where_clauses.append("(h.name LIKE ? OR h.locality LIKE ? OR h.zone LIKE ?)")
        term = f"%{q}%"
        params.extend([term, term, term])
    if tier:
        where_clauses.append("h.trauma_tier = ?")
        params.append(tier)
        
    where_sql = " AND ".join(where_clauses)
    
    count_sql = f"SELECT COUNT(*) as count FROM hospitals h WHERE {where_sql}"
    total_row = query_db(count_sql, params, one=True)
    total_count = total_row["count"] if total_row else 0
    
    sql = f"""
    SELECT h.hospital_uid, h.name, h.locality, h.zone, h.trauma_tier, h.contact_phone, h.is_demo, h.data_source,
           COALESCE(SUM(CASE WHEN b.bed_type LIKE '%ICU%' AND b.status = 'Available' THEN 1 ELSE 0 END), 0) AS icu_available,
           COALESCE(SUM(CASE WHEN b.bed_type LIKE '%Oxygen%' AND b.status = 'Available' THEN 1 ELSE 0 END), 0) AS oxy_available
    FROM hospitals h
    LEFT JOIN hospital_beds b ON h.hospital_uid = b.hospital_uid
    WHERE {where_sql}
    GROUP BY h.hospital_uid
    LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    rows = query_db(sql, params)
    
    results = []
    for r in rows:
        results.append({
            "uid": r["hospital_uid"],
            "name": r["name"],
            "area": f"{r['locality']} ({r['zone']})",
            "trauma_tier": r["trauma_tier"],
            "icu": r["icu_available"],
            "oxy": r["oxy_available"],
            "contact": r["contact_phone"],
            "is_demo": bool(r["is_demo"]),
            "data_source": r["data_source"]
        })
    return {"total": total_count, "page": page, "limit": limit, "items": results}

def get_blood_banks_data(q=None):
    where_clauses = ["1=1"]
    params = []
    if q:
        where_clauses.append("(name LIKE ? OR locality LIKE ? OR zone LIKE ?)")
        term = f"%{q}%"
        params.extend([term, term, term])
        
    where_sql = " AND ".join(where_clauses)
    sql = f"SELECT bank_uid, name, locality, zone, contact_phone, is_demo, data_source FROM blood_banks WHERE {where_sql} LIMIT 50"
    banks = query_db(sql, params)
    
    results = []
    for b in banks:
        stock_rows = query_db("SELECT blood_group, component_type, units_available FROM blood_stock WHERE bank_uid = ?", [b["bank_uid"]])
        o_neg = sum(s["units_available"] for s in stock_rows if s["blood_group"] == "O-")
        platelets = sum(s["units_available"] for s in stock_rows if "Platelets" in s["component_type"] or "SDP" in s["component_type"])
        
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
    return results

def get_conditions_data(q=None, category=None, page=1, limit=30):
    offset = (page - 1) * limit
    params = []
    where_clauses = ["1=1"]
    if q:
        where_clauses.append("(name LIKE ? OR category LIKE ?)")
        term = f"%{q}%"
        params.extend([term, term])
    if category:
        where_clauses.append("category = ?")
        params.append(category)
        
    where_sql = " AND ".join(where_clauses)
    total_row = query_db(f"SELECT COUNT(*) as count FROM clinical_conditions WHERE {where_sql}", params, one=True)
    total_count = total_row["count"] if total_row else 0
    
    sql = f"SELECT condition_code, name, category, severity_grade, dos_json, donts_json, is_demo, data_source FROM clinical_conditions WHERE {where_sql} LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = query_db(sql, params)
    
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
    return {"total": total_count, "page": page, "limit": limit, "items": items}

def get_dashboard_stats():
    hosp_cnt = query_db("SELECT COUNT(*) as cnt FROM hospitals", one=True)["cnt"]
    bed_icu = query_db("SELECT COUNT(*) as cnt FROM hospital_beds WHERE bed_type LIKE '%ICU%' AND status = 'Available'", one=True)["cnt"]
    bed_oxy = query_db("SELECT COUNT(*) as cnt FROM hospital_beds WHERE bed_type LIKE '%Oxygen%' AND status = 'Available'", one=True)["cnt"]
    amb_cnt = query_db("SELECT COUNT(*) as cnt FROM ambulances WHERE current_status != 'Maintenance'", one=True)["cnt"]
    cond_cnt = query_db("SELECT COUNT(*) as cnt FROM clinical_conditions", one=True)["cnt"]
    
    return {
        "total_facilities": hosp_cnt,
        "available_icu_beds": bed_icu,
        "available_oxygen_beds": bed_oxy,
        "active_ambulances": amb_cnt,
        "indexed_protocols": cond_cnt,
        "data_mode": "SYNTHETIC_HYBRID"
    }
