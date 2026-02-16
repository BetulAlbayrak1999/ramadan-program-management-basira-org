# Ramadan Program Management - Production Deployment Guide

## 🚀 Overview

This guide covers the complete deployment process for the Ramadan Program Management System with:

- **Separate PostgreSQL and Application containers**
- **Cloudflare Tunnel integration**
- **Secure user separation** (postgres admin, ramadan_app backend, monitor health)
- **Optimized for 12GB RAM, 6 CPU cores, 100GB SSD**

---

## 📋 Prerequisites

1. Docker & Docker Compose installed
2. Cloudflare account with tunnel configured
3. Server with minimum 12GB RAM, 6 CPU cores, 100GB SSD
4. Domain name configured in Cloudflare

---

## 🔐 Security Architecture

### Database Users:

1. **postgres** (superuser) - Administrative tasks only, never used by application
2. **ramadan_app** - Backend application user with restricted privileges
3. **monitor** - Read-only user for health checks and monitoring

### Network Security:

- PostgreSQL: Bound to `127.0.0.1:5432` (localhost only)
- Application: Bound to `127.0.0.1:8000` (localhost only)
- Cloudflare Tunnel: Connects to `127.0.0.1:8000` and exposes to internet

---

## 📁 Directory Structure

```
ramadan-program-management-basira-org/
├── .env                          # Application environment variables (CREATE THIS)
├── docker-compose.yml            # Application container
├── Dockerfile                    # Application image
├── devops/
│   ├── .env                      # PostgreSQL environment variables (CREATE THIS)
│   ├── docker-compose.postgres.yml
│   └── postgresql/
│       ├── 00-init-users.sh      # User creation script
│       ├── 01-init.sql            # Database initialization
│       ├── postgresql.conf        # Optimized for your server
│       └── pg_hba.conf            # Authentication rules
└── backend/                      # Application code
```

---

## ⚙️ Step 1: Environment Configuration

### 1.1 Configure PostgreSQL Environment

```bash
cd devops
cp .env.example .env
```

Edit `devops/.env` with strong passwords:

```bash
# Database name
POSTGRES_DB=ramadan_db

# Admin password (for 'postgres' superuser)
POSTGRES_PASSWORD=your_strong_admin_password_here_min_20_chars

# Application password (for 'ramadan_app' user - used by backend)
APP_USER_PASSWORD=your_strong_app_password_here_min_20_chars

# Monitor password (for 'monitor' user - health checks)
MONITOR_USER_PASSWORD=your_monitor_password_here_min_16_chars
```

**🔒 Security Tips:**

- Use different passwords for each user
- Minimum 20 characters for production passwords
- Generate strong passwords: `openssl rand -base64 32`

### 1.2 Configure Application Environment

```bash
cd ..  # Back to root directory
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Database connection - USE THE SAME APP_USER_PASSWORD from devops/.env
DATABASE_URL=postgresql://ramadan_app:YOUR_APP_PASSWORD_HERE@postgres:5432/ramadan_db
POSTGRES_DB=ramadan_db
APP_USER_PASSWORD=YOUR_APP_PASSWORD_HERE  # Same as devops/.env

# JWT Secret - Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your_generated_jwt_secret_key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Email configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password

# Super Admin account (created on first startup)
SUPER_ADMIN_EMAIL=admin@yourdomain.com
SUPER_ADMIN_PASSWORD=your_admin_password

# Notifications
ENABLE_EMAIL_NOTIFICATIONS=true
```

**⚠️ CRITICAL:** The `APP_USER_PASSWORD` in root `.env` MUST match the `APP_USER_PASSWORD` in `devops/.env`

### 1.3 Secure Environment Files

```bash
# Restrict permissions (Linux/Mac)
chmod 600 .env
chmod 600 devops/.env

# Verify .gitignore includes .env files
cat .gitignore | grep ".env"
```

---

## 🐳 Step 2: Docker Network Setup

Create the shared network for containers to communicate:

```bash
docker network create ramadan_network
```

Verify:

```bash
docker network ls | grep ramadan_network
```

---

## 🗄️ Step 3: Start PostgreSQL Database

### 3.1 Start PostgreSQL Container

```bash
cd devops
docker-compose -f docker-compose.postgres.yml up -d
```

### 3.2 Verify PostgreSQL is Running

```bash
# Check container status
docker ps | grep ramadan_postgres

# Check logs for initialization
docker logs ramadan_postgres

# You should see:
# ✅ "Created application user: ramadan_app"
# ✅ "Created monitoring user: monitor"
# ✅ "Database initialization completed"
```

### 3.3 Verify Database Users

```bash
# Connect as admin
docker exec -it ramadan_postgres psql -U postgres -c "\du"
docker exec -it ramadan_postgres psql -U postgres -c "\l"


# You should see:
# - postgres (superuser)
# - ramadan_app (with limited privileges)
# - monitor (with monitoring privileges)

```

### 3.4 Test Application User Connection

```bash
# Test ramadan_app user can connect
docker exec -it ramadan_postgres psql -U ramadan_app -d ramadan_db -c "SELECT current_user, current_database();"

# Should output:
#  current_user | current_database
# --------------+------------------
#  ramadan_app  | ramadan_db
```

