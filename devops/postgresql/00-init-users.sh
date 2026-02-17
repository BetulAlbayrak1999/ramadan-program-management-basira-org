#!/bin/bash
# Docker entrypoint script for creating PostgreSQL users
# This runs before 01-init.sql in alphabetical order
# Environment variables are provided by docker-compose

set -e

echo "======================================"
echo "Creating PostgreSQL Users"
echo "======================================"

# Validate required environment variables
if [ -z "$APP_USER_PASSWORD" ]; then
    echo "ERROR: APP_USER_PASSWORD environment variable is not set"
    exit 1
fi

if [ -z "$MONITOR_USER_PASSWORD" ]; then
    echo "ERROR: MONITOR_USER_PASSWORD environment variable is not set"
    exit 1
fi

# Create SQL commands with environment variable substitution
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create application user
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'ramadan_app') THEN
            CREATE USER ramadan_app WITH PASSWORD '$APP_USER_PASSWORD';
            RAISE NOTICE 'Created application user: ramadan_app';
        ELSE
            RAISE NOTICE 'Application user ramadan_app already exists';
        END IF;
    END
    \$\$;

    -- Create monitoring user
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'monitor') THEN
            CREATE USER monitor WITH PASSWORD '$MONITOR_USER_PASSWORD';
            RAISE NOTICE 'Created monitoring user: monitor';
        ELSE
            RAISE NOTICE 'Monitoring user monitor already exists';
        END IF;
    END
    \$\$;

    -- Log completion
    SELECT 'User creation completed at ' || NOW() as status;
EOSQL

echo "======================================"
echo "PostgreSQL users created successfully"
echo "======================================"
