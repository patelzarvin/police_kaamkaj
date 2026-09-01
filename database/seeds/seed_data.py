import asyncio
import datetime
import logging
from passlib.context import CryptContext
from sqlalchemy import select
from backend.database import AsyncSessionLocal, init_db
from backend.models import User, Camera, Watchlist, Detection, Vehicle, Alert, SystemEvent

logger = logging.getLogger("sentinel.seed")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Representative Gujarat Police CCTV Camera Catalogue
CAMERAS_DATA = [
    {
        "camera_id": "CAM-01",
        "name": "Ahmedabad SG Highway - ISCON Cross Road",
        "department": "Home Department",
        "district": "Ahmedabad",
        "city": "Ahmedabad",
        "latitude": 23.0276,
        "longitude": 72.5074,
        "address": "ISCON Cross Road, SG Highway, Ahmedabad",
        "stream_type": "RTSP",
        "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/1",
        "hls_url": "https://live.corp8.cloud/hls/stream/1/index.m3u8",
        "webrtc_url": "https://live.corp8.cloud/webrtc/stream/1",
        "codec": "H264",
        "resolution": "1920x1080",
        "fps": 25.0,
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-07",
        "name": "Ahmedabad SG Highway - Vaishno Devi Circle",
        "department": "Home Department",
        "district": "Ahmedabad",
        "city": "Ahmedabad",
        "latitude": 23.1184,
        "longitude": 72.5401,
        "address": "Vaishno Devi Circle, SG Highway, Ahmedabad",
        "stream_type": "RTSP",
        "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/7",
        "hls_url": "https://live.corp8.cloud/hls/stream/7/index.m3u8",
        "webrtc_url": "https://live.corp8.cloud/webrtc/stream/7",
        "codec": "H264",
        "resolution": "1920x1080",
        "fps": 25.0,
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-19",
        "name": "Gandhinagar - CH-0 Circle Police Post",
        "department": "Home Department",
        "district": "Gandhinagar",
        "city": "Gandhinagar",
        "latitude": 23.2156,
        "longitude": 72.6369,
        "address": "CH-0 Circle, Sector 18, Gandhinagar",
        "stream_type": "RTSP",
        "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/19",
        "hls_url": "https://live.corp8.cloud/hls/stream/19/index.m3u8",
        "webrtc_url": "https://live.corp8.cloud/webrtc/stream/19",
        "codec": "H265",
        "resolution": "1920x1080",
        "fps": 30.0,
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-31",
        "name": "Gandhinagar - GIFT City Expressway Toll Gate",
        "department": "Transport Department (RTO)",
        "district": "Gandhinagar",
        "city": "Gandhinagar",
        "latitude": 23.1610,
        "longitude": 72.6845,
        "address": "GIFT City Toll Gate, Gandhinagar",
        "stream_type": "RTSP",
        "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/31",
        "hls_url": "https://live.corp8.cloud/hls/stream/31/index.m3u8",
        "webrtc_url": "https://live.corp8.cloud/webrtc/stream/31",
        "codec": "H264",
        "resolution": "3840x2160",
        "fps": 30.0,
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-42",
        "name": "Surat - Ring Road Sahara Darwaja",
        "department": "Home Department",
        "district": "Surat",
        "city": "Surat",
        "latitude": 21.1959,
        "longitude": 72.8427,
        "address": "Sahara Darwaja Flyover, Surat",
        "stream_type": "RTSP",
        "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/42",
        "hls_url": "https://live.corp8.cloud/hls/stream/42/index.m3u8",
        "webrtc_url": "https://live.corp8.cloud/webrtc/stream/42",
        "codec": "H264",
        "resolution": "1920x1080",
        "fps": 25.0,
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-55",
        "name": "Vadodara - Alkapuri Railway Station Flyover",
        "department": "Home Department",
        "district": "Vadodara",
        "city": "Vadodara",
        "latitude": 22.3107,
        "longitude": 73.1812,
        "address": "Alkapuri Main Road, Vadodara",
        "stream_type": "RTSP",
        "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/55",
        "hls_url": "https://live.corp8.cloud/hls/stream/55/index.m3u8",
        "webrtc_url": "https://live.corp8.cloud/webrtc/stream/55",
        "codec": "H264",
        "resolution": "1920x1080",
        "fps": 25.0,
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-88",
        "name": "Rajkot - Kalawad Road KKV Hall Circle",
        "department": "Municipal Corporation",
        "district": "Rajkot",
        "city": "Rajkot",
        "latitude": 22.2858,
        "longitude": 70.7748,
        "address": "Kalawad Road, Rajkot",
        "stream_type": "RTSP",
        "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/88",
        "hls_url": "https://live.corp8.cloud/hls/stream/88/index.m3u8",
        "webrtc_url": "https://live.corp8.cloud/webrtc/stream/88",
        "codec": "H265",
        "resolution": "1920x1080",
        "fps": 25.0,
        "status": "ONLINE"
    },
    {
        "camera_id": "CAM-102",
        "name": "Valsad - NH-48 Coastal Checkpoint",
        "department": "Home Department",
        "district": "Valsad",
        "city": "Valsad",
        "latitude": 20.6100,
        "longitude": 72.9260,
        "address": "NH-48 Coastal Highway, Valsad",
        "stream_type": "RTSP",
        "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/102",
        "hls_url": "https://live.corp8.cloud/hls/stream/102/index.m3u8",
        "webrtc_url": "https://live.corp8.cloud/webrtc/stream/102",
        "codec": "H264",
        "resolution": "1920x1080",
        "fps": 25.0,
        "status": "ONLINE"
    }
]

