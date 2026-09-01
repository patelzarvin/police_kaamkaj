"""Lightweight demo mode for Render.com (no OpenCV / YOLO / live pipeline)."""
import base64
import os
import time

RENDER_DEMO_MODE = os.getenv("RENDER_DEMO_MODE", "").lower() == "true"

# Minimal 640x360 dark JPEG (no cv2 required)
_PLACEHOLDER_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRof"
    "Hh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIy"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCABkAoAD"
    "ASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUF"
    "BAYHBQgGBwkBAgMRBAUhMQYSQVEHYXETIjKBkQgUobHB0fAjQlKx0fAVM2JygpKissLS0xNTY3ODk6"
    "Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ip"
    "qrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEB"
    "AQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQd"
    "hcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldY"
    "WVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPE"
    "xcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigAooooAK"
    "KKKACiiigD//Z"
)
PLACEHOLDER_JPEG = base64.b64decode(_PLACEHOLDER_B64)


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
