# Railway Deployment Guide

This guide will help you deploy the Traffic AI Engine to Railway.

## 🚀 Quick Start

### Prerequisites

- GitHub account with your code pushed
- Railway account (free tier available)
- Railway CLI (optional, but recommended)

### Step 1: Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Ready for Railway deployment"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/traffic-ai-engine.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy API to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `traffic-ai-engine` repository
4. Railway will auto-detect Python and use `railway.toml`
5. Click "Deploy"

### Step 3: Configure Database

Railway automatically provides PostgreSQL. Add the environment variable:

1. Go to your project → Settings → Variables
2. Add `DATABASE_URL` with the value from Railway's PostgreSQL service
3. Or let Railway auto-link the database service

### Step 4: Deploy Streamlit Frontend

1. In your Railway project, click "New Service"
2. Select "GitHub Repo" again
3. Select the same repository
4. In the service settings, change the config file to `railway-frontend.toml`
5. Or manually set the start command:
   ```
   streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
   ```
6. Click "Deploy"

### Step 5: Connect Frontend to API

1. Go to your API service → Settings → Domains
2. Copy the API URL (e.g., `https://traffic-ai-api.up.railway.app`)
3. Go to your Frontend service → Settings → Variables
4. Add `API_URL` with the API URL

## 📁 Deployment Files

### railway.toml (API)
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
```

### railway-frontend.toml (Frontend)
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true"
healthcheckPath = "/"
healthcheckTimeout = 300
```

## 🔧 Environment Variables

### Required for API
- `DATABASE_URL` - PostgreSQL connection string (Railway provides this)
- `KMP_DUPLICATE_LIB_OK` - Set to `TRUE` (already in railway.toml)

### Optional for Frontend
- `API_URL` - URL of the API service

## 📊 Service Architecture

```
Railway Project
├── API Service (Port 8000)
│   ├── FastAPI backend
│   ├── YOLOv8 model
│   └── PostgreSQL database
└── Frontend Service (Port 8501)
    └── Streamlit web interface
```

## 🧪 Testing Deployment

### Test API Health
```bash
curl https://your-api-url.railway.app/health
```

### Test Analysis Endpoint
```bash
curl -X POST "https://your-api-url.railway.app/api/v1/analyze" \
  -F "file=@test_video.mp4"
```

### Access Frontend
Open your frontend URL in browser (e.g., `https://your-frontend-url.railway.app`)

## 💾 Persistent Storage

Railway provides persistent volumes for file storage. The following directories are persisted:

- `data/input/` - Uploaded videos
- `data/output/` - Processed videos
- `static/` - Static files for API serving

## 🔄 Updating Deployment

### Automatic Updates
Railway automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push
```

### Manual Redeploy
1. Go to Railway project
2. Click on the service
3. Click "Redeploy" button

## 📈 Monitoring

### View Logs
1. Go to Railway project
2. Click on service
3. Click "Logs" tab

### View Metrics
1. Go to Railway project
2. Click on service
3. Click "Metrics" tab

### Set Up Alerts
1. Go to Railway project
2. Click "Settings"
3. Configure alert rules

## 🐛 Troubleshooting

### Build Fails
- Check that `requirements.txt` is up to date
- Verify Python version compatibility
- Check build logs for errors

### Service Won't Start
- Check that start command is correct
- Verify environment variables are set
- Check service logs for errors

### Database Connection Issues
- Verify `DATABASE_URL` is set correctly
- Check that PostgreSQL service is running
- Test connection locally first

### Video Processing Fails
- Check that model file exists in `models/`
- Verify sufficient memory (Railway free tier: 512MB)
- Check logs for OpenCV/YOLO errors

## 💰 Cost Management

### Free Tier Limits
- $5/month credit
- 512MB RAM per service
- 0.5 vCPU per service
- 1GB storage

### Optimizing Costs
- Use smaller model (yolov8n.pt instead of yolov8m.pt)
- Limit video processing duration
- Clean up old files regularly
- Scale down when not in use

## 🔐 Security

### Environment Variables
- Never commit `.env` file
- Use Railway's encrypted variables
- Rotate secrets regularly

### API Security
- Add authentication middleware
- Rate limit API endpoints
- Validate file uploads
- Sanitize user inputs

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway Python Guide](https://docs.railway.app/guides/python)
- [Streamlit on Railway](https://docs.railway.app/guides/deploying-streamlit)
- [FastAPI on Railway](https://docs.railway.app/guides/deploying-fastapi)
