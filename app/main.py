import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import cv2
import uuid
import shutil
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from ultralytics import YOLO

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(title="Traffic AI Engine")
app.mount("/static", StaticFiles(directory="static"), name="static")

model = YOLO('yolov8m.pt') 

def save_to_neon(job_id, filename, total_cars, video_url):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # 1. Insert the new record
        cursor.execute("""
            INSERT INTO traffic_logs (job_id, filename, total_cars, video_url)
            VALUES (%s, %s, %s, %s)
        """, (job_id, filename, total_cars, video_url))
        
        # 2. AUTO-CLEAN: Keep only the 3 most recent records in the DB
        cursor.execute("""
            DELETE FROM traffic_logs 
            WHERE id NOT IN (
                SELECT id FROM traffic_logs 
                ORDER BY created_at DESC 
                LIMIT 3
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Job {job_id} saved. Database cleaned to keep only last 3 records.")
    except Exception as e:
        print(f"❌ Database Error: {e}")

@app.post("/api/v1/analyze")
async def analyze_video(file: UploadFile = File(...)):
    # Local Folder Cleanup: Keep only the 2 most recent files so the 3rd upload fits
    all_videos = sorted([os.path.join("static", f) for f in os.listdir("static") if f.endswith(".mp4")], 
                        key=os.path.getmtime)
    while len(all_videos) >= 3:
        old_file = all_videos.pop(0)
        if os.path.isfile(old_file): os.unlink(old_file)

    # File Setup
    original_filename = file.filename
    job_id = str(uuid.uuid4())[:8]
    input_path = os.path.join("data", original_filename)
    output_filename = f"output_{job_id}.mp4"
    output_path = os.path.join("static", output_filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # AI Processing
    cap = cv2.VideoCapture(input_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    counted_ids = set()
    vehicle_positions = {} 
    total_cars_passed = 0

    while True:
        ret, frame = cap.read()
        if not ret: break
        results = model.track(frame, classes=[2, 5, 7], persist=True, tracker="bytetrack.yaml", conf=0.35, verbose=False)
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            for box, track_id in zip(boxes, track_ids):
                center_y = int((box[1] + box[3]) / 2)
                if track_id not in counted_ids:
                    # Logic: if previous Y was above line and current Y is below line
                    if track_id in vehicle_positions and vehicle_positions[track_id] < int(height*0.5) <= center_y:
                        counted_ids.add(track_id)
                        total_cars_passed += 1
                vehicle_positions[track_id] = center_y
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        out.write(frame)

    cap.release()
    out.release()
    
    video_url_path = f"/static/{output_filename}"
    save_to_neon(job_id, original_filename, total_cars_passed, video_url_path)
    if os.path.exists(input_path): os.remove(input_path)

    return {
        "status": "success",
        "job_id": job_id,
        "original_filename": original_filename,
        "video_url": video_url_path
    }