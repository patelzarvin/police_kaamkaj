# Gujarat Police Sentinel — API Reference Specifications

---

## 1. Official Sentinel Ingestion Contract (`/api/ingest`)

### `GET /api/ingest`
Returns dynamic camera asset metadata contract per Sentinel Integrator's Guide.

**Sample Response (`200 OK`)**:
```json
[
  {
    "id": "CAM-01",
    "name": "Ahmedabad SG Highway - ISCON Cross Road",
    "department": "Home Department",
    "district": "Ahmedabad",
    "city": "Ahmedabad",
    "latitude": 23.0276,
    "longitude": 72.5074,
    "codec": "H264",
    "resolution": "1920x1080",
    "fps": 25.0,
    "live_status": "ONLINE",
    "rtsp_url": "rtsp://localhost:8554/stream/1",
    "hls_url": "http://localhost:8888/stream/1/index.m3u8",
    "webrtc_url": "http://localhost:8889/stream/1",
    "properties": {
      "transport": "tcp",
      "pts_timestamp_support": true
    }
  }
]
```

---

## 2. Vehicle Journey Reconstruction API

### `GET /api/vehicles/{plate_number}/journey`
Reconstructs multi-camera vehicle movement history sorted chronologically by Presentation Timestamp (PTS).

**Parameters**:
- `plate_number` (path): License registration number (e.g. `GJ01AB1234`).

**Sample Response (`200 OK`)**:
```json
{
  "plate_number": "GJ01AB1234",
  "vehicle_class": "Car",
  "total_detections": 4,
  "first_seen": "2026-08-22T11:47:00Z",
  "last_seen": "2026-08-22T12:23:00Z",
  "watchlist_status": "STOLEN",
  "watchlist_category": "STOLEN",
  "route_coordinates": [
    [23.0276, 72.5074],
    [23.1184, 72.5401],
    [23.2156, 72.6369],
    [23.1610, 72.6845]
  ],
  "journey_steps": [
    {
      "step_number": 1,
      "camera_id": "CAM-01",
      "camera_name": "Ahmedabad SG Highway - ISCON Cross Road",
      "timestamp": "2026-08-22T11:47:00Z",
      "formatted_time": "10:32 AM",
      "latitude": 23.0276,
      "longitude": 72.5074,
      "plate_number": "GJ01AB1234",
      "vehicle_class": "Car",
      "plate_confidence": 0.96,
      "detection_confidence": 0.94,
      "image_path": "/data/demo/vehicle_GJ01AB1234_crop.jpg",
      "plate_crop_path": "/data/demo/plate_GJ01AB1234_crop.jpg",
      "watchlist_status": "STOLEN"
    }
  ]
}
```

---

## 3. Real-Time Watchlist API

### `GET /api/watchlist`
Lists all active police watchlist entries.

### `POST /api/watchlist`
Adds a vehicle registration number to the police watchlist.

---

## 4. Real-Time Alert & WebSockets API

### `GET /api/alerts`
Retrieves automated watchlist alerts feed.

### `WS /ws/alerts`
WebSocket connection broadcasting real-time alert JSON payloads.
