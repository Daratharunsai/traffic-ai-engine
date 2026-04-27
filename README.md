# 🏎️ Traffic AI Engine

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-yellow)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker)

A production-ready computer vision microservice that tracks vehicles in real-time, overlays analytics, and logs traffic density. Features both a REST API and a Streamlit web interface.

## 🧠 How It Works

1. **Upload:** Send a traffic video via API or web interface
2. **Process:** YOLOv8 and ByteTrack track vehicles with tripwire detection
3. **Count:** Vehicles are counted only when crossing the detection zone
4. **Return:** Annotated video with vehicle counts and sequence numbers

## 📁 Project Structure

```
traffic-ai-engine/
├── api/                    # FastAPI backend
│   ├── __init__.py
│   └── main.py            # REST API endpoints
├── frontend/              # Streamlit web interface
│   ├── __init__.py
│   └── app.py             # Web UI
├── core/                  # Shared detection logic
│   ├── __init__.py
│   ├── detector.py        # YOLO detection & counting
│   └── config.py          # Configuration settings
├── data/                  # Data storage
│   ├── input/            # Uploaded videos
│   └── output/           # Processed videos
├── models/               # AI models
│   └── yolov8m.pt       # YOLOv8 model weights
├── static/               # Static files for API
├── tests/                # Test files
├── requirements.txt      # Python dependencies
├── Dockerfile           # API container
├── Dockerfile.frontend  # Frontend container
├── docker-compose.yml   # Multi-container setup
└── .env                 # Environment variables
```

## 💻 Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, Python 3.10 |
| Frontend | Streamlit |
| AI/Vision | YOLOv8m, OpenCV, ByteTrack |
| Database | PostgreSQL (NeonDB) |
| Infrastructure | Docker, Docker Compose |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/Daratharunsai/traffic-ai-engine.git
cd traffic-ai-engine
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Download the model**
```bash
# The model should be in models/yolov8m.pt
# If missing, it will be auto-downloaded on first run
```

4. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your DATABASE_URL
```

5. **Run the API**
```bash
uvicorn api.main:app --reload --port 8000
```

6. **Run the Frontend**
```bash
streamlit run frontend/app.py --server.port 8501
```

### Docker Deployment

**Using Docker Compose (Recommended)**
```bash
docker-compose up -d
```

**Individual Containers**
```bash
# Build and run API
docker build -t traffic-engine-api .
docker run -p 8000:8000 -v "$(pwd)/data:/app/data" -v "$(pwd)/static:/app/static" traffic-engine-api

# Build and run Frontend
docker build -f Dockerfile.frontend -t traffic-engine-frontend .
docker run -p 8501:8501 -v "$(pwd)/data:/app/data" traffic-engine-frontend
```

### Railway Deployment (Recommended for Production)

**Quick Deploy:**
```bash
# 1. Push to GitHub
git add .
git commit -m "Ready for Railway"
git push origin main

# 2. Go to railway.app and deploy from GitHub
# Railway will auto-detect Python and use railway.toml
```

**Manual Setup:**
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will deploy the API automatically
5. Add a second service for the frontend using `railway-frontend.toml`
6. Connect the services and set environment variables

**See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.**

## 📡 API Endpoints

### POST /api/v1/analyze
Analyze a traffic video and count vehicles.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@traffic_video.mp4"
```

**Response:**
```json
{
  "status": "success",
  "job_id": "abc12345",
  "original_filename": "traffic_video.mp4",
  "total_vehicles": 42,
  "video_url": "/static/output_abc12345.mp4",
  "duration": 120.5,
  "resolution": "1920x1080"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "database_connected": true
}
```

### GET /api/v1/results
Get recent analysis results from database.

## 🎨 Detection Features

### Tripwire Logic
Vehicles are counted **only** when their centroid crosses the absolute middle line of the detection zone. This prevents false positives from:
- Shadows and reflections
- Stationary objects
- Partial detections

### Visual Indicators

| Element | Color | Meaning |
|---------|-------|---------|
| Detection Zone | Red (30% opacity) | Counting area |
| Zone Boundaries | Red lines | Top and bottom limits |
| Bounding Box | Green | Vehicle counted |
| Bounding Box | Red | Vehicle not counted |
| Center Dot | Box color | Vehicle centroid |
| Counter Box | Green | Total vehicles passed |

### Vehicle Classes
- 🚗 **Car** (4 wheels) - Class 2
- 🚌 **Bus** (6+ wheels) - Class 5
- 🚚 **Truck** (6+ wheels) - Class 7

## ⚙️ Configuration

Edit `core/config.py` to customize:

```python
# Detection zone
ZONE_CENTER_RATIO = 0.5  # Center position (0.0-1.0)
ZONE_HEIGHT = 160        # Zone height in pixels

# Detection settings
CONFIDENCE_THRESHOLD = 0.45
VEHICLE_CLASSES = [2, 5, 7]  # car, bus, truck

# Storage
MAX_STORED_VIDEOS = 3
MAX_STORED_RECORDS = 3
```

## 🗄️ Database Schema

**Table: `traffic_logs`**

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| job_id | VARCHAR(8) | Unique job identifier |
| filename | VARCHAR | Original video filename |
| total_cars | INTEGER | Vehicle count |
| video_url | VARCHAR | Processed video path |
| created_at | TIMESTAMP | Creation time |

## 🧪 Testing

```bash
# Test with sample video
python -c "
from core.detector import TrafficDetector
detector = TrafficDetector('models/yolov8m.pt')
result = detector.process_video('data/input/sample.mp4', 'data/output/result.mp4')
print(f'Total vehicles: {result[\"total_vehicles\"]}')
"
```

## 📝 Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@host:port/dbname?sslmode=require
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Ultralytics](https://github.com/ultralytics/ultralytics) for YOLOv8
- [ByteTrack](https://github.com/ifzhang/ByteTrack) for tracking algorithm
