import sqlite3

DB_NAME = "jeevansetu.db"

def seed_medical():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Core high-priority clinical dataset (ICD-10 mapped)
    diseases = [
        ("I21.9", "Acute Myocardial Infarction", "Cardiovascular", "chest pain, left arm radiation, profuse sweating, dyspnea", "CRITICAL", "Aspirin 300mg chewable, high-flow O2, cath-lab priority transfer", "Cardiologist"),
        ("I63.9", "Acute Ischemic Stroke", "Neurological", "facial drop, hemiparesis, slurred speech, sudden loss of balance", "CRITICAL", "Golden Hour protocol (<4.5h), non-contrast CT head, IV thrombolysis", "Neurologist"),
        ("J45.901", "Severe Acute Asthma / Status Asthmaticus", "Respiratory", "wheezing, severe dyspnea, blue lips, chest tightness, tripod positioning", "CRITICAL", "Nebulized Salbutamol + Ipratropium, IV hydrocortisone, high-flow O2", "Pulmonologist"),
        ("A01.0", "Typhoid Fever (Enteric)", "Infectious", "step-ladder fever, abdominal pain, bradycardia, rose spots", "MODERATE", "Blood cultures, Ceftriaxone / Azithromycin, aggressive fluid resuscitation", "General Physician"),
        ("E11.65", "Diabetic Ketoacidosis (DKA)", "Endocrine", "Kussmaul breathing, fruity breath, dehydration, high blood glucose", "CRITICAL", "Regular insulin IV infusion, isotonic saline rehydration, potassium correction", "Endocrinologist"),
        ("K35.80", "Acute Appendicitis", "Gastroenterology", "periumbilical to RLQ migrating pain, McBurney tenderness, vomiting", "MODERATE", "NPO status, IV broad-spectrum antibiotics, emergency appendectomy", "General Surgeon"),
        ("S06.9", "Traumatic Brain Injury (TBI)", "Trauma", "concussion, unequal pupils, amnesia, clear fluid from nose/ears", "CRITICAL", "C-spine stabilization, immediate non-contrast head CT, ICP monitoring", "Neurosurgeon"),
        ("A90", "Dengue Hemorrhagic Fever", "Infectious", "high-grade continuous fever, retro-orbital pain, thrombocytopenia, petechiae", "CRITICAL", "Hematocrit monitoring, isotonic crystalloid titration, avoid NSAIDs", "Internal Medicine"),
        ("J18.9", "Community-Acquired Pneumonia", "Respiratory", "productive rusty sputum cough, pleuritic chest pain, fever, crackles", "MODERATE", "Empiric Beta-lactam + Macrolide, supplemental oxygenation", "Pulmonologist"),
        ("K25.9", "Acute Peptic Ulcer Perforation", "Gastroenterology", "sudden board-like rigid abdomen, burning epigastric pain, hematemesis", "CRITICAL", "Immediate surgical exploratory laparotomy, IV PPI, IV fluids", "General Surgeon")
    ]

    medicines = [
        ("Disprin / Ecosprin", "Aspirin", "Antiplatelet", "Tablet", "75mg / 150mg / 300mg", "Acute coronary syndrome, ischemic stroke prevention", "Active GI bleeding, hemophilia", 0),
        ("Asthalin", "Salbutamol", "Beta-2 Agonist", "Inhaler / Respules", "100mcg / 2.5mg", "Bronchospasm, acute asthma, COPD exacerbations", "Severe cardiac arrhythmia", 1),
        ("Calpol / Dolo", "Paracetamol", "Antipyretic / Analgesic", "Tablet / IV Infusion", "500mg / 650mg / 1g", "Pyrexia, acute mild-to-moderate pain", "Severe hepatic impairment", 0),
        ("Pantocid", "Pantoprazole", "Proton Pump Inhibitor", "Tablet / IV Injection", "40mg", "Acid peptic disease, stress ulcer prophylaxis", "Hypersensitivity to PPIs", 0),
        ("Monocef", "Ceftriaxone", "Cephalosporin (3rd Gen)", "IV / IM Injection", "1g / 2g", "Bacterial meningitis, severe sepsis, pneumonia", "Concurrent IV calcium solutions in neonates", 1),
        ("Adrenaline / EpiPen", "Epinephrine", "Sympathomimetic", "Ampoule / Auto-Injector", "1:1000 (1mg/mL)", "Anaphylactic shock, cardiopulmonary arrest", "No absolute contraindications in cardiac arrest", 1),
        ("Atorva", "Atorvastatin", "Statin / Lipid-lowering", "Tablet", "10mg / 20mg / 40mg", "Dyslipidemia, acute post-MI plaque stabilization", "Active hepatic failure, pregnancy", 1),
        ("Augmentin", "Amoxicillin + Clavulanate", "Penicillin + Beta-lactamase Inhibitor", "Tablet / IV", "625mg / 1.2g", "Bacterial respiratory infections, skin/soft tissue infections", "History of penicillin-induced cholestatic jaundice", 1)
    ]

    cursor.executemany("""
        INSERT INTO diseases (icd_code, disease_name, category, symptoms_keywords, severity_level, emergency_protocol, recommended_specialist)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, diseases)

    cursor.executemany("""
        INSERT INTO medicines (brand_name, generic_name, drug_class, dosage_form, standard_strength, primary_indications, contraindications, prescription_required)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, medicines)

    conn.commit()
    conn.close()
    print("✅ Clinical knowledge base (Diseases & Formulations) successfully seeded!")

if __name__ == "__main__":
    seed_medical()
