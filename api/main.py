"""FastAPI backend for Traffic AI Engine."""

import os
import sys
from pathlib import Path
from typing import Optional

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from dotenv import load_dotenv

from core.detector import TrafficDetector
from core.config import Config


# Load environment
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description="AI-powered traffic vehicle counting service"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(Config.STATIC_DIR)), name="static")

# Initialize detector
detector = TrafficDetector(str(Config.MODEL_PATH))


# Pydantic models
class AnalysisResponse(BaseModel):
    status: str
    job_id: str
    original_filename: str
    total_vehicles: int
    video_url: str
    duration: float
    resolution: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    database_connected: bool


# Database helper
def save_to_database(job_id: str, filename: str, total_cars: int, video_url: str):
    """Save analysis results to PostgreSQL."""
    if not Config.DATABASE_URL:
        print("⚠️  DATABASE_URL not set, skipping database save.")
        return

    try:
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO traffic_logs (job_id, filename, total_cars, video_url) VALUES (%s, %s, %s, %s)",
            (job_id, filename, total_cars, video_url)
        )

        # Keep only recent records
        cursor.execute(
            "DELETE FROM traffic_logs WHERE id NOT IN (SELECT id FROM traffic_logs ORDER BY created_at DESC LIMIT %s)",
            (Config.MAX_STORED_RECORDS,)
        )

        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Job {job_id} saved to database.")

    except Exception as e:
        print(f"❌ Database Error: {e}")


def cleanup_old_files():
    """Remove old files to manage disk space."""
    # Clean static directory
    static_files = sorted(
        [f for f in Config.STATIC_DIR.glob("*.mp4")],
        key=lambda x: x.stat().st_mtime
    )
    while len(static_files) >= Config.MAX_STORED_VIDEOS:
        old_file = static_files.pop(0)
        old_file.unlink()
        print(f"🗑️  Removed old file: {old_file.name}")

    # Clean output directory
    output_files = sorted(
        [f for f in Config.OUTPUT_DIR.glob("*.mp4")],
        key=lambda x: x.stat().st_mtime
    )
    while len(output_files) >= Config.MAX_STORED_VIDEOS:
        old_file = output_files.pop(0)
        old_file.unlink()
        print(f"🗑️  Removed old output: {old_file.name}")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "service": Config.API_TITLE,
        "version": Config.API_VERSION,
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    db_connected = False
    if Config.DATABASE_URL:
        try:
            conn = psycopg2.connect(Config.DATABASE_URL)
            conn.close()
            db_connected = True
        except:
            pass

    return HealthResponse(
        status="healthy",
        model_loaded=detector.model is not None,
        database_connected=db_connected
    )


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_video(file: UploadFile = File(...)):
    """
    Analyze traffic video and count vehicles.

    Args:
        file: Video file to analyze

    Returns:
        Analysis results with processed video URL
    """
    # Cleanup old files
    cleanup_old_files()

    # Setup file paths
    job_id = str(uuid.uuid4())[:8]
    input_filename = f"{job_id}_{file.filename}"
    input_path = Config.INPUT_DIR / input_filename
    output_filename = f"output_{job_id}.mp4"
    output_path = Config.OUTPUT_DIR / output_filename
    static_output_path = Config.STATIC_DIR / output_filename

    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process video
    try:
        result = detector.process_video(
            str(input_path),
            str(output_path),
            zone_center_ratio=Config.ZONE_CENTER_RATIO,
            zone_height=Config.ZONE_HEIGHT,
            confidence=Config.CONFIDENCE_THRESHOLD
        )

        # Copy to static directory for serving
        shutil.copy(str(output_path), str(static_output_path))

        # Save to database
        video_url = f"/static/{output_filename}"
        save_to_database(job_id, file.filename, result['total_vehicles'], video_url)

        return AnalysisResponse(
            status="success",
            job_id=job_id,
            original_filename=file.filename,
            total_vehicles=result['total_vehicles'],
            video_url=video_url,
            duration=result['video_duration'],
            resolution=result['resolution']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/v1/results")
async def get_results():
    """Get recent analysis results."""
    if not Config.DATABASE_URL:
        return {"results": []}

    try:
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT job_id, filename, total_cars, video_url, created_at FROM traffic_logs ORDER BY created_at DESC LIMIT 10"
        )
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "results": [
                {
                    "job_id": row[0],
                    "filename": row[1],
                    "total_cars": row[2],
                    "video_url": row[3],
                    "created_at": row[4].isoformat() if row[4] else None
                }
                for row in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