**🔴 If this fails, check:**

1. APP_USER_PASSWORD is correct in `devops/.env`
2. Check logs: `docker logs ramadan_postgres`
3. Ensure `00-init-users.sh` is executable: `chmod +x devops/postgresql/00-init-users.sh`

---

## 🚀 Step 4: Start Application Container

### 4.1 Build and Start Application

```bash
cd ..  # Back to root directory
docker-compose up -d --build
```

### 4.2 Verify Application is Running

```bash
# Check container status
docker ps | grep ramadan_app

# Check logs
docker logs ramadan_app -f

# You should see:
# ✅ "Super admin created: admin@yourdomain.com"
# ✅ Uvicorn running on http://0.0.0.0:8000
```

### 4.3 Test Application Health

```bash
# Test from server
curl http://127.0.0.1:8000/

# Test database connectivity
docker logs ramadan_app | grep "database\|connection"
```

**🔴 If connection fails:**

1. Verify PostgreSQL is running: `docker ps | grep postgres`
2. Check if both containers are on the same network:
   ```bash
   docker inspect ramadan_app | grep ramadan_network
   docker inspect ramadan_postgres | grep ramadan_network
   ```
3. Verify DATABASE_URL in root `.env` uses `ramadan_app` user
4. Check APP_USER_PASSWORD matches between both `.env` files---

## 🔍 Step 5: Verification & Testing

### 6.1 Complete System Check

```bash
# 1. Check all containers are running
docker ps

# Should see:
# - ramadan_postgres (healthy)
# - ramadan_app (healthy)

# 2. Check health status
docker inspect ramadan_postgres | grep -A 5 Health
docker inspect ramadan_app | grep -A 5 Health

# 3. Check application logs
docker logs ramadan_app --tail 50

# 4. Check database logs
docker logs ramadan_postgres --tail 50

# 5. Test endpoints
curl http://127.0.0.1:8000/
curl https://yourdomain.com/
```

### 6.2 Database Connection Test

```bash
# Test from application container
docker exec ramadan_app python3 -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT current_user, version()'))
    print(result.fetchone())
"
```

Should output: `('ramadan_app', 'PostgreSQL 16.x ...')`

### 6.3 Monitor Performance

```bash
# PostgreSQL monitoring
docker exec -it ramadan_postgres psql -U monitor -d ramadan_db -c "SELECT * FROM active_connections;"

# Application logs
docker logs ramadan_app -f --tail 100

# System resources
docker stats
```

---

## 📊 Step 6: Monitoring & Maintenance

### 7.1 Daily Health Checks

```bash
# Container status
docker ps -a

# Disk usage
df -h
docker system df

# Database size
docker exec -it ramadan_postgres psql -U monitor -d ramadan_db -c "SELECT * FROM database_size_info;"

# Active connections
docker exec -it ramadan_postgres psql -U monitor -d ramadan_db -c "SELECT count(*) FROM active_connections;"
```

### 7.2 Log Management

```bash
# View logs
docker logs ramadan_app --tail 100
docker logs ramadan_postgres --tail 100

# Follow logs in real-time
docker logs ramadan_app -f

# Clear old logs (if needed)
docker logs ramadan_app --tail 1000 > app_backup.log
```

### 7.3 Backup Database

```bash
# Create backup directory
mkdir -p ~/backups

# Backup database
docker exec ramadan_postgres pg_dump -U postgres ramadan_db > ~/backups/ramadan_db_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker exec ramadan_postgres pg_dump -U postgres ramadan_db | gzip > ~/backups/ramadan_db_$(date +%Y%m%d_%H%M%S).sql.gz

# Automated daily backup (crontab)
crontab -e
# Add: 0 2 * * * docker exec ramadan_postgres pg_dump -U postgres ramadan_db | gzip > ~/backups/ramadan_db_$(date +\%Y\%m\%d).sql.gz
```

### 7.4 Restore Database

```bash
# Stop application
docker-compose down

# Restore from backup
cd devops
docker exec -i ramadan_postgres psql -U postgres ramadan_db < ~/backups/ramadan_db_20260215.sql

# Or from compressed backup
gunzip -c ~/backups/ramadan_db_20260215.sql.gz | docker exec -i ramadan_postgres psql -U postgres ramadan_db

# Restart application
cd ..
docker-compose up -d
```

---

## 🔄 Step 8: Updates & Maintenance

### 8.1 Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Check logs
docker logs ramadan_app -f
```

### 8.2 Update PostgreSQL Configuration

If you need to modify PostgreSQL settings:

```bash
# Edit configuration
nano devops/postgresql/postgresql.conf

# Restart PostgreSQL
cd devops
docker-compose -f docker-compose.postgres.yml restart

# Verify changes
docker exec -it ramadan_postgres psql -U postgres -c "SHOW shared_buffers;"
```

### 8.3 Database Migrations

If schema changes are needed:

```bash
# Connect as application user
docker exec -it ramadan_postgres psql -U ramadan_app -d ramadan_db

