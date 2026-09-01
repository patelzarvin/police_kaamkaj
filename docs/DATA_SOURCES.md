# Gujarat Police Sentinel — Data Sources & Video Asset Registry

This document records all CCTV videos, traffic datasets, and model weights used by the Gujarat Police Sentinel platform for AI development, local video pipeline testing, and hackathon evaluation.

---

## 1. Local Video Streams & Testing Assets

| Asset Name | Source / Provider | URL / Access Path | License | Operational Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Synthetic CCTV Stream Generator** | OpenCV + MediaMTX RTSP Simulator | `data/videos/synthetic_traffic_stream.mp4` / `scripts/generate_test_video.py` | Open Source (Apache 2.0 / MIT) | Real-time frame decoding, YOLO vehicle detection, multi-object tracking, and ANPR crop generation in local dev environment. |
| **Pexels Free Traffic CCTV Video** | Pexels (Open Stock License) | `https://www.pexels.com/video/traffic-on-the-city-street-2053100/` | Pexels Free License (Commercial & Non-Commercial Use Allowed, No Attribution Required) | Live RTSP stream simulation via MediaMTX for multi-camera evaluation testing. |

---

## 2. Pretrained AI Models

| Model Name | Source / Developer | License | Purpose |
| :--- | :--- | :--- | :--- |
| **YOLOv8 Nano (`yolov8n.pt`)** | Ultralytics Inc. | AGPL-3.0 / Open Source | Real-time vehicle detection (Cars, Motorcycles, Buses, Trucks, Auto-rickshaws). |
| **EasyOCR (En)** | Jaided AI | Apache 2.0 | OCR text extraction for Indian standard license plates. |

---

## 3. Licensing Compliance Notice
- All video streams and datasets strictly adhere to open-source, CC0, or Pexels free licenses.
- No confidential, private, or unauthorized police surveillance data is stored or committed to the repository.
