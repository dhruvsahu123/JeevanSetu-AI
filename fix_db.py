import sqlite3
import os

found = False
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith(('.db', '.sqlite', '.sqlite3')):
            db_path = os.path.join(root, file)
            print(f'Database mil gayi: {db_path}')
            found = True
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cols = [
                    ('icu_beds', 'INTEGER DEFAULT 0'),
                    ('oxygen_beds', 'INTEGER DEFAULT 0'),
                    ('active_ventilators', 'INTEGER DEFAULT 0'),
                    ('emergency_contact', 'TEXT'),
                    ('location', 'TEXT')
                ]
                for col_name, col_type in cols:
                    try:
                        cursor.execute(f'ALTER TABLE hospitals ADD COLUMN {col_name} {col_type};')
                        print(f'  + Column add ho gaya: {col_name}')
                    except Exception as e:
                        print(f'  - Skip: {col_name} ({e})')
                conn.commit()
                conn.close()
                print('Database update complete!')
            except Exception as e:
                print(f'DB error: {e}')

if not found:
    print('Koi bhi .db file nahi mili.')
