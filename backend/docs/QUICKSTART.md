# Quick Start: Deploy to Cloudflare Workers

## 1. Install prerequisites

```powershell
# Install uv (Python package manager)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Restart your terminal, then:
cd backend
uv tool install workers-py
```

## 2. Initialize and test locally

```powershell
uv sync
uv run pywrangler dev
```

## 3. Deploy to Cloudflare

```powershell
# Set secrets (run each command and enter the value when prompted)
uv run pywrangler secret put JWT_SECRET_KEY
uv run pywrangler secret put INIT_SECRET
uv run pywrangler secret put SUPER_ADMIN_EMAIL
uv run pywrangler secret put SUPER_ADMIN_PASSWORD

# Deploy
uv run pywrangler deploy
```

## 4. Update frontend

Update the API URL in `frontend/src/utils/api.js` to your Worker URL.

---

**Important**: See [CLOUDFLARE_DEPLOYMENT.md](./CLOUDFLARE_DEPLOYMENT.md) for full documentation including database setup options (D1 or Hyperdrive).
