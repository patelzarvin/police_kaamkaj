# Walkthrough — Multi-Source Video Intelligence & Real-Time Canvas AI Overlay System

We have successfully implemented the **Multi-Source Video Intelligence & Analysis Module** with **Real-Time HTML5 Canvas AI Bounding Box Overlays** and **Isolated Video Search**, while preserving the **Sentinel 30-Camera Live Grid (`https://live.corp8.cloud/api/ingest`) 100% intact**.

---

## 1. Accomplished Features & Verification

### A. Sentinel Live Camera Grid Preservation
- **Preserved unchanged**: The 30-camera Sentinel Live Camera Grid, RTSP over TCP transport, HLS/WHEP streaming, PTS-based timing, reconnection backoff, and live grid UI remain 100% intact.

### B. Multi-Source Local Video Intelligence (`GET /api/videos`)
- Automatically discovers all local surveillance video files inside `data/videos/`.
- Extracts video metadata (resolution, duration, FPS, total frames) via OpenCV.
- Categorizes videos into **Source Types**:
  - `REAL_WORLD`: Real-world wide-angle traffic surveillance (`gettyimages-1164849900-640_adpp.mp4`).
  - `SYNTHETIC_TEST`: Controlled offline test stream (`test_cctv_stream.mp4`).

### C. Background AI Indexing (`POST /api/videos/{video_id}/process`)
- Runs `YOLOv8` vehicle detection, crop extraction, license plate detection, `EasyOCR` text extraction, Indian plate normalization, and `TemporalConsensusTracker` across frames.
- Supports flexible processing modes:
  - `full` (Stride 1 - Every frame processed)
  - `balanced` (Stride 2 - Every 2nd frame processed)
  - `fast` (Stride 5 - Every 5th frame processed)

### D. Real-Time HTML5 Canvas AI Bounding Box Overlays
- Renders a transparent HTML5 `<canvas>` positioned over the `<video>` element in `VideoIntelligenceView.tsx`.
- Converts native video bounding box coordinates `[videoWidth, videoHeight]` to displayed player dimensions `[canvas.clientWidth, canvas.clientHeight]` dynamically.
- Draws color-coded AI bounding box overlays:
  - **Cyan (`#00f3ff`)**: Genuinely recognized plate (e.g. `CAR | DL2CA27993 | 68%`).
  - **Amber (`#ffb700`)**: Unrecognized plate (e.g. `CAR | PLATE UNKNOWN`).
- Live HUD indicator badge: `AI ANALYSIS OVERLAY ACTIVE | Vehicles: N | Recognized Plates: M`.

### E. Multi-Source Isolated Vehicle Search (`GET /api/videos/search/plates`)
- Allows filtering by specific video source OR searching across all local videos.
- Returns matching source filename, timestamp in seconds, frame index, vehicle class, confidence, plate crop thumbnail, and vehicle crop path.
- **Interactive Seek-to-Timestamp**: Clicking any search result item immediately opens the video in the player, sets `video.currentTime = timestamp_seconds`, and highlights the bounding box overlay.

---

## 2. Empirical API Verification Results

### `GET /api/videos`
```json
[
  {
    "video_id": "gettyimages-1164849900-640_adpp",
    "filename": "gettyimages-1164849900-640_adpp.mp4",
    "file_path": "/data/videos/gettyimages-1164849900-640_adpp.mp4",
    "source_type": "REAL_WORLD",
    "display_name": "Real-World Stock Traffic Footage",
    "resolution": "768x432",
    "duration_seconds": 19.96,
    "fps": 25.0,
    "total_frames": 499,
    "processing_status": "INDEXED",
    "total_detections": 487
  },
  {
    "video_id": "test_cctv_stream",
    "filename": "test_cctv_stream.mp4",
    "file_path": "/data/videos/test_cctv_stream.mp4",
    "source_type": "SYNTHETIC_TEST",
    "display_name": "Synthetic Test CCTV Stream",
    "resolution": "1280x720",
    "duration_seconds": 10.0,
    "fps": 25.0,
    "total_frames": 250,
    "processing_status": "INDEXED",
    "total_detections": 250
  }
]
```

### `GET /api/videos/search/plates?plate_number=DL2CA27993&source_id=all`
```json
{
  "query_plate": "DL2CA27993",
  "source_id": "all",
  "total_matches": 16,
  "results": [
    {
      "detection_id": 115,
      "video_id": "test_cctv_stream",
      "source_filename": "test_cctv_stream.mp4",
      "source_type": "SYNTHETIC_TEST",
      "source_display_name": "Synthetic Test CCTV Stream",
      "frame_number": 115,
      "video_timestamp_ms": 4600.0,
      "timestamp_seconds": 4.6,
      "vehicle_class": "Car",
      "vehicle_confidence": 0.94,
      "plate_number": "DL2CA27993",
      "plate_confidence": 0.67,
      "image_path": "/data/vehicle_crops/vehicle_DL2CA27993_test_cctv_stream-F115-D0.jpg",
      "plate_crop_path": "/data/plates/plate_DL2CA27993_test_cctv_stream-F115-D0.jpg"
    }
  ]
}
```

---

## 3. Modified & Created Files

- [backend/models.py](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/models.py): Added `LocalVideo` and `VideoDetection` database models.
- [backend/routers/video_intelligence.py](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/routers/video_intelligence.py): Created FastAPI router for video discovery, background indexing, canvas overlay detections, and isolated plate search.
- [backend/main.py](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/backend/main.py): Included `video_intelligence` router under prefix `/api`.
- [frontend/src/services/api.ts](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/services/api.ts): Added API client methods (`fetchLocalVideos`, `processLocalVideo`, `fetchVideoDetections`, `searchVideoPlates`).
- [frontend/src/components/VideoIntelligenceView.tsx](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/components/VideoIntelligenceView.tsx): Built complete React component with HTML5 Canvas AI Bounding Box Overlay player, source cards, and multi-source vehicle search.
- [frontend/src/components/Navigation.tsx](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/components/Navigation.tsx): Integrated `video_intel` tab with `Film` icon.
- [frontend/src/App.tsx](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/App.tsx): Integrated `VideoIntelligenceView` component into top-level dashboard layout.
- [frontend/src/types.ts](file:///c:/Users/DELL/OneDrive/Desktop/police_hack/frontend/src/types.ts): Corrected type definition for `CameraAsset.camera_id`.
