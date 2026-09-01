# DATA FLOW AUDIT — Gujarat Police Sentinel Platform

**Audit Date**: August 22, 2026  
**Auditor**: Lead Architect & Engineering Team  
**Scope**: Codebase Data Flow, API Sources, AI Inference Status, and Seed/Mock Attribution

---

## 1. Executive Summary & Audit Purpose

This audit evaluates whether the current Gujarat Police Sentinel application processes live video frames via real-time AI/ANPR pipelines or presents mock, seeded, or hardcoded demonstration data.

**Key Finding**: The backend API (`GET /api/vehicles/{plate}/journey`) and database schema are **REAL and fully functional**, but the actual detection records returned (such as vehicle `GJ01AB1234`, 4 detections, timestamps, confidence scores, and Unsplash stock bus images) are **SEEDED DATABASE RECORDS and HARDCODED FRONTEND PLACEHOLDERS**. The live AI inference loop (`ai/pipeline.py`) is implemented in code but was **NOT actively processing live video streams**.

---

## 2. Component Data Flow Analysis

### ## Frontend
- **API Consumed**: `GET /api/vehicles/{plate}/journey`, `GET /api/cameras`, `GET /api/alerts`, `GET /api/health`.
- **Hardcoded / Static Fallbacks**:
  - `frontend/src/components/VehicleJourneyView.tsx` (Line 140): Hardcoded Unsplash stock bus image URL (`https://images.unsplash.com/photo-1544620347-c4fd4a3d5957...`) used as a placeholder frame preview.
  - `frontend/src/components/DashboardOverview.tsx` (Line 105): Hardcoded Unsplash stock bus image URL.
  - `frontend/src/components/LiveCameraGrid.tsx` (Line 35): Hardcoded Unsplash stock bus image URL.
  - `frontend/src/App.tsx` (Line 16): Default state target plate `'GJ01AB1234'`.
  - `frontend/src/services/api.ts` (Lines 110–190): Hardcoded static fallback object returned if the FastAPI backend is offline.

### ## Backend
- **Endpoints**: `GET /api/vehicles/{plate}/journey` in `backend/routers/vehicles.py`, `GET /api/ingest` in `backend/routers/ingest.py`, `GET /api/cameras` in `backend/routers/cameras.py`.
- **API Reality**: The API logic is 100% real FastAPI python code executing SQL queries (`select(Detection).where(Detection.plate_number == plate)`). However, it queries tables containing pre-seeded database rows.

### ## Database
- **Tables**: `users`, `cameras`, `detections`, `watchlist`, `alerts`, `vehicles`.
- **Data Origin**: Pre-populated at startup by `database/seeds/seed_data.py`.
- **Seeded Rows**:
  - `GJ01AB1234` inserted into `vehicles` table.
  - 4 Detection rows (`DET-1001`, `DET-1002`, `DET-1003`, `DET-1004`) inserted into `detections` table with hardcoded coordinates, timestamps, and confidence values (`0.96`, `0.98`, `0.95`, `0.97`).
  - 1 Watchlist row (`GJ01AB1234` - STOLEN) inserted into `watchlist` table.
  - 1 Alert row inserted into `alerts` table.

### ## AI Pipeline
- **Status**: **NOT ACTIVELY RUNNING LIVE**.
- **Code Inspection**: `ai/detection/detector.py` contains valid YOLOv8 wrapper code, and `ai/pipeline.py` contains frame processing logic, but the pipeline daemon was not launched to decode live video files or RTSP streams into frames.

### ## ANPR/OCR
- **Status**: **IMPLEMENTED IN CODE & TESTED VIA UNIT TESTS, BUT NOT RUNNING ON LIVE VIDEO**.
- **Code Inspection**: `ai/anpr/anpr_engine.py` contains EasyOCR and regex plate normalizer (`normalize_plate`). 5 unit tests passed in `tests/test_anpr_normalizer.py`. However, during app startup, OCR is not actively executing on camera frames; the OCR confidence scores displayed (`96%`, `98%`) came from database seed columns.

### ## Tracking
- **Status**: **MOCK / SEEDED**.
- **Code Inspection**: Seed data assigns static `track_id=101`. ByteTrack multi-object tracking is not actively computing feature vectors or Kalman filters on video.

### ## CCTV
- **Status**: **NOT PROCESSING LIVE FOOTAGE**.
- **Code Inspection**: No local MP4 file or live RTSP stream was actively being demuxed frame-by-frame by OpenCV/FFmpeg into the detection pipeline during app execution.

### ## Sentinel
- **Status**: **SIMULATED LOCAL CONTRACT**.
- **Code Inspection**: `backend/routers/ingest.py` mimics the Sentinel `/api/ingest` camera catalogue contract locally returning 8 seed cameras across Gujarat. No live government RTSP credentials or host URL were provided.

---

## 3. Direct Answers to Audit Questions

