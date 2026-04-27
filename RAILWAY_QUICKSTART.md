# 🚀 Railway Deployment Quick Start

## Step 1: Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Ready for Railway deployment"

# Push (replace with your repo URL)
git push origin main
```

## Step 2: Deploy API to Railway

1. Go to [railway.app](https://railway.app) and sign up/login
2. Click **"New Project"**
3. Click **"Deploy from GitHub repo"**
4. Select your `traffic-ai-engine` repository
5. Railway will auto-detect Python and use `railway.toml`
6. Click **"Deploy"**

## Step 3: Add Database

1. In your Railway project, click **"New Service"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will create a PostgreSQL database
4. Go to your API service → **"Settings"** → **"Variables"**
5. Add `DATABASE_URL` with the value from the PostgreSQL service

## Step 4: Deploy Frontend

1. In your Railway project, click **"New Service"**
2. Click **"Deploy from GitHub repo"**
3. Select the same repository
4. In the service settings, change the config file to `railway-frontend.toml`
5. Click **"Deploy"**

## Step 5: Get Your URLs

1. Go to your API service → **"Settings"** → **"Domains"**
2. Copy the API URL (e.g., `https://traffic-ai-api.up.railway.app`)
3. Go to your Frontend service → **"Settings"** → **"Domains"**
4. Copy the Frontend URL (e.g., `https://traffic-ai-frontend.up.railway.app`)

## Step 6: Test

Open your Frontend URL in a browser and upload a test video!

## 📚 More Information

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.
