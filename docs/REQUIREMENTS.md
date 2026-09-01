# Gujarat Police Sentinel — AI-Powered Unified CCTV Intelligence Platform
## Requirements Specification & Functional Scope

---

## 1. Executive Overview & Official Problem Context

The Government of Gujarat (Home Department / State Crime Record Bureau) is conducting the **Gujarat Police Innovation Challenge 2026 (Sentinel)**. Currently, 26 government departments operate independent, siloed CCTV systems across Gujarat (~80,000 cameras across border districts to coastal cities like Valsad, Dahod, Somnath, Jamnagar, and Dwarka).

### Primary Objective
Build a unified, modular, scalable, vendor-neutral **CCTV Intelligence and Vehicle Tracking Platform** that:
1. Ingests live streams (RTSP/RTP, WebRTC, HLS) via an `/api/ingest` catalogue contract.
2. Performs real-time AI analytics (Vehicle Detection, License Plate Recognition / ANPR with PaddleOCR/YOLO).
3. Indexes detections with PostGIS spatial coordinates, timestamps (PTS-driven), confidence, and vehicle attributes.
4. Reconstructs vehicle movement history across multiple camera feeds (`GJ01AB1234` timeline & route visualization).
5. Cross-references detections with representative Watchlists (Stolen, Wanted, Suspicious) and generates automated real-time alerts.
6. Integrates with state databases (VAHAN, SARTHI, eGujCop/CCTNS, AFIS/NAFIS readiness).
7. Visualizes GIS layers, live camera health, route trajectories, and command center analytics.

---

## 2. Key Functional Requirements

### F1. Sentinel Camera Catalog & Feed Ingestion Gateway
- Dynamic ingestion from `/api/ingest` endpoint yielding camera metadata (`id`, `location`, `codec`, `status`, `rtsp_url`, `hls_url`, `webrtc_url`).
- Protocol handling: Mandatory `rtsp_transport=tcp` over RTP/RTSP, WebRTC/WHEP low-latency preview, and HLS fallback.
- Codec support: Mixed H.264 & H.265 (with dynamic depayloaders: `rtph264depay` / `rtph265depay`), mixed resolutions, and variable bitrates.
- Stream Health & Fault Tolerance: Reconnection engine using exponential backoff (2s initial to 30s cap), decoder error tolerance (IDR frame synchronization), non-blocking frame buffer queueing.
- Accurate Timestamping: Presentation Timestamp (PTS / `CAP_PROP_POS_MSEC`) driven timeline tracking; strictly avoids `CAP_PROP_FPS` or wall-clock arrival time.

### F2. Real-Time AI Vehicle Analytics & Tracking
- **Vehicle Detection**: YOLO-based detection covering Cars, Motorcycles, Buses, Trucks, and Auto-rickshaws with bounding boxes and confidence scoring.
- **Vehicle Tracking**: Multi-object tracking using ByteTrack / BoT-SORT to assign persistent `track_id` per camera session.
- **ANPR (Automatic Number Plate Recognition)**:
  - Plate localization crop.
  - Image preprocessing (contrast enhancement, bilateral filtering, deskewing).
  - OCR Engine (PaddleOCR / EasyOCR) for text extraction.
  - Text Normalization (Indian standard plate formats e.g. `GJ01AB1234` regex normalization, character confusion repair `O->0, I->1`).
  - Confidence scoring and crop image persistence.

### F3. Real-Time Watchlist & Alert Engine
- Categorized Watchlist database (Stolen, Wanted, Suspicious, Unregistered).
- Instant cross-referencing upon ANPR extraction.
- Automated alert trigger: Severity classification (CRITICAL, HIGH, MEDIUM), camera location tag, vehicle metadata, timestamp, image crop.
- Push delivery via WebSocket to Police Command Center Dashboard.

### F4. Vehicle Journey Reconstruction & Multi-Camera Trajectory
- Query interface for license plate search (`GJ01AB1234`).
- Sequential chronological sorting of detection events across camera nodes.
- Inter-camera route graph calculation: Displays timeline (`Cam 01 @ 10:32` -> `Cam 07 @ 10:41` -> `Cam 19 @ 10:55` -> `Cam 31 @ 11:08`).
- GIS Route Animation: Leaflet/MapLibre map rendering animated polylines connecting detected camera locations with PostGIS spatial topology.

### F5. Police Command Center Dashboard UI
- **Design Language**: Futuristic dark command-center aesthetic, information-dense, sleek glassmorphism, responsive grid.
- **Live Video Grid**: Multi-camera stream playback (WebRTC / HLS relay).
- **Interactive GIS Map**: Real-time camera markers (online/offline status), coverage heatmap, alert pins, vehicle route overlay.
- **ANPR Search & Intelligence Hub**: Multi-attribute filtering (Plate, Date/Time, Camera ID, Vehicle Type, Watchlist Flag).
- **Alert Desk**: Live alert feed with sound/visual pulse, read/unread management, dispatch notes.
- **System Health Monitor**: Stream gateway worker status, CPU/GPU utilization, reconnection metrics.

---

## 3. Technical & Non-Functional Requirements

| Requirement Area | Specification & Technical Rule |
| :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.11+), Pydantic v2 async endpoints, OpenAPI auto-docs. |
| **Frontend Framework** | React 18, TypeScript, Vite, Tailwind CSS, Lucide icons, Leaflet / MapLibre GL. |
| **Database & GIS** | PostgreSQL 16 + PostGIS extension, SQLAlchemy 2.0 async ORM, Alembic migrations. |
| **Caching & Messaging** | Redis 7 for cache, pub/sub alert broad-casting, and stream status tracking. |
| **AI Frameworks** | PyTorch, Ultralytics YOLOv8/v11, ByteTrack, PaddleOCR / EasyOCR. |
| **Stream Processing** | FFmpeg, MediaMTX RTSP relay, OpenCV with `rtsp_transport=tcp`. |
| **Scalability Target** | Modular edge-worker architecture designed to scale to ~80,000 cameras using Kafka/RabbitMQ event streams and GPU cluster pools. |
| **Security** | JWT Authentication, Argon2/Bcrypt password hashing, Role-Based Access Control (RBAC), zero hardcoded secrets. |
| **Demo Resilience** | Seamless fallback mode supporting simulated RTSP / local CCTV MP4 video streams via MediaMTX alongside official Sentinel live grid endpoints. |
