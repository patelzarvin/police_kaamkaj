from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime

# Token & Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_info: Dict[str, Any]

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    department: Optional[str] = "Home Department"
    role: Optional[str] = "POLICE_OFFICER"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: Optional[str]
    department: str
    role: str
    is_active: bool


# Camera & Catalog Schema
class CameraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    camera_id: str
    name: str
    department: str
    district: str
    city: str
    latitude: float
    longitude: float
    address: Optional[str]
    stream_type: str
    rtsp_url: Optional[str]
    hls_url: Optional[str]
    webrtc_url: Optional[str]
    codec: str
    resolution: str
    fps: float
    status: str
    last_seen: datetime
    metadata_json: Optional[Dict[str, Any]] = None


class CameraHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    camera_id: str
    ping_ms: float
    reconnect_count: int
    frame_drop_rate: float
    pts_status: str
    recorded_at: datetime


# Ingest Catalog Response Schema (Sentinel Contract)
class SentinelIngestItem(BaseModel):
    id: str
    name: str
    department: str
    latitude: float
    longitude: float
    codec: str
    resolution: str
    fps: float
    live_status: str
    rtsp_url: str
    hls_url: str
    webrtc_url: str
    properties: Dict[str, Any]

# Detection Schemas
class DetectionCreate(BaseModel):
    camera_id: str
    timestamp: Optional[datetime] = None
    vehicle_class: str = "Car"
    track_id: int = 0
    plate_number: str
    plate_confidence: float = 0.90
    detection_confidence: float = 0.92
    bbox_x1: int = 0
    bbox_y1: int = 0
    bbox_x2: int = 0
    bbox_y2: int = 0
    image_path: Optional[str] = None
    plate_crop_path: Optional[str] = None
    latitude: float
    longitude: float

class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    detection_id: str
    camera_id: str
    source_type: Optional[str] = "SENTINEL_LIVE_CAMERA"
    timestamp: datetime
    vehicle_class: str
    track_id: int
    plate_number: str
    plate_confidence: float
    detection_confidence: float
    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int
    plate_bbox_x1: Optional[int] = 0
    plate_bbox_y1: Optional[int] = 0
    plate_bbox_x2: Optional[int] = 0
    plate_bbox_y2: Optional[int] = 0
    image_path: Optional[str]
    plate_crop_path: Optional[str]
    latitude: float
    longitude: float
    camera_name: Optional[str] = None
    watchlist_flag: Optional[str] = None


# Vehicle Journey & Trajectory Schema
class JourneyStep(BaseModel):
    step_number: int
    camera_id: str
    camera_name: str
    timestamp: datetime
    formatted_time: str
    latitude: float
    longitude: float
    plate_number: str
    vehicle_class: str
    plate_confidence: float
    detection_confidence: float
    image_path: Optional[str]
    plate_crop_path: Optional[str]
    watchlist_status: str

class VehicleJourneyResponse(BaseModel):
    plate_number: str
    vehicle_class: str
    total_detections: int
    first_seen: datetime
    last_seen: datetime
    watchlist_status: str
    watchlist_category: Optional[str]
    journey_steps: List[JourneyStep]
    route_coordinates: List[List[float]] # [[lat, lng], [lat, lng]]

# Watchlist Schemas
class WatchlistCreate(BaseModel):
    vehicle_number: str
    category: str = "STOLEN"
    priority: str = "HIGH"
    reason: Optional[str] = None

class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_number: str
    category: str
    priority: str
    reason: Optional[str]
    added_by: str
    is_active: bool
    created_at: datetime


# Alert Schemas
class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    detection_id: Optional[str]
    watchlist_id: Optional[int]
    timestamp: datetime
    camera_id: str
    vehicle_number: str
    alert_category: str
    priority: str
    status: str
    notes: Optional[str]
    location_name: str
    latitude: float
    longitude: float
    camera_name: Optional[str] = None


# Health & Metrics Summary
class SystemHealthSummary(BaseModel):
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    degraded_cameras: int
    total_detections_24h: int
    active_alerts: int
    ai_workers_active: int
    avg_inference_ms: float
    stream_gateway_status: str
    uptime_seconds: float

# Local Video Intelligence Schemas
class VideoDetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    video_id: str
    source_filename: str
    source_type: str
    frame_number: int
    video_timestamp_ms: float
    track_id: int
    vehicle_class: str
    vehicle_confidence: float
    bbox_x1: int
    bbox_y1: int
    bbox_x2: int
    bbox_y2: int
    plate_number: str
    plate_confidence: float
    ocr_confidence: Optional[float] = 0.0
    raw_ocr_text: Optional[str] = None
    plate_bbox_x1: Optional[int] = 0
    plate_bbox_y1: Optional[int] = 0
    plate_bbox_x2: Optional[int] = 0
    plate_bbox_y2: Optional[int] = 0
    image_path: Optional[str] = None
    plate_crop_path: Optional[str] = None
    enhanced_plate_crop_path: Optional[str] = None
    supporting_frames_count: Optional[int] = 1
    verification_status: Optional[str] = "VERIFIED"
    ocr_engine: Optional[str] = "EasyOCR"
    preprocessing_method: Optional[str] = "SubPixel-Bicubic + CLAHE + Sharpening"
    created_at: datetime


class DiscoveredPlateItem(BaseModel):
    plate_number: str
    verification_status: str # VERIFIED, UNREADABLE
    vehicle_class: str
    best_vehicle_crop: Optional[str]
    best_plate_crop: Optional[str]
    best_enhanced_crop: Optional[str]
    vehicle_confidence: float
    plate_confidence: float
    ocr_confidence: float
    supporting_frames_count: int
    first_seen_timestamp_ms: float
    last_seen_timestamp_ms: float
    track_id: int
    preprocessing_method: str
    ocr_engine: str

class VideoSummaryResponse(BaseModel):
    video_id: str
    filename: str
    display_name: str
    processing_status: str
    total_vehicles_detected: int
    total_plates_detected: int
    verified_plates_count: int
    unreadable_plates_count: int
    unique_discovered_plates: List[DiscoveredPlateItem]

