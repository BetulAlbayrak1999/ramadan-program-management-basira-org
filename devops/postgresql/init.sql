-- Database initialization script
-- This script runs only on first container startup
-- Note: Users are created by 00-init-users.sh before this script
-- Security: Configures privileges for application and monitoring users

-- Note: The main database ramadan_db is already created by POSTGRES_DB environment variable
-- Connect to the database
\c ramadan_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set timezone
SET timezone = 'UTC';

-- ============================================
-- PRIVILEGE MANAGEMENT
-- ============================================

-- Grant necessary privileges to application user (ramadan_app)
GRANT CONNECT ON DATABASE ramadan_db TO ramadan_app;
GRANT USAGE, CREATE ON SCHEMA public TO ramadan_app;

-- Grant table privileges (for existing and future tables)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ramadan_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ramadan_app;

-- Grant sequence privileges (for auto-increment IDs)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ramadan_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ramadan_app;

-- Grant monitoring privileges to monitor user (read-only access to statistics)
GRANT CONNECT ON DATABASE ramadan_db TO monitor;
GRANT pg_monitor TO monitor;

-- ============================================
-- PERFORMANCE MONITORING VIEWS
-- ============================================

-- Active connections view
CREATE OR REPLACE VIEW active_connections AS
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    backend_start,
    state,
    query,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE state != 'idle'
  AND pid != pg_backend_pid()
ORDER BY backend_start;

-- Grant view access to monitor user
GRANT SELECT ON active_connections TO monitor;

-- Database size monitoring view
CREATE OR REPLACE VIEW database_size_info AS
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'ramadan_db';

GRANT SELECT ON database_size_info TO monitor;

-- ============================================
-- SECURITY SETTINGS
-- ============================================

-- Revoke public schema privileges from PUBLIC role for security
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- Ensure application user owns the public schema
ALTER SCHEMA public OWNER TO ramadan_app;

-- ============================================
-- PERFORMANCE OPTIMIZATIONS
-- ============================================

-- Enable parallel query execution for the application user
ALTER USER ramadan_app SET max_parallel_workers_per_gather = 3;

-- Set reasonable statement timeout (30 seconds) to prevent long-running queries
ALTER USER ramadan_app SET statement_timeout = '30s';

-- Log completion with timestamp
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Database initialization completed at %', NOW();
    RAISE NOTICE 'Database: ramadan_db';
    RAISE NOTICE 'Application user: ramadan_app (for backend connection)';
    RAISE NOTICE 'Monitoring user: monitor (for health checks)';
    RAISE NOTICE 'Admin user: postgres (for administrative tasks)';
    RAISE NOTICE '================================================';
END
$$;