1. **Where does `GJ01AB1234` come from?**
   - Seeded in database via `database/seeds/seed_data.py` (L120, L142-145, L185) and set as default search state in `frontend/src/App.tsx` (L16).
2. **Where do the 4 detections come from?**
   - Inserted into database table `detections` by `database/seeds/seed_data.py` (L142–160).
3. **Where do the timestamps come from?**
   - Seeded in `database/seeds/seed_data.py` (L137–140) as `now - 45m`, `now - 36m`, `now - 22m`, `now - 9m`.
4. **Where do the camera locations come from?**
   - Seeded in `database/seeds/seed_data.py` (L11–110) for 8 Gujarat cameras.
5. **Where does the vehicle image come from?**
   - Hardcoded Unsplash stock bus image URL (`https://images.unsplash.com/photo-1544620347-c4fd4a3d5957...`) in `VehicleJourneyView.tsx` (L140).
6. **Where does OCR confidence come from?**
   - Seeded float values (`0.96`, `0.98`, `0.95`, `0.97`) in `seed_data.py` (L142–145).
7. **Where does the STOLEN watchlist status come from?**
   - Seeded row in `watchlist` table in `seed_data.py` (L115–123).
8. **Is any of this hardcoded in frontend?**
   - YES (Default search plate string `'GJ01AB1234'`, Unsplash bus image URL, fallback API object).
9. **Is any of this seeded in the database?**
   - YES (`database/seeds/seed_data.py` pre-populates PostgreSQL/SQLite DB).
10. **Is there a real API generating these results?**
    - YES (`GET /api/vehicles/{plate}/journey` in `backend/routers/vehicles.py` is real SQL execution), but it queries seeded table rows.
11. **Is YOLO actually running?**
    - NO (Code exists in `ai/detection/detector.py`, but frame loop was inactive).
12. **Is OCR actually running?**
    - NO (Code exists in `ai/anpr/anpr_engine.py`, but frame loop was inactive).
13. **Is vehicle tracking actually running?**
    - NO (`track_id=101` was static seed integer).
14. **Is any CCTV video actually being processed?**
    - NO (No video file or stream demuxing loop was active).
15. **Is Sentinel camera catalogue/API actually connected?**
    - NO (Local `/api/ingest` simulator endpoint).
16. **Is any RTSP stream actually being consumed?**
    - NO (`StreamManager` thread loop was inactive).
17. **Are detections generated from video frames or inserted as seed data?**
    - **INSERTED AS SEED DATA**.

---

## 4. REAL vs MOCK STATUS TABLE

| Feature | REAL | MOCK/SEEDED | NOT IMPLEMENTED |
| :--- | :---: | :---: | :---: |
| **FastAPI REST API Architecture** | ✅ REAL | | |
| **PostgreSQL + PostGIS Schema** | ✅ REAL | | |
| **ANPR Regex Normalizer Code** | ✅ REAL | | |
| **Camera Catalogue Contract (`/api/ingest`)** | ✅ REAL | | |
| **Vehicle Journey Database Query** | ✅ REAL | | |
| **Vehicle Detections Data** | | ⚠️ SEEDED | |
| **Vehicle Registration Number (`GJ01AB1234`)** | | ⚠️ SEEDED | |
| **Detection Timestamps & Coordinates** | | ⚠️ SEEDED | |
| **OCR Confidence Metrics** | | ⚠️ SEEDED | |
| **Watchlist Matches (`STOLEN`)** | | ⚠️ SEEDED | |
| **Vehicle Image Crops** | | ⚠️ HARDCODED (Unsplash) | |
| **Live CCTV Video Processing** | | ⚠️ NOT ACTIVE | |
| **Live RTSP Ingestion Worker** | | ⚠️ NOT ACTIVE | |
| **YOLO Live Frame Inference** | | ⚠️ NOT ACTIVE | |
| **ByteTrack Feature Tracking** | | | ❌ NOT IMPLEMENTED |
| **Vehicle Re-ID Embeddings** | | | ❌ NOT IMPLEMENTED |

---

## 5. Exact Files & Functions Responsible for Mock/Seed Data

1. **`database/seeds/seed_data.py`** $\rightarrow$ `seed_database()`
   - Inserts `GJ01AB1234` detections `DET-1001` to `DET-1004`, timestamps, coordinates, and watchlist alert into DB.
2. **`frontend/src/components/VehicleJourneyView.tsx`** $\rightarrow$ Line 140
   - Uses hardcoded `https://images.unsplash.com/photo-1544620347-c4fd4a3d5957...` static bus image.
3. **`frontend/src/components/DashboardOverview.tsx`** $\rightarrow$ Line 105
   - Uses hardcoded Unsplash bus image.
4. **`frontend/src/components/LiveCameraGrid.tsx`** $\rightarrow$ Line 35
   - Uses hardcoded Unsplash bus image.
5. **`frontend/src/services/api.ts`** $\rightarrow$ `fetchVehicleJourney()`
   - Contains fallback static journey array.
