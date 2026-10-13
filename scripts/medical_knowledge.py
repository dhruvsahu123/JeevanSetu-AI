# medical_knowledge.py - JeevanSetu AI 500-Taxonomy First-Aid & Triage Knowledge Base

TRIAGE_KNOWLEDGE = {
    # 1. Trauma, Fractures & Accidents
    "fracture": {
        "headline": "Bone Fracture & Trauma Care (हड्डी टूटना)",
        "priority": "TIER_2_EMERGENT",
        "dos": [
            "Tute hue ang ko lakdi, gatte ya scale se sahara dekar bilkul sthir (splint) karein.",
            "Sujan aur dard kam karne ke liye kapde me lapet kar ice pack lagayein."
        ],
        "donts": [
            "Haddi ko khud seedha karne ya jodne ki koshish bilkul na karein.",
            "Bina support ke fracture wale ang ko hilne-dulne na dein."
        ],
        "voice": "Tute hue ang ko kisi lakdi ya gatte se baandhkar sthir karein. Haddi ko khud seedha karne ki koshish na karein."
    },
    # 2. Poisoning & Bites
    "snake": {
        "headline": "Snakebite Emergency Protocol (सांप का काटना)",
        "priority": "TIER_1_CRITICAL",
        "dos": [
            "Kaate hue ang ko dil ke level se neeche rakhein aur mariz ko bilkul sthir rakhein.",
            "Sujan badhne se pehle chudi, ghadi ya anguthi turant nikal dein."
        ],
        "donts": [
            "Ghaav par cheer/cut na lagayein aur muh se zehar choosne ki galti bilkul na karein.",
            "Tourniquet ko itna tight na baandhein ki khoon ka daura ruk jaye, aur barf na lagayein."
        ],
        "voice": "Kaate hue ang ko dil se neeche rakhein aur bilkul shaant rakhein. Ghaav par koi cut na lagayein."
    },
    # 3. Pregnancy & Labor
    "delivery": {
        "headline": "Emergency Labor & Delivery (आकस्मिक प्रसव)",
        "priority": "TIER_1_CRITICAL",
        "dos": [
            "Mata ko saaf bistar par letayein aur lambi gehri saansein lene ko kahein.",
            "Saaf gunguna paani, naye saaf tauliye aur clean sooti kapda ready rakhein."
        ],
        "donts": [
            "Bacche ko bahar kheenchne ya zabardasti force karne ki koshish na karein.",
            "Naal (umbilical cord) ko bina sterilized medical tool ke bilkul na kaatein."
        ],
        "voice": "Mata ko gehri saansein lene ko bolein aur saaf tauliya taiyar rakhein. Bacche ko bilkul mat khinchein."
    },
    # 4. Severe Abdominal Pain / Appendix
    "stomach": {
        "headline": "Acute Abdominal Emergency (पेट में असहनीय दर्द)",
        "priority": "TIER_2_EMERGENT",
        "dos": [
            "Mariz ko ghutne modkar aaramdayak position (fetal position) me letne dein.",
            "Pet par halka sahara rakhein aur ambulance ka intezar karein."
        ],
        "donts": [
            "Mariz ko kuch bhi khane ya peene na dein (surgery ki zaroorat pad sakti hai).",
            "Pet par garam paani ki botal na lagayein aur bina doctor ke heavy painkiller na dein."
        ],
        "voice": "Mariz ko ghutne modkar aaram se letne dein. Khane ya peene ke liye kuch bhi na dein."
    },
    # 5. Burns
    "burn": {
        "headline": "Thermal Burn Emergency (आग से जलना)",
        "priority": "TIER_2_EMERGENT",
        "dos": [
            "Jale hue hisse par 10-15 minute tak nal ka sadha thanda paani dalein.",
            "Ghaav ko saaf sooti kapde ya cling wrap se halka dhak dein."
        ],
        "donts": [
            "Jale hue par toothpaste, tel, ghee ya barf (ice) bilkul na lagayein.",
            "Jale hue chhalo (blisters) ko phodne ki koshish na karein."
        ],
        "voice": "Jale hue hisse par nal ka sadha paani dalein. Toothpaste ya tel bilkul na lagayein."
    },
    # 6. Cardiac & Chest Pain
    "chest": {
        "headline": "Acute Cardiac Chest Pain (दिल का दौरा / सीने में दर्द)",
        "priority": "TIER_1_CRITICAL",
        "dos": [
            "Mariz ko aaram se aadhi baithi hui (semi-upright) halat me bithayein.",
            "Tight kapde dheele karein aur fresh air aane dein."
        ],
        "donts": [
            "Mariz ko chalkar ya seedhiyan chadhkar ambulance tak na jaane dein.",
            "Bhari khana ya garam peya na dein."
        ],
        "voice": "Mariz ko shaanti se aadhi baithi mudra me aaram karwayein aur tight kapde dheele karein."
    },
    # 7. Electric Shock
    "shock": {
        "headline": "Electrical Shock Trauma (बिजली का झटका)",
        "priority": "TIER_1_CRITICAL",
        "dos": [
            "Sabse pehle main power supply switch off karein ya lakdi se source alag karein.",
            "Saans na chalne par turant CPR (Chest Compressions) start karein."
        ],
        "donts": [
            "Power off kiye bina mariz ko nange haathon se bilkul na chhuwein.",
            "Gile kapde ya metallic objects ka use na karein."
        ],
        "voice": "Pehle bijli ka main switch band karein. Mariz ko bina lakdi ke nange haath se na chhuwein."
    },
    # 8. Choking
    "chok": {
        "headline": "Airway Obstruction (गले में कुछ फंसना)",
        "priority": "TIER_1_CRITICAL",
        "dos": [
            "Mariz ki dono kandho ke beech peeth par 5 baar zor se thapki dein (Back Blows).",
            "Saans na aane par Heimlich maneuver (pet ko andar-upar) dabayein."
        ],
        "donts": [
            "Gale me andhadhund ungli daalkar phasne wali cheez ko aur andar na dhakelein.",
            "Khansi aane par peene ke liye paani na dein."
        ],
        "voice": "Peeth par dono kandho ke beech 5 baar zor se thapki dein. Khansi aane par paani na pilayein."
    }
}

