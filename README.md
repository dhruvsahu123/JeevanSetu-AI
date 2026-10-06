# make_readme.py - Auto-generates SIH documentation

content = """# 🚑 JeevanSetu AI (जीवनसेतु)
### Intelligent Emergency Healthcare Grid, Bed Telemetry & Pre-Arrival Triage
*Developed for Smart India Hackathon (SIH) | Aligned with ABDM*

[![Live Portal](https://img.shields.io/badge/Live_Portal-Active-emerald?style=for-the-badge)](https://dhruvsahu123.github.io/JeevanSetu-AI/)
[![Cloud API](https://img.shields.io/badge/Cloud_API-Render_Active-blue?style=for-the-badge)](https://jeevansetu-ai-7e5y.onrender.com/api/health)

---

## 📌 Problem Statement
During highway accidents and acute medical crises along the **Kanpur & Rooma NH-19 corridor**, patients frequently lose their lives during the **Golden Hour** due to:
1. **Hospital Bouncing:** Lack of verified real-time ICU and oxygen bed availability.
2. **First-Aid Panic Errors:** Attendants making lethal mistakes before ambulance arrival (e.g. cutting snakebites, moving fractures).
3. **Casuality Delays:** 15-20 minutes lost in manual ER registration paperwork.

---

## 🌟 Key SIH Innovations
- **🛣️ OSRM Highway Routing:** Real-time road corridor polyline & driving ETA on Leaflet maps.
- **🎙️ Multilingual AI Voice Triage:** Hindi/English voice input with Google Gemini 2.5 Flash.
- **⚠️ Pre-Arrival First-Aid (DOs & DON'Ts):** Instant life-saving instructions spoken aloud via Text-to-Speech.
- **⚡ 110 BPM CPR Metronome:** Web Audio API generating precise acoustic rhythm for chest compressions.
- **🎫 Digital ER Gate Pass:** Zero-paperwork pre-admission token (#JS-EM-KAN-2026) for casualty desks.
- **🩸 Blood Bank Inventory:** Real-time rare blood units tracking (O-, AB-, etc.).
- **📶 Offline PWA:** Service Worker caching for highway low-connectivity zones.

---

## 🛠 Tech Stack
- **Frontend:** HTML5, CSS3 Grid, Vanilla ES6+ JavaScript, Leaflet.js
- **Audio/Speech:** Web Audio API, Web Speech API (SpeechRecognition & SpeechSynthesis)
- **Backend:** Python (Flask), Flask-CORS, REST APIs
- **AI/ML:** Google Gemini 2.5 Flash SDK (`google-genai`)
- **Database:** SQLite3 with automated Kanpur/Rooma hospital seeding
- **Deployment:** GitHub Pages (Frontend) + Render Cloud (Backend)

---

## 👥 Team
- **Lead Developer:** Dhruv Sahu
- **Institution:** Axis Colleges, Kanpur
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ README.md successfully ban gayi hai!")