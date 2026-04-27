"""Core detection module for traffic vehicle counting."""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import cv2
from ultralytics import YOLO
from typing import Tuple, List, Dict, Optional
import numpy as np


class TrafficDetector:
    """Vehicle detection and counting using YOLOv8 with tripwire logic."""

    def __init__(self, model_path: str = 'models/yolov8m.pt'):
        """Initialize detector with YOLO model."""
        self.model = YOLO(model_path)
        self.vehicle_classes = [2, 5, 7]  # car, bus, truck

    def process_video(
        self,
        input_path: str,
        output_path: str,
        zone_center_ratio: float = 0.5,
        zone_height: int = 160,
        confidence: float = 0.45,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Process video and count vehicles crossing the detection zone.

        Args:
            input_path: Path to input video
            output_path: Path to save processed video
            zone_center_ratio: Center position of zone (0.0-1.0)
            zone_height: Height of detection zone in pixels
            confidence: YOLO confidence threshold
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with detection results
        """
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {input_path}")

        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Detection zone setup
        middle_line = int(height * zone_center_ratio)
        zone_top = middle_line - zone_height // 2
        zone_bottom = middle_line + zone_height // 2

        # Tracking state
        counted_ids = set()
        car_sequence_numbers = {}
        vehicle_positions = {}
        total_cars_passed = 0

        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Draw detection zone
            self._draw_zone(frame, width, zone_top, zone_bottom)

            # Run YOLO detection with tracking
            results = self.model.track(
                frame,
                classes=self.vehicle_classes,
                persist=True,
                tracker="bytetrack.yaml",
                conf=confidence,
                verbose=False
            )

            # Process detections
            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.int().cpu().tolist()
                track_ids = results[0].boxes.id.int().cpu().tolist()

                for box, track_id in zip(boxes, track_ids):
                    center_x = int((box[0] + box[2]) / 2)
                    center_y = int((box[1] + box[3]) / 2)

                    # Track vehicle position
                    if track_id not in vehicle_positions:
                        vehicle_positions[track_id] = center_y

                    prev_y = vehicle_positions[track_id]

                    # Tripwire logic - count only when crossing middle line
                    if track_id not in counted_ids:
                        if (prev_y < middle_line <= center_y) or (prev_y > middle_line >= center_y):
                            counted_ids.add(track_id)
                            total_cars_passed += 1
                            car_sequence_numbers[track_id] = total_cars_passed

                    # Update position
                    vehicle_positions[track_id] = center_y

                    # Draw vehicle box
                    self._draw_vehicle(
                        frame, box, center_x, center_y,
                        track_id, counted_ids, car_sequence_numbers
                    )

            # Draw counter
            self._draw_counter(frame, total_cars_passed)

            out.write(frame)
            frame_count += 1

            # Progress callback
            if progress_callback and frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                progress_callback(progress, frame_count, total_frames, total_cars_passed)

        cap.release()
        out.release()

        return {
            'total_vehicles': total_cars_passed,
            'total_frames': frame_count,
            'video_duration': frame_count / fps,
            'fps': fps,
            'resolution': f"{width}x{height}"
        }

    def _draw_zone(self, frame: np.ndarray, width: int, zone_top: int, zone_bottom: int):
        """Draw the red detection zone."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, zone_top), (width, zone_bottom), (0, 0, 255), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        cv2.line(frame, (0, zone_top), (width, zone_top), (0, 0, 255), 2)
        cv2.line(frame, (0, zone_bottom), (width, zone_bottom), (0, 0, 255), 2)

    def _draw_vehicle(
        self,
        frame: np.ndarray,
        box: List[int],
        center_x: int,
        center_y: int,
        track_id: int,
        counted_ids: set,
        car_sequence_numbers: Dict
    ):
        """Draw vehicle bounding box and label."""
        if track_id in counted_ids:
            box_color = (0, 255, 0)  # Green for counted
            sequence = car_sequence_numbers.get(track_id, "?")
            label_text = f"Counted: #{sequence}"
        else:
            box_color = (0, 0, 255)  # Red for uncounted
            label_text = "Uncounted"

        cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), box_color, 2)
        cv2.circle(frame, (center_x, center_y), 6, box_color, -1)
        cv2.putText(frame, label_text, (box[0], box[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

    def _draw_counter(self, frame: np.ndarray, count: int):
        """Draw total counter box."""
        text = f"TOTAL PASSED: {count}"
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        cv2.rectangle(frame, (20, 20), (20 + text_width + 20, 20 + text_height + 20), (0, 255, 0), -1)
        cv2.putText(frame, text, (30, 20 + text_height + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
