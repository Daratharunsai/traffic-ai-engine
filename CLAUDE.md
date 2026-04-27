# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Local Development
```bash
# Install dependencies
make install
# or: pip install -r requirements.txt

# Run FastAPI backend
make run-api
# or: uvicorn api.main:app --reload --port 8000

# Run Streamlit frontend
make run-frontend
# or: streamlit run frontend/app.py --server.port 8501

# Run tests
make test
# or: pytest tests/ -v

# Clean generated files
make clean
```

### Docker
```bash
# Build and start all containers
make docker-up
# or: docker-compose up -d

# Stop containers
make docker-down
# or: docker-compose down

# View logs
make docker-logs
# or: docker-compose logs -f
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Analyze video
curl -X POST "http://localhost:8000/api/v1/analyze" -F "file=@data/input/sample.mp4"

# Get recent results
curl http://localhost:8000/api/v1/results
```

## Architecture

### Module Structure

The project is split into three main modules with a shared core:

- **`api/`** - FastAPI REST backend
- **`frontend/`** - Streamlit web interface
- **`core/`** - Shared detection logic and configuration

**Critical Import Pattern**: Both `api/` and `frontend/` modules add the parent directory to `sys.path` at the top of their entry files to enable imports from `core/`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Core Detection Pipeline (`core/detector.py`)

The `TrafficDetector` class encapsulates all vehicle detection and counting logic:

1. **Initialization**: Loads YOLOv8m model, sets vehicle classes [2, 5, 7] (car, bus, truck)
2. **Processing**: Iterates through video frames, applies YOLO detection with ByteTrack
3. **Tripwire Logic**: Counts vehicles only when centroid crosses the middle line
4. **Visualization**: Draws red zone, colored boxes, and sequence numbers

**Key Method**: `process_video(input_path, output_path, zone_center_ratio, zone_height, confidence, progress_callback)`

Returns dictionary with: `total_vehicles`, `total_frames`, `video_duration`, `fps`, `resolution`

### Tripwire Logic (Critical)

Vehicles are counted ONLY when their centroid crosses the absolute middle line of the detection zone. This requires tracking historical position (`prev_y` vs `center_y`) to prevent false positives from:

- Shadows and reflections
- Stationary objects
- Partial detections

**Implementation** (in `core/detector.py`):
```python
if (prev_y < middle_line <= center_y) or (prev_y > middle_line >= center_y):
    counted_ids.add(track_id)
    total_cars_passed += 1
```

### Configuration (`core/config.py`)

Centralized configuration class that:
- Defines all paths (BASE_DIR, DATA_DIR, INPUT_DIR, OUTPUT_DIR, MODELS_DIR, STATIC_DIR)
- Sets detection parameters (ZONE_CENTER_RATIO, ZONE_HEIGHT, CONFIDENCE_THRESHOLD)
- Manages storage limits (MAX_STORED_VIDEOS, MAX_STORED_RECORDS)
- Creates directories on import via `Config.create_directories()`

**Important**: Config is imported at module level in both API and frontend, so directories are created automatically.

### API Architecture (`api/main.py`)

FastAPI backend with three main endpoints:

1. **POST /api/v1/analyze** - Main analysis endpoint
   - Accepts video upload via `UploadFile`
   - Generates unique job_id (8-char UUID)
   - Saves to `data/input/`, processes to `data/output/`, copies to `static/`
   - Returns `AnalysisResponse` with video URL

2. **GET /health** - Health check
   - Returns model loaded status and database connection status

3. **GET /api/v1/results** - Recent results
   - Queries PostgreSQL for last 10 records
   - Returns job_id, filename, total_cars, video_url, created_at

**Automatic Cleanup**: Before each analysis, `cleanup_old_files()` removes old videos from `static/` and `data/output/` to manage disk space (keeps MAX_STORED_VIDEOS).

### Frontend Architecture (`frontend/app.py`)

Streamlit web interface with:

- **Sidebar controls**: Zone center, zone height, confidence threshold
- **Video upload**: File uploader with preview
- **Progress tracking**: Real-time progress bar during processing
- **Results display**: Metrics, processed video, download button
- **History**: Recent results stored in `st.session_state`

**State Management**: Uses `st.session_state` for:
- `last_result` - Most recent analysis
- `results_history` - List of all analyses in session

### Database Schema (PostgreSQL)

**Table: `traffic_logs`**
- `id` - SERIAL primary key
- `job_id` - VARCHAR(8) unique identifier
- `filename` - Original video filename
- `total_cars` - Vehicle count
- `video_url` - Path to processed video
- `created_at` - TIMESTAMP

**Cleanup**: Keeps only `MAX_STORED_RECORDS` (default 3) most recent records.

### Visual System

| Element | Color | Meaning |
|---------|-------|---------|
| Detection Zone | Red (30% opacity) | Counting area between zone_top and zone_bottom |
| Zone Boundaries | Red lines | Top and bottom limits |
| Bounding Box | Green | Vehicle counted |
| Bounding Box | Red | Vehicle not counted |
| Center Dot | Box color | Vehicle centroid |
| Counter Box | Green | Total vehicles passed |

### Important Implementation Details

**OpenMP Conflict**: All entry files set `os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'` at the top to handle Intel MKP library conflicts on Windows.

**Video Codec**: Uses `mp4v` codec for output videos. This is widely compatible but may need adjustment for specific players.

**ByteTrack**: The tracker configuration file `bytetrack.yaml` is not in the repo - it's a default tracker included with ultralytics. Do not add it to the repo.

**Progress Callback**: The `process_video` method accepts an optional `progress_callback(progress, frame, total, count)` that's called every 30 frames. The frontend uses this to update the progress bar.

**File Paths**: All paths use `pathlib.Path` objects from `Config` class. When passing to OpenCV or other libraries, convert to string with `str(path)`.

**Static Files**: FastAPI mounts `/static` to serve processed videos. The API copies processed videos from `data/output/` to `static/` after processing.

### Environment Variables

Required in `.env`:
```
DATABASE_URL=postgresql://user:password@host:port/dbname?sslmode=require
```

Optional: If `DATABASE_URL` is not set, the API will skip database operations and continue functioning (with a warning).

### File Structure Notes

- `data/input/` - Uploaded videos (not in git)
- `data/output/` - Processed videos (not in git)
- `static/` - Videos served via FastAPI (not in git)
- `models/yolov8m.pt` - Model weights (50MB, excluded by .gitignore but should be in repo)
- `tests/` - Test files (pytest)

### Deployment Notes

**Streamlit Cloud**: Deploy only the frontend. Set deploy command to `streamlit run frontend/app.py --server.port=8501`.

**Railway/Render**: Deploy the full stack. The API runs on `$PORT` environment variable. Set start command to `uvicorn api.main:app --host 0.0.0.0 --port $PORT`.

**Docker**: Two containers - API (port 8000) and Frontend (port 8501). Both mount `data/` and `static/` volumes for persistence.