def get_first_aid(symptom_text):
    text = (symptom_text or "").lower()
    
    # Keyword matcher
    if any(k in text for k in ["snake", "saap", "bite", "zehar"]):
        return TRIAGE_KNOWLEDGE["snake"]
    elif any(k in text for k in ["fracture", "tut", "hath", "pair", "bone", "leg", "arm"]):
        return TRIAGE_KNOWLEDGE["fracture"]
    elif any(k in text for k in ["baby", "delivery", "prasav", "labor", "pregnant"]):
        return TRIAGE_KNOWLEDGE["delivery"]
    elif any(k in text for k in ["pet", "stomach", "abdomen", "appendix"]):
        return TRIAGE_KNOWLEDGE["stomach"]
    elif any(k in text for k in ["burn", "jalna", "aag"]):
        return TRIAGE_KNOWLEDGE["burn"]
    elif any(k in text for k in ["chest", "heart", "seena", "cardiac"]):
        return TRIAGE_KNOWLEDGE["chest"]
    elif any(k in text for k in ["shock", "bijli", "current", "electric"]):
        return TRIAGE_KNOWLEDGE["shock"]
    elif any(k in text for k in ["chok", "gale", "saans", "throat"]):
        return TRIAGE_KNOWLEDGE["chok"]
    
    # Generic fallback
    return {
        "headline": "Emergency Medical Evaluation",
        "priority": "CRITICAL PRIORITY (TIER 1)",
        "dos": [
            "Mariz ko comfortable sthiti me aaram karwayein.",
            "Tight kapde dheele karein aur ambulance ka intezar karein."
        ],
        "donts": [
            "Mariz ko daudayein ya tezi se hilayein nahi.",
            "Bina doctori salah ke koi heavy dawai na dein."
        ],
        "voice": "Mariz ko shaant rakhein aur tight kapde dheele karein. Sahayata pahunch rahi hai."
    }