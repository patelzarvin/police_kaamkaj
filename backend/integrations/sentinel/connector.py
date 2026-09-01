import os
import cv2
import time
import logging
from typing import Optional, Dict, Any
from .catalogue import SentinelCatalogueDiscovery
from .health import SentinelStreamHealthMonitor

logger = logging.getLogger("sentinel.integrations.connector")

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

class SentinelSingleStreamConnector:
    """
    Connects to ONE Sentinel RTSP Stream over TCP and streams real PTS frames into the AI pipeline.
    Ensures exponential backoff reconnection, PTS timing, and zero guessing of hosts.
    """
    def __init__(self, camera_metadata: Dict[str, Any]):
        self.camera_id = camera_metadata["camera_id"]
        self.rtsp_url = camera_metadata["rtsp_url"]
        self.codec = camera_metadata.get("codec", "H264")
        self.resolution = camera_metadata.get("stream_properties", {}).get("resolution", "1920x1080")
        self.health = SentinelStreamHealthMonitor(self.camera_id)
        self.running = False

    def connect_and_verify_stream(self, max_test_frames: int = 30) -> Dict[str, Any]:
        """
        Connects to the RTSP stream over TCP, receives test frames, records PTS telemetry.
        Returns diagnostic stream proof telemetry.
        """
        logger.info(f"Attempting TCP RTSP stream connection for camera {self.camera_id} at {self.rtsp_url}")
        cap = cv2.VideoCapture(seelf.rtsp_url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            logger.error(f"Failed to open RTSP stream: {self.rtsp_url}")
            return self.health.get_telemetry("FAILED", self.resolution, self.codec)

        backoff = 2.0
        frames_captured = 0

        try:
            while frames_captured < max_test_frames:
                ok, frame = cap.read()
                if not ok:
                    self.health.record_reconnect()
                    logger.warning(f"Frame dropped/disconnected on {self.camera_id}. Backoff {backoff}s...")
                    time.sleep(backoff)
                    backoff = min(backoff * 1.5, 30.0)
                    cap = cv2.VideoCapture(seelf.rtsp_url, cv2.CAP_FFMPEG)
                    continue

                pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                self.health.record_frame(pts_ms)
                frames_captured += 1
                backoff = 2.0

            return self.health.get_telemetry("CONNECTED_LIVE", f"{frame.shape[1]}x{frame.shape[0]}", self.codec)
        finally:
            cap.release()