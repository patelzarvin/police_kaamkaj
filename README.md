# Gujarat Police Sentinel — AI-Powered Unified CCTV Intelligence & Vehicle Tracking Platform

[![Gujarat Police Sentinel](https://img.shields.io/badge/Gujarat%20Police-Sentinel%20Hackathon%202026-blue)](https://sentinel.gujarat.gov.in)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-cyan)](https://react.dev/)
[![PostGIS](https://img.shields.io/badge/PostgreSQL-16%20%2B%20PostGIS-336791)](https://postgis.net/)

An enterprise-grade, modular, scalable, vendor-neutral CCTV intelligence and vehicle tracking platform developed for the **Gujarat Police Innovation Challenge 2026 (Sentinel)**.

---

## 🌟 Primary Mission & Capabilities

A police officer inputs a vehicle registration number (e.g. `GJ01AB1234`). The platform instantly:
1. **Queries PostGIS CCTV Detection Database**: Finds every historical & live detection.
2. **Displays ANPR Visual Evidence**: Bounding box crop, license plate crop, and OCR confidence metrics.
3. **Cross-References Watchlists**: Real-time correlation against Stolen, Wanted, and Suspicious vehicle databases with automated WebSocket push alert generation.
4. **Reconstructs Chronological Vehicle Journey**: Displays timeline progression across nodes (`Cam 01 @ 10:32 AM` -> `Cam 07 @ 10:41 AM` -> `Cam 19 @ 10:55 AM` -> `Cam 31 @ 11:08 AM`).
5. **Animates GIS Spatial Route**: Renders Leaflet GIS map with PostGIS spatial coordinates and trajectory polylines.

---

## 🏗 System Architecture & Sentinel Ingestion Contract

The system strictly adheres to the official Sentinel Camera Grid Integrator's Guide:
- **Dynamic Catalogue Integration (`/api/ingest`)**: Reads camera IDs, locations, codecs (`H.264`/`H.265`), resolutions, and stream URLs (`rtsp_url`, `hls_url`, `webrtc_url`).
- **Protocol Enforcers**: Mandatory `rtsp_transport=tcp` over RTP/RTSP, WebRTC (WHEP) for low-latency command center playback, and HLS fallback.
- **PTS Timestamp Extraction**: Uses Presentation Timestamp (`CAP_PROP_POS_MSEC`), eliminating reliance on inaccurate `CAP_PROP_FPS` or arrival time.
- **Fault-Tolerant Reconnector**: Exponential backoff reconnect loop (2s initial to 30s max cap) with IDR keyframe recovery.

---

## 🚀 Quick Start & One-Command Demo

### 1. Fast Start with Docker Compose
```bash
docker compose up --build
```
Access Police Command Center Dashboard at `http://localhost:3000` and API documentation at `http://localhost:8000/docs`.

### 2. Manual Local Development Setup
```bash
# Install Python backend dependencies
pip install -r requirements.txt

# Run Database Seeding
python database/seeds/seed_data.py

# Launch FastAPI Backend Core
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

In a second terminal:
```bash
# Install Frontend dependencies
cd frontend
npm install
npm run dev
```

### 3. Run One-Command Demo Flow Script
```bash
python scripts/demo_simulation.py
```

---

## 📁 Repository Structure

```
police_hack/
├── frontend/                # React 18 + TypeScript + Vite + Leaflet GIS Dashboard
├── backend/                 # FastAPI REST API, WebSockets & PostGIS ORM Models
│   ├── main.py              # Application entry point
│   ├── database.py          # SQLAlchemy Async Engine
│   ├── models.py            # PostgreSQL + PostGIS Schema
│   └── routers/             # Endpoints for Ingest, Cameras, Detections, Journey, Watchlist, Alerts
├── stream_gateway/          # Sentinel RTSP Stream Gateway & Catalogue Client
│   ├── catalog_client.py    # Official /api/ingest Catalogue Consumer
│   └── stream_manager.py    # RTSP TCP transport, PTS extractor & Backoff Reconnector
├── ai/                      # AI Analytics Engine
│   ├── detection/           # YOLO Vehicle Object Detector
│   ├── tracking/            # ByteTrack Multi-Object Tracker
│   ├── anpr/                # License Plate Localization & EasyOCR Normalizer
│   └── pipeline.py          # Stream-to-Alert Processing Pipeline
├── database/                # Seeding and Migration Scripts
├── tests/                   # Pytest Unit & API Integration Tests
├── docs/                    # Architectural & Requirements Documentation
├── docker-compose.yml       # Docker container orchestration
└── README.md
```
=======
# police_kaamkaj
>>>>>>> 69af17193e86e36a864afc939e9d234ebdb2d89b
