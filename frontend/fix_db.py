import sqlite3
import os

# Project ke andar saari .db / .sqlite files dhund kar update karega
found = False
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith((".db", ".sqlite", ".sqlite3")):
            db_path = os.path.join(root, file)
            print(f"Database mil gayi: {db_path}")
            found = True
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                columns = [
                    ("icu_beds", "INTEGER DEFAULT 0"),
                    ("oxygen_beds", "INTEGER DEFAULT 0"),
                    ("active_ventilators", "INTEGER DEFAULT 0"),
                    ("emergency_contact", "TEXT"),
                    ("location", "TEXT")
                ]
                
                for col_name, col_type in columns:
                    try:
                        cursor.execute(f"ALTER TABLE hospitals ADD COLUMN {col_name} {col_type};")
                        print(f"  + Added column: {col_name}")
                    except Exception as e:
                        print(f"  - Skipped {col_name}: {e}")
                        
                conn.commit()
                conn.close()
                print("Database successfully updated!\n")
            except Exception as e:
                print(f"Database open karne me error: {e}")

if not found:
    print("Project me koi bhi .db ya .sqlite file nahi mili.")