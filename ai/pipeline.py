import os
import cv2
import time
import asyncio
import logging
import datetime
import numpy as np
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from backend.database import AsyncSessionLocal
from backend.models import Camera, Detection, Watchlist, Alert
from backend.ws_manager import ws_manager
from backend.config import settings
from stream_gateway.stream_manager import StreamManager

logger = logging.getLogger("sentinel.ai.pipeline")

class PipelineHealthTracker:
    """Tracks live operational metrics and stores latest annotated video frames per camera."""
    def __init__(self):
        self.start_time = time.time()
        self.frames_processed = 0
        self.detections_generated = 0
        self.ocr_attempts = 0
        self.ocr_valid_plates = 0
        self.ocr_conf_sum = 0.0
        self.db_inserts = 0
        self.errors_count = 0
        self.last_inference_ms = 0.0
        self.latest_frames: Dict[str, bytes] = {}
        self._fallback_frame: Optional[bytes] = None

    def _get_fallback_frame(self) -> bytes:
        if self._fallback_frame is None:
            # Generate 640x360 dark placeholder image with CCTV overlay text
            img = np.zeros((360, 640, 3), dtype=np.uint8)
            img[:, :] = (15, 23, 35) # Dark slate background
            cv2.putText(img, "SENTINEL CCTV FEED - CONNECTING...", (120, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 215, 255), 2)
            cv2.putText(img, "LIVE RTSP/TCP INGESTION ACTIVE", (160, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 200, 120), 1)
            ok, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            self._fallback_frame = buf.tobytes() if ok else b""
        return self._fallback_frame

    def set_latest_frame(self, camera_id: str, frame: np.ndarray):
        try:
            ok, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), settings.FRAME_JPEG_QUALITY])
            if ok:
                self.latest_frames[camera_id] = buffer.tobytes()
        except Exception as e:
            logger.error(f"Error encoding frame for {camera_id}: {e}")

    def get_latest_frame_jpeg(self, camera_id: str) -> bytes:
        return self.latest_frames.get(camera_id) or self._get_fallback_frame()

    def get_summary(self, stream_manager: StreamManager) -> dict:
        uptime = time.time() - self.start_time
        stream_metrics = stream_manager.get_stream_metrics()
        fps = round(self.frames_processed / max(1.0, uptime), 1)
        valid_rate = round((self.ocr_valid_plates / max(1, self.ocr_attempts)) * 100, 1)
        avg_conf = round((self.ocr_conf_sum / max(1, self.ocr_attempts)) * 100, 1)
        
        return {
            "processing_mode": "REAL_VIDEO_PROCESSING",
            "uptime_seconds": round(uptime, 1),
            "stream_status": "ACTIVE" if stream_metrics["active_streams"] > 0 else "IDLE",
            "active_streams": stream_metrics["active_streams"],
            "frames_received": stream_metrics["total_frames_read"],
            "frames_processed": self.frames_processed,
            "pipeline_fps": fps,
            "yolo_inference_ms": round(self.last_inference_ms, 2),
            "detections_generated": self.detections_generated,
            "ocr_attempts": self.ocr_attempts,
            "ocr_valid_plates": self.ocr_valid_plates,
            "ocr_valid_plate_rate": valid_rate,
            "ocr_avg_confidence": avg_conf,
            "db_inserts": self.db_inserts,
            "reconnects_and_errors": self.errors_count
        }

global_health_tracker = PipelineHealthTracker()

