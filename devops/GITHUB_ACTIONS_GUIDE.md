# GitHub Actions Deployment Workflows

This document explains how to use the GitHub Actions workflows for deploying the Ramadan Program Management System.

## 📋 Overview

We have **two separate workflows**:

1. **`deploy-app.yml`** - Deploys the application (Frontend + Backend)
   - ✅ Runs **automatically** when you push to `master` branch
   - ✅ Can also be triggered **manually** from GitHub Actions UI
   
2. **`deploy-postgres.yml`** - Deploys PostgreSQL database  
   - ⚠️ Runs **ONLY MANUALLY** (never automatic)
   - Requires confirmation to prevent accidental deployments

---

## 🔐 GitHub Secrets Setup

Before using the workflows, you **MUST** configure these secrets in your GitHub repository:

### Navigate to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

### Required Secrets:

#### SSH Connection
| Secret Name | Description | Example |
|------------|-------------|---------|
| `SSH_HOST` | Server IP or hostname | `123.45.67.89` |
| `SSH_USER` | SSH username | `root` |
| `SSH_PRIVATE_KEY` | Private SSH key for authentication | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

#### Database
| Secret Name | Description | How to Generate |
|------------|-------------|-----------------|
| `DATABASE_URL` | Full PostgreSQL connection URL | `postgresql://ramadan_app:PASSWORD@postgres:5432/ramadan_db` |
| `POSTGRES_PASSWORD` | PostgreSQL admin password | `openssl rand -base64 32` |
| `APP_USER_PASSWORD` | Application database user password | `openssl rand -base64 32` |
| `MONITOR_USER_PASSWORD` | Monitor user password | `openssl rand -base64 32` |

#### JWT & Security
| Secret Name | Description | How to Generate |
|------------|-------------|-----------------|
| `JWT_SECRET_KEY` | JWT token signing key | `openssl rand -hex 32` |

#### Email
| Secret Name | Description | Example |
|------------|-------------|---------|
| `MAIL_USERNAME` | SMTP email username | `your-email@gmail.com` |
| `MAIL_PASSWORD` | SMTP email password/app password | For Gmail: use App Password |

#### Admin Account
| Secret Name | Description |
|------------|-------------|
| `SUPER_ADMIN_EMAIL` | Super admin email |
| `SUPER_ADMIN_PASSWORD` | Super admin password (min 16 chars) |

---

## 🔧 GitHub Variables Setup (Optional)

These have sensible defaults but can be customized:

### Navigate to: `Settings` → `Secrets and variables` → `Actions` → `Variables` tab → `New repository variable`

| Variable Name | Default Value | Description |
|--------------|---------------|-------------|
| `POSTGRES_DB` | `ramadan_db` | Database name |
| `JWT_ACCESS_TOKEN_EXPIRES` | `2592000` | Token expiry (seconds, 30 days) |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USE_TLS` | `true` | Enable TLS |
| `ENABLE_EMAIL_NOTIFICATIONS` | `true` | Enable email notifications |

---

## 🚀 Usage Guide

### 1. Deploy Application (Automatic or Manual)

#### Automatic Deployment
Simply push to the `master` branch:
```bash
git add .
git commit -m "Your changes"
git push origin master
```

The workflow will automatically:
1. ✅ Pull latest code on the server
2. ✅ Create `.env` file with all secrets
3. ✅ Build and deploy with Docker Compose
4. ✅ Verify the deployment

#### Manual Deployment
1. Go to **GitHub** → **Actions** → **Deploy Application to Production**
2. Click **Run workflow** → **Run workflow** button
3. Wait for completion

### 2. Deploy PostgreSQL (Manual Only)

⚠️ **WARNING**: This can delete your database if you choose to recreate volumes!

#### Steps:
1. Go to **GitHub** → **Actions** → **Deploy PostgreSQL Database (Manual Only)**
2. Click **Run workflow**
3. Fill in the inputs:
   - **Confirmation**: Type exactly `deploy-postgres`
   - **Recreate volumes**: 
     - ❌ `false` (default) - Keep existing data (safe)
     - ⚠️ `true` - DELETE all data and recreate (dangerous!)
4. Click **Run workflow** button
5. Wait for completion

#### When to Use Each Option:

| Recreate Volumes | Use Case | Data Loss |
|-----------------|----------|-----------|
| ❌ **false** | Update PostgreSQL configuration<br>Restart container<br>Apply schema changes | ✅ No data loss |
| ⚠️ **true** | First-time setup<br>Complete database reset<br>Corrupted data recovery | ❌ **ALL DATA DELETED** |

---

## 📁 Server Directory Structure

The workflows assume this structure on your server:

```
/opt/ramadan-program/ramadan-program-management-basira-org/
├── .env                          # Created by deploy-app.yml
├── docker-compose.yml            # Application deployment
├── frontend/                     # React app
├── backend/                      # FastAPI app
└── devops/
    ├── .env                      # Created by deploy-postgres.yml
    ├── docker-compose.postgres.yml
    └── postgresql/
        ├── 00-init-users.sh
        ├── init.sql
        ├── pg_hba.conf
        └── postgresql.conf
