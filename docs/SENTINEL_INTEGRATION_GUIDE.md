# Gujarat Police Sentinel Sandbox — Ingestion & Stream Integration Guide

Official Integration Reference & Pre-Submission Compliance Checklist for Gujarat Police Sentinel Sandbox (`https://sentinel.gujarat.gov.in/resource`).

---

## 1. Protocol & Catalogue Reference

Every camera in the Sentinel Sandbox is published as a live RTP/RTSP stream with monotonic Presentation Timestamps (PTS).

### Available Endpoints by Protocol

| Protocol | Endpoint Format | Intended Purpose |
| :--- | :--- | :--- |
| **RTSP** | `rtsp://<host>:8554/stream/<id>` | AI Inference (OpenCV, GStreamer, FFmpeg, DeepStream) |
| **WebRTC (WHEP)** | `http://<host>:8889/stream/<id>/whep` | Low-latency browser preview |
| **HLS** | `http://<host>/live/stream/<id>/index.m3u8` | Dashboards, mobile, restricted networks |

### Live Catalogue Contract (`GET /api/ingest`)

Always discover camera feeds dynamically via `/api/ingest`:

```bash
curl -s http://localhost:8000/api/ingest
```

Sample Catalogue Response:
```json
[
  {
    "id": "CAM-01",
    "name": "SG Highway Junction - Ahmedabad",
    "location": {
      "lat": 23.0225,
      "lng": 72.5714,
      "city": "Ahmedabad",
      "district": "Ahmedabad",
      "address": "SG Highway Crossroads"
    },
    "codec": "H264",
    "live": true,
    "rtsp_url": "rtsp://localhost:8554/stream/cam01",
    "whep_url": "http://localhost:8889/stream/cam01/whep",
    "hls_url": "http://localhost:8000/live/stream/cam01/index.m3u8",
    "stream_properties": {
      "resolution": "1920x1080",
      "declared_fps": 25,
      "transport": "tcp",
      "depayloader": "rtph264depay",
      "pts_monotonic": true,
      "reconnect_exponential_backoff": true
    }
  }
]
```

---

## 2. Pre-Submission Verification Checklist

| Checklist Item | Implementation Status | Technical Mechanism in Codebase |
| :--- | :--- | :--- |
| **1. Force RTSP over TCP** | `VERIFIED` | `os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"` set globally in `stream_gateway/stream_manager.py`. |
| **2. Timing driven by PTS (Not declared FPS / arrival time)** | `VERIFIED` | OpenCV `CAP_PROP_POS_MSEC` read per frame; wall-clock arrival time is ignored. |
| **3. Tolerance to inter-frame gaps** | `VERIFIED` | Thread-safe ring buffer (`queue.Queue(maxsize=30)`) handles variable frame delivery without stalling pipelines. |
| **4. Exponential Backoff Reconnection** | `VERIFIED` | `CameraStreamWorker._handle_reconnect()` starts at 2s and caps at 30s (`min(delay * 1.5, 30.0)`). |
| **5. Non-fatal join decoder warnings** | `VERIFIED` | Mid-stream join decoder warnings are caught in worker thread loop and self-correct on the first IDR keyframe. |
| **6. Catalogue Dynamic Discovery** | `VERIFIED` | `SentinelIngestCatalogue.fetch_catalogue()` fetches live streams directly from `/api/ingest`. |
| **7. Mixed H.264 / H.265 & Resolution Support** | `VERIFIED` | OpenCV FFmpeg backend handles H.264/H.265 dynamically based on depayloader; YOLO detector resizes inputs to $640 \times 640$. |
| **8. Scene Discontinuity & Loop Recovery** | `VERIFIED` | `TemporalConsensusTracker` uses sliding window confidence decay to gracefully reset track states at stream cuts. |
| **9. Read-only Consumption** | `VERIFIED` | System strictly consumes streams from gateway endpoints; no stream publishing or control API calls. |
| **10. Load Pacing** | `VERIFIED` | Dedicated `CameraStreamWorker` threads only ingest active cameras; inactive streams stop cleanly via `.stop()`. |

---

## 3. Code Integration Examples

### OpenCV Python Client (RTSP Over TCP)
```python
import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
import cv2

cap = cv2.VideoCapture("rtsp://localhost:8554/stream/cam01", cv2.CAP_FFMPEG)
while cap.isOpened():
    ok, frame = cap.read()
    if not ok:
        break # Reconnect with backoff
    pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
```

### FFmpeg / FFplay CLI Inspection
```bash
ffplay -rtsp_transport tcp rtsp://localhost:8554/stream/cam01
ffprobe -rtsp_transport tcp rtsp://localhost:8554/stream/cam01
```
