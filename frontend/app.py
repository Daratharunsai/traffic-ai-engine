"""Streamlit frontend for Traffic AI Engine."""

import os
import sys
from pathlib import Path

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import uuid

from core.detector import TrafficDetector
from core.config import Config


# Page config
st.set_page_config(
    page_title="Traffic AI Engine",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize detector
@st.cache_resource
def get_detector():
    """Get cached detector instance."""
    return TrafficDetector(str(Config.MODEL_PATH))


def main():
    """Main application."""
    st.markdown('<h1 class="main-header">🚗 Traffic AI Engine</h1>', unsafe_allow_html=True)
    st.markdown("Upload traffic videos to count vehicles using AI-powered zone detection.")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        st.subheader("Detection Zone")
        zone_center = st.slider(
            "Zone Center Position",
            0.1, 0.9, Config.ZONE_CENTER_RATIO, 0.05,
            help="Center position of counting zone (0.1 = top, 0.9 = bottom)"
        )
        zone_height = st.slider(
            "Zone Height (pixels)",
            50, 300, Config.ZONE_HEIGHT, 10,
            help="Height of detection zone"
        )

        st.subheader("Detection Settings")
        confidence = st.slider(
            "Confidence Threshold",
            0.1, 0.9, Config.CONFIDENCE_THRESHOLD, 0.05,
            help="Minimum confidence for vehicle detection"
        )

        st.markdown("---")
        st.markdown("### 📊 How It Works")
        st.markdown("""
        1. **Red Zone** - Detection area
        2. **Green Box** - Counted vehicle
        3. **Red Box** - Uncounted vehicle
        4. **Tripwire** - Vehicles counted only when crossing middle line
        """)

        st.markdown("### 🚗 Vehicle Classes")
        st.markdown("""
        - 🚗 Car (4 wheels)
        - 🚌 Bus (6+ wheels)
        - 🚚 Truck (6+ wheels)
        """)

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📤 Upload Video")
        uploaded_file = st.file_uploader(
            "Select a traffic video",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="Supported formats: MP4, AVI, MOV, MKV"
        )

        if uploaded_file:
            # Display video info
            st.video(uploaded_file)
            st.info(f"📁 File: {uploaded_file.name} | 📏 Size: {uploaded_file.size / (1024*1024):.2f} MB")

            # Process button
            if st.button("🚀 Analyze Traffic", type="primary", use_container_width=True):
                process_video(uploaded_file, zone_center, zone_height, confidence)

    with col2:
        st.subheader("📈 Recent Results")
        display_recent_results()

    # Display results if available
    if 'last_result' in st.session_state:
        display_results(st.session_state.last_result)


def process_video(uploaded_file, zone_center, zone_height, confidence):
    """Process uploaded video."""
    detector = get_detector()

    # Save uploaded file
    job_id = str(uuid.uuid4())[:8]
    input_filename = f"{job_id}_{uploaded_file.name}"
    input_path = Config.INPUT_DIR / input_filename
    output_filename = f"output_{job_id}.mp4"
    output_path = Config.OUTPUT_DIR / output_filename

    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(progress, frame, total, count):
        """Update progress bar."""
        progress_bar.progress(progress / 100)
        status_text.text(f"Processing: {progress:.1f}% | Frames: {frame}/{total} | Counted: {count}")

    # Process video
    try:
        with st.spinner("Analyzing video... This may take a few minutes."):
            result = detector.process_video(
                str(input_path),
                str(output_path),
                zone_center_ratio=zone_center,
                zone_height=zone_height,
                confidence=confidence,
                progress_callback=progress_callback
            )

        # Store result
        result['job_id'] = job_id
        result['input_filename'] = uploaded_file.name
        result['output_filename'] = output_filename
        result['output_path'] = str(output_path)
        result['timestamp'] = datetime.now().isoformat()
        result['zone_center'] = zone_center
        result['zone_height'] = zone_height

        st.session_state.last_result = result
        st.session_state.results_history = st.session_state.get('results_history', [])
        st.session_state.results_history.append(result)

        progress_bar.progress(1.0)
        status_text.text("✅ Analysis complete!")

        st.success(f"Analysis complete! {result['total_vehicles']} vehicles counted.")

    except Exception as e:
        st.error(f"Error processing video: {str(e)}")


def display_results(result):
    """Display analysis results."""
    st.markdown("---")
    st.subheader("📊 Analysis Results")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Vehicles", result['total_vehicles'])
    col2.metric("Total Frames", result['total_frames'])
    col3.metric("Duration (s)", f"{result['video_duration']:.1f}")
    col4.metric("Resolution", result['resolution'])

    # Processed video
    st.subheader("🎥 Processed Video")
    if Path(result['output_path']).exists():
        st.video(str(result['output_path']))

        # Download button
        with open(result['output_path'], "rb") as f:
            st.download_button(
                "📥 Download Processed Video",
                f,
                file_name=result['output_filename'],
                mime="video/mp4"
            )
    else:
        st.warning("Processed video not found.")

    # Analysis summary
    st.subheader("📋 Analysis Summary")
    st.info(f"""
    **Detection Settings:**
    - Zone Center: {result['zone_center']:.2f}
    - Zone Height: {result['zone_height']} pixels
    - Confidence: {Config.CONFIDENCE_THRESHOLD}

    **Results:**
    - Total vehicles counted: {result['total_vehicles']}
    - Average vehicles per minute: {result['total_vehicles'] / max(1, result['video_duration'] / 60):.1f}
    - Processing time: {result['total_frames']} frames at {result['fps']} FPS
    """)


def display_recent_results():
    """Display recent analysis results."""
    if 'results_history' not in st.session_state or not st.session_state.results_history:
        st.info("No recent results. Upload a video to get started.")
        return

    for result in reversed(st.session_state.results_history[-5:]):
        with st.expander(f"📹 {result['input_filename']} - {result['total_vehicles']} vehicles"):
            st.write(f"**Time:** {result['timestamp']}")
            st.write(f"**Duration:** {result['video_duration']:.1f}s")
            st.write(f"**Resolution:** {result['resolution']}")


if __name__ == "__main__":
    main()