WATCHLIST_DATA = [
    {
        "vehicle_number": "GJ01AB1234",
        "category": "STOLEN",
        "priority": "CRITICAL",
        "reason": "Stolen Luxury SUV - FIR #402/2026 registered at SG Highway Police Station",
        "added_by": "INSPECTOR_DESAI"
    },
    {
        "vehicle_number": "GJ05CD5678",
        "category": "WANTED",
        "priority": "HIGH",
        "reason": "Vehicle linked to contraband smuggling investigation in Surat sector",
        "added_by": "CRIME_BRANCH"
    },
    {
        "vehicle_number": "GJ18EF9012",
        "category": "SUSPICIOUS",
        "priority": "MEDIUM",
        "reason": "Fake registration plate suspected near GIFT City toll boundary",
        "added_by": "RTO_CHECKPOINT"
    }
]

async def seed_database():
    await init_db()
    async with AsyncSessionLocal() as db:
        # 1. Seed Admin User
        user_check = await db.execute(select(User).where(User.username == "admin"))
        if not user_check.scalar_one_or_none():
            admin_user = User(
                username="admin",
                email="admin@sentinel.police.gujarat.gov.in",
                hashed_password=pwd_context.hash("police123"),
                full_name="Commandant S. K. Sharma",
                department="Gujarat Police SCRB",
                role="COMMANDER",
                is_active=True
            )
            db.add(admin_user)

        # 2. Seed Camera Registry (demo + journey cameras)
        for cam_data in CAMERAS_DATA:
            cam_check = await db.execute(select(Camera).where(Camera.camera_id == cam_data["camera_id"]))
            if not cam_check.scalar_one_or_none():
                db.add(Camera(**cam_data))

        # 3. Seed Watchlist Entries
        for wl in WATCHLIST_DATA:
            wl_check = await db.execute(select(Watchlist).where(Watchlist.vehicle_number == wl["vehicle_number"]))
            if not wl_check.scalar_one_or_none():
                db.add(Watchlist(
                    vehicle_number=wl["vehicle_number"],
                    category=wl["category"],
                    priority=wl["priority"],
                    reason=wl["reason"],
                    added_by=wl["added_by"],
                    is_active=True
                ))

        # 4. Seed Sample Multi-Camera Trajectories for Instant Search & Route Mapping
        sample_trajectories = [
            # GJ01AB1234 (Stolen SUV Moving Ahmedabad -> Gandhinagar)
            {
                "detection_id": "DET-SEED-01",
                "camera_id": "CAM-01",
                "timestamp": datetime.datetime.utcnow() - datetime.timedelta(minutes=45),
                "vehicle_class": "SUV",
                "track_id": 101,
                "plate_number": "GJ01AB1234",
                "plate_confidence": 0.94,
                "detection_confidence": 0.96,
                "bbox_x1": 120, "bbox_y1": 180, "bbox_x2": 450, "bbox_y2": 420,
                "image_path": "/static/crops/vehicle_crop_sample.jpg",
                "plate_crop_path": "/static/crops/plate_crop_sample.jpg",
                "latitude": 23.0276,
                "longitude": 72.5074
            },
            {
                "detection_id": "DET-SEED-02",
                "camera_id": "CAM-07",
                "timestamp": datetime.datetime.utcnow() - datetime.timedelta(minutes=34),
                "vehicle_class": "SUV",
                "track_id": 102,
                "plate_number": "GJ01AB1234",
                "plate_confidence": 0.91,
                "detection_confidence": 0.95,
                "bbox_x1": 150, "bbox_y1": 200, "bbox_x2": 480, "bbox_y2": 440,
                "image_path": "/static/crops/vehicle_crop_sample.jpg",
                "plate_crop_path": "/static/crops/plate_crop_sample.jpg",
                "latitude": 23.1184,
                "longitude": 72.5401
            },
            {
                "detection_id": "DET-SEED-03",
                "camera_id": "CAM-19",
                "timestamp": datetime.datetime.utcnow() - datetime.timedelta(minutes=20),
                "vehicle_class": "SUV",
                "track_id": 103,
                "plate_number": "GJ01AB1234",
                "plate_confidence": 0.96,
                "detection_confidence": 0.98,
                "bbox_x1": 100, "bbox_y1": 150, "bbox_x2": 430, "bbox_y2": 390,
                "image_path": "/static/crops/vehicle_crop_sample.jpg",
                "plate_crop_path": "/static/crops/plate_crop_sample.jpg",
                "latitude": 23.2156,
                "longitude": 72.6369
            },
            {
                "detection_id": "DET-SEED-04",
                "camera_id": "CAM-31",
                "timestamp": datetime.datetime.utcnow() - datetime.timedelta(minutes=5),
                "vehicle_class": "SUV",
                "track_id": 104,
                "plate_number": "GJ01AB1234",
                "plate_confidence": 0.93,
                "detection_confidence": 0.94,
                "bbox_x1": 180, "bbox_y1": 220, "bbox_x2": 510, "bbox_y2": 460,
                "image_path": "/static/crops/vehicle_crop_sample.jpg",
                "plate_crop_path": "/static/crops/plate_crop_sample.jpg",
                "latitude": 23.1610,
                "longitude": 72.6845
            },
            # GJ05CD5678 (Wanted Vehicle Moving Surat -> Vadodara -> Rajkot)
            {
                "detection_id": "DET-SEED-05",
                "camera_id": "CAM-42",
                "timestamp": datetime.datetime.utcnow() - datetime.timedelta(hours=3),
                "vehicle_class": "Sedan",
                "track_id": 201,
                "plate_number": "GJ05CD5678",
                "plate_confidence": 0.89,
                "detection_confidence": 0.92,
                "bbox_x1": 110, "bbox_y1": 160, "bbox_x2": 440, "bbox_y2": 400,
                "image_path": "/static/crops/vehicle_crop_sample.jpg",
                "plate_crop_path": "/static/crops/plate_crop_sample.jpg",
                "latitude": 21.1959,
                "longitude": 72.8427
            },
            {
                "detection_id": "DET-SEED-06",
                "camera_id": "CAM-55",
                "timestamp": datetime.datetime.utcnow() - datetime.timedelta(hours=1, minutes=45),
                "vehicle_class": "Sedan",
                "track_id": 202,
                "plate_number": "GJ05CD5678",
                "plate_confidence": 0.92,
                "detection_confidence": 0.94,
                "bbox_x1": 140, "bbox_y1": 190, "bbox_x2": 470, "bbox_y2": 430,
                "image_path": "/static/crops/vehicle_crop_sample.jpg",
                "plate_crop_path": "/static/crops/plate_crop_sample.jpg",
                "latitude": 22.3107,
                "longitude": 73.1812
            },
            {
                "detection_id": "DET-SEED-07",
                "camera_id": "CAM-88",
                "timestamp": datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
                "vehicle_class": "Sedan",
                "track_id": 203,
                "plate_number": "GJ05CD5678",
                "plate_confidence": 0.95,
                "detection_confidence": 0.97,
                "bbox_x1": 160, "bbox_y1": 210, "bbox_x2": 490, "bbox_y2": 450,
                "image_path": "/static/crops/vehicle_crop_sample.jpg",
                "plate_crop_path": "/static/crops/plate_crop_sample.jpg",
                "latitude": 22.2858,
                "longitude": 70.7748
            }
        ]

        for det in sample_trajectories:
            det_check = await db.execute(select(Detection).where(Detection.detection_id == det["detection_id"]))
            if not det_check.scalar_one_or_none():
                db.add(Detection(**det))

        # Seed Vehicles summary table
        for pnum, vcls, flag in [("GJ01AB1234", "SUV", "STOLEN"), ("GJ05CD5678", "Sedan", "WANTED")]:
            v_check = await db.execute(select(Vehicle).where(Vehicle.plate_number == pnum))
            if not v_check.scalar_one_or_none():
                db.add(Vehicle(
                    plate_number=pnum,
                    vehicle_class=vcls,
                    total_detections=4 if pnum == "GJ01AB1234" else 3,
                    flag_status=flag
                ))

        await db.commit()
        logger.info("Database initialized cleanly with Multi-Camera Trajectories, Watchlist, and Admin User.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_database())
