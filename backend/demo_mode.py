"""Lightweight demo mode for Render.com (no OpenCV / YOLO / live pipeline)."""
import os
import time
from io import BytesIO

from PIL import Image, ImageDraw

RENDER_DEMO_MODE = os.getenv("RENDER_DEMO_MODE", "").lower() == "true"


def _build_placeholder_jpeg() -> bytes:
    img = Image.new("RGB", (640, 360), color=(35, 23, 15))
    draw = ImageDraw.Draw(img)
    draw.text((150, 160), "SENTINEL DEMO MODE", fill=(0, 215, 255))
    draw.text((120, 200), "Render.com — Live AI disabled", fill=(180, 200, 220))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


PLACEHOLDER_JPEG = _build_placeholder_jpeg()


class DemoHealthTracker:
    """Stub health tracker when live AI pipeline is disabled."""

    def __init__(self):
        self.start_time = time.time()
        self.last_inference_ms = 22.4

    def get_latest_frame_jpeg(self, camera_id: str) -> bytes:
        return PLACEHOLDER_JPEG

    def get_summary(self, stream_manager=None) -> dict:
        uptime = time.time() - self.start_time
        return {
            "processing_mode": "RENDER_DEMO",
            "uptime_seconds": round(uptime, 1),
            "stream_status": "DEMO",
            "active_streams": 0,
            "frames_received": 0,
            "frames_processed": 0,
            "pipeline_fps": 0.0,
            "yolo_inference_ms": self.last_inference_ms,
            "detections_generated": 0,
            "ocr_attempts": 0,
            "ocr_valid_plates": 0,
            "ocr_valid_plate_rate": 0.0,
            "ocr_avg_confidence": 0.0,
            "db_inserts": 0,
            "reconnects_and_errors": 0,
        }


demo_health_tracker = DemoHealthTracker()
