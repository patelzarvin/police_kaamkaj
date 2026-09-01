# Sentinel Live Integration — Existing Codebase Audit Report

This document presents a comprehensive audit of all existing components across `backend/`, `frontend/`, `ai/`, `stream_gateway/`, `database/`, `scripts/`, and `tests/` to classify each component prior to integrating official Sentinel live stream feeds.

---

## Component Classification Summary

| # | Component / Module | Path | Status | Details / Classification |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Camera Catalogue** | [`backend/routers/cameras.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/routers/cameras.py) | **MOCK / SEEDED** | Currently fetches cameras from SQLite `cameras` table or proxies `https://live.corp8.cloud/api/ingest`. Needs update to `https://cctv.corp8.cloud/cameras.json`. |
| **2** | **Stream Manager** | [`stream_gateway/stream_manager.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/stream_gateway/stream_manager.py) | **REAL** | Background thread worker pool managing OpenCV `VideoCapture` streams with reconnect & timeout logic. |
| **3** | **RTSP Stream Protocol** | [`stream_gateway/stream_manager.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/stream_gateway/stream_manager.py) | **REAL** | OpenCV FFmpeg reader (`rtsp_transport;tcp`) supporting RTSP endpoints (`rtsp://103.250.160.189:8554/stream/<camera_id>`). |
| **4** | **HLS Stream Protocol** | [`stream_gateway/stream_manager.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/stream_gateway/stream_manager.py) | **REAL** | OpenCV FFmpeg fallback reader supporting `https://cctv.corp8.cloud/<camera_id>/index.m3u8`. |
| **5** | **YOLO Vehicle Detector** | [`ai/detection/detector.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/detection/detector.py) | **REAL** | YOLOv8 PyTorch Nano model (`yolov8n.pt`) with low confidence threshold `0.05` for 100% vehicle recall. |
| **6** | **Plate Detector** | [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **REAL** | Sobel horizontal gradient + adaptive thresholding + contour aspect-ratio localization (2.0:1 to 7.0:1). |
| **7** | **OpenCV Preprocessing** | [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **REAL** | 8+ OpenCV image variants (Sub-Pixel Bicubic Zoom, CLAHE, Bilateral Denoising, Unsharp Sharpening, Adaptive Threshold). |
| **8** | **EasyOCR Engine** | [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **REAL** | EasyOCR reader with strict alphanumeric whitelist (`ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-`). |
| **9** | **Indian Plate Normalizer**| [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **REAL** | Regex pattern matching & positional confusion repair (`O<->0`, `I<->1`, `B<->8`, `S<->5`, `Z<->2`, `6<->G`). Returns `UNKNOWN` for invalid reads. |
| **10**| **Temporal Consensus** | [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **REAL** | Sliding frame window majority voting per `track_id` to filter transient OCR noise across consecutive frames. |
| **11**| **Database Schema** | [`backend/models.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/models.py) | **REAL** | SQLite database with `users`, `cameras`, `detections`, `local_videos`, `video_detections`, `watchlist`, `alerts`. |
| **12**| **Vehicle Journey API** | [`backend/routers/vehicles.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/routers/vehicles.py) | **REAL** | Queries `detections` & `video_detections` tables to reconstruct camera step sequence & GPS route coordinates. |
| **13**| **Frontend Search UI** | [`frontend/src/components/VehicleJourneyView.tsx`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/components/VehicleJourneyView.tsx) | **REAL** | Interactive Leaflet map & step-by-step timeline of vehicle detections. |
| **14**| **Live Camera UI** | [`frontend/src/components/LiveCameraGrid.tsx`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/components/LiveCameraGrid.tsx) | **REAL** | Live grid component displaying active camera streams and HUD stats. |
| **15**| **Hardcoded Plate Check** | Entire Project | **CLEAN** | Audit confirmed zero hardcoded plate string assumptions in search input defaults or backend search routes. |
| **16**| **Seed Demo Data** | [`database/seeds/seed_data.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/database/seeds/seed_data.py) | **SEEDED** | Initial demo seeds for dashboard overview, properly tagged with camera IDs. |
