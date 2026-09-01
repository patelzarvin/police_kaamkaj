# 🔴 USER ACTIONS TRACKER — Gujarat Police Sentinel

This document maintains required user inputs, credentials, hardware context, and environment prerequisites for the Gujarat Police Sentinel hackathon project.

---

## 🔴 DO NOW (Action Required / Information Request)

### Item 1: Sentinel Sandbox Credentials & Endpoint Access (Optional)
- **What I need**: Registration status, Sentinel Sandbox login credentials / API Key, or base URL for live `/api/ingest` camera catalogue if assigned.
- **Why**: To connect the Stream Gateway directly to official Government live RTSP/WebRTC feeds.
- **Where to provide it**: In your `.env` file.
- **Can development continue without it?**: **YES**. Development continues immediately using simulated live RTSP streams via local MediaMTX / FFmpeg and synthetic Sentinel camera catalogue metadata endpoints.

---

## 🟡 DO LATER (Non-Blocking Infrastructure Details)

### Item 2: Target Deployment Hardware Details
- **What I need**: CPU model, RAM, GPU model & VRAM, CUDA version, free disk space on your local system / target server.
- **Why**: To optimize batching size for YOLO and worker pool scaling.
- **Can development continue without it?**: **YES**. Initial AI worker defaults to CPU with CUDA auto-detection enabled.

---

## 🟢 COMPLETED

- [x] Extracted and analyzed official Gujarat Police Sentinel Problem Statement & Resource Integrator's Guide.
- [x] Authored `docs/REQUIREMENTS.md` and `docs/ARCHITECTURE.md`.
- [x] Built FastAPI async core backend (`backend/main.py`, `backend/database.py`, `backend/models.py`, `backend/schemas.py`).
- [x] Built Sentinel Catalogue Contract router (`backend/routers/ingest.py`).
- [x] Built Vehicle Journey Reconstruction API (`/api/vehicles/{plate}/journey`).
- [x] Built Watchlist & Alert Engine routers (`backend/routers/watchlist.py`, `backend/routers/alerts.py`).
- [x] Built Stream Gateway with RTSP TCP transport, PTS timestamp extraction, and exponential backoff reconnects (`stream_gateway/stream_manager.py`).
- [x] Built YOLO Vehicle Object Detector & ANPR Engine (`ai/detection/detector.py`, `ai/anpr/anpr_engine.py`).
- [x] Built AI Pipeline (`ai/pipeline.py`) connecting streams -> detection -> ANPR -> PostGIS -> WebSockets.
- [x] Built React + TypeScript + Vite + Tailwind CSS + Leaflet GIS Command Center Dashboard UI (`frontend/src/`).
- [x] Created `docker-compose.yml`, `.env.example`, and seed dataset (`database/seeds/seed_data.py`).
- [x] Authored and passed 100% unit and integration tests (`tests/test_anpr_normalizer.py`, `tests/test_journey.py`).
- [x] Authored complete documentation (`README.md`, `SETUP.md`, `API.md`, `SCALABILITY.md`, `PERFORMANCE.md`, `DEMO_GUIDE.md`, `HACKATHON_SUBMISSION.md`).
