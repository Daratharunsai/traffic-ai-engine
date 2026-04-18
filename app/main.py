import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import cv2
import uuid
import shutil
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware  
from ultralytics import YOLO

# --- 1. ENVIRONMENT & FOLDERS ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

# --- 2. INITIALIZE API & SETTINGS ---
app = FastAPI(title="Traffic AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://traffic-ai-dashboard.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
model = YOLO('yolov8m.pt') 

# --- 3. DATABASE HELPER ---
def save_to_neon(job_id, filename, total_cars, video_url):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO traffic_logs (job_id, filename, total_cars, video_url) VALUES (%s, %s, %s, %s)", 
                       (job_id, filename, total_cars, video_url))
        cursor.execute("DELETE FROM traffic_logs WHERE id NOT IN (SELECT id FROM traffic_logs ORDER BY created_at DESC LIMIT 3)")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Job {job_id} saved and DB cleaned.")
    except Exception as e:
        print(f"❌ Database Error: {e}")


# --- 4. THE MAIN ENDPOINT ---
@app.post("/api/v1/analyze")
async def analyze_video(file: UploadFile = File(...)):
    
    # Storage Cleanup
    all_videos = sorted([os.path.join("static", f) for f in os.listdir("static") if f.endswith(".mp4")], key=os.path.getmtime)
    while len(all_videos) >= 3:
        old_file = all_videos.pop(0)
        if os.path.isfile(old_file): os.unlink(old_file)

    # Setup file paths
    original_filename = file.filename
    job_id = str(uuid.uuid4())[:8]
    input_path = os.path.join("data", original_filename)
    output_filename = f"output_{job_id}.mp4"
    output_path = os.path.join("static", output_filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Setup OpenCV
    cap = cv2.VideoCapture(input_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    # --- DETECTION ZONE ---
    middle_line = int(height * 0.5)
    zone_top = middle_line - 80 
    zone_bottom = middle_line + 80 

    counted_ids = set()
    car_sequence_numbers = {} 
    vehicle_positions = {} # NEW: Tracks where the car was in the last frame
    total_cars_passed = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Draw the shaded red zone
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, zone_top), (width, zone_bottom), (0, 0, 255), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        cv2.line(frame, (0, zone_top), (width, zone_top), (0, 0, 255), 2)
        cv2.line(frame, (0, zone_bottom), (width, zone_bottom), (0, 0, 255), 2)
        
        # Run YOLO - CONFIDENCE BUMPED TO 0.45 TO KILL GHOSTS
        results = model.track(frame, classes=[2, 5, 7], persist=True, tracker="bytetrack.yaml", conf=0.45, verbose=False)
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            
            for box, track_id in zip(boxes, track_ids):
                center_x = int((box[0] + box[2]) / 2)
                center_y = int((box[1] + box[3]) / 2)
                
                # If this is the first time seeing the car, save its position
                if track_id not in vehicle_positions:
                    vehicle_positions[track_id] = center_y
                    
                prev_y = vehicle_positions[track_id]
                
                # --- BULLETPROOF TRIPWIRE LOGIC ---
                if track_id not in counted_ids:
                    # The car MUST cross the absolute middle line to be counted.
                    # This requires historical movement, killing stationary "ghost" flashes.
                    if (prev_y < middle_line <= center_y) or (prev_y > middle_line >= center_y):
                        counted_ids.add(track_id)
                        total_cars_passed += 1
                        car_sequence_numbers[track_id] = total_cars_passed
                
                # Update the car's position for the next frame
                vehicle_positions[track_id] = center_y
                
                # --- APPLY ACCURATE VISUALS ---
                if track_id in counted_ids:
                    box_color = (0, 255, 0) # Green for counted
                    strict_sequence = car_sequence_numbers.get(track_id, "?")
                    label_text = f"Counted: #{strict_sequence}"
                else:
                    box_color = (0, 0, 255) # Red for uncounted
                    label_text = "Uncounted"

                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), box_color, 2)
                cv2.circle(frame, (center_x, center_y), 6, box_color, -1)
                cv2.putText(frame, label_text, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
        
        # --- DRAW GREEN TOTAL COUNTER BOX ---
        text = f"TOTAL PASSED: {total_cars_passed}"
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        cv2.rectangle(frame, (20, 20), (20 + text_width + 20, 20 + text_height + 20), (0, 255, 0), -1)
        cv2.putText(frame, text, (30, 20 + text_height + 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
                
        out.write(frame) 

    cap.release()
    out.release()
    
    # Save to Neon DB
    video_url_path = f"/static/{output_filename}"
    save_to_neon(job_id, original_filename, total_cars_passed, video_url_path)

    return {
        "status": "success",
        "job_id": job_id,
        "original_filename": original_filename,
        "video_url": video_url_path
    }