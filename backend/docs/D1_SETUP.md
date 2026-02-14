# Setting Up Cloudflare D1 Database

## What is D1?

Cloudflare D1 is a serverless SQLite database that's fully integrated with Cloudflare Workers. It's ideal for your Ramadan Program Management backend because:
- Built for serverless/edge computing
- Automatic scaling
- Low latency
- Cost-effective

## Setup Steps

### 1. Create a D1 Database

```powershell
uv run pywrangler d1 create ramadan-db
```

This will output something like:
```
✅ Successfully created DB 'ramadan-db'
Created your database using D1's new storage backend.

[[d1_databases]]
binding = "DB"
database_name = "ramadan-db"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### 2. Update wrangler.toml

Copy the output from step 1 and update your [wrangler.toml](./wrangler.toml):

```toml
[[d1_databases]]
binding = "DB"
database_name = "ramadan-db"
database_id = "YOUR-DATABASE-ID-HERE"  # Replace with your actual ID
```

### 3. Create Database Schema

Since you're migrating from PostgreSQL to SQLite (D1), you need to create your tables in D1.

#### Option A: Use SQL Migration File

Create a file `schema.sql` with your database schema (SQLite syntax):

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    gender TEXT,
    age INTEGER,
    phone TEXT,
    email TEXT UNIQUE NOT NULL,
    country TEXT,
    password_hash TEXT,
    role TEXT DEFAULT 'participant',
    status TEXT DEFAULT 'pending',
    member_id INTEGER UNIQUE,
    halqa_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (halqa_id) REFERENCES halqas(id)
);

CREATE TABLE IF NOT EXISTS halqas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    supervisor_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supervisor_id) REFERENCES users(id)
);

-- Add other tables: daily_cards, site_settings, etc.
```

Then execute it:

```powershell
uv run pywrangler d1 execute ramadan-db --file=schema.sql
```

#### Option B: Use SQLAlchemy Migrations (Requires Code Changes)

You'll need to update your code to use SQLite-compatible syntax. Key differences from PostgreSQL:

1. **Auto-increment**: Use `AUTOINCREMENT` instead of PostgreSQL's `SERIAL`
2. **Column types**: SQLite has fewer types (TEXT, INTEGER, REAL, BLOB)
3. **JSON**: SQLite has native JSON support but syntax differs
4. **ALTER TABLE**: More limited in SQLite

### 4. Update Your Code for D1

You'll need to modify your database connection to work with D1:

**In [app/database.py](./app/database.py):**

```python
from workers.runtime.context import runtime

def get_d1_engine():
    """Get D1 database engine when running in Cloudflare Workers"""
    # Check if running in Cloudflare Workers
    if hasattr(runtime, 'env') and hasattr(runtime.env, 'DB'):
        # Use D1 binding
        # Note: D1 uses HTTP API, not direct SQLite connection
        # You may need to use d1-orm or similar adapter
        return create_engine("sqlite:///", creator=lambda: runtime.env.DB)
    else:
        # Local development
        return create_engine("sqlite:///./ramadan_local.db")
```

### 5. Test Locally with SQLite

Before deploying to D1, test with SQLite locally:

```powershell
# Update .env
# DATABASE_URL=sqlite:///./ramadan_local.db

# Run locally
uv run pywrangler dev
```

### 6. Deploy to Cloudflare

```powershell
uv run pywrangler deploy
```

## Common D1 Commands

### View Database Info
```powershell
uv run pywrangler d1 info ramadan-db
```

### Execute SQL
```powershell
uv run pywrangler d1 execute ramadan-db --command="SELECT * FROM users LIMIT 5"
```

### Export Data
```powershell
uv run pywrangler d1 export ramadan-db --output=backup.sql
```

### Import Data
```powershell
uv run pywrangler d1 execute ramadan-db --file=backup.sql
```

## Alternative: Use Hyperdrive with PostgreSQL

If you prefer to keep PostgreSQL, use Cloudflare Hyperdrive:

```powershell
uv run pywrangler hyperdrive create ramadan-postgres `
  --connection-string="postgresql://ramadan_user:your_password@your-host:5432/ramadan_db"
```

Then update [wrangler.toml](./wrangler.toml):

```toml
[[hyperdrive]]
binding = "HYPERDRIVE"
id = "your-hyperdrive-id"
```

And in your code:

```python
# DATABASE_URL will be automatically provided by Hyperdrive
database_url = runtime.env.HYPERDRIVE.connectionString
```

## PostgreSQL to SQLite Migration Tips

### Data Type Mapping:
- `VARCHAR/TEXT` → `TEXT`
- `INTEGER/BIGINT/SERIAL` → `INTEGER`
- `DECIMAL/NUMERIC/DOUBLE PRECISION` → `REAL`
- `TIMESTAMP` → `TEXT` (ISO8601 format) or `INTEGER` (unix timestamp)
- `BOOLEAN` → `INTEGER` (0 or 1)

### Common Issues:
1. **No SERIAL type**: Use `INTEGER PRIMARY KEY AUTOINCREMENT`
2. **No ENUM type**: Use `TEXT` with CHECK constraints
3. **Limited ALTER TABLE**: May need to recreate tables
4. **Case sensitivity**: SQLite is case-insensitive for column names by default

## Environment Variables for D1

In [.env](./.env):
```env
# Local development with SQLite
DATABASE_URL=sqlite:///./ramadan_local.db
```

For Cloudflare Workers, the D1 binding in `wrangler.toml` provides the database connection automatically.

## Resources

- [Cloudflare D1 Documentation](https://developers.cloudflare.com/d1/)
- [D1 Limits](https://developers.cloudflare.com/d1/platform/limits/)
- [SQLite to PostgreSQL differences](https://www.sqlite.org/different.html)
