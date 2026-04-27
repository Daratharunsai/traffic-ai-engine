"""Configuration settings for Traffic AI Engine."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration."""

    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    INPUT_DIR = DATA_DIR / "input"
    OUTPUT_DIR = DATA_DIR / "output"
    MODELS_DIR = BASE_DIR / "models"
    STATIC_DIR = BASE_DIR / "static"

    # Model settings
    MODEL_PATH = MODELS_DIR / "yolov8m.pt"
    VEHICLE_CLASSES = [2, 5, 7]  # car, bus, truck
    CONFIDENCE_THRESHOLD = 0.45

    # Detection zone settings
    ZONE_CENTER_RATIO = 0.5
    ZONE_HEIGHT = 160

    # API settings
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    API_TITLE = "Traffic AI Engine"
    API_VERSION = "1.0.0"

    # Storage settings
    MAX_STORED_VIDEOS = 3
    MAX_STORED_RECORDS = 3

    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8501",
        "https://traffic-ai-dashboard.vercel.app"
    ]

    @classmethod
    def create_directories(cls):
        """Create necessary directories."""
        cls.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)


# Create directories on import
Config.create_directories()
