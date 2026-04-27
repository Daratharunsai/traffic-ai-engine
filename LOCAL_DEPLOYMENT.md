# 🚀 Local Deployment Guide

This guide will help you run the Traffic AI Engine locally for development and client testing.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Daratharunsai/traffic-ai-engine.git
cd traffic-ai-engine
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if you want to use a database
# For local testing without database, you can leave DATABASE_URL empty
```

### 4. Run the Application

#### Option A: Run Both API and Frontend

**Terminal 1 - API:**
```bash
make run-api
# or
uvicorn api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
make run-frontend
# or
streamlit run frontend/app.py --server.port 8501
```

#### Option B: Run Frontend Only (Standalone)

The frontend can run standalone without the API for basic testing:

```bash
streamlit run frontend/app.py --server.port 8501
```

### 5. Access the Application

- **Frontend:** http://localhost:8501
- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Using Make Commands

```bash
# Install dependencies
make install

# Run API backend
make run-api

# Run Streamlit frontend
make run-frontend

# Run tests
make test

# Clean generated files
make clean
```

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Analyze a Video
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@data/input/sample.mp4"
```

### Get Recent Results
```bash
curl http://localhost:8000/api/v1/results
```

## Docker Deployment (Local)

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Containers

```bash
# Build API image
docker build -t traffic-engine-api .

# Run API
docker run -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/static:/app/static" \
  traffic-engine-api

# Build Frontend image
docker build -f Dockerfile.frontend -t traffic-engine-frontend .

# Run Frontend
docker run -p 8501:8501 \
  -v "$(pwd)/data:/app/data" \
  traffic-engine-frontend
```

## Client Testing Setup

### For Client Demo

1. **Run the application locally:**
   ```bash
   # Terminal 1
   make run-api

   # Terminal 2
   make run-frontend
   ```

2. **Share with client:**
   - Option 1: Use ngrok to expose localhost
   - Option 2: Deploy to a VPS (DigitalOcean, AWS, etc.)
   - Option 3: Use Railway paid tier (not free)

### Using ngrok for Client Access

```bash
# Install ngrok
# https://ngrok.com/download

# Expose API
ngrok http 8000

# Expose Frontend (in another terminal)
ngrok http 8501
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Mac/Linux

# Kill the process
taskkill /PID <PID> /F  # Windows
kill -9 <PID>  # Mac/Linux
```

### Module Not Found Error

```bash
# Make sure you're in the project root
cd traffic-ai-engine

# Reinstall dependencies
pip install -r requirements.txt
```

### OpenCV Import Error

```bash
# Install system dependencies (Linux)
sudo apt-get install libgl1-mesa-glx libglib2.0-0

# On Windows/Mac, this should work with pip install
```

### Model Not Found

The YOLO model will be auto-downloaded on first run. If you encounter issues:

```bash
# Download manually
wget https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8m.pt -O models/yolov8m.pt
```

## Performance Tips

### For Faster Processing

1. **Use smaller videos** for testing
2. **Reduce video resolution** before processing
3. **Use GPU** if available (CUDA)
4. **Adjust confidence threshold** in `core/config.py`

### GPU Acceleration

```bash
# Install PyTorch with CUDA support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# The detector will automatically use GPU if available
```

## Security Notes

### For Production Use

1. **Add authentication** to the API
2. **Use HTTPS** (SSL certificates)
3. **Validate file uploads** (size, type)
4. **Rate limit** API endpoints
5. **Sanitize user inputs**

### Environment Variables

Never commit `.env` file with real credentials. Use `.env.example` as a template.

## Next Steps

- Test with sample videos
- Adjust detection zone settings
- Customize vehicle classes
- Add custom preprocessing
- Train on custom datasets

## Support

For issues or questions:
- Check the [README.md](README.md)
- Review [CLAUDE.md](CLAUDE.md) for architecture details
- Open an issue on GitHub
