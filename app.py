# -------------------------------------------------------------
# 3. HOSPITALS & BED MANAGEMENT
# -------------------------------------------------------------
@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    conn = get_db_connection()
    query = '''
        SELECT h.id, h.name, h.locality, h.distance_km, h.trauma_level, h.phone, h.lat, h.lng,
               b.icu_available, b.icu_total, b.oxygen_available
        FROM hospitals h
        LEFT JOIN hospital_beds b ON h.id = b.hospital_id
    '''
    rows = conn.execute(query).fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "name": r["name"],
            "location": r["locality"],
            "distanceKm": r["distance_km"],
            "traumaLevel": r["trauma_level"],
            "phone": r["phone"],
            "lat": r["lat"],
            "lng": r["lng"],
            "icuAvailable": r["icu_available"] if r["icu_available"] is not None else 0,
            "totalIcu": r["icu_total"] if r["icu_total"] is not None else 0,
            "oxygenBeds": r["oxygen_available"] if r["oxygen_available"] is not None else 0
        })
    return jsonify(results), 200