```

---

## 🐳 Docker Containers

After deployment, you should have:

| Container Name | Purpose | Port | Network |
|---------------|---------|------|---------|
| `ramadan_app` | Frontend + Backend | `127.0.0.1:8000` | `ramadan_network` |
| `ramadan_postgres` | PostgreSQL 16 | `127.0.0.1:5432` | `ramadan_network` |

---

## 🔍 Monitoring & Troubleshooting

### Check Deployment Status
- **GitHub**: Go to **Actions** tab to see workflow runs
- **Email**: GitHub will email you if a deployment fails

### SSH into Server for Manual Checks

```bash
# SSH into server
ssh -p 199 your-user@your-server

# Navigate to project
cd /opt/ramadan-program/ramadan-program-management-basira-org

# Check running containers
docker ps

# View application logs
docker logs ramadan_app -f

# View PostgreSQL logs
docker logs ramadan_postgres -f

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Common Issues

#### 1. Application won't start
```bash
# Check logs
docker logs ramadan_app --tail 50

# Check if database is accessible
docker exec ramadan_app ping postgres

# Restart application
docker compose up -d --force-recreate
```

#### 2. PostgreSQL connection issues
```bash
# Check PostgreSQL is running
docker ps | grep ramadan_postgres

# Test connection
docker exec ramadan_postgres pg_isready -U postgres

# Check database users
docker exec ramadan_postgres psql -U postgres -d ramadan_db -c "\du"
```

#### 3. Static files not loading (Frontend)
```bash
# Check if build exists
docker exec ramadan_app ls -la /app/frontend/build/

# Rebuild and force recreate
docker compose up -d --build --force-recreate
```

#### 4. Environment variables not applied
```bash
# Check .env file exists and has correct permissions
ls -la .env
cat .env  # Verify content

# Restart container
docker compose restart
```

---

## 🔄 Deployment Flow

### Application Deployment Flow:
```
Push to master
    ↓
GitHub Actions triggered
    ↓
SSH to server
    ↓
Pull latest code
    ↓
Create .env with secrets
    ↓
docker compose up -d --build --force-recreate
    ↓
Health check
    ↓
✅ Success / ❌ Failure notification
```

### PostgreSQL Deployment Flow:
```
Manual trigger from GitHub Actions
    ↓
Confirm "deploy-postgres"
    ↓
SSH to server
    ↓
Pull latest code
    ↓
Stop existing PostgreSQL
    ↓
[Optional] Recreate volumes (DELETE DATA)
    ↓
Create .env with DB secrets
    ↓
docker compose -f docker-compose.postgres.yml up -d
    ↓
Wait for PostgreSQL ready
    ↓
Verify users and connections
    ↓
✅ Success / ❌ Failure notification
```

---

## 📊 Environment Configuration

### Production Environment

Both workflows use the `production` environment. You can configure environment-specific settings:

1. Go to **Settings** → **Environments** → **production**
2. Add required reviewers if you want manual approval before deployment
3. Add environment-specific secrets/variables

---

## 🔒 Security Best Practices

1. ✅ **Never commit `.env` files** - They're in `.gitignore`
2. ✅ **Use strong passwords** - At least 20 characters for database passwords
3. ✅ **Rotate secrets regularly** - Update GitHub secrets periodically
4. ✅ **Use SSH keys** - Never use password authentication
5. ✅ **Restrict SSH access** - Use firewall rules and key-based auth only
6. ✅ **Monitor logs** - Check deployment logs regularly
7. ✅ **Backup database** - Before using `recreate_volumes: true`

---

## 📞 Support

If you encounter issues:

1. Check the **Actions** tab for workflow logs
2. SSH into server and check container logs
3. Review this documentation
4. Check Docker network: `docker network inspect ramadan_network`

---

## 🎯 Quick Reference

| Action | Command |
|--------|---------|
| Deploy app automatically | Push to `master` branch |
| Deploy app manually | GitHub Actions → Deploy Application → Run workflow |
| Deploy PostgreSQL | GitHub Actions → Deploy PostgreSQL → Type "deploy-postgres" → Run |
| View app logs | `docker logs ramadan_app -f` |
| View DB logs | `docker logs ramadan_postgres -f` |
| Restart app | `docker compose restart` |
| Rebuild app | `docker compose up -d --build --force-recreate` |
| Check health | `docker ps --format "table {{.Names}}\t{{.Status}}"` |

---

**Last Updated**: February 2026  
**Version**: 1.0  
**Maintained By**: DevOps Team
