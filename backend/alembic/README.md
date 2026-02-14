# Alembic Database Migrations

This directory contains Alembic configuration for managing database schema migrations.

## Setup

Alembic is already configured and ready to use. The migration framework is set up with:
- `alembic.ini` - Main configuration file
- `alembic/env.py` - Migration environment setup
- `alembic/versions/` - Directory for migration scripts

## Usage

### Generate a New Migration

Auto-generate a migration based on model changes:
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

### Apply Migrations

Apply all pending migrations:
```bash
cd backend
alembic upgrade head
```

### Rollback Migrations

Rollback the last migration:
```bash
cd backend
alembic downgrade -1
```

### View Migration History

Show current migration version:
```bash
cd backend
alembic current
```

Show migration history:
```bash
cd backend
alembic history
```

## Notes

- The framework automatically imports all models from `app/models/`
- Database URL is read from `app/config.py` settings
- Migrations work with both PostgreSQL and SQLite (D1)
- Always review auto-generated migrations before applying them

## For Cloudflare Deployment

Database initialization is handled differently for Cloudflare Workers:
- Initial setup via `/system/initialize-database` endpoint
- Startup code moved to `app/initialization.py`
- Automatic initialization via cron trigger (yearly check)

For traditional server deployments, the commented startup code in `main.py` can be restored.
