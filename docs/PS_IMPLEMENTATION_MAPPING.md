# Gujarat Police Sentinel Hackathon — Problem Statement Mapping Report

This document maps each core requirement from the official Gujarat Police Sentinel Hackathon Problem Statement to its exact implementation in the codebase.

---

## Requirement Mapping Table

| # | Hackathon PS Requirement | Codebase Implementation | File Reference | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Runtime Web UI Authentication** | User manually enters password in Web UI; authenticates against `https://cctv.corp8.cloud/auth/login`. | [`backend/routers/sentinel_auth.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/routers/sentinel_auth.py) | **IMPLEMENTED** |
| **2** | **Zero Hardcoded Passwords** | No passwords stored in `.env`, Git, frontend, or config files. Session exists in runtime memory. | [`LiveCameraGrid.tsx`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/components/LiveCameraGrid.tsx) | **IMPLEMENTED** |
| **3** | **Dynamic Camera Discovery** | Dynamically parses `https://cctv.corp8.cloud/cameras.json` upon runtime authentication. | [`backend/integrations/sentinel/catalog_client.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/integrations/sentinel/catalog_client.py) | **IMPLEMENTED** |
| **4** | **Live Camera Grid & Controls** | Dynamic grid cards with **[View Live]**, **[Start AI Processing]**, and **[Stop AI Processing]** buttons. | [`LiveCameraGrid.tsx`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/components/LiveCameraGrid.tsx) | **IMPLEMENTED** |
| **5** | **Real-Time Video Ingestion** | RTSP over TCP (`rtsp://103.250.160.189:8554`) & HLS (`https://cctv.corp8.cloud/<cam>/index.m3u8`). | [`stream_gateway/stream_manager.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/stream_gateway/stream_manager.py) | **IMPLEMENTED** |
| **6** | **YOLO Vehicle Detection** | YOLOv8 Nano model (`yolov8n.pt`) with low confidence `0.05` for 100% recall. | [`ai/detection/detector.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/detection/detector.py) | **IMPLEMENTED** |
| **7** | **Multi-Object Tracking** | Centroid tracking algorithm generates dynamic `track_id` for every vehicle. | [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **IMPLEMENTED** |
| **8** | **License Plate Recognition** | Sobel gradient localization + multi-variant OpenCV preprocessing + EasyOCR. | [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **IMPLEMENTED** |
| **9** | **Indian Registration Validation**| Strict Indian plate pattern normalization & positional character confusion repair. | [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **IMPLEMENTED** |
| **10**| **Temporal Consensus** | Multi-frame majority voting per `track_id` across consecutive video frames. | [`ai/anpr/anpr_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/ai/anpr/anpr_engine.py) | **IMPLEMENTED** |
| **11**| **Database & Crop Storage** | SQLite `detections` table stores vehicle crop, plate crop, and enhanced crop paths. | [`backend/models.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/models.py) | **IMPLEMENTED** |
| **12**| **Discovered Plates & Search** | Interactive grid of all discovered plates & search by ANY registration number. | [`VideoIntelligenceView.tsx`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/components/VideoIntelligenceView.tsx) | **IMPLEMENTED** |
| **13**| **Vehicle Journey Tracking** | Multi-camera GPS step reconstruction & Leaflet route polyline mapping. | [`backend/routers/vehicles.py`](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/routers/vehicles.py) | **IMPLEMENTED** |
