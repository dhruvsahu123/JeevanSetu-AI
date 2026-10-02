# 🚑 JeevanSetu AI (जीवनसेतु)
> **AI-Orchestrated Emergency Response & Hospital Bed Telemetry Network**  
> *Optimized for Critical Care & Highway Trauma Response across Kanpur & Rooma NH-19 Corridor.*

[![Live Web Application](https://img.shields.io/badge/Live-Demo_Online-brightgreen?style=for-the-badge&logo=render)](https://dhruvsahu123.github.io/JeevanSetu-AI/)
[![Backend Status](https://img.shields.io/badge/Backend-Render_Cloud-blue?style=for-the-badge&logo=fastapi)](https://jeevansetu-ai-7e5y.onrender.com/api/health)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

## 🌟 The Problem
During severe highway trauma or cardiac emergencies along regional corridors, patients lose critical "Golden Hour" minutes due to:
1. Lack of real-time ICU/Oxygen bed availability data.
2. Uncoordinated ambulance dispatches leading to hospital bouncing.
3. Language and communication barriers during high-panic triage calls.

## 💡 The Solution
**JeevanSetu AI** bridges the communication divide between citizens, ambulance fleets, and emergency rooms:
- **Satellite GPS Tracking & Live Map:** Uses browser geolocation and Haversine spatial algorithms to calculate real road distance to 26+ verified medical institutions.
- **Multilingual AI Voice Triage:** Powered by Google Gemini API & Web Speech recognition for natural language symptom evaluation in Hindi and English.
- **HMS Bed Inventory Sliders:** Hospital ER staff adjust ICU/ventilator beds in real-time, syncing immediately with public-facing maps.
- **Emergency QR Health ID:** Portable medical passport storing blood group, chronic conditions, and guardian contacts for unconscious casualties.
- **WhatsApp Live Coordinate Dispatch:** One-tap guardian alerting transmitting precise Google Maps pin coordinates.
- **Offline PWA Engine:** Service Worker caching guarantees emergency hotlines and navigation remain accessible in low-connectivity areas.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 Modern Flex/Grid, Vanilla ES6+ JavaScript, Leaflet.js |
| **Backend API** | Python, Flask, Flask-CORS, Google GenAI SDK |
| **Database** | SQLite3 with Automated Schema Seeding |
| **Intelligence** | Google Gemini 2.5 Flash clinical prompt orchestration |
| **Deployment** | GitHub Pages (Frontend), Render Cloud (Backend Web Service) |

---

## 🚀 Key Modules & Entry Points

- **Public Emergency Grid:** `frontend/index.html`
- **Hospital Control Desk:** `frontend/hospital-dashboard.html`
- **Ambulance Live Telemetry:** `frontend/ambulance-tracking.html`
- **Citizen Health Vault & QR:** `frontend/customer-dashboard.html`
- **Public Emergency Medical Scan ID:** `frontend/emergency-card.html`

---

## 💻 Local Setup & Execution

```bash
# 1. Clone the repository
git clone [https://github.com/dhruvsahu123/JeevanSetu-AI.git](https://github.com/dhruvsahu123/JeevanSetu-AI.git)
cd JeevanSetu-AI

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Seed verified Kanpur hospital dataset
python seed_kanpur_hospitals.py

# 4. Start local Flask backend
python app.py