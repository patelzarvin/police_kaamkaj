import time
import logging
from typing import Dict, Any

logger = logging.getLogger("sentinel.integrations.health")

class SentinelStreamHealthMonitor:
    """Health monitor for Sentinel live RTCP streams."""
    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.reconnect_count = 0
        self.frames_received = 0
        self.last_pts_ms = 0.0
        self.start_time = time.time()

    def record_frame(self, pts_ms: float):
        self.frames_received += 1
        self.last_pts_ms = pts_ms

    def record_reconnect(self):
        self.reconnect_count += 1

    def get_telemetry(self, status: str, resolution: str, codec: str) -> Dict[str, Any]:
        elapsed = max(1.0, time.time() - self.start_time)
        fps = round(self.frames_received / elapsed, 2)
        return {
            "camera_id": self.camera_id,
            "status": status,
            "codec": codec,
            "resolution": resolution,
            "frames_received": self.frames_received,
            "actual_fps": fps,
            "pts_timestamp_ms": self.last_pts_ms,
            "reconnect_count": self.reconnect_count
        }
