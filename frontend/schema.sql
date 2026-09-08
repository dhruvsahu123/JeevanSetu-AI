-- =============================================================
-- JEEVANSETU AI - Production MySQL Database Schema
-- Version: 1.0 (Relational Architecture for Emergency Triage)
-- =============================================================

CREATE DATABASE IF NOT EXISTS jeevansetu_db;
USE jeevansetu_db;

-- -------------------------------------------------------------
-- 1. USERS & AUTHENTICATION (Patients, Hospitals, Drivers, Admins)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('PATIENT', 'HOSPITAL', 'AMBULANCE', 'ADMIN') NOT NULL DEFAULT 'PATIENT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- 2. PATIENT PROFILE & EMERGENCY TELEMETRY METADATA
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'),
    age INT,
    gender ENUM('MALE', 'FEMALE', 'OTHER'),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    medical_allergies TEXT,
    chronic_conditions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- 3. HOSPITALS & CRITICAL CARE RESOURCE TRACKER
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(160) NOT NULL,
    address TEXT NOT NULL,
    locality VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    trauma_level TINYINT DEFAULT 2, -- Level 1, 2, 3
    emergency_desk_phone VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- 4. REAL-TIME BED INVENTORY (ICU, Oxygen, General)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospital_beds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    bed_type ENUM('ICU', 'OXYGEN', 'VENTILATOR', 'GENERAL_TRAUMA') NOT NULL,
    total_beds INT DEFAULT 0,
    available_beds INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    UNIQUE KEY (hospital_id, bed_type)
);

-- -------------------------------------------------------------
-- 5. AMBULANCE FLEETS & ACTIVE UNITS
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ambulances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    driver_user_id INT NOT NULL,
    vehicle_number VARCHAR(30) UNIQUE NOT NULL,
    fleet_type ENUM('ALS', 'BLS', 'NEONATAL') NOT NULL DEFAULT 'BLS',
    current_latitude DECIMAL(10, 7),
    current_longitude DECIMAL(10, 7),
    operational_status ENUM('AVAILABLE', 'DISPATCHED', 'IN_TRANSIT', 'OFF_DUTY') DEFAULT 'AVAILABLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- -------------------------------------------------------------
-- 6. EMERGENCY DISPATCH PIPELINE & AI TRIAGE SCORING
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS emergency_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    assigned_hospital_id INT,
    assigned_ambulance_id INT,
    triage_priority ENUM('TIER_1_CRITICAL', 'TIER_2_URGENT', 'TIER_3_STABLE') NOT NULL,
    primary_symptom VARCHAR(120),
    pickup_latitude DECIMAL(10, 7) NOT NULL,
    pickup_longitude DECIMAL(10, 7) NOT NULL,
    status ENUM('INITIATED', 'AMBULANCE_DISPATCHED', 'BED_RESERVED', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED') DEFAULT 'INITIATED',
    patient_spo2 VARCHAR(10),
    patient_pulse VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_ambulance_id) REFERENCES ambulances(id) ON DELETE SET NULL
);

-- -------------------------------------------------------------
-- 7. INITIAL SEED DATA (Mock Hospitals & Beds for Testing)
-- -------------------------------------------------------------
-- 1. Insert Hospital Users
INSERT INTO users (id, full_name, email, phone, password_hash, role)
VALUES 
(1, 'Apex Emergency Admin', 'admin@apextrauma.org', '9876543210', 'scrypt:32768:8:1$hashedpassword', 'HOSPITAL'),
(2, 'Metro Care Admin', 'contact@metroheart.org', '9876543211', 'scrypt:32768:8:1$hashedpassword', 'HOSPITAL');

-- 2. Insert Hospitals
INSERT INTO hospitals (id, user_id, name, address, locality, latitude, longitude, trauma_level, emergency_desk_phone)
VALUES 
(1, 1, 'Apex Emergency & Trauma Institute', 'Civil Lines Central', 'Civil Lines', 26.4499, 80.3319, 1, '+91-512-2550101'),
(2, 2, 'Metro Heart & Critical Care Hub', 'Swaroop Nagar Bypass', 'Swaroop Nagar', 26.4712, 80.3120, 2, '+91-512-2550102');

-- 3. Insert Real-Time Bed Matrix
INSERT INTO hospital_beds (hospital_id, bed_type, total_beds, available_beds)
VALUES 
(1, 'ICU', 16, 4),
(1, 'OXYGEN', 24, 12),
(1, 'VENTILATOR', 8, 3),
(2, 'ICU', 10, 2),
(2, 'OXYGEN', 15, 8),
(2, 'VENTILATOR', 5, 1);