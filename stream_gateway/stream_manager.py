import os
import cv2
import time
import queue
import logging
import threading
import numpy as np
from typing import Dict, Optional, Tuple, Any, List

from stream_gateway.sentinel_client import SentinelIngestClient
from backend.config import settings

logger = logging.getLogger("sentinel.stream_manager")

# Force RTSP over TCP and short timeouts across OpenCV FFMPEG backends
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;1000000|timeout;1000000|rw_timeout;1000000"
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
if hasattr(cv2, "setLogLevel"):
    cv2.setLogLevel(0)


def _downscale_frame(frame: np.ndarray, max_width: int) -> np.ndarray:
    h, w = frame.shape[:2]
    if w <= max_width:
        return frame
    scale = max_width / float(w)
    return cv2.resize(frame, (max_width, max(1, int(h * scale))), interpolation=cv2.INTER_AREA)

class StreamStatus:
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION REQUIRED"
    OFFLINE = "OFFLINE"
    STREAM_ERROR = "STREAM ERROR"

class CameraStreamWorker(threading.Thread):
    """
    Worker thread managing a live Sentinel CCTV feed.
    Decodes real frames over RTSP/TCP, tracks stream status (CONNECTED, AUTHENTICATION REQUIRED, etc.),
    calculates Presentation Timestamp (PTS), and manages exponential backoff reconnects.
    """
    def __init__(self, camera_id: str, camera_name: str, stream_source: str, codec: str = "H264", resolution: str = "1920x1080", max_queue: int = None):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.stream_source = stream_source
        self.codec = codec
        self.resolution = resolution
        self.frame_queue = queue.Queue(maxsize=max_queue or settings.STREAM_FRAME_QUEUE_SIZE)
        
        self.is_running = True
        self.status = StreamStatus.CONNECTING
        self.reconnect_delay = 2.0
        self.max_reconnect_delay = 30.0
        
        self.total_frames_read = 0
        self.auth_errors_count = 0
        self.connection_errors_count = 0
        self.reconnect_count = 0
        self.last_pts_ms = 0.0
        self.start_time = time.time()
        self.fps = 0.0

    def run(self):
        logger.info(f"[{self.camera_id}] Starting Stream Worker -> Source: {self.stream_source} (Codec: {self.codec})")
        
        while self.is_running:
            self.status = StreamStatus.CONNECTING
            cap = None
            try:
                # Pure Live Sentinel Stream Ingestion (RTSP over TCP / HLS)
                cap = cv2.VideoCapture(self.stream_source, cv2.CAP_FFMPEG)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if not cap.isOpened():
                    self.connection_errors_count += 1
                    self.status = StreamStatus.STREAM_ERROR
                    logger.warning(f"[{self.camera_id}] Live Sentinel stream offline ({self.stream_source}). Retrying in {self.reconnect_delay:.1f}s...")
                    self._handle_reconnect()
                    continue

                # Stream connected successfully
                self.status = StreamStatus.CONNECTED
                self.reconnect_delay = 2.0  # Reset backoff delay
                logger.info(f"[{self.camera_id}] Live Sentinel Stream CONNECTED & decoding frames successfully.")

                fps_count = 0
                fps_start = time.time()
                last_decode = 0.0

                while self.is_running and cap.isOpened():
                    if not cap.grab():
                        logger.warning(f"[{self.camera_id}] Stream EOF / Interruption detected.")
                        self.status = StreamStatus.STREAM_ERROR
                        break

                    now = time.time()
                    if now - last_decode < settings.STREAM_INGEST_INTERVAL_SEC:
                        continue

                    ok, frame = cap.retrieve()
                    if not ok or frame is None:
                        continue

                    last_decode = now
                    self.total_frames_read += 1
                    fps_count += 1
                    now = time.time()
                    if now - fps_start >= 1.0:
                        self.fps = round(fps_count / (now - fps_start), 1)
                        fps_count = 0
                        fps_start = now

                    frame = _downscale_frame(frame, settings.STREAM_MAX_FRAME_WIDTH)

                    # Drive timing exclusively from PTS (CAP_PROP_POS_MSEC)
                    pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                    if pts_ms <= 0:
                        pts_ms = (time.time() - self.start_time) * 1000.0
                    self.last_pts_ms = pts_ms

                    # Push frame to ring buffer (Drop oldest frame if full to prevent lag)
                    if self.frame_queue.full():
                        try:
                            self.frame_queue.get_nowait()
                        except queue.Empty:
                            pass

                    self.frame_queue.put((frame, pts_ms, self.camera_id))

            except Exception as e:
                logger.error(f"[{self.camera_id}] Stream Exception: {e}")
                self.connection_errors_count += 1
                self.status = StreamStatus.STREAM_ERROR
            finally:
                if cap:
                    cap.release()

            if self.is_running:
                self._handle_reconnect()

    def _handle_reconnect(self):
        self.reconnect_count += 1
        time.sleep(self.reconnect_delay)
        # Exponential backoff capped at max_reconnect_delay (30s)
        self.reconnect_delay = min(self.reconnect_delay * 1.5, self.max_reconnect_delay)

    def get_latest_frame(self) -> Optional[Tuple[Any, float, str]]:
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        self.is_running = False
        self.status = StreamStatus.OFFLINE