class SentinelAIPipeline:
    """
    Real Video Processing AI Pipeline with 2-Stage ANPR & Temporal Consensus.
    - YOLO Vehicle Detection
    - Centroid Multi-Object Tracking
    - Dedicated License Plate Locator & Image Preprocessing (CLAHE, Bilateral)
    - EasyOCR Alphanumeric Recognition
    - Indian Plate Normalization & Validation (UNKNOWN for low conf)
    - Temporal Consensus Aggregation per track_id
    """
    def __init__(self, stream_manager: Optional[StreamManager] = None):
        self.stream_manager = stream_manager or StreamManager()
        self.detector = None
        self.tracker = None
        self.anpr = None
        self.consensus_tracker = None
        self.is_running = False
        self._camera_rotation_index = 0
        self._pipeline_cameras: List[Camera] = []
        self._models_ready = False

    def _ensure_models(self):
        """Lazy-load heavy YOLO + EasyOCR only when pipeline actually starts."""
        if self._models_ready:
            return
        from ai.detection.detector import VehicleDetector
        from ai.tracking.tracker import CentroidTracker
        from ai.anpr.anpr_engine import ANPREngine, TemporalConsensusTracker
        self.detector = VehicleDetector()
        self.tracker = CentroidTracker()
        self.anpr = ANPREngine()
        self.consensus_tracker = TemporalConsensusTracker()
        self._models_ready = True

    @staticmethod
    def _prepare_frame(frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        target_w = settings.PIPELINE_FRAME_WIDTH
        if w <= target_w:
            return frame
        scale = target_w / float(w)
        return cv2.resize(frame, (target_w, max(1, int(h * scale))), interpolation=cv2.INTER_AREA)

    async def process_camera_frame(self, camera_id: str, camera_name: str, lat: float, lon: float, frame_data: Any = None):
        """Process a single real frame from stream worker and update live stream frame."""
        if frame_data is None:
            frame_data = self.stream_manager.get_frame(camera_id)

        if not frame_data:
            return

        frame, pts_ms, cam_id = frame_data
        if frame is None or frame.size == 0:
            return

        frame = self._prepare_frame(frame)
        global_health_tracker.frames_processed += 1
        annotated_frame = frame.copy()
        h, w, _ = annotated_frame.shape

        # Publish raw live frame immediately (before heavy YOLO/OCR init)
        global_health_tracker.set_latest_frame(camera_id, annotated_frame)

        self._ensure_models()

        # 1. Run YOLO Vehicle Detection in thread pool to prevent event loop blocking
        t0 = time.time()
        detections = await asyncio.to_thread(self.detector.detect_vehicles, frame)
        global_health_tracker.last_inference_ms = (time.time() - t0) * 1000.0

        if not detections:
            # Draw HUD overlays even if no vehicle detected in frame
            cv2.putText(annotated_frame, f"LIVE RTSP/TCP | {camera_id}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 120), 2, cv2.LINE_AA)
            cv2.putText(annotated_frame, f"PTS: {int(pts_ms)} ms", (w - 170, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)
            global_health_tracker.set_latest_frame(camera_id, annotated_frame)
            return

        # 2. Update Dynamic Multi-Object Vehicle Tracker (ByteTrack/Centroid)
        tracked_detections = self.tracker.update(detections)

        for det in tracked_detections:
            global_health_tracker.detections_generated += 1
            bbox = det["bbox"]
            v_class = det["vehicle_class"]
            det_conf = float(det["confidence"])
            track_id = det.get("track_id", 101)
            crop = det["crop"]

            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

            # 3. Dedicated Plate Locator, Preprocessing, & EasyOCR in thread pool
            global_health_tracker.ocr_attempts += 1
            anpr_res = await asyncio.to_thread(self.anpr.process_vehicle_crop, crop)

            raw_plate = "UNKNOWN"
            raw_conf = 0.0
            is_valid = False
            plate_crop = crop

            if anpr_res:
                raw_plate = anpr_res["plate_number"]
                raw_conf = float(anpr_res["confidence"])
                is_valid = anpr_res["valid_plate"]
                plate_crop = anpr_res["plate_crop"]

            global_health_tracker.ocr_conf_sum += raw_conf

            # 4. Temporal OCR Consensus Aggregation across frames for this track_id
            self.consensus_tracker.add_detection(track_id, raw_plate, raw_conf, is_valid)
            plate_number, consensus_conf, consensus_valid = self.consensus_tracker.get_consensus_plate(track_id)

            if consensus_valid:
                global_health_tracker.ocr_valid_plates += 1

            # 5. Draw Bounding Box & HUD Label on Annotated Frame for Live Camera Grid
            box_color = (255, 230, 0) if consensus_valid else (0, 165, 255) # Cyan if valid ANPR, Orange if searching
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)

            label_text = f"{plate_number} [ANPR {int(consensus_conf*100)}%]" if consensus_valid else f"{v_class} #{track_id}"
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated_frame, (x1, max(0, y1 - 25)), (x1 + tw + 10, y1), (15, 23, 42), -1)
            cv2.putText(annotated_frame, label_text, (x1 + 5, y1 - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            # 6. Save Actual Image Crops to Disk
            det_id = f"REAL-DET-{int(time.time()*1000)}"
            img_filename = f"vehicle_{plate_number}_{det_id}.jpg"
            plate_filename = f"plate_{plate_number}_{det_id}.jpg"

            os.makedirs(os.path.join("data", "vehicle_crops"), exist_ok=True)
            os.makedirs(os.path.join("data", "plates"), exist_ok=True)

            img_disk_path = os.path.join("data", "vehicle_crops", img_filename)
            plate_disk_path = os.path.join("data", "plates", plate_filename)

            cv2.imwrite(img_disk_path, crop)
            cv2.imwrite(plate_disk_path, plate_crop)

            web_img_path = f"/data/vehicle_crops/{img_filename}"
            web_plate_path = f"/data/plates/{plate_filename}"

            # 7. Insert Real Detection Event into Database
            async with AsyncSessionLocal() as db:
                timestamp = datetime.datetime.utcnow()

                db_det = Detection(
                    detection_id=det_id,
                    camera_id=camera_id,
                    timestamp=timestamp,
                    vehicle_class=v_class,
                    track_id=track_id,
                    plate_number=plate_number,
                    plate_confidence=consensus_conf,
                    detection_confidence=det_conf,
                    bbox_x1=x1, bbox_y1=y1, bbox_x2=x2, bbox_y2=y2,
                    image_path=web_img_path,
                    plate_crop_path=web_plate_path,
                    latitude=lat,
                    longitude=lon
                )
                db.add(db_det)
                global_health_tracker.db_inserts += 1

                # Check Real Watchlist Match (Only for valid recognized plates)
                if plate_number != "UNKNOWN":
                    wl_stmt = select(Watchlist).where(Watchlist.vehicle_number == plate_number, Watchlist.is_active == True)
                    wl_res = await db.execute(wl_stmt)
                    wl_item = wl_res.scalar_one_or_none()

                    if wl_item:
                        logger.info(f"🚨 REAL WATCHLIST ALERT TRIGGERED! Plate: {plate_number} at {camera_name} (Track #{track_id})")

                        alert = Alert(
                            detection_id=det_id,
                            watchlist_id=wl_item.id,
                            timestamp=timestamp,
                            camera_id=camera_id,
                            vehicle_number=plate_number,
                            alert_category=f"{wl_item.category}_VEHICLE",
                            priority=wl_item.priority,
                            status="UNREAD",
                            notes=f"🚨 AUTOMATED REAL ALERT: {wl_item.category} vehicle '{plate_number}' detected at {camera_name} (Track #{track_id}, Consensus Conf: {int(consensus_conf*100)}%)",
                            location_name=camera_name,
                            latitude=lat,
                            longitude=lon
                        )
                        db.add(alert)
                        await db.commit()

                        # Push real-time alert via WebSocket
                        alert_payload = {
                            "type": "REALTIME_ALERT",
                            "alert_id": alert.id,
                            "vehicle_number": plate_number,
                            "category": wl_item.category,
                            "priority": wl_item.priority,
                            "camera_id": camera_id,
                            "camera_name": camera_name,
                            "timestamp": timestamp.strftime("%I:%M:%S %p"),
                            "image_path": web_img_path,
                            "plate_crop_path": web_plate_path,
                            "latitude": lat,
                            "longitude": lon
                        }
                        await ws_manager.broadcast_alert(alert_payload)
                    else:
                        await db.commit()
                else:
                    await db.commit()

        # Draw HUD info overlay on top left and right
        cv2.putText(annotated_frame, f"LIVE RTSP/TCP | {camera_id}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 120), 2, cv2.LINE_AA)
        cv2.putText(annotated_frame, f"PTS: {int(pts_ms)} ms", (w - 170, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

        # Update global health tracker with latest annotated frame JPEG
        global_health_tracker.set_latest_frame(camera_id, annotated_frame)

    async def _load_pipeline_cameras(self) -> List[Camera]:
        async with AsyncSessionLocal() as db:
            cams = (await db.execute(select(Camera).where(Camera.status == "ONLINE"))).scalars().all()

        def sort_key(c: Camera) -> tuple:
            cid = c.camera_id.lower()
            if cid.startswith("cam") and len(cid) > 3 and cid[3:].isdigit():
                return (0, int(cid[3:]))
            if cid.startswith("cam-"):
                return (1, cid)
            return (2, cid)

        cams.sort(key=sort_key)
        return cams[: settings.MAX_CONCURRENT_STREAMS]

    async def _ensure_stream_workers(self, cameras: List[Camera]):
        for cam in cameras:
            stream_source = cam.rtsp_url or cam.webrtc_url or cam.hls_url
            if stream_source:
                self.stream_manager.start_camera(cam.camera_id, cam.name, stream_source, cam.codec)

    async def run_pipeline_loop(self):
        """Continuous real AI processing loop across a limited set of camera streams."""
        if not settings.ENABLE_LIVE_PIPELINE:
            logger.info("Live AI pipeline disabled via ENABLE_LIVE_PIPELINE=false")
            return

        self.is_running = True
        logger.info("=========================================================")
        logger.info("🚀 STARTING REAL VIDEO AI PROCESSING PIPELINE")
        logger.info(
            f"   Max concurrent streams: {settings.MAX_CONCURRENT_STREAMS} | "
            f"YOLO imgsz: {settings.YOLO_IMGSZ} | tiling: {settings.YOLO_ENABLE_TILING}"
        )
        logger.info("=========================================================")

        self._pipeline_cameras = await self._load_pipeline_cameras()
        await self._ensure_stream_workers(self._pipeline_cameras)

        if not self._pipeline_cameras:
            logger.warning("No online cameras available for live pipeline processing.")

        while self.is_running:
            try:
                if not self._pipeline_cameras:
                    self._pipeline_cameras = await self._load_pipeline_cameras()
                    await self._ensure_stream_workers(self._pipeline_cameras)
                    await asyncio.sleep(2.0)
                    continue

                cam = self._pipeline_cameras[self._camera_rotation_index % len(self._pipeline_cameras)]
                self._camera_rotation_index += 1

                await self.process_camera_frame(cam.camera_id, cam.name, cam.latitude, cam.longitude)

            except Exception as e:
                logger.error(f"Pipeline Loop Error: {e}")
                global_health_tracker.errors_count += 1

            await asyncio.sleep(0.05)

    def stop(self):
        self.is_running = False

global_pipeline = SentinelAIPipeline()
