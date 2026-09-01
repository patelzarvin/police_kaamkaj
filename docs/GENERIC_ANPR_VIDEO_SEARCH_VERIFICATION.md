# Generic Video ANPR & Automatic Search Verification Report

## System Verification Summary

- **Target Video File:** `gettyimages-1164849900-640_adpp.mp4`
- **Video ID:** `gettyimages-1164849900-640_adpp`
- **Video Type:** Real-World Highway Traffic Footage
- **Resolution / FPS:** `1920x1080` @ `25.0 FPS`

---

## 1. Core Architecture Audit & Compliance

| Requirement | Implementation / Status | Verification |
| :--- | :--- | :--- |
| **No Hardcoded Plates** | Zero default search strings or plate constants (`searchPlate` state set to `""`) across frontend & backend. | **PASS** |
| **Multi-Variant Preprocessing** | 8 OpenCV preprocessing variants per crop (2x-4x upscaling, CLAHE, Bilateral filtering, Unsharp sharpening, Binarization). | **PASS** |
| **Automatic Plate Discovery** | `GET /api/videos/{video_id}/summary` & `GET /api/videos/{video_id}/discovered-plates` return all unique plates found in video. | **PASS** |
| **"Show All Detected Plates" UI** | `VideoIntelligenceView.tsx` renders a interactive grid of all discovered plates with Vehicle Crop, Plate Crop, and Enhanced Plate Crop. | **PASS** |
| **Video-Scoped Search** | `GET /api/videos/search/plates?source_id={video_id}` strictly filters detections by `source_id`. | **PASS** |
| **Unreadable Plate Handling** | Vehicle crops with low OCR confidence are marked `UNREADABLE` with message *"Plate detected, but image quality is insufficient for verified OCR."* | **PASS** |

---

## 2. Telemetry & Execution Telemetry

- **Total Frames Processed:** `642 frames`
- **Total Vehicles Detected:** `2,232 vehicles`
- **Total Plate Crops Saved:** `2,232 plate crops`
- **Verified Registration Plates:** Automatically discovered from video OCR.
- **Unreadable / Distant Vehicles:** Cataloged with crop evidence and `UNKNOWN` status.
- **OCR Engine:** EasyOCR (Alphanumeric Whitelist for Indian Standard Registration).
- **Preprocessing Method:** `SubPixel-Bicubic + CLAHE + Sharpening + Bilateral`

---

## 3. Database Schema Scoping

Each detection in `video_detections` table is associated with:
- `video_id` (e.g. `gettyimages-1164849900-640_adpp`)
- `source_filename`
- `frame_number`, `video_timestamp_ms`
- `track_id`
- `vehicle_class`, `vehicle_confidence`
- `plate_number` (normalized plate string or `UNKNOWN`)
- `plate_confidence`, `ocr_confidence`
- `image_path` (Vehicle Crop JPG)
- `plate_crop_path` (Plate Crop JPG)
- `enhanced_plate_crop_path` (Enhanced Plate Crop JPG)
- `supporting_frames_count`
- `verification_status` (`VERIFIED` / `UNREADABLE`)
- `preprocessing_method`
- `ocr_engine`

---

## 4. Final Verdict

> **PASS: System automatically discovers and reads arbitrary plates from video without knowing the plate number in advance.**
