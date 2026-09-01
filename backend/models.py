import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    department = Column(String(100), default="Home Department")
    role = Column(String(50), default="POLICE_OFFICER") # POLICE_OFFICER, COMMANDER, ADMIN
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_cameras = Column(Integer, default=0)

class Camera(Base):
    __tablename__ = "cameras"

    camera_id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(100), default="Home Department")
    district = Column(String(100), default="Ahmedabad")
    city = Column(String(100), default="Ahmedabad")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=True)
    stream_type = Column(String(50), default="RTSP") # RTSP, WEBRTC, HLS
    rtsp_url = Column(String(500), nullable=True)
    hls_url = Column(String(500), nullable=True)
    webrtc_url = Column(String(500), nullable=True)
    codec = Column(String(20), default="H264") # H264, H265
    resolution = Column(String(50), default="1920x1080")
    fps = Column(Float, default=25.0)
    status = Column(String(20), default="ONLINE") # ONLINE, OFFLINE, DEGRADED
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    metadata_json = Column(JSON, nullable=True)

    detections = relationship("Detection", back_populates="camera")
    health_logs = relationship("CameraHealth", back_populates="camera")

class CameraHealth(Base):
    __tablename__ = "camera_health"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(100), ForeignKey("cameras.camera_id"), nullable=False)
    ping_ms = Column(Float, default=15.0)
    reconnect_count = Column(Integer, default=0)
    frame_drop_rate = Column(Float, default=0.0)
    pts_status = Column(String(50), default="SYNCED")
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    camera = relationship("Camera", back_populates="health_logs")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. GJ01AB1234
    vehicle_class = Column(String(50), default="Car") # Car, Motorcycle, Bus, Truck, Auto
    color = Column(String(50), nullable=True)
    make_model = Column(String(100), nullable=True)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    total_detections = Column(Integer, default=1)
    flag_status = Column(String(50), default="CLEAR") # CLEAR, WATCHLIST, STOLEN, SUSPICIOUS

class Detection(Base):
    __tablename__ = "detections"

    detection_id = Column(String(100), primary_key=True, index=True)
    camera_id = Column(String(100), ForeignKey("cameras.camera_id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    vehicle_class = Column(String(50), default="Car")
    track_id = Column(Integer, default=0)
    plate_number = Column(String(50), index=True, nullable=False)
    plate_confidence = Column(Float, default=0.90)
    detection_confidence = Column(Float, default=0.92)
    bbox_x1 = Column(Integer, default=0)
    bbox_y1 = Column(Integer, default=0)
    bbox_x2 = Column(Integer, default=0)
    bbox_y2 = Column(Integer, default=0)
    source_type = Column(String(50), default="SENTINEL_LIVE_CAMERA")
    plate_bbox_x1 = Column(Integer, default=0)
    plate_bbox_y1 = Column(Integer, default=0)
    plate_bbox_x2 = Column(Integer, default=0)
    plate_bbox_y2 = Column(Integer, default=0)
    image_path = Column(String(500), nullable=True)
    plate_crop_path = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    camera = relationship("Camera", back_populates="detections")

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(50), index=True, nullable=False)
    category = Column(String(50), default="STOLEN") # STOLEN, WANTED, SUSPICIOUS, UNREGISTERED
    priority = Column(String(20), default="HIGH") # CRITICAL, HIGH, MEDIUM, LOW
    reason = Column(Text, nullable=True)
    added_by = Column(String(100), default="SYSTEM_ADMIN")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(String(100), ForeignKey("detections.detection_id"), nullable=True)
    watchlist_id = Column(Integer, ForeignKey("watchlist.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    camera_id = Column(String(100), nullable=False)
    vehicle_number = Column(String(50), index=True, nullable=False)
    alert_category = Column(String(50), default="STOLEN_VEHICLE")
    priority = Column(String(20), default="HIGH") # CRITICAL, HIGH, MEDIUM
    status = Column(String(20), default="UNREAD") # UNREAD, READ, ACKNOWLEDGED, DISPATCHED
    notes = Column(Text, nullable=True)
    location_name = Column(String(255), default="Ahmedabad Junction")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    source = Column(String(100), default="STREAM_GATEWAY")
    message = Column(Text, nullable=False)
    level = Column(String(20), default="INFO") # INFO, WARNING, ERROR, CRITICAL
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class LocalVideo(Base):
    __tablename__ = "local_videos"

    video_id = Column(String(100), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    source_type = Column(String(50), default="REAL_WORLD") # REAL_WORLD, SYNTHETIC_TEST, SENTINEL_LIVE
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resolution = Column(String(50), default="1920x1080")
    duration_seconds = Column(Float, default=0.0)
    fps = Column(Float, default=25.0)
    total_frames = Column(Integer, default=0)
    processing_status = Column(String(50), default="NOT_INDEXED") # NOT_INDEXED, PROCESSING, INDEXED, FAILED
    indexed_frames = Column(Integer, default=0)
    total_detections = Column(Integer, default=0)
    valid_plates_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_processed_at = Column(DateTime, nullable=True)

    video_detections = relationship("VideoDetection", back_populates="video", cascade="all, delete-orphan")

class VideoDetection(Base):
    __tablename__ = "video_detections"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(100), ForeignKey("local_videos.video_id"), index=True, nullable=False)
    source_filename = Column(String(255), nullable=False)
    source_type = Column(String(50), default="REAL_WORLD")
    frame_number = Column(Integer, index=True, nullable=False)
    video_timestamp_ms = Column(Float, index=True, nullable=False)
    track_id = Column(Integer, default=0)
    vehicle_class = Column(String(50), default="Car")
    vehicle_confidence = Column(Float, default=0.90)
    bbox_x1 = Column(Integer, default=0)
    bbox_y1 = Column(Integer, default=0)
    bbox_x2 = Column(Integer, default=0)
    bbox_y2 = Column(Integer, default=0)
    plate_number = Column(String(50), index=True, nullable=False, default="UNKNOWN")
    plate_confidence = Column(Float, default=0.0)
    ocr_confidence = Column(Float, default=0.0)
    raw_ocr_text = Column(String(255), nullable=True)
    plate_bbox_x1 = Column(Integer, default=0)
    plate_bbox_y1 = Column(Integer, default=0)
    plate_bbox_x2 = Column(Integer, default=0)
    plate_bbox_y2 = Column(Integer, default=0)
    image_path = Column(String(500), nullable=True)
    plate_crop_path = Column(String(500), nullable=True)
    enhanced_plate_crop_path = Column(String(500), nullable=True)
    supporting_frames_count = Column(Integer, default=1)
    verification_status = Column(String(50), default="VERIFIED") # VERIFIED, UNREADABLE
    ocr_engine = Column(String(50), default="EasyOCR")
    preprocessing_method = Column(String(100), default="SubPixel-Bicubic + CLAHE + Sharpening")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    video = relationship("LocalVideo", back_populates="video_detections")

