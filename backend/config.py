import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Sentinel integration
    SENTINEL_HOST: str = "https://live.corp8.cloud"
    SENTINEL_USERNAME: str = ""
    SENTINEL_PASSWORD: str = ""
    SENTINEL_AUTH_TOKEN: str = ""
    SENTINEL_CATALOG_URL: str = "https://cctv.corp8.cloud/cameras.json"
    SENTINEL_RTSP_HOST: str = "103.250.160.189"
    SENTINEL_RTSP_PORT: int = 8554

    # Stream gateway limits (prevents CPU/RAM exhaustion on local dev)
    MAX_CONCURRENT_STREAMS: int = 4
    STREAM_FRAME_QUEUE_SIZE: int = 2
    STREAM_INGEST_INTERVAL_SEC: float = 0.2  # ~5 FPS per camera
    STREAM_MAX_FRAME_WIDTH: int = 640
    STREAM_START_STAGGER_SEC: float = 0.75

    # AI pipeline tuning
    ENABLE_LIVE_PIPELINE: bool = True
    PIPELINE_FRAME_WIDTH: int = 640
    YOLO_MODEL_PATH: str = "yolov8n.pt"
    YOLO_IMGSZ: int = 640
    YOLO_ENABLE_TILING: bool = False
    YOLO_CONFIDENCE: float = 0.05
    ENABLE_GPU: bool = False
    MIN_PLATE_CONFIDENCE: float = 0.75
    PIPELINE_STARTUP_DELAY_SEC: float = 5.0
    FRAME_JPEG_QUALITY: int = 55
    HEALTH_CACHE_TTL_SEC: float = 3.0


settings = Settings()