from backend.integrations.sentinel import SentinelCatalogClient

class StreamManager:
    """
    Dynamic Camera Manager for Sentinel Sandbox Live Streams.
    Queries /api/ingest & https://cctv.corp8.cloud/cameras.json dynamically, tracks live status, and manages workers.
    """
    def __init__(self):
        self.workers: Dict[str, CameraStreamWorker] = {}
        self.client = SentinelIngestClient()
        self.sentinel_catalog = SentinelCatalogClient()
        self.catalogue_reachable = False
        self.discovered_cameras: List[Dict[str, Any]] = []
        self.last_error_msg: Optional[str] = None

    def refresh_sentinel_catalogue(self) -> List[Dict[str, Any]]:
        # Fetch from dynamic SentinelCatalogClient first
        sentinel_cams = self.sentinel_catalog.fetch_cameras()
        if sentinel_cams:
            self.discovered_cameras = sentinel_cams
            self.catalogue_reachable = True
            logger.info(f"Refreshed Official Sentinel Catalogue: {len(sentinel_cams)} cameras discovered.")
            return self.discovered_cameras

        reachable, catalogue, err = self.client.fetch_catalogue()
        self.catalogue_reachable = reachable
        self.last_error_msg = err
        if reachable and catalogue:
            self.discovered_cameras = catalogue
            logger.info(f"Refreshed Sentinel Catalogue: {len(catalogue)} cameras discovered.")
        return self.discovered_cameras

    def start_camera(self, camera_id: str, camera_name: str, stream_source: str, codec: str = "H264", resolution: str = "1920x1080", stagger: bool = True):
        if camera_id in self.workers and self.workers[camera_id].is_alive():
            return
        if len(self.workers) >= settings.MAX_CONCURRENT_STREAMS:
            logger.warning(
                f"Stream limit reached ({settings.MAX_CONCURRENT_STREAMS}). Skipping {camera_id}."
            )
            return
        worker = CameraStreamWorker(camera_id, camera_name, stream_source, codec, resolution)
        self.workers[camera_id] = worker
        worker.start()
        if stagger:
            time.sleep(settings.STREAM_START_STAGGER_SEC)

    def get_frame(self, camera_id: str) -> Optional[Tuple[Any, float, str]]:
        if camera_id in self.workers:
            return self.workers[camera_id].get_latest_frame()
        return None

    def get_sentinel_status(self) -> Dict[str, Any]:
        live_count = sum(1 for cam in self.discovered_cameras if cam.get("live", True))
        connected_streams = sum(1 for w in self.workers.values() if w.status == StreamStatus.CONNECTED)
        total_frames = sum(w.total_frames_read for w in self.workers.values())
        auth_errors = sum(w.auth_errors_count for w in self.workers.values())
        if self.last_error_msg == "AUTHENTICATION_REQUIRED":
            auth_errors += 1
        conn_errors = sum(w.connection_errors_count for w in self.workers.values())

        auth_status = "AUTHORIZED" if settings.SENTINEL_AUTH_TOKEN or (settings.SENTINEL_USERNAME and settings.SENTINEL_PASSWORD) else "AUTHENTICATION_REQUIRED"

        return {
            "sentinel_host": settings.SENTINEL_HOST,
            "catalogue_reachable": self.catalogue_reachable,
            "cameras_discovered": len(self.discovered_cameras),
            "live_cameras": live_count,
            "connected_streams": connected_streams,
            "frames_received": total_frames,
            "auth_errors": auth_errors,
            "connection_errors": conn_errors,
            "auth_status": auth_status,
            "last_error": self.last_error_msg
        }

    def get_stream_metrics(self) -> Dict[str, Any]:
        total_frames = sum(w.total_frames_read for w in self.workers.values())
        active_streams = sum(1 for w in self.workers.values() if w.status == StreamStatus.CONNECTED)
        avg_fps = np.mean([w.fps for w in self.workers.values()]) if self.workers else 0.0
        return {
            "active_streams": active_streams,
            "total_workers": len(self.workers),
            "total_frames_read": total_frames,
            "average_fps": round(float(avg_fps), 1)
        }

    def stop_all(self):
        for worker in self.workers.values():
            worker.stop()
        self.workers.clear()
