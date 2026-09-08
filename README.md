# 🚑 JeevanSetu AI: Intelligent Emergency Healthcare & Triage Grid

> **Next-Generation Emergency Response System** bridging citizens, ambulance telemetry, hospital trauma bays, and AI-assisted clinical triage in real time.

---

## 📌 Executive Summary
In critical trauma and acute cardiac emergencies, every minute lost in triage ambiguity or hospital bed unavailability lowers survival chances significantly. **JeevanSetu AI** solves this by establishing a zero-latency telemetry and coordination bridge:
- **Instant AI Triage**: Evaluates patient symptoms and suggests clinical department tiers before hospital arrival using Gemini AI.
- **Live ICU & Bed Synchronization**: Two-way synchronization between regional trauma hubs and central dispatchers.
- **Citizen 1-Click SOS Beacon**: Instant broadcast pipeline routing patient cases directly to hospital casualty consoles.
- **Ambulance Telemetry**: Real-time transit speed, ETA countdown, and in-cabin vitals telemetry stream.

---

## 🏗️ System Architecture

```text
       [ Citizen Portal ]                [ Ambulance Unit ]
        (customer-dashboard)             (ambulance-tracking)
                 │                                │
                 ▼                                ▼
       ┌──────────────────────────────────────────────────┐
       │             Flask REST API Backend               │
       │               ([https://jeevansetu-ai-7e5y.onrender.com](https://jeevansetu-ai-7e5y.onrender.com))            │
       └──────────────┬───────────────────┬───────────────┘
                      │                   │
                      ▼                   ▼
           ┌──────────────────┐   ┌──────────────────────┐
           │ SQLite Database  │   │ Gemini AI Engine     │
           │ (jeevansetu.db)  │   │ (Clinical Triage)    │
           └──────────────────┘   └──────────────────────┘
                      │
                      ▼
            [ Hospital Console ]
           (hospital-dashboard)