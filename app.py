import os
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, abort

app = Flask(__name__)

# Base path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Health Check API
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "JeevanSetu-AI"}), 200

# Root Route: Serves index.html
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Universal Dynamic Route Handler for frontend pages, subfolders, CSS and JS
@app.route('/<path:path>')
def serve_files(path):
    # 1. Exact path match in frontend
    direct_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(direct_path) and os.path.isfile(direct_path):
        return send_from_directory(FRONTEND_DIR, path)

    # 2. Match direct filename inside frontend subdirectories (pages, triage, inventory, etc.)
    target_filename = os.path.basename(path)
    for root, dirs, files in os.walk(FRONTEND_DIR):
        if target_filename in files:
            return send_from_directory(root, target_filename)

    # 3. Match filename without .html extension (e.g. /hospital-dashboard -> hospital-dashboard.html)
    if not target_filename.endswith('.html'):
        target_html = target_filename + '.html'
        for root, dirs, files in os.walk(FRONTEND_DIR):
            if target_html in files:
                return send_from_directory(root, target_html)

    # 4. Fallback if 404 page exists
    fallback_404 = os.path.join(FRONTEND_DIR, '404.html')
    if os.path.exists(fallback_404):
        return send_from_directory(FRONTEND_DIR, '404.html'), 404

    abort(404)

if __name__ == '__main__':
    app.run(debug=True, port=5000)