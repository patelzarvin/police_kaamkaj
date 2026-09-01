# Official Sentinel Live Camera Grid Integration Guide

## Overview

The Gujarat Police Sentinel AI system integrates directly with the official Sentinel Live Camera Grid endpoints:

- **HLS Stream Pattern:** `https://cctv.corp8.cloud/<camera_id>/index.m3u8`
- **RTSP Stream Pattern (AI Input):** `rtsp://103.250.160.189:8554/stream/<camera_id>`
- **WebRTC WHEP Stream Pattern:** `http://103.250.160.189:8889/stream/<camera_id>/whep`
- **Catalogue Endpoint:** `https://cctv.corp8.cloud/cameras.json`

---

## Architecture Diagram

```
      Sentinel Live Camera Grid (https://cctv.corp8.cloud / 103.250.160.189)
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
   Browser Live Stream (HLS)                   RTSP Stream (OpenCV / TCP)
               │                                         │
   Frontend UI Grid Card                       Frame Decoder (PTS Timestamp)
               │                                         │
    HTML5 Video Player                       YOLOv8 Vehicle Detection (0.05 conf)
                                                         │
                                               Vehicle Centroid Tracker
                                                         │
                                             Plate Detection & Bounding Box
                                                         │
                                           OpenCV Multi-Variant Preprocessing
                                           (Sub-Pixel Bicubic, CLAHE, Bilateral)
                                                         │
                                              EasyOCR Alphanumeric Reader
                                                         │
                                           Indian Registration Normalization
                                                         │
                                             Temporal Multi-Frame Consensus
                                                         │
                                           SQLite Database & Crop Storage
                                                         │
                                           Search, Alerts, & Journey Timeline
```

---

## Authentication & Credentials Configuration

Sentinel server authentication is handled via session login or token authorization. Credentials are stored securely in `.env`:

```env
SENTINEL_HLS_HOST=https://cctv.corp8.cloud
SENTINEL_RTSP_HOST=103.250.160.189
SENTINEL_RTSP_PORT=8554
SENTINEL_WHEP_HOST=http://103.250.160.189:8889
SENTINEL_CATALOG_URL=https://cctv.corp8.cloud/cameras.json
SENTINEL_HLS_PASSWORD=<your_access_password>
```

When unauthenticated requests access `https://cctv.corp8.cloud/cameras.json`, the server returns a Sign In HTML page (`POST https://cctv.corp8.cloud/auth/login`). `SentinelCatalogClient` handles login gracefully and maintains session cookies.

---

## Multi-Variant OpenCV Preprocessing Pipeline

For low-quality or blurred plate crops, `ANPREngine` executes 8+ OpenCV image enhancement variants:
1. Original Crop
2. Sub-Pixel Bicubic Upscaling (`480px` min width)
3. Grayscale conversion
4. CLAHE Contrast Equalization (`clipLimit=4.0, tileGridSize=(8,8)`)
5. Bilateral Edge-Preserving Denoising (`d=9, sigmaColor=75, sigmaSpace=75`)
6. Sharpening / Unsharp Masking (`cv2.addWeighted`)
7. Otsu Binarization / Adaptive Thresholding

---

## Verification & Diagnostics

To execute full live system diagnostics:

```bash
python scripts/verify_sentinel_live.py
```