# Run migration SQL
-- Your migration SQL here
```

---

## 🚨 Troubleshooting

### Issue: Application can't connect to database

**Symptoms:**

- Application logs show "connection refused"
- Health check fails

**Solutions:**

```bash
# 1. Verify PostgreSQL is running
docker ps | grep postgres

# 2. Check both containers are on same network
docker network inspect ramadan_network

# 3. Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
# Should be: postgresql://ramadan_app:password@postgres:5432/ramadan_db

# 4. Test connection
docker exec ramadan_app ping postgres

# 5. Check PostgreSQL accepts connections
docker exec ramadan_postgres psql -U ramadan_app -d ramadan_db -c "SELECT 1;"
```

### Issue: "password authentication failed for user ramadan_app"

**Cause:** Password mismatch between `.env` files

**Solution:**

```bash
# 1. Verify passwords match
grep APP_USER_PASSWORD .env
grep APP_USER_PASSWORD devops/.env

# 2. If passwords don't match, update both files
nano .env
nano devops/.env

# 3. Reset database user password
docker exec -it ramadan_postgres psql -U postgres -d ramadan_db -c "ALTER USER ramadan_app WITH PASSWORD 'new_password';"

# 4. Restart application
docker-compose restart
```

### Issue: Cloudflare tunnel not accessible

**Symptoms:**

- Domain doesn't resolve
- Connection timeout

**Solutions:**

```bash
# 1. Check tunnel status
cloudflared tunnel info ramadan-app
sudo systemctl status cloudflared

# 2. Check DNS records
cloudflared tunnel route dns list

# 3. Verify application is listening
curl http://127.0.0.1:8000/

# 4. Check tunnel logs
sudo journalctl -u cloudflared -f

# 5. Restart tunnel
sudo systemctl restart cloudflared
```

### Issue: High database connections

**Symptoms:**

- "too many connections" error
- Slow performance

**Solutions:**

```bash
# 1. Check active connections
docker exec -it ramadan_postgres psql -U monitor -d ramadan_db -c "SELECT count(*) FROM active_connections;"

# 2. Check max connections
docker exec -it ramadan_postgres psql -U postgres -c "SHOW max_connections;"

# 3. If needed, kill idle connections
docker exec -it ramadan_postgres psql -U postgres -d ramadan_db -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'ramadan_db' 
  AND state = 'idle' 
  AND state_change < NOW() - INTERVAL '10 minutes';
"

# 4. Consider implementing connection pooling (PgBouncer)
```

---

## 📈 Performance Optimization

### Current Configuration (12GB RAM, 6 CPU):

- `shared_buffers`: 3GB (25% of RAM)
- `effective_cache_size`: 9GB (75% of RAM)
- `max_connections`: 300
- `max_worker_processes`: 6
- `max_parallel_workers`: 6

### If you upgrade server resources:

Edit `devops/postgresql/postgresql.conf`:

```properties
# For 16GB RAM:
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 5MB

# For 8 CPU cores:
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

Then restart PostgreSQL:

```bash
cd devops
docker-compose -f docker-compose.postgres.yml restart
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` files** - They contain sensitive credentials
2. **Use strong passwords** - Minimum 20 characters for production
3. **Regular backups** - Daily automated backups
4. **Monitor access** - Check `active_connections` view regularly
5. **Keep software updated** - Update Docker images monthly
6. **Firewall rules** - Only allow connections from Cloudflare IPs
7. **SSL/TLS** - Cloudflare provides SSL automatically
8. **Fail2ban** - Consider installing for SSH brute-force protection

---

## 📞 Support & Maintenance

### Log Locations:

- Application: `docker logs ramadan_app`
- PostgreSQL: `docker logs ramadan_postgres`
- Cloudflare: `sudo journalctl -u cloudflared`

### Important Files:

- `.env` - Application configuration
- `devops/.env` - Database configuration
- `/etc/cloudflared/config.yml` - Tunnel configuration

### Regular Maintenance Schedule:

- **Daily**: Check logs, monitor disk space
- **Weekly**: Review database size, check backups
- **Monthly**: Update Docker images, security patches
- **Quarterly**: Review performance metrics

---

## ✅ Deployment Checklist

Before going live, verify:

- [ ] PostgreSQL container is running and healthy
- [ ] Application container is running and healthy
- [ ] All three database users created (postgres, ramadan_app, monitor)
- [ ] Application connects using `ramadan_app` user, not admin
- [ ] Environment variables configured correctly
- [ ] Strong passwords set for all accounts
- [ ] Cloudflare tunnel configured and running
- [ ] Domain resolves correctly
- [ ] HTTPS works (via Cloudflare)
- [ ] Super admin can log in
- [ ] Email notifications working
- [ ] Backup cron job configured
- [ ] Monitoring in place
- [ ] `.env` files secured (chmod 600)
- [ ] `.env` files NOT in git

---

**🎉 Deployment Complete!**

Your Ramadan Program Management System is now running securely with:

- ✅ Separate database and application users
- ✅ Optimized PostgreSQL for your server specs
- ✅ Cloudflare Tunnel for secure public access
- ✅ Health monitoring and logging
- ✅ Automated backups

Access your application at: **https://yourdomain.com**
