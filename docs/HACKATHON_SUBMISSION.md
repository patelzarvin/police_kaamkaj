# Gujarat Police Sentinel — Official Hackathon Submission Report

---

## Executive Summary

- **Project Title**: Gujarat Police Sentinel — AI-Powered Unified CCTV Intelligence & Vehicle Tracking Platform
- **Challenge**: Gujarat Police Innovation Challenge 2026 (Sentinel)
- **Target Use Case**: Unified multi-department CCTV stream ingestion (~80,000 cameras), real-time ANPR analytics, watchlist cross-referencing, automated alert generation, and vehicle movement reconstruction (`GJ01AB1234`).
- **Core Technology Stack**: React 18, TypeScript, Vite, Tailwind CSS, Leaflet GIS, FastAPI, Async SQLAlchemy, PostgreSQL + PostGIS, Redis, YOLOv8/v11, EasyOCR, OpenCV, FFmpeg, RTSP over TCP.

---

## Submission Checklist Compliance

- [x] **Catalogue API Ingestion (`/api/ingest`)**: Fully implemented dynamically parsing camera properties, codecs, and stream URLs.
- [x] **RTSP Over TCP Transport**: Enforced across stream workers to eliminate UDP NAT/firewall frame corruption.
- [x] **Presentation Timestamp (PTS) Tracking**: Driven by frame PTS (`CAP_PROP_POS_MSEC`) to guarantee timing accuracy without relying on `CAP_PROP_FPS`.
- [x] **Vehicle Journey Reconstruction (`/api/vehicles/{plate}/journey`)**: Reconstructs chronological movement timeline across camera nodes (`Cam 01` -> `Cam 07` -> `Cam 19` -> `Cam 31`).
- [x] **GIS Spatial Trajectory Map**: Visualizes Leaflet GIS map with PostGIS spatial coordinates and trajectory polylines.
- [x] **Watchlist Cross-Referencing & Real-Time Alerts**: Automated alert generation for Stolen, Wanted, and Suspicious vehicles pushing live alerts via WebSockets.
- [x] **~80,000 Camera Scalability Plan**: Detailed federated architecture strategy in `docs/SCALABILITY.md`.
- [x] **Automated Unit & Integration Tests**: 100% passing tests in `tests/test_anpr_normalizer.py` and `tests/test_journey.py`.
