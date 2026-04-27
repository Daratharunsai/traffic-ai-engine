"""Test suite for Traffic AI Engine."""

import pytest
from pathlib import Path
from core.detector import TrafficDetector
from core.config import Config


def test_config_directories():
    """Test that configuration directories are created."""
    assert Config.INPUT_DIR.exists()
    assert Config.OUTPUT_DIR.exists()
    assert Config.STATIC_DIR.exists()
    assert Config.MODELS_DIR.exists()


def test_detector_initialization():
    """Test detector initialization."""
    detector = TrafficDetector(str(Config.MODEL_PATH))
    assert detector.model is not None
    assert detector.vehicle_classes == [2, 5, 7]


def test_zone_calculation():
    """Test detection zone calculations."""
    height = 1080
    zone_center = int(height * Config.ZONE_CENTER_RATIO)
    zone_top = zone_center - Config.ZONE_HEIGHT // 2
    zone_bottom = zone_center + Config.ZONE_HEIGHT // 2

    assert 0 <= zone_top < zone_bottom <= height


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
