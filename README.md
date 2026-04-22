# 🏎️ Traffic AI Engine

![Python](https://img.shields.io/badge/Python-3.10-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-yellow)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker)

A containerized computer vision microservice that tracks vehicles in real-time, overlays analytics, and logs traffic density to a cloud database. 

> **[🎥 Watch the AI in action here](samples/sample_output.mp4)**

## 🧠 How It Works
1. **Upload:** Send a raw traffic video to the FastAPI endpoint.
2. **Process:** YOLOv8 and OpenCV track vehicles. A custom "tripwire" algorithm eliminates false positives (like shadows) by forcing vehicles to cross a strict detection zone.
3. **Store & Return:** The annotated video is saved, vehicle counts are pushed to a serverless PostgreSQL database (NeonDB), and a public URL is returned.

## 💻 Tech Stack
* **Backend:** FastAPI, Python
* **AI / Vision:** YOLOv8m (Ultralytics), OpenCV
* **Database:** PostgreSQL (NeonDB)
* **Infrastructure:** Docker

## 🚀 Quick Start (Docker)

1. Clone the repo and create a `.env` file with your `DATABASE_URL`.
2. Build and run the engine:
```bash
docker build -t traffic-engine-api .
docker run -p 8000:8000 -v "$(pwd)/static:/app/static" -v "$(pwd)/data:/app/data" traffic-engine-api
