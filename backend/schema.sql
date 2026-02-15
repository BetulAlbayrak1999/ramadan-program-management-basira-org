-- D1 Database Schema for Ramadan Program Management
-- This file recreates all tables with the correct schema
-- Run with: wrangler d1 execute ramadan-db --remote --file=schema.sql

-- Drop existing tables (in correct order due to foreign keys)
DROP TABLE IF EXISTS daily_cards;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS halqas;
DROP TABLE IF EXISTS site_settings;

-- Create halqas table (must be created before users due to foreign key)
CREATE TABLE IF NOT EXISTS halqas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
    supervisor_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supervisor_id) REFERENCES users(id)
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('participant', 'supervisor', 'admin', 'super_admin')),
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'suspended', 'pending', 'rejected', 'withdrawn')),
    phone TEXT,
    member_id INTEGER UNIQUE,
    supervisor_id INTEGER,
    halqa_id INTEGER,
    gender TEXT,
    age INTEGER,
    country TEXT,
    referral_source TEXT,
    rejection_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supervisor_id) REFERENCES users(id),
    FOREIGN KEY (halqa_id) REFERENCES halqas(id)
);

-- Create daily_cards table (NEW SCHEMA with updated fields)
CREATE TABLE IF NOT EXISTS daily_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    user_id INTEGER NOT NULL,
    quran REAL DEFAULT 0,
    tadabbur REAL DEFAULT 0,
    duas REAL DEFAULT 0,
    taraweeh REAL DEFAULT 0,
    tahajjud REAL DEFAULT 0,
    duha REAL DEFAULT 0,
    rawatib REAL DEFAULT 0,
    main_lesson REAL DEFAULT 0,
    enrichment_lesson REAL DEFAULT 0,
    charity_worship REAL DEFAULT 0,
    extra_work REAL DEFAULT 0,
    extra_work_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date)
);

-- Create site_settings table
CREATE TABLE IF NOT EXISTS site_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enable_email_notifications INTEGER DEFAULT 1
);

-- Insert default site settings
INSERT INTO site_settings (enable_email_notifications) VALUES (1);

-- Note: Super admin user will be created by the application on first run
-- or you can manually insert it here if needed
-- The application uses environment variables: SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD