# Frontend Deployment to Cloudflare Pages

## Prerequisites

1. **Cloudflare Account**: Sign up at https://dash.cloudflare.com
2. **Wrangler CLI**: Install globally
   ```bash
   npm install -g wrangler
   ```
3. **Authentication**: Login to Cloudflare
   ```bash
   wrangler login
   ```

## Quick Deployment Steps

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Install Dependencies (First Time Only)
```bash
npm install
```

### 3. Configure Environment Variables in Cloudflare Dashboard

**IMPORTANT:** React environment variables (REACT_APP_*) must be set in Cloudflare Pages Dashboard, NOT in wrangler.toml.

#### Steps to Set Environment Variables:

1. Go to Cloudflare Dashboard: https://dash.cloudflare.com
2. Navigate to: **Pages** > **ramadan-platform-frontend** > **Settings** > **Environment variables**
3. Click **Add variable**
4. Add the following variable:
   - **Variable name:** `REACT_APP_API_URL`
   - **Value:** `https://ramadan-program-backend.it-basirah.workers.dev/api`
   - **Environment:** Select both **Production** and **Preview**
5. Click **Save**
6. Redeploy your site for changes to take effect

**Note:** For local development, create `.env` file from `.env.example` template.

### 4. Deploy to Cloudflare Pages

**Option A: Quick Deploy**
```bash
npm run deploy
```

**Option B: Production Deploy**
```bash
npm run deploy:production
```

**Option C: Staging Deploy**
```bash
npm run deploy:staging
```

**Option D: Manual Deploy**
```bash
npm run build
wrangler pages deploy build --project-name=ramadan-platform-frontend
```

## First Time Deployment

On first deployment, Cloudflare will:
1. Create a new Pages project
2. Assign a default URL: `https://ramadan-platform-frontend.pages.dev`
3. You can configure custom domains in Cloudflare dashboard

## Post-Deployment Configuration

### 1. Verify Environment Variable is Set

After deployment, verify the environment variable is being used:
- Open browser console on your deployed site
- Check Network tab > Request URL should point to your backend
- If it still shows localhost, redeploy after ensuring the variable is set in dashboard

### 2. Set Custom Domain (Optional)
- Go to Cloudflare Dashboard > Pages > Your Project > Custom domains
- Add your domain (e.g., `basira.info`)
- Update DNS records as instructed
- **IMPORTANT:** After adding custom domain, update backend CORS settings to include it

### 3. Set Up Automatic Deployments (Optional)
- Connect your GitHub/GitLab repository
- Cloudflare will auto-deploy on every push

## CORS Configuration

Ensure your backend allows requests from your frontend domain. The CORS configuration is in `backend/main.py`:

```python
allow_origins=[
    "https://basira.info",
    "https://*.basira.info",
    "https://ramadan-platform-frontend.pages.dev",
    "https://*.ramadan-platform-frontend.pages.dev",
    "http://localhost:3000",
],
```

**After updating CORS, redeploy the backend:**
```bash
cd backend
wrangler deploy
```

## Troubleshooting

### API Still Points to Localhost
**Problem:** Frontend is using hardcoded localhost URL instead of environment variable.

**Solution:**
1. Verify `REACT_APP_API_URL` is set in Cloudflare Pages Dashboard (not wrangler.toml)
2. Go to: Pages > Your Project > Settings > Environment variables
3. Add variable for both Production and Preview environments
4. **Redeploy** the site after adding the variable
5. Check browser Network tab to verify the correct URL is being used

### CORS Error: "No 'Access-Control-Allow-Origin' header"
**Problem:** Backend is not allowing requests from your frontend domain.

**Solution:**
1. Check backend `main.py` includes your frontend domain in CORS origins
2. Redeploy backend: `cd backend && wrangler deploy`
3. Verify your frontend domain matches exactly (check https vs http, www vs non-www)
4. Clear browser cache and try again

### Build Fails
- Check that all dependencies are installed: `npm install`
- Verify Node.js version (requires 14+)
- Clear cache: `rm -rf node_modules build && npm install`

### Deployment Fails
- Verify wrangler login: `wrangler whoami`
- Ensure build folder exists: `npm run build`

## Updating Deployment

To update your deployed frontend:
```bash
npm run deploy
```

This will:
1. Build the latest changes
2. Deploy to Cloudflare Pages
3. Create a new deployment (previous versions are kept)

## Rollback

If you need to rollback to a previous version:
1. Go to Cloudflare Dashboard > Pages > Your Project > Deployments
2. Find the previous working deployment
3. Click "Rollback to this deployment"

## Monitoring

- View deployment logs: Cloudflare Dashboard > Pages > Your Project > Deployments
- View analytics: Cloudflare Dashboard > Pages > Your Project > Analytics
- Monitor performance: Use Cloudflare Web Analytics

## Cost

Cloudflare Pages Free Tier includes:
- Unlimited requests
- Unlimited bandwidth
- 500 builds per month
- 100 custom domains

---

**Deployment URL**: After first deployment, your app will be available at:
`https://ramadan-platform-frontend.pages.dev`

For custom domains, configure in Cloudflare Dashboard.